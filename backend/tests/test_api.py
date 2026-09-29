import io
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from pypdf import PdfReader
from reportlab.pdfgen import canvas
from openpyxl import load_workbook
from docx import Document

from app.main import app
from app.core.config import settings
from app.utils.cleanup import remove_expired
from app.utils.filename import download_name
from app.utils.page_ranges import parse_pages
from app.services.document_service import libreoffice_executable


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "temp_root", str(tmp_path))
    with TestClient(app) as test_client:
        yield test_client


def pdf_bytes(pages=3):
    stream = io.BytesIO()
    document = canvas.Canvas(stream)
    for number in range(pages):
        document.drawString(100, 700, f"Page {number + 1}")
        document.showPage()
    document.save()
    return stream.getvalue()


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_valid_conversion_and_download(client):
    response = client.post("/api/convert/txt-to-pdf", files={"file": ("notes.txt", b"Hello world", "text/plain")})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["filename"] == "notes.pdf"
    assert data["mime_type"] == "application/pdf"
    download = client.get("/api/download/" + data["download_id"])
    assert download.status_code == 200
    assert download.content.startswith(b"%PDF-")
    assert "notes.pdf" in download.headers["content-disposition"]
    directory = settings.storage_root / data["download_id"]
    assert not (directory / "input.txt").exists()


def test_rejects_wrong_extension_and_corrupt_pdf(client):
    wrong = client.post("/api/convert/pdf-to-txt", files={"file": ("thing.exe", b"MZ...", "application/octet-stream")})
    assert wrong.status_code == 400
    corrupt = client.post("/api/convert/pdf-to-txt", files={"file": ("thing.pdf", b"not pdf", "application/pdf")})
    assert corrupt.status_code == 400
    damaged = client.post("/api/convert/pdf-to-txt", files={"file": ("thing.pdf", b"%PDF-invalid", "application/pdf")})
    assert damaged.status_code == 400
    assert list(settings.storage_root.iterdir()) == []


def test_rejects_multiple_files(client):
    response = client.post("/api/convert/txt-to-pdf", files=[("file", ("a.txt", b"a", "text/plain")), ("file", ("b.txt", b"b", "text/plain"))])
    assert response.status_code == 400
    assert response.json()["detail"] == "Choose one file at a time."


def test_size_limit(client, monkeypatch):
    monkeypatch.setattr(settings, "max_upload_size", 4)
    response = client.post("/api/convert/txt-to-pdf", files={"file": ("big.txt", b"12345", "text/plain")})
    assert response.status_code == 413
    assert list(settings.storage_root.iterdir()) == []


def test_pdf_page_tools(client):
    content = pdf_bytes()
    inspect = client.post("/api/pdf/inspect", files={"file": ("test.pdf", content, "application/pdf")})
    assert inspect.status_code == 200, inspect.text
    assert inspect.json()["page_count"] == 3
    response = client.post("/api/pdf/extract", files={"file": ("test.pdf", content, "application/pdf")}, data={"options": '{"pages":"3,1"}'})
    assert response.status_code == 200, response.text
    data = client.get("/api/download/" + response.json()["download_id"]).content
    reader = PdfReader(io.BytesIO(data))
    assert len(reader.pages) == 2
    assert "Page 3" in reader.pages[0].extract_text()
    bad = client.post("/api/pdf/reorder", files={"file": ("test.pdf", content, "application/pdf")}, data={"options": '{"pages":"1,1,3"}'})
    assert bad.status_code == 400


def test_image_conversion(client):
    image = Image.new("RGBA", (12, 8), (0, 0, 0, 0))
    image.putpixel((0, 0), (255, 0, 0, 255))
    stream = io.BytesIO(); image.save(stream, "PNG")
    response = client.post("/api/convert/png-to-jpg", files={"file": ("image.png", stream.getvalue(), "image/png")})
    assert response.status_code == 200, response.text
    downloaded = client.get("/api/download/" + response.json()["download_id"])
    with Image.open(io.BytesIO(downloaded.content)) as jpg:
        assert jpg.format == "JPEG"
        assert all(channel >= 250 for channel in jpg.getpixel((11, 7)))


def test_csv_and_excel_conversion(client):
    response = client.post("/api/convert/csv-to-excel", files={"file": ("data.csv", b"name,value\nitem,42\n", "text/csv")})
    assert response.status_code == 200, response.text
    workbook_bytes = client.get("/api/download/" + response.json()["download_id"]).content
    workbook = load_workbook(io.BytesIO(workbook_bytes))
    assert workbook.active["B2"].value == "42"
    stream = io.BytesIO(); workbook.save(stream)
    response = client.post("/api/convert/excel-to-csv", files={"file": ("data.xlsx", stream.getvalue(), "application/octet-stream")})
    assert response.status_code == 200, response.text
    assert b"item,42" in client.get("/api/download/" + response.json()["download_id"]).content


def test_docx_and_pdf_text(client):
    document = Document(); document.add_paragraph("A clear paragraph")
    stream = io.BytesIO(); document.save(stream)
    response = client.post("/api/convert/docx-to-txt", files={"file": ("note.docx", stream.getvalue(), "application/octet-stream")})
    assert response.status_code == 200, response.text
    assert b"A clear paragraph" in client.get("/api/download/" + response.json()["download_id"]).content
    response = client.post("/api/convert/pdf-to-txt", files={"file": ("pages.pdf", pdf_bytes(), "application/pdf")})
    assert response.status_code == 200, response.text
    assert b"Page 1" in client.get("/api/download/" + response.json()["download_id"]).content


def test_pdf_to_word(client):
    response = client.post("/api/convert/pdf-to-word", files={"file": ("pages.pdf", pdf_bytes(1), "application/pdf")})
    assert response.status_code == 200, response.text
    document = Document(io.BytesIO(client.get("/api/download/" + response.json()["download_id"]).content))
    assert any("Page 1" in paragraph.text for paragraph in document.paragraphs)


def test_word_to_pdf_when_libreoffice_available(client):
    try:
        libreoffice_executable()
    except ValueError:
        pytest.skip("LibreOffice is not installed")
    document = Document(); document.add_paragraph("QuickFileConvert conversion check")
    stream = io.BytesIO(); document.save(stream)
    response = client.post("/api/convert/word-to-pdf", files={"file": ("test.docx", stream.getvalue(), "application/octet-stream")})
    assert response.status_code == 200, response.text
    pdf = client.get("/api/download/" + response.json()["download_id"]).content
    assert "QuickFileConvert conversion check" in PdfReader(io.BytesIO(pdf)).pages[0].extract_text()


def test_expiry_and_filename_safety(client):
    assert download_name("../../evil\\name.txt", "", "pdf") == "name.pdf"
    response = client.post("/api/convert/txt-to-pdf", files={"file": ("okay.txt", b"hello", "text/plain")})
    token = response.json()["download_id"]
    directory = settings.storage_root / token
    old = time.time() - 400
    import os
    os.utime(directory, (old, old))
    remove_expired(settings.storage_root, 300)
    assert not directory.exists()
    assert client.get("/api/download/" + token).status_code == 404


@pytest.mark.parametrize("expression", ["0", "-1", "4", "2-1", "1,,2", "1,1", "abc"])
def test_bad_page_ranges(expression):
    with pytest.raises(ValueError):
        parse_pages(expression, 3)
