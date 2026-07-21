"""
This is the heart of the product: takes a judgment PDF, gets text out of it,
and asks Gemini to find the directives, parties, and deadlines inside it.

Everything this file returns is treated as a DRAFT — it always gets saved with
verification_status = "pending_verification" and a human has to approve it
before it becomes a real, tracked action. This file must never mark anything
as approved.
"""
import os
import json
import re
from datetime import date, timedelta
import pdfplumber
from google import genai
from google.genai import types
from dotenv import load_dotenv


EXTRACTION_PROMPT = """You are analyzing an Indian court judgment. Read the text below and extract:

1. Case metadata: case_number, court_name, order_date (YYYY-MM-DD if determinable), petitioner, respondent.
2. Every distinct actionable directive the court has ordered some government body to carry out.
   For each directive, extract:
   - raw_description: a plain-language, one-sentence rewrite of what must be done
   - source_page: the page number where this appears (best guess if unclear, use 1)
   - source_snippet: the exact original sentence(s) from the text supporting this directive (max ~40 words)
   - deadline_expression_raw: the exact timeline language used (e.g. "within 30 days", "forthwith"). Use "" if none stated.
   - ai_confidence: "high", "medium", or "low" based on how explicit/unambiguous the directive is
   - suggested_department: your best guess at which government department should be responsible
     (choose from: Revenue Department, District Registrar Office, Public Works Department,
     Home Department, Forest & Environment Dept., Municipal Corporation, or propose another if none fit)

Respond with ONLY valid JSON, no markdown fences, no commentary, in this exact shape:
{
  "case_number": "",
  "court_name": "",
  "order_date": "",
  "petitioner": "",
  "respondent": "",
  "directives": [
    {
      "raw_description": "",
      "source_page": 1,
      "source_snippet": "",
      "deadline_expression_raw": "",
      "ai_confidence": "high",
      "suggested_department": ""
    }
  ]
}

JUDGMENT TEXT:
---
{text}
---
"""
load_dotenv()

print("API KEY FOUND:", bool(os.getenv("GEMINI_API_KEY")))  # ----------------DELETE _________________PLEASE DELETE AFTER

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

def extract_text_from_pdf(file_path: str) -> tuple[str, str]:
    """Returns (full_text, document_type). document_type is 'digital' if pdfplumber
    found real text, or 'scanned' if the PDF appears to be image-only and needs OCR."""
    pages_text = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages_text.append(text)
    full_text = "\n".join(pages_text)

    # If barely any text came out, this is almost certainly a scanned/image PDF.
    if len(full_text.strip()) < 200:
        ocr_text = _ocr_pdf(file_path)
        return ocr_text, "scanned"

    return full_text, "digital"


def _ocr_pdf(file_path: str) -> str:
    """Fallback for scanned PDFs: converts each page to an image and runs OCR on it."""
    from pdf2image import convert_from_path
    import pytesseract

    images = convert_from_path(file_path)
    text_parts = []
    for img in images:
        text_parts.append(pytesseract.image_to_string(img))
    return "\n".join(text_parts)


def run_ai_extraction(judgment_text: str) -> dict:
    """
    Sends the judgment text to Gemini and returns structured JSON.
    """

    prompt = EXTRACTION_PROMPT.replace("{text}", judgment_text[:30000])

    print("Sending request to Gemini...")

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )

    print("Received response")

    raw = response.text.strip()

    raw = re.sub(r"^```json|```$", "", raw).strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Gemini did not return valid JSON: {e}\nRaw response:\n{raw[:500]}"
        )

    if "directives" not in data or not isinstance(data["directives"], list):
        raise ValueError("Gemini response is missing a valid 'directives' list")

    return data


def compute_deadline(order_date_str: str, deadline_expression: str) -> date | None:
    """Converts a relative deadline expression into an absolute date.
    Deliberately deterministic code, NOT the LLM, to avoid arithmetic hallucination."""
    if not order_date_str:
        return None
    try:
        anchor = date.fromisoformat(order_date_str)
    except ValueError:
        return None

    expr = (deadline_expression or "").lower()

    if not expr or "forthwith" in expr:
        return anchor

    match = re.search(r"(\d+)\s*day", expr)
    if match:
        return anchor + timedelta(days=int(match.group(1)))

    match = re.search(r"(\d+)\s*month", expr)
    if match:
        return anchor + timedelta(days=int(match.group(1)) * 30)

    match = re.search(r"(\d+)\s*week", expr)
    if match:
        return anchor + timedelta(days=int(match.group(1)) * 7)

    # Couldn't confidently parse it — leave for the human reviewer to set manually.
    return None
