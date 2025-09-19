from typing import Optional, TypedDict, Any
from langgraph.graph import StateGraph, END
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import SecretStr
from dotenv import load_dotenv
import os
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain.chains import RetrievalQA
from core import settings
from langchain_core.tools import tool
from langchain.chat_models import init_chat_model
from langchain.schema import HumanMessage, SystemMessage
import re
load_dotenv()

# 1. Define state type
class State(TypedDict, total=False):
    userId: str
    tone: str
    email_body: str
    tool_instructions: Optional[str]
    collection_name: Optional[str]
    input: Optional[str]
    final_response: Optional[str]
    tool_outputs: Optional[Any]


# 2. Define some tools
@tool
def organization_rag_fetcher(query: str , collection_name: str = "hr_documents") -> dict:
    """
    Retrieve relevant documents from the email_classification PGVector database and generate a context-aware response using an LLM.
    - Input: Natural language query related to any document type (e.g., HR, procurement, policy, order, approval, technical, legal, etc.).
    - Output: AI-generated answer informed by the most relevant documents, plus a list of supporting document excerpts and metadata (source, page).
    - Use case: When a user email or request requires factual information, policy details, or document-based evidence from the organization's database.

    Usage:
    - If tool_instructions is 'rag' and a collection_name is provided, this tool will be invoked to fetch relevant documents and generate a context-aware answer using the specified collection.
    """
    # Embeddings
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small", api_key=SecretStr(settings.OPENAI_API_KEY)
    )

    # Connect to PGVector
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=settings.DATABASE_URL,
    )

    # Retriever
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3},
    )

    # LLM for response generation
    # llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # Retrieval + QA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        return_source_documents=True,
    )

    # Run query
    result = qa_chain.invoke({"query": query})

    # Format output
    answer = result["result"]
    source_docs = []
    for doc in result["source_documents"]:
        source_docs.append({
            "content": doc.page_content,
            "source": doc.metadata.get("source", "Unknown"),
            "page": doc.metadata.get("page", "Unknown")
        })

    return {
        "query": query,
        "answer": answer,
        "sources": source_docs
    }
    
    
    
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
            cursor.execute(sql)
            if cursor.description:  # If the query returns rows
                results = cursor.fetchall()
                return results
            else:
                return {"message": "Query executed successfully, no results to return."}
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

@tool
def db_query_generator(s: str) -> str:
    """Generate a safe SELECT SQL query for the Jharkhand procurement database."""
    return generate_select_query(s)

@tool
def generic_email_generator(email_text: str) -> str:
    """Analyze the input email and generate a generic, polite, context-aware reply."""
    
    system_prompt = """
    You are an assistant that generates polite, professional, and context-aware email replies. 
    Rules:
    1. Reply in a formal and concise tone.
    2. Acknowledge the sender’s request or concern.
    3. Provide a generic but relevant response (no sensitive or fabricated details).
    4. End with a professional closing.
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", f"Email received:\n\n{email_text}\n\nWrite a professional reply:")
    ])

    chain = prompt | llm
    response = chain.invoke({})
    # Ensure the return value is always a string
    if isinstance(response.content, str):
        return response.content
    else:
        return str(response.content)


tools = [organization_rag_fetcher, db_query_generator, generic_email_generator]

# 3. Create LLM

llm = init_chat_model(
    model="gpt-4o-mini",
    temperature=0,
    api_key=settings.OPENAI_API_KEY
)

# 4. Create a default prompt for the agent (must include agent_scratchpad)
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI assistant that can use tools when needed."),
    ("user", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),  # required placeholder
])

# 5. Build agent that knows about the tools
agent = create_openai_functions_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


# 6. Define nodes
def prepare_input(state: State):
    userId = state.get("userId", "")
    email_body = state.get("email_body", "")
    tone = state.get("tone", "professional")
    tool_instructions = state.get("tool_instructions", "")
    state["input"] = (
    f"User ID: {userId}\n"
    f"Email Body: {email_body}\n"
    f"Desired Tone: {tone}\n\n"
    f"Tool Instructions: {tool_instructions}\n"
    "Based on the above email, generate a polite and context-aware reply. "
    "If the email requires database information, first generate a safe SQL SELECT query "
    "to fetch the necessary data from the Jharkhand procurement database, then use that data to inform your reply. "
    "You may also use document retrieval tools to fetch relevant HR documents if needed. "
    "Use the tools at your disposal as needed."
)
    return state


def tool_execution(state: State):
    """Pass state.get('input') to the agent executor and store result."""
    response = agent_executor.invoke({"input": state.get("input")})
    state["tool_outputs"] = response.get("output")
    return state


def final_response(state: State):
    tool_outputs = state.get("tool_outputs")
    # Generate a user-facing final response
    if tool_outputs:
        state["final_response"] = tool_outputs
    else:
        state["final_response"] = "No reply could be generated."
    return state


# 7. Build graph
workflow = StateGraph(State)

workflow.add_node("prepare_input", prepare_input)
workflow.add_node("tool_execution", tool_execution)
workflow.add_node("final_response", final_response)

workflow.set_entry_point("prepare_input")
workflow.add_edge("prepare_input", "tool_execution")
workflow.add_edge("tool_execution", "final_response")
workflow.add_edge("final_response", END)

# 8. Compile graph
graph = workflow.compile()


# if __name__ == "__main__":
#     initial_state: State = {
#         "input": "Reverse this number 123456789."
#     }
#     result = graph.invoke(initial_state)
#     print("\n=== Final Result ===")
#     print(result)
