import os
import json
import fitz  # PyMuPDF
import google.genai as genai
import google.genai.types as types
from dotenv import load_dotenv

load_dotenv()

# Initialize the Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Gemini model to use — gemini-2.0-flash is free tier and fast
GEMINI_MODEL = "gemini-2.0-flash"


def pdf_to_image_parts(pdf_path: str) -> list:
    """
    Converts every page of a PDF into a Gemini-compatible image Part.
    Works for both digital PDFs and scanned/photographed documents.
    Returns a list of types.Part objects, one per page.
    """
    doc = fitz.open(pdf_path)
    parts = []

    for page_number in range(len(doc)):
        page = doc[page_number]
        # dpi=150 is a good balance of quality vs speed
        pix = page.get_pixmap(dpi=150)
        # Convert page to PNG bytes directly
        img_bytes = pix.tobytes("png")
        # Wrap as a Gemini Part using from_bytes
        part = types.Part.from_bytes(data=img_bytes, mime_type="image/png")
        parts.append(part)

    doc.close()
    return parts


async def extract_criteria(tender_path: str) -> dict:
    """
    Takes the tender PDF path.
    Returns a dict with 'criteria' list and 'conflicts' list.
    """
    image_parts = pdf_to_image_parts(tender_path)

    # Build the contents list: all page images + instruction text
    contents = image_parts + [
        types.Part.from_text(text="""You are a government procurement specialist.
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
    },
    {
      "id": "C2",
      "category": "Technical",
      "description": "Must have completed 2 similar projects in last 5 years",
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
If no conflicts exist, return an empty array for conflicts.""")
    ]

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            max_output_tokens=4000,
            temperature=0.1  # Low temperature = more consistent, structured output
        )
    )

    raw = response.text
    # Remove markdown code fences if Gemini added them
    raw = raw.replace("```json", "").replace("```", "").strip()

    return json.loads(raw)


async def evaluate_bidder(
    bidder_path: str,
    bidder_name: str,
    criteria: list,
    tender_path: str
) -> dict:
    """
    Takes bidder PDF, their name, and the list of criteria.
    Returns a full evaluation dict with verdict per criterion.
    """
    image_parts = pdf_to_image_parts(bidder_path)

    criteria_text = json.dumps(criteria, indent=2)

    # Build contents: intro text + all page images + evaluation instruction
    contents = (
        [types.Part.from_text(text=f"BIDDER NAME: {bidder_name}\n\nThe following pages are the bidder's submitted documents:")]
        + image_parts
        + [types.Part.from_text(text=f"""You are a government procurement evaluation officer.

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
      "explanation": "The bidder's audited balance sheet shows turnover of 80L, 90L, and 110L for FY21, FY22, FY23.",
      "appeal_risk": false,
      "appeal_reason": ""
    }}
  ]
}}

RULES YOU MUST FOLLOW:
- overall_status must be one of: ELIGIBLE, NOT ELIGIBLE, NEEDS REVIEW
- verdict must be one of: ELIGIBLE, NOT ELIGIBLE, NEEDS REVIEW
- If you cannot find supporting evidence, set verdict to NEEDS REVIEW — never silently reject
- appeal_risk must be true if the rejection reason is vague, ambiguous, or legally challengeable
- confidence is a decimal between 0.0 and 1.0
- document_quality must be: GOOD, POOR, or UNREADABLE
- If pages are blurry, tilted, or hard to read, set document_quality to POOR and explain in quality_note
- source_text must be a real quote from the bidder document, not fabricated""")]
    )

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            max_output_tokens=4000,
            temperature=0.1
        )
    )

    raw = response.text
    raw = raw.replace("```json", "").replace("```", "").strip()

    return json.loads(raw)
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
    },
    {
      "id": "C2",
      "category": "Technical",
      "description": "Must have completed 2 similar projects in last 5 years",
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

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[{"role": "user", "content": content}]
    )

    raw = response.content[0].text
    # Remove markdown code fences if Claude added them
    raw = raw.replace("```json", "").replace("```", "").strip()

    return json.loads(raw)


async def evaluate_bidder(
    bidder_path: str,
    bidder_name: str,
    criteria: list,
    tender_path: str
) -> dict:
    """
    Takes bidder PDF, their name, and the list of criteria.
    Returns a full evaluation dict with verdict per criterion.
    """
    images = pdf_to_images(bidder_path)

    content = []

    content.append({
        "type": "text",
        "text": f"BIDDER NAME: {bidder_name}\n\nThe following pages are the bidder's submitted documents:"
    })

    # Add every page of the bidder document as an image
    for img_b64 in images:
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": img_b64
            }
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
      "explanation": "The bidder's audited balance sheet shows turnover of 80L, 90L, and 110L for FY21, FY22, FY23.",
      "appeal_risk": false,
      "appeal_reason": ""
    }}
  ]
}}

RULES YOU MUST FOLLOW:
- overall_status must be one of: ELIGIBLE, NOT ELIGIBLE, NEEDS REVIEW
- verdict must be one of: ELIGIBLE, NOT ELIGIBLE, NEEDS REVIEW
- If you cannot find supporting evidence, set verdict to NEEDS REVIEW — never silently reject
- appeal_risk must be true if the rejection reason is vague, ambiguous, or legally challengeable
- confidence is a decimal between 0.0 and 1.0
- document_quality must be: GOOD, POOR, or UNREADABLE
- If pages are blurry, tilted, or hard to read, set document_quality to POOR and explain in quality_note
- source_text must be a real quote from the bidder document, not fabricated"""
    })

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[{"role": "user", "content": content}]
    )

    raw = response.content[0].text
    raw = raw.replace("```json", "").replace("```", "").strip()

    return json.loads(raw)
