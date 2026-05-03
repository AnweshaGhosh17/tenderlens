async def extract_criteria(tender_path: str) -> dict:
    return {
        "criteria": [
            {"id": "C1", "category": "Financial", "description": "Test criterion", "source_text": "test", "mandatory": True}
        ],
        "conflicts": []
    }

async def evaluate_bidder(bidder_path, bidder_name, criteria, tender_path) -> dict:
    return {
        "bidder_name": bidder_name,
        "overall_status": "NEEDS REVIEW",
        "document_quality": "GOOD",
        "quality_note": "Stub response",
        "evaluations": [
            {"criteria_id": "C1", "verdict": "NEEDS REVIEW", "confidence": 0.5,
             "source_text": "stub", "explanation": "Test mode", "appeal_risk": False, "appeal_reason": ""}
        ]
    }