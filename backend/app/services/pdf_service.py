from pathlib import Path
from pypdf import PdfReader, PdfWriter
from app.utils.page_ranges import parse_pages


def process_pdf(tool: str, source: Path, target: Path, options: dict) -> None:
    reader = PdfReader(str(source))
    if reader.is_encrypted:
        raise ValueError("Password-protected PDFs are not supported.")
    count = len(reader.pages)
    if not count:
        raise ValueError("The PDF has no pages.")
    if tool == "pdf-to-txt":
        text = "\n\n".join(page.extract_text() or "" for page in reader.pages).strip()
        if not text:
            raise ValueError("This PDF contains no extractable text.")
        target.write_text(text + "\n", encoding="utf-8")
        return
    if tool == "split":
        expression = str(options.get("pages", ""))
        if "," in expression:
            raise ValueError("Enter one continuous page range, such as 1-3.")
        pages = parse_pages(expression, count)
    elif tool == "extract":
        pages = parse_pages(str(options.get("pages", "")), count)
    elif tool == "reorder":
        pages = parse_pages(str(options.get("pages", "")), count)
        if len(pages) != count:
            raise ValueError(f"Enter every page exactly once (1 through {count}).")
    elif tool == "rotate":
        try:
            rotation = int(options.get("rotation", 0))
        except (TypeError, ValueError) as exc:
            raise ValueError("Choose a rotation of 90, 180, or 270 degrees.") from exc
        if rotation not in (90, 180, 270):
            raise ValueError("Choose a rotation of 90, 180, or 270 degrees.")
        selection = str(options.get("pages", "all"))
        pages = list(range(count)) if selection.lower() == "all" else parse_pages(selection, count)
    else:
        raise ValueError("Unsupported PDF operation.")
    writer = PdfWriter()
    if tool == "rotate":
        chosen = set(pages)
        for index, page in enumerate(reader.pages):
            writer.add_page(page)
            if index in chosen:
                writer.pages[-1].rotate(rotation)
    else:
        for index in pages:
            writer.add_page(reader.pages[index])
    with target.open("wb") as file:
        writer.write(file)
