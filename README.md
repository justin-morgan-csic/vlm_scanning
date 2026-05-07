# VLM document scanning — Gemini PDF to per-page Excel extraction

This script sends a PDF to Gemini page by page, asks it to extract a complex table with a strict JSON schema (no guessing) and saves one Excel file per page.

## 1) Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.

## 2) Set your API key

```bash
export GEMINI_API_KEY="your_key_here"
```

Optional:

```bash
export GEMINI_MODEL="gemini-2.5-flash"
```

## 3) Add your input PDF

Place the PDF at:

- `input/test_pdf.pdf`

## 4) Run extraction

```bash
python gemini_connect.py
```

The script writes one workbook per page to `output/` with this format:

- `inputfilename_ppX_vlm_scanned.xlsx`
- Example: `output/test_pdf_pp1_vlm_scanned.xlsx`


The output workbook includes additional reliability columns: `confidence` and `source_note`.
