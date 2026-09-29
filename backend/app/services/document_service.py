import subprocess
import tempfile
import os
import shutil
from pathlib import Path
from docx import Document
from pdf2docx import Converter
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from app.core.config import settings


def libreoffice_executable() -> str:
    configured = settings.libreoffice_path or os.environ.get("LIBREOFFICE_PATH")
    if configured:
        if Path(configured).is_file():
            return configured
        raise ValueError("The configured LibreOffice executable was not found.")
    found = shutil.which("libreoffice") or shutil.which("soffice")
    if found:
        return found
    if os.name == "nt":
        for variable in ("ProgramFiles", "ProgramFiles(x86)"):
            base = os.environ.get(variable)
            if base:
                candidate = Path(base) / "LibreOffice" / "program" / "soffice.exe"
                if candidate.is_file():
                    return str(candidate)
    raise ValueError("Word to PDF requires LibreOffice on the backend. Install it, then try again.")


def process_document(tool: str, source: Path, target: Path, options: dict) -> None:
    if tool == "pdf-to-word":
        converter = Converter(str(source))
        try:
            converter.convert(str(target))
        finally:
            converter.close()
    elif tool == "word-to-pdf":
        # LibreOffice may briefly keep profile registry files open after it exits on Windows.
        # The per-job directory is still removed by the normal expiry cleanup.
        with tempfile.TemporaryDirectory(dir=source.parent, ignore_cleanup_errors=True) as profile:
            command = [libreoffice_executable(), "-env:UserInstallation=" + Path(profile).as_uri(),
                       "--headless", "--convert-to", "pdf", "--outdir", str(target.parent), str(source)]
            try:
                result = subprocess.run(command, capture_output=True, text=True, timeout=90, check=False)
            except FileNotFoundError as exc:
                raise ValueError("Word to PDF requires LibreOffice on the backend. Install it, then try again.") from exc
            except subprocess.TimeoutExpired as exc:
                raise ValueError("The conversion took too long.") from exc
            produced = source.with_suffix(".pdf")
            if result.returncode != 0 or not produced.exists():
                raise ValueError("Conversion could not be completed.")
            produced.replace(target)
    elif tool == "docx-to-txt":
        document = Document(source)
        lines = [paragraph.text for paragraph in document.paragraphs]
        for table in document.tables:
            lines.extend("\t".join(cell.text for cell in row.cells) for row in table.rows)
        target.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    elif tool == "txt-to-pdf":
        text = source.read_text(encoding="utf-8-sig")
        font_path = next((path for path in (Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"), Path("C:/Windows/Fonts/arial.ttf")) if path.exists()), None)
        font = "Helvetica"
        if font_path:
            pdfmetrics.registerFont(TTFont("DejaVu", str(font_path)))
            font = "DejaVu"
        page = canvas.Canvas(str(target), pagesize=A4)
        width, height = A4
        margin, line_height = 54, 17
        y = height - margin
        page.setFont(font, 11)
        for raw_line in text.splitlines():
            lines = simpleSplit(raw_line.expandtabs(4), font, 11, width - 2 * margin) or [""]
            for line in lines:
                if y < margin:
                    page.showPage()
                    page.setFont(font, 11)
                    y = height - margin
                page.drawString(margin, y, line)
                y -= line_height
        page.save()
    else:
        raise ValueError("Unsupported document operation.")
