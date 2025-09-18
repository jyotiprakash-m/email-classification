from fastapi import APIRouter, Form
from services.generate_email_from_db import generate_select_query

router = APIRouter(prefix="/v1/db-query", tags=["DB Query Generator"])

@router.post("/run_query")
async def run_query_api(user_request: str = Form(...)):
	"""
	Generate and execute a safe SQL SELECT query using LLM and return the results.
	"""
	result = generate_select_query(user_request)
	return {"result": result}
