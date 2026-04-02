import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class GstRequest(BaseModel):
    gstin: str
    business_name: str
    pan_number: Optional[str] = None


@router.post("/mock-gst/validate")
def validate_gst(request: GstRequest):
    """
    Mock GST validation endpoint.
    Simulates a GSTIN lookup and business verification service.

    Logic:
    - If GSTIN starts with '00' → returns gstin_valid: false, status INACTIVE
    - Otherwise → returns gstin_valid: true, status ACTIVE
    """
    is_invalid = request.gstin.startswith("00")

    if is_invalid:
        return {
            "status": "completed",
            "gstin_valid": False,
            "business_name_on_record": "NOT FOUND",
            "gst_status": "INACTIVE",
            "last_filing_date": None,
            "validation_id": str(uuid.uuid4()),
        }

    return {
        "status": "completed",
        "gstin_valid": True,
        "business_name_on_record": request.business_name,
        "gst_status": "ACTIVE",
        "last_filing_date": "2026-03-15",
        "validation_id": str(uuid.uuid4()),
    }
