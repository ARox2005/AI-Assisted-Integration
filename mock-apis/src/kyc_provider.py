import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class KycRequest(BaseModel):
    full_name: str
    date_of_birth: str
    pan_number: str
    aadhaar_last4: Optional[str] = None

@router.post("/mock-kyc/verify")
def verify_kyc(request: KycRequest):
    """
    Mock KYC verification endpoint.
    Simulates an identity verification service using PAN and Aadhaar.
    Logic:
    - If PAN starts with 'INVALID' → returns kyc_verified: false
    - Otherwise → returns kyc_verified: true with score 92
    """
    # Simulate a failure case for demo purposes
    is_invalid = request.pan_number.upper().startswith("INVALID")

    if is_invalid:
        return {
            "status": "completed",
            "kyc_verified": False,
            "identity_score": 23,
            "name_match": "NONE",
            "verification_id": str(uuid.uuid4()),
        }
        
    return {
        "status": "completed",
        "kyc_verified": True,
        "identity_score": 92,
        "name_match": "EXACT",
        "verification_id": str(uuid.uuid4()),
    }