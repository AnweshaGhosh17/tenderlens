import os
import json
import fitz
from groq import Groq

from dotenv import load_dotenv
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

def pdf_to_text(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for i in range(len(doc)):
        text += doc[i].get_text()
    doc.close()
    return text[:15000]

async def extract_criteria(tender_path):
    text = pdf_to_text(tender_path)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "Extract all eligibility criteria from this tender document. Return ONLY valid JSON no markdown: {\"criteria\": [{\"id\": \"C1\", \"category\": \"Financial\", \"description\": \"...\", \"source_text\": \"...\", \"mandatory\": true}], \"conflicts\": []}\n\nTENDER:\n" + text}],
        max_tokens=4000
    )
    raw = response.choices[0].message.content
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())

async def evaluate_bidder(bidder_path, bidder_name, criteria, tender_path):
    text = pdf_to_text(bidder_path)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "Evaluate bidder " + bidder_name + " against criteria: " + json.dumps(criteria) + ". Return ONLY valid JSON no markdown with fields: bidder_name, overall_status, document_quality, quality_note, evaluations array with criteria_id, verdict, confidence, source_text, explanation, appeal_risk, appeal_reason.\n\nBIDDER DOCUMENT:\n" + text}],
        max_tokens=4000
    )
    raw = response.choices[0].message.content
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())

