# VLM document scanning — Gemini API bootstrap

This repo now includes a minimal Python connectivity check for the Gemini API so you can start building a document-scanning pipeline.

## 1) Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2) Set your API key

Create an API key in Google AI Studio, then export it:

```bash
export GEMINI_API_KEY="your_key_here"
```

Optional: override model (defaults to `gemini-2.5-flash`):

```bash
export GEMINI_MODEL="gemini-2.5-flash"
```

## 3) Run the connectivity check

```bash
python gemini_connect.py
```

Expected output includes:

- `Model: gemini-2.5-flash`
- `Gemini API connected`

## Notes

- `gemini-2.5-flash` is a high-capability model that is generally available in Gemini Developer API docs and listed with a free tier in Gemini pricing docs (limits/rates can change).
- If your key or project tier does not have access, the script will fail with a model/access error; switch to a model currently available to your project.
