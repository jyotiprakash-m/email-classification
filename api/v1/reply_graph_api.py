from fastapi import APIRouter, Form
from typing import Optional

from langsmith import traceable
from graphs.reply_graph import graph, State

router = APIRouter(prefix="/v1/reply-graph", tags=["Reply Graph"])

@traceable(name="classify_reply_api")
@router.post("/run")
async def run_reply_graph_api(
    email_body: Optional[str] = Form(None),
    email_subject: Optional[str] = Form(None),
    custom_query_input: Optional[str] = Form(None),
    collection_name: Optional[str] = Form(None),
    tone: Optional[str] = Form("professional"),
    tool_instructions: Optional[str] = Form(None)
):
    """
    API endpoint to run the reply graph.
    """
    state: State = {
        "email_body": email_body or "",
        "tone": tone or "professional",
        "tool_instructions": tool_instructions or "",
        "collection_name": collection_name or "",
        "email_subject": email_subject or "",
        "custom_query_input": custom_query_input or "",
        "input": "",
        "final_response": "",
        "tool_outputs": ""
    }
    result = graph.invoke(state)
    return result
