from services.classify_email import classify_email
from sqlmodel import Session, select
from models.schema import Org
from models.request_response import OrgRead
from core.database import engine
from typing import Optional, TypedDict
from langgraph.graph import StateGraph, END
import imaplib
import email
import json
import re
from bs4 import BeautifulSoup
from core import settings
from langchain.chat_models import init_chat_model
from langchain.schema import HumanMessage, SystemMessage
#  Create LLM

llm = init_chat_model(
    model="gpt-4o-mini",
    temperature=0,
    api_key=settings.OPENAI_API_KEY
)


# 1. Define state
class State(TypedDict, total=False):
    userId: str
    orgId: str
    offset: Optional[int]
    limit: Optional[int]
    emails: Optional[list]
    


# 2. Define nodes
def fetch_emails(state: State):

    # Get Org details
    org_id = state.get("orgId")
    limit = state.get("limit", 1)
    offset = state.get("offset", 0)
    org_details = None
    if org_id:
        with Session(engine) as session:
            statement = select(Org).where(Org.id == int(org_id))
            result = session.exec(statement).first()
            if result:
                org_read = OrgRead.model_validate(result)
                org_details = org_read.model_dump()
                print(f"Step 1: Fetched Org Details: {org_details}")
    
    # Now we will fetch emails for this org
    if org_details:
        gmail_user = org_details.get("email")
        gmail_app_pass = org_details.get("password")
        imap_server = "imap.gmail.com"
        imap_port = 993
        fetched_emails_data = []
        if isinstance(gmail_user, str) and isinstance(gmail_app_pass, str):
            try:
                mail = imaplib.IMAP4_SSL(imap_server, imap_port)
                mail.login(gmail_user, gmail_app_pass)
                status, messages = mail.select("inbox")
                if status == 'OK':
                    status, email_ids = mail.search(None, 'ALL')
                    if status == 'OK' and email_ids[0]:
                        all_email_ids = email_ids[0].split()
                        # Apply offset and limit
                        offset = state.get("offset")
                        limit = state.get("limit")
                        # Ensure offset and limit are integers
                        offset = int(offset) if offset is not None else 0
                        limit = int(limit) if limit is not None else 1
                        # Get the correct slice (latest emails first)
                        selected_ids = all_email_ids[::-1][offset:offset+limit]
                        for email_id in selected_ids:
                            status, msg_data = mail.fetch(email_id, "(RFC822)")
                            if status == 'OK' and msg_data and msg_data[0]:
                                raw_email = msg_data[0][1] if isinstance(msg_data[0], tuple) and len(msg_data[0]) > 1 else None
                                if isinstance(raw_email, bytes):
                                    msg = email.message_from_bytes(raw_email)
                                    subject = msg['subject']
                                    from_address = msg['from']
                                    date = msg['date']
                                    plain_text_body = ""
                                    html_body_content = ""
                                    if msg.is_multipart():
                                        for part in msg.walk():
                                            ctype = part.get_content_type()
                                            cdispo = part.get_content_disposition()
                                            if ctype == 'text/plain' and cdispo is None:
                                                payload = part.get_payload(decode=True)
                                                if isinstance(payload, bytes):
                                                    plain_text_body = payload.decode(errors='ignore')
                                                    break
                                            elif ctype == 'text/html' and cdispo is None:
                                                payload = part.get_payload(decode=True)
                                                if isinstance(payload, bytes):
                                                    html_body_content = payload.decode(errors='ignore')
                                    else:
                                        payload = msg.get_payload(decode=True)
                                        if isinstance(payload, bytes):
                                            plain_text_body = payload.decode(errors='ignore')
                                    def clean_email_body(body: str) -> str:
                                        """
                                        Removes HTML tags and inline styles from email body.
                                        Returns clean plain text.
                                        """
                                        if body is None:
                                            return ""
                                        soup = BeautifulSoup(body, "html.parser")
                                        for script_or_style in soup(["script", "style"]):
                                            script_or_style.extract()
                                        import bs4
                                        for tag in soup.find_all(True):
                                            if isinstance(tag, bs4.element.Tag) and "style" in tag.attrs:
                                                del tag.attrs["style"]
                                        text = soup.get_text(separator="\n", strip=True)
                                        text = re.sub(r'\n\s*\n', '\n\n', text).strip()
                                        return text
                                    final_body = plain_text_body if plain_text_body else clean_email_body(html_body_content)
                                    email_data = {
                                        "email_id": email_id.decode() if isinstance(email_id, bytes) else str(email_id),
                                        "subject": subject,
                                        "from": from_address,
                                        "date": date,
                                        "body": final_body,
                                    }
                                    fetched_emails_data.append(email_data)
                mail.logout()
            except Exception as e:
                print(f"Error fetching email: {e}")
        state["emails"] = fetched_emails_data
    return state


def custom_model_classification(state: State):
    emails = state.get("emails", [])
    if emails and isinstance(emails, list):
        for email_obj in emails:
            email_body = email_obj.get("body", "")
            try:
                email_obj["classification_report"] = classify_email(email_body)
            except Exception as e:
                email_obj["classification_report"] = {"error": str(e)}
    else:
        state["emails"] = [{"classification_report": {"error": "No email body available for classification."}}]
    return state

sentiment_system_prompt = """
You are a sentiment analysis assistant.  
Classify the sentiment of the given text into one of these categories:  
- Positive  
- Negative  
- Neutral  

Guidelines:  
1. Focus only on emotional tone, not factual accuracy.  
2. If multiple sentiments are present, choose the dominant one.  
3. If the text contains no clear emotion (e.g., instructions, facts, or neutral descriptions), classify as Neutral.  
4. Respond with only the category name (Positive, Negative, or Neutral). Do not add explanations.  
"""



def sentiment_analysis(state: State):
    emails = state.get("emails", [])
    if emails and isinstance(emails, list):
        for email_obj in emails:
            email_body = email_obj.get("body", "")
            email_subject = email_obj.get("subject", "")
            try:
                if not email_body.strip() and not email_subject.strip():
                    email_obj["sentiment_analysis"] = "Neutral"
                    continue

                # Combine subject and body for sentiment analysis
                prompt_text = f"Subject: {email_subject}\nBody: {email_body}"
                response = llm.invoke([
                    SystemMessage(content=sentiment_system_prompt),
                    HumanMessage(content=prompt_text)
                ])

                if hasattr(response, 'content'):
                    content = response.content
                    if isinstance(content, str):
                        sentiment = content.strip()
                    elif isinstance(content, list):
                        sentiment = " ".join(str(item) for item in content).strip()
                    else:
                        sentiment = str(content).strip()
                else:
                    sentiment = str(response).strip()
                email_obj["sentiment_analysis"] = sentiment
            except Exception as e:
                email_obj["sentiment_analysis"] = {"error": str(e)}
    else:
        state["emails"] = [{"sentiment_analysis": {"error": "No email body available for sentiment analysis."}}]
    return state


# 3. Build graph
workflow = StateGraph(State)

workflow.add_node("fetch_emails", fetch_emails)
workflow.add_node("custom_model_classification", custom_model_classification)
workflow.add_node("sentiment_analysis", sentiment_analysis)

workflow.set_entry_point("fetch_emails")
workflow.add_edge("fetch_emails", "custom_model_classification")
workflow.add_edge("custom_model_classification", "sentiment_analysis")
workflow.add_edge("sentiment_analysis", END)

# 4. Compile
graph = workflow.compile()


# if __name__ == "__main__":
#     result = graph.invoke({"userId": "1", "orgId": "1"})
#     print("\n=== Final Result ===")
#     print(result)
