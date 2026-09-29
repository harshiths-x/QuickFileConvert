import csv
from pathlib import Path
from openpyxl import Workbook, load_workbook


def process_spreadsheet(tool: str, source: Path, target: Path, options: dict) -> None:
    def safe_cell(value):
        # Prevent spreadsheet programs from evaluating imported CSV text as a formula.
        if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
            return "'" + value
        return value

    if tool == "csv-to-excel":
        workbook = Workbook(write_only=True)
        sheet = workbook.create_sheet("Sheet1")
        with source.open("r", encoding="utf-8-sig", newline="") as file:
            for row in csv.reader(file):
                sheet.append([safe_cell(value) for value in row])
        workbook.save(target)
    elif tool == "excel-to-csv":
        workbook = load_workbook(source, read_only=True, data_only=True, keep_links=False)
        try:
            requested = str(options.get("sheet", ""))
            if requested and requested not in workbook.sheetnames:
                raise ValueError("The selected worksheet was not found.")
            sheet = workbook[requested] if requested else workbook.worksheets[0]
            with target.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.writer(file)
                writer.writerows([safe_cell(value) for value in row] for row in sheet.values)
        finally:
            workbook.close()
    else:
        raise ValueError("Unsupported spreadsheet operation.")
