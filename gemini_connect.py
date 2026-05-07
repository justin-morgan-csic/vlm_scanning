#!/usr/bin/env python3
"""Extract structured table data from each page of a PDF using Gemini and save to per-page Excel files."""

import json
import os
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

Some products have hierarchical headers. Include headers in the item name joined with ": ". Example: Meat > Chilled > Lamb should be written as Meat: Chilled: Lamb.

Return ONLY valid JSON (no markdown, no commentary) with this shape:
{
  "rows": [
    {
      "item": "...",
      "country": "...",
      "measurement": "...",
      "q_values": ["...", "...", "..."],
      "v_values": ["...", "...", "..."],
      "page": "{page_label}",
      "confidence": 0.0,
      "source_note": "short note quoting nearby text used"
    }
  ]
}

Rules:
- Use exactly 3 entries in q_values and 3 entries in v_values.
- If uncertain or unreadable, use empty string for that value and lower confidence. Do NOT guess.
- The page field must be exactly "{page_label}" for every row.
- When there is a Total value, put the country as Total.
- Remove From from the country column.
- Make sure all country names are spelled correctly.
"""

OUTPUT_HEADER = [
    "item",
    "country",
    "measurement",
    "Q_yearX",
    "Q_yearX",
    "Q_yearX",
    "V_yearX",
    "V_yearX",
    "V_yearX",
    "page",
    "confidence",
    "source_note",
]


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


def parse_response_json(response_text: str) -> dict:
    text = (response_text or "").strip()
    if not text:
        raise ValueError("Empty model response.")
    return json.loads(text)


def normalize_cell(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def validate_and_flatten_rows(payload: dict, expected_page: str) -> list[list[str]]:
    if not isinstance(payload, dict) or "rows" not in payload or not isinstance(payload["rows"], list):
        raise ValueError("Model response JSON must be an object with a rows list.")

    table_rows: list[list[str]] = [OUTPUT_HEADER]
    for i, row in enumerate(payload["rows"], start=1):
        if not isinstance(row, dict):
            raise ValueError(f"Row {i} is not an object.")

        q_values = row.get("q_values")
        v_values = row.get("v_values")
        if not isinstance(q_values, list) or len(q_values) != 3:
            raise ValueError(f"Row {i} q_values must be a list of 3 values.")
        if not isinstance(v_values, list) or len(v_values) != 3:
            raise ValueError(f"Row {i} v_values must be a list of 3 values.")

        page = normalize_cell(row.get("page"))
        if page != expected_page:
            raise ValueError(f"Row {i} page must be '{expected_page}', got '{page}'.")

        conf_raw = row.get("confidence", "")
        try:
            confidence = float(conf_raw)
        except (TypeError, ValueError):
            confidence = 0.0
        confidence = min(max(confidence, 0.0), 1.0)

        table_rows.append(
            [
                normalize_cell(row.get("item")),
                normalize_cell(row.get("country")),
                normalize_cell(row.get("measurement")),
                normalize_cell(q_values[0]),
                normalize_cell(q_values[1]),
                normalize_cell(q_values[2]),
                normalize_cell(v_values[0]),
                normalize_cell(v_values[1]),
                normalize_cell(v_values[2]),
                page,
                f"{confidence:.2f}",
                normalize_cell(row.get("source_note")),
            ]
        )

    if len(table_rows) == 1:
        raise ValueError("No rows returned by model.")
    return table_rows


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

        payload = parse_response_json(response.text or "")
        rows = validate_and_flatten_rows(payload, expected_page=page_label)

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
