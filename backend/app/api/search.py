from fastapi import (
    APIRouter,
    Depends,
    Query,
)

from sqlalchemy import bindparam, select, text, literal_column, Float, exists, func

from app.services.search_snippet import (
    create_snippet,
    highlight_text,
)

import math

from sqlalchemy.sql.functions import GenericFunction
from sqlalchemy.ext.compiler import compiles

from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_password_changed

from app.services.deposit_access import is_global_admin

from app.models.user import User

from app.models.document import (
    Document,
)

from app.models.document import (
    DocumentPage,
)

from app.models.document import (
    DocumentChunk,
)

from app.models.deposit_access import (
    DepositAccess,
)

from app.models.group_member import (
    GroupMember,
)

from app.schemas.search import (
    DocumentSearchResponse,
    DocumentSearchResult,
)

router = APIRouter()


class MatchAgainst(
    GenericFunction,
):

    type = Float

    inherit_cache = True

    name = "match_against"


@compiles(
    MatchAgainst,
    "mysql",
)
def compile_match_against(
    element,
    compiler,
    **kwargs,
):

    content = compiler.process(
        element.clauses.clauses[0],
        **kwargs,
    )

    query = compiler.process(
        element.clauses.clauses[1],
        **kwargs,
    )

    return f"MATCH({content}) " f"AGAINST({query} IN BOOLEAN MODE)"


@router.get(
    "/documents",
    response_model=DocumentSearchResponse,
)
def search_documents(
    q: str = Query(
        min_length=1,
        max_length=500,
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(
        get_db,
    ),
    current_user: User = Depends(
        require_password_changed,
    ),
):
    query = q.strip()

    offset = (page - 1) * page_size

    if not query:

        return DocumentSearchResponse(
            query=q,
            results=[],
        )

    relevance_expression = MatchAgainst(
        DocumentChunk.content,
        bindparam(
            "search_query",
            query,
        ),
    )

    statement = (
        select(
            Document.id.label(
                "document_id",
            ),
            Document.title.label(
                "document_name",
            ),
            DocumentPage.id.label(
                "page_id",
            ),
            DocumentPage.page_number,
            DocumentChunk.id.label(
                "chunk_id",
            ),
            DocumentChunk.content,
            relevance_expression.label(
                "relevance",
            ),
        )
        .join(
            DocumentPage,
            DocumentPage.document_id == Document.id,
        )
        .join(
            DocumentChunk,
            DocumentChunk.page_id == DocumentPage.id,
        )
        .where(
            relevance_expression > 0,
        )
        .params(
            search_query=query,
        )
    )

    if not is_global_admin(db=db, user=current_user):

        statement = (
            statement.join(
                DepositAccess,
                DepositAccess.deposit_id == Document.deposit_id,
            )
            .join(
                GroupMember,
                GroupMember.group_id == DepositAccess.group_id,
            )
            .where(
                GroupMember.user_id == current_user.id,
            )
        )

    statement = (
        statement.order_by(
            relevance_expression.desc(),
        )
        .offset(
            offset,
        )
        .limit(
            page_size,
        )
    )

    rows = db.execute(
        statement,
    ).all()

    results = []

    for row in rows:

        snippet = create_snippet(
            content=row.content,
            query=query,
        )

        highlighted_snippet = highlight_text(
            text=snippet,
            query=query,
        )

        results.append(
            DocumentSearchResult(
                document_id=row.document_id,
                document_name=(row.document_name),
                page_id=row.page_id,
                page_number=(row.page_number),
                chunk_id=row.chunk_id,
                content=row.content,
                snippet=snippet,
                highlighted_snippet=(highlighted_snippet),
                relevance=float(
                    row.relevance,
                ),
            )
        )

    access_condition = exists(
        select(1)
        .select_from(
            DepositAccess,
        )
        .join(
            GroupMember,
            GroupMember.group_id == DepositAccess.group_id,
        )
        .where(
            DepositAccess.deposit_id == Document.deposit_id,
            GroupMember.user_id == current_user.id,
        )
    )

    statement = statement.where(
        access_condition,
    )

    count_statement = (
        select(
            func.count(
                DocumentChunk.id,
            ),
        )
        .select_from(
            DocumentChunk,
        )
        .join(
            DocumentPage,
            DocumentPage.id == DocumentChunk.page_id,
        )
        .join(
            Document,
            Document.id == DocumentPage.document_id,
        )
        .where(
            relevance_expression,
        )
    )

    if not is_global_admin(db=db, user=current_user):

        count_statement = count_statement.where(
            access_condition,
        )

    total = (
        db.scalar(
            count_statement,
        )
        or 0
    )

    total_pages = math.ceil(
        total / page_size,
    )

    return DocumentSearchResponse(
        query=q,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        results=results,
    )
