class TextChunker:

    def __init__(
        self,
        chunk_size: int = 2000,
        overlap: int = 200,
    ) -> None:

        self.chunk_size = chunk_size

        self.overlap = overlap

    def split(
        self,
        text: str,
    ) -> list[str]:

        text = text.strip()

        if not text:

            return []

        chunks = []

        start = 0

        text_length = len(
            text,
        )

        while start < text_length:

            end = (
                start
                + self.chunk_size
            )

            chunk = text[
                start:end
            ].strip()

            if chunk:

                chunks.append(
                    chunk,
                )

            if end >= text_length:

                break

            start = (
                end
                - self.overlap
            )

        return chunks