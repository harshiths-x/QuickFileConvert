from pathlib import Path
from app.services.document_service import process_document
from app.services.image_service import process_image
from app.services.pdf_service import process_pdf
from app.services.spreadsheet_service import process_spreadsheet


def process(tool: str, source: Path, target: Path, options: dict) -> None:
    if tool in {"pdf-to-word", "word-to-pdf", "docx-to-txt", "txt-to-pdf"}:
        process_document(tool, source, target, options)
    elif tool in {"pdf-to-txt", "split", "rotate", "extract", "reorder"}:
        process_pdf(tool, source, target, options)
    elif tool in {"jpg-to-png", "png-to-jpg", "image-to-pdf"}:
        process_image(tool, source, target, options)
    elif tool in {"csv-to-excel", "excel-to-csv"}:
        process_spreadsheet(tool, source, target, options)
    else:
        raise ValueError("Unsupported conversion tool.")
