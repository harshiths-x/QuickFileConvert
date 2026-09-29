import re


def parse_pages(expression: str, page_count: int, *, allow_duplicates: bool = False) -> list[int]:
    if not expression or not re.fullmatch(r"[0-9,\-\s]+", expression):
        raise ValueError("Invalid PDF page range.")
    pages: list[int] = []
    for token in expression.replace(" ", "").split(","):
        if not token:
            raise ValueError("Invalid PDF page range.")
        if "-" in token:
            if not re.fullmatch(r"[1-9][0-9]*-[1-9][0-9]*", token):
                raise ValueError("Invalid PDF page range.")
            start, end = map(int, token.split("-"))
            if start > end:
                raise ValueError("Invalid PDF page range.")
            pages.extend(range(start, end + 1))
        else:
            if not re.fullmatch(r"[1-9][0-9]*", token):
                raise ValueError("Invalid PDF page range.")
            pages.append(int(token))
    if not pages or any(page > page_count for page in pages):
        raise ValueError(f"Page numbers must be between 1 and {page_count}.")
    if not allow_duplicates and len(set(pages)) != len(pages):
        raise ValueError("Duplicate page numbers are not allowed.")
    return [page - 1 for page in pages]
