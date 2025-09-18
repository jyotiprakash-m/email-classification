from fastapi import APIRouter, Form
from services.generate_email_using_rag import generate_email_with_rag
from services.generic_email_replyer import generate_email_reply

router = APIRouter(prefix="/v1/email-reply", tags=["Generic Email Replyer"])

@router.post("/generate_reply")
async def generate_reply_api(email_text: str = Form(...)):
	"""
	Generate a polite, professional, and context-aware email reply using LLM.
	"""
	reply = generate_email_reply(email_text)
	return {"reply": reply}


# generate_email_with_rag
@router.post("/generate_email_with_rag")
async def generate_email_with_rag_api(
	email_text: str = Form(...),
	collection_name: str = Form(...),
	k: int = Form(3)
):
	"""
	Generate a polite, professional, and context-aware email reply using RAG.
	"""
	reply = generate_email_with_rag(email_text, collection_name, k)
	return {"reply": reply}