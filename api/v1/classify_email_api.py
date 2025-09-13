from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from core.database import get_session
import services.classify_email as classify_email_service
from models.request_response import EmailClassificationRequest,EmailClassificationResponse
router = APIRouter(prefix="/v1", tags=["Classify Email"])

@router.post("/email-classify", response_model=EmailClassificationResponse)
def create(analysis: EmailClassificationRequest, session: Session = Depends(get_session)):
    try:
        result = classify_email_service.classify_email(analysis.email_content)
        return EmailClassificationResponse(**result)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")