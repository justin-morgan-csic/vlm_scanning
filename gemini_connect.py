#!/usr/bin/env python3
"""Minimal Gemini API connectivity check for document-scanning workflows."""

import os
import sys

from google import genai
from google.genai import types


def main() -> int:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Missing GEMINI_API_KEY environment variable.", file=sys.stderr)
        return 1

    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    client = genai.Client(api_key=api_key)

    # Basic call confirms auth + model access.
    response = client.models.generate_content(
        model=model,
        contents=[
            types.Content(
                role="user",
                parts=[types.Part.from_text(text="Reply with: Gemini API connected")],
            )
        ],
    )

    print(f"Model: {model}")
    print(response.text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
