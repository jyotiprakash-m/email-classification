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
from services.generate_email_from_db import generate_select_query
from services.rag_retrieval import retrieve_from_pgvector
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
    email_subject: Optional[str]
    tool_instructions: Optional[str]
    collection_name: Optional[str]
    custom_query_input: Optional[str]
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
    result = retrieve_from_pgvector(query, collection_name, k=3)
    # Format output for the tool
    source_docs = []
    for doc in result["results"]:
        source_docs.append({
            "content": doc.page_content,
            "source": doc.metadata.get("source", "Unknown"),
            "page": doc.metadata.get("page", "Unknown")
        })
    return {
        "query": query,
        "answer": result["llm_answer"],
        "sources": source_docs
    }
    

@tool
def db_query_generator(input: str) -> str:
    """
    We will pass either the custom_query_input (if provided) or the input to generate a SQL SELECT query and execute it.
    - Input: Natural language request or question that requires data from the organization's PostgreSQL database (e.g., procurement, orders, approvals, users, etc.).
    - Output: Executes a validated SELECT query and returns the results as structured data.
    - Use case: When tool_instructions is 'db' or the user request requires factual information from the database, this tool will be invoked to generate and run a secure SQL SELECT query.
    """
    return generate_select_query(input)

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
    email_body = state.get("email_body", "")
    email_subject = state.get("email_subject", "")
    tone = state.get("tone", "professional")
    tool_instructions = state.get("tool_instructions", "")
    collection_name = state.get("collection_name", "")
    custom_query_input = state.get("custom_query_input", "")

    if custom_query_input:
        state["input"] = custom_query_input
        return state

    prompt_lines = [
        f"Email Body: {email_body}",
        f"Email Subject: {email_subject}",
        f"Desired Tone: {tone}"
    ]
    if tool_instructions:
        prompt_lines.append(f"Tool Instructions: {tool_instructions}")
    if collection_name:
        prompt_lines.append(f"Collection Name: {collection_name}")
    prompt_lines.append(
        "Generate a polite, context-aware reply to the above email. Use tools for database or document retrieval if needed."
    )
    state["input"] = "\n".join(prompt_lines)
    return state


def tool_execution(state: State):
    """Pass state.get('input') to the agent executor and store result."""
    response = agent_executor.invoke({"input": state.get("input")})
    state["tool_outputs"] = response.get("output")
    return state


def final_response(state: State):
    tool_outputs = state.get("tool_outputs")
    # Use LLM to format the final response as a professional email
    if tool_outputs:
        format_prompt = (
            "Format the following content as a professional, polite, and context-aware email reply. "
            "Ensure proper greeting, body, and closing.\n\nContent to format:\n" + str(tool_outputs)
        )
        response = llm.invoke(format_prompt)
        if hasattr(response, "content"):
            state["final_response"] = response.content if isinstance(response.content, str) else str(response.content)
        else:
            state["final_response"] = str(response)
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
