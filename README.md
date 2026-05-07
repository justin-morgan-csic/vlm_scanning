# VLM document scanning — Gemini PDF to Excel extraction

This script sends a PDF to Gemini, asks it to extract a complex table using a structured prompt, and saves the result as an Excel file.

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

The script writes:

- `output.xlsx`
