#!/usr/bin/env python3
"""Extract a table from an image with Gemini and save it as CSV."""

import csv
import os
import re
import sys
from pathlib import Path

from google import genai
from google.genai import types


def output_csv_path(input_path: Path) -> Path:
    return input_path.with_name(f"{input_path.stem}_VLM_SCANNED.csv")


def extract_csv_text(model_text: str) -> str:
    code_block_match = re.search(r"```(?:csv)?\s*(.*?)\s*```", model_text, re.DOTALL | re.IGNORECASE)
    if code_block_match:
        return code_block_match.group(1).strip()
    return model_text.strip()


def validate_csv(csv_text: str) -> str:
    rows = list(csv.reader(csv_text.splitlines()))
    if not rows:
        raise ValueError("The model returned empty CSV data.")
    return "\n".join(",".join(row) for row in rows)


def main() -> int:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Missing GEMINI_API_KEY environment variable.", file=sys.stderr)
        return 1

    input_path = Path("input/test_image.jpg")
    if not input_path.exists():
        print(f"Input image not found: {input_path}", file=sys.stderr)
        return 1

    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    client = genai.Client(api_key=api_key)

    image_bytes = input_path.read_bytes()

    response = client.models.generate_content(
        model=model,
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(
                        text=(
                            "Extract the table from this image and return only CSV text. "
                            "No markdown, no explanations, no extra text."
                        )
                    ),
                    types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                ],
            )
        ],
    )

    csv_text = extract_csv_text(response.text or "")
    clean_csv = validate_csv(csv_text)

    output_path = output_csv_path(input_path)
    output_path.write_text(clean_csv + "\n", encoding="utf-8")

    print(f"Model: {model}")
    print(f"Input: {input_path}")
    print(f"Output CSV: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
