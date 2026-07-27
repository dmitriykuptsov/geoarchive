import re


def create_snippet(
    content: str,
    query: str,
    context_size: int = 250,
) -> str:

    content_lower = content.lower()
    query_lower = query.lower()

    match_position = content_lower.find(
        query_lower,
    )

    if match_position == -1:

        return content[: context_size * 2]

    start = max(
        0,
        match_position - context_size,
    )

    end = min(
        len(content),
        match_position + len(query) + context_size,
    )

    snippet = content[start:end].strip()

    if start > 0:

        snippet = "..." + snippet

    if end < len(content):

        snippet = snippet + "..."

    return snippet


def highlight_text(
    text: str,
    query: str,
) -> str:

    if not query.strip():

        return text

    pattern = re.compile(
        re.escape(
            query,
        ),
        re.IGNORECASE,
    )

    return pattern.sub(
        lambda match: ("<mark>" + match.group(0) + "</mark>"),
        text,
    )
