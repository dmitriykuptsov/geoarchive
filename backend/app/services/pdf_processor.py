import fitz


class PDFProcessor:

    def extract(
        self,
        file_path: str,
    ) -> list[dict]:

        document = fitz.open(
            file_path,
        )

        pages = []

        try:

            for page_index in range(
                document.page_count,
            ):

                page = document.load_page(
                    page_index,
                )

                text = page.get_text(
                    "text",
                )

                rect = page.rect

                pages.append(
                    {
                        "page_number": (page_index + 1),
                        "width": rect.width,
                        "height": rect.height,
                        "text": text,
                    }
                )

        finally:

            document.close()

        return pages
