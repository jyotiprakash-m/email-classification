from fastapi import APIRouter, Form
from typing import Optional

from langsmith import traceable
from graphs.email_classification_graph import graph, State

router = APIRouter(prefix="/v1/email-graph", tags=["Email Classification Graph"])

@traceable(name="classify_email_api")
@router.post("/run")
async def run_email_graph_api(
    user_id: str = Form(...),
    org_id: str = Form(...),
    offset: Optional[int] = Form(None),
    limit: Optional[int] = Form(None)
):
    """
    API endpoint to run the email classification graph.
    """
    state: State = {
        "userId": user_id or "",
        "orgId": org_id or "",
        "offset": offset,
        "limit": limit,
        "emails": None
    }
    result = graph.invoke(state)
    return result
