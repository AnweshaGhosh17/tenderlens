import os
import json
import base64
import fitz  # PyMuPDF
from groq import Groq
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
from dotenv import load_dotenv

load_dotenv()

import httpx
client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
    http_client=httpx.Client(verify=False)
)


def pdf_to_images(pdf_path: str) -> list:
    """Convert PDF pages to base64 PNG images."""
    doc = fitz.open(pdf_path)
    images = []
    for page_number in range(len(doc)):
        page = doc[page_number]
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")
        images.append(img_b64)
    doc.close()
    return images


async def extract_criteria(tender_path: str) -> dict:
    images = pdf_to_images(tender_path)

    content = []
    for img_b64 in images:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{img_b64}"}
        })

    content.append({
        "type": "text",
        "text": """You are a government procurement specialist.
Carefully read this entire tender document and do two things:

1. Extract EVERY eligibility criterion a bidder must meet to qualify.
2. Identify any contradictions or conflicts between criteria.

Return ONLY a valid JSON object. No explanation before or after. No markdown.
Use this exact structure:

{
  "criteria": [
    {
      "id": "C1",
      "category": "Financial",
      "description": "Minimum annual turnover of 50 Lakhs for last 3 years",
      "source_text": "exact sentence copied from the document",
      "mandatory": true
    }
  ],
  "conflicts": [
    {
      "criteria_ids": ["C1", "C3"],
      "description": "C1 requires 3 years turnover but C3 references only 2 years"
    }
  ]
}

Categories to use: Financial, Technical, Legal, Certifications, Experience, Other
If no conflicts exist, return an empty array for conflicts."""
    })

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{"role": "user", "content": content}],
        max_tokens=4000
    )

    raw = response.choices[0].message.content
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


async def evaluate_bidder(
    bidder_path: str,
    bidder_name: str,
    criteria: list,
    tender_path: str
) -> dict:
    images = pdf_to_images(bidder_path)

    content = []
    content.append({
        "type": "text",
        "text": f"BIDDER NAME: {bidder_name}\n\nThe following pages are the bidder's submitted documents:"
    })

    for img_b64 in images:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{img_b64}"}
        })

    criteria_text = json.dumps(criteria, indent=2)

    content.append({
        "type": "text",
        "text": f"""You are a government procurement evaluation officer.

You must evaluate whether the bidder named "{bidder_name}" meets each of the following eligibility criteria based on their submitted documents above.

CRITERIA TO EVALUATE AGAINST:
{criteria_text}

Return ONLY a valid JSON object. No explanation. No markdown. Use this exact structure:

{{
  "bidder_name": "{bidder_name}",
  "overall_status": "ELIGIBLE",
  "document_quality": "GOOD",
  "quality_note": "",
  "evaluations": [
    {{
      "criteria_id": "C1",
      "verdict": "ELIGIBLE",
      "confidence": 0.95,
      "source_text": "exact text from bidder document that supports this verdict",
      "explanation": "Clear explanation of why this verdict was given.",
      "appeal_risk": false,
      "appeal_reason": ""
    }}
  ]
}}

RULES YOU MUST FOLLOW:
- overall_status must be one of: ELIGIBLE, NOT ELIGIBLE, NEEDS REVIEW
- verdict must be one of: ELIGIBLE, NOT ELIGIBLE, NEEDS REVIEW
- If you cannot find supporting evidence, set verdict to NEEDS REVIEW
- appeal_risk must be true if rejection reason is vague or legally challengeable
- confidence is a decimal between 0.0 and 1.0
- document_quality must be: GOOD, POOR, or UNREADABLE
- source_text must be a real quote from the bidder document"""
    })

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{"role": "user", "content": content}],
        max_tokens=4000
    )

    raw = response.choices[0].message.content
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)
