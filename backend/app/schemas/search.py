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

    snippet: str

    highlighted_snippet: str

    relevance: float


class DocumentSearchResponse(
    BaseModel,
):

    query: str

    page: int

    page_size: int

    total: int

    total_pages: int

    results: list[
        DocumentSearchResult
    ]