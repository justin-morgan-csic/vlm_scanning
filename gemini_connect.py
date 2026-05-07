#!/usr/bin/env python3
"""Extract structured table data from each page of a PDF using Gemini and save to per-page Excel files."""

import csv
import os
import re
import sys
from io import BytesIO
from pathlib import Path

from google import genai
from google.genai import types
from openpyxl import Workbook
from pypdf import PdfReader, PdfWriter

PROMPT_TEMPLATE = """Hello. I have a pdf with a table. The table structure is as follows:
The first column is the item and country. Next to the item/country is a measurement. If marked with \"\", it is the same measurement as the item above.
The structure here is
Item1:
country1
country2
...
Item2:
country1
country2
and so forth.
each row has 12 values, in addition to the product/country and measurement.
The first 6 columns are data in quantity. the first three of these columns are years for monthly data, the second 3 of these columns are years for yearly data. I only want the last 3 columns of this set. The second 6 columns in the data are in value. I would like the last 3 columns of this set as well.
Can you use a visual language model to scan this pdf and return CSV with the following structure? replace yearX with the year (for example, 1911 would be Q_1911)
item,country,measurement,Q_yearX,Q_yearX,Q_yearX,V_yearX,V_yearX,V_yearX,page

The page column should have the name of the pdf plus the page in which this data point is found. For this page, set all page cells to: {page_label}
When there is a Total value, put the country as Total. Remove From from the country column. Make sure all columns and rows are properly scanned. Make sure all country names are spelled correctly.
Return only CSV text, no markdown, no extra commentary."""


def extract_csv_text(model_text: str) -> str:
    code_block_match = re.search(r"```(?:csv)?\s*(.*?)\s*```", model_text, re.DOTALL | re.IGNORECASE)
    if code_block_match:
        return code_block_match.group(1).strip()
    return model_text.strip()


def parse_csv_rows(csv_text: str) -> list[list[str]]:
    rows = list(csv.reader(csv_text.splitlines()))
    if not rows:
        raise ValueError("The model returned empty CSV data.")
    return rows


def write_excel(rows: list[list[str]], output_path: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "scanned_table"
    for row in rows:
        ws.append(row)
    wb.save(output_path)


def page_pdf_bytes(reader: PdfReader, page_index: int) -> bytes:
    writer = PdfWriter()
    writer.add_page(reader.pages[page_index])
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def main() -> int:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Missing GEMINI_API_KEY environment variable.", file=sys.stderr)
        return 1

    input_path = Path("input/test_pdf.pdf")
    if not input_path.exists():
        print(f"Input PDF not found: {input_path}", file=sys.stderr)
        return 1

    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    client = genai.Client(api_key=api_key)

    reader = PdfReader(str(input_path))
    if not reader.pages:
        print(f"Input PDF has no pages: {input_path}", file=sys.stderr)
        return 1

    created_files: list[Path] = []
    for idx, _ in enumerate(reader.pages, start=1):
        page_label = f"{input_path.stem}_pp{idx}"
        prompt = PROMPT_TEMPLATE.format(page_label=page_label)
        single_page_pdf = page_pdf_bytes(reader, idx - 1)

        response = client.models.generate_content(
            model=model,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=prompt),
                        types.Part.from_bytes(data=single_page_pdf, mime_type="application/pdf"),
                    ],
                )
            ],
        )

        csv_text = extract_csv_text(response.text or "")
        rows = parse_csv_rows(csv_text)

        output_path = output_dir / f"{input_path.stem}_pp{idx}_vlm_scanned.xlsx"
        write_excel(rows, output_path)
        created_files.append(output_path)

    print(f"Model: {model}")
    print(f"Input PDF: {input_path}")
    for output_path in created_files:
        print(f"Output Excel: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
