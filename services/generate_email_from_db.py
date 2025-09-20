from typing import Any
from langchain.chat_models import init_chat_model
from core import settings
from langchain_core.tools import tool
from langchain.chat_models import init_chat_model
from langchain.schema import HumanMessage, SystemMessage
import re


llm = init_chat_model(
    model="gpt-4o-mini",
    temperature=0,
    api_key=settings.OPENAI_API_KEY
)


db_system_prompt = """
You are an expert SQL generator for a PostgreSQL database.

Rules:
- Always return only a single SQL SELECT query.
- Never use INSERT, UPDATE, DELETE, DROP, ALTER, or CREATE.
- Query must always begin with SELECT.
- Do not include explanations or comments, return only SQL.
- Do NOT wrap the SQL in markdown code blocks (do not use triple backticks or add 'sql' at the start).
- Always use fully qualified table names (e.g., public."user").
- If a table name is a reserved word, use double quotes (e.g., "user").
- Prefer queries with WHERE clauses or ORDER BY for more useful results.

Database Schema (PostgreSQL):

1. public."user"(user_id, username, email, password_hash, first_name, last_name, phone, employee_id, designation, department, office_address, user_role, approval_level, is_active, last_login, created_at, updated_at)
2. public.applications(application_id, application_number, applicant_user_id, application_type, description, estimated_cost, priority_level, application_date, status, created_at, updated_at)
3. public.approvals(approval_id, application_id, approver_user_id, approval_level, approval_status, approval_date, comments, created_at)
4. public.orders(order_id, application_id, order_number, order_type, vendor_name, vendor_contact, vendor_address, order_amount, order_date, expected_completion_date, terms_and_conditions, status, created_at, updated_at)
5. public.order_items(item_id, order_id, item_name, item_description, quantity, unit_price, total_price, specifications)
6. public.deliveries(delivery_id, order_id, delivery_number, delivery_agent_user_id, delivery_date, delivery_address, delivery_contact, tracking_number, delivery_status, delivery_notes, received_by_user_id, received_date, created_at, updated_at)
7. public.documents(document_id, reference_type, reference_id, document_name, document_path, file_size, uploaded_by_user_id, uploaded_at)
8. public.audit_log(log_id, table_name, record_id, action, old_values, new_values, changed_by_user_id, changed_at)

Foreign Keys:
- applications.applicant_user_id → public."user".user_id
- approvals.application_id → public.applications.application_id
- approvals.approver_user_id → public."user".user_id
- orders.application_id → public.applications.application_id
- order_items.order_id → public.orders.order_id
- deliveries.order_id → public.orders.order_id
- deliveries.delivery_agent_user_id → public."user".user_id
- deliveries.received_by_user_id → public."user".user_id
- documents.uploaded_by_user_id → public."user".user_id
- audit_log.changed_by_user_id → public."user".user_id

ENUM Types:
- user_role_enum: Admin, Applicant, Approver, Vendor, Delivery_Agent
- priority_level_enum: Low, Medium, High, Critical
- status_enum: Submitted, Under Review, Approved, Rejected
- approval_status_enum: Pending, Approved, Rejected, Returned
- order_type_enum: Work Order, Purchase Order
- order_status_enum: Draft, Issued, In Progress, Completed, Cancelled
- delivery_status_enum: Pending, In Transit, Delivered, Failed, Returned
- reference_type_enum: Application, Approval, Order, Delivery
- audit_action_enum: INSERT, UPDATE, DELETE
"""

def enforce_select_only(sql: str) -> str:
    
    # print(f"Enforcing SELECT only on SQL: {sql}")
    # Remove SQL comments
    sql_no_comments = re.sub(r'(--.*?$|/\\*.*?\\*/)', '', sql, flags=re.MULTILINE | re.DOTALL)
    # Remove markdown code block formatting (triple backticks, optional 'sql') at start and end, even if on their own lines
    lines = sql_no_comments.splitlines()
    # Remove lines that are only triple backticks or triple backticks with 'sql'
    lines = [line for line in lines if not re.match(r'^```(sql)?\\s*$', line.strip(), re.IGNORECASE)]
    sql_clean = '\n'.join(lines).strip()
    # Remove leading whitespace and newlines
    sql_stripped = sql_clean.lstrip()
    # Find first non-empty line
    lines = [line.strip() for line in sql_stripped.splitlines() if line.strip()]
    if not lines:
        raise ValueError(f"Empty SQL query: {sql}")
    first_line = lines[0].lower()
    # Check for SELECT at the start (word boundary, after whitespace)
    if not first_line.startswith('select'):
        raise ValueError(f"Only SELECT queries are allowed. Got: {sql}")
    # Check for forbidden keywords as whole words in the whole query
    sql_lower = sql_stripped.lower()
    forbidden = ["insert", "update", "delete", "drop", "alter", "create"]
    for word in forbidden:
        if re.search(rf'\\b{word}\\b', sql_lower):
            raise ValueError(f"Unsafe SQL detected ('{word}'): {sql}")
    return sql_stripped

def normalize_content(content) -> str:
    """Ensure model output is converted into a plain string."""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        # Sometimes returned as [{"text": "..."}]
        return " ".join(str(c.get("text", c)) if isinstance(c, dict) else str(c) for c in content)
    else:
        return str(content)

# Query Executor
def execute_query(sql: str) -> Any:
    import psycopg2
    from psycopg2.extras import RealDictCursor

    conn = psycopg2.connect(settings.DATABASE_URL)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            try:
                cursor.execute(sql)
                if cursor.description:  # If the query returns rows
                    results = cursor.fetchall()
                    if not results:
                        return {"message": "Query executed successfully, but no data found.", "data": []}
                    return results
                else:
                    return {"message": "Query executed successfully, no results to return."}
            except Exception as e:
                return {"error": str(e), "message": "Error executing query."}
    finally:
        conn.close()

def generate_select_query(user_request: str) -> str:
    response = llm.invoke([
        SystemMessage(content=db_system_prompt),
        HumanMessage(content=user_request)
    ])
    sql_query = normalize_content(response.content).strip()
    
    # print(f"Generated SQL: {sql_query}")
    enforce_query =  enforce_select_only(sql_query)
    return execute_query(enforce_query)