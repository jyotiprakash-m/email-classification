from fastapi import APIRouter, Form
from typing import Optional
from graphs.email_classification_graph import graph, State

router = APIRouter(prefix="/v1/email-graph", tags=["Email Classification Graph"])

@router.post("/run")
async def run_email_graph_api(
	user_id: str = Form(...),
	org_id: str = Form(...),
	offset: Optional[str] = Form(None),
	limit: Optional[int] = Form(None)
):
	"""
	API endpoint to run the email classification graph.
	"""
	state: State = {
		"userId": user_id or "",
		"orgId": org_id or "",
		"offset": offset or None,
		"limit": limit or None,
		"emails": None
	}
	result = graph.invoke(state)
	return result
