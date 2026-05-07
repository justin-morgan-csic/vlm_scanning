# VLM document scanning — Gemini table extraction

This script sends an image to Gemini, asks it to extract the table, and saves the result as CSV.

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

## 3) Add your input image

Place the table image at:

- `input/test_image.jpg`

## 4) Run extraction

```bash
python gemini_connect.py
```

The script writes:

- `input/test_image_VLM_SCANNED.csv`

## Naming rule

Output name is always:

- `<original_filename>_VLM_SCANNED.csv`

in the same directory as the input file.
