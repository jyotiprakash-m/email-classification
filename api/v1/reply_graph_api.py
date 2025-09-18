from fastapi import APIRouter, Form
from typing import Optional
from graphs.reply_graph import graph, State

router = APIRouter(prefix="/v1/reply-graph", tags=["Reply Graph"])

@router.post("/run")
async def run_reply_graph_api(
	user_id: str = Form(...),
	email_body: str = Form(...),
	tone: Optional[str] = Form("professional"),
	tool_instructions: Optional[str] = Form(None)
):
	"""
	API endpoint to run the reply graph.
	"""
	state: State = {
		"userId": user_id or "",
		"email_body": email_body or "",
		"tone": tone or "professional",
		"tool_instructions": tool_instructions or "",
		"input": "",
		"final_response": "",
		"tool_outputs": ""
	}
	result = graph.invoke(state)
	return result
