from pydantic import BaseModel


class DocumentSearchResult(
    BaseModel,
):

    document_id: int

    document_name: str

    page_id: int

    page_number: int

    chunk_id: int

    content: str

    relevance: float


class DocumentSearchResponse(
    BaseModel,
):

    query: str

    results: list[
        DocumentSearchResult
    ]