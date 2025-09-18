from langchain.chat_models import init_chat_model
from langchain.prompts import ChatPromptTemplate
from core import settings
from services.rag_retrieval import retrieve_from_pgvector

def generate_email_with_rag(email_text: str, collection_name: str, k: int = 3) -> str:
	"""
	Generate an email reply using RAG: retrieve context from PGVector and use LLM to answer.
	"""
	result = retrieve_from_pgvector(email_text, collection_name, k)
	context = "\n\n".join([doc.page_content for doc in result["results"]])

	system_prompt = """
	You are an assistant that generates polite, professional, and context-aware email replies.
	Rules:
	1. Reply in a formal and concise tone.
	2. Acknowledge the sender’s request or concern.
	3. Use the provided context to inform your reply (do not fabricate details).
	4. End with a professional closing.
	"""

	llm = init_chat_model(
		model="gpt-4o-mini",
		temperature=0,
		api_key=settings.OPENAI_API_KEY
	)

	prompt = ChatPromptTemplate.from_messages([
		("system", system_prompt),
		("human", f"Context:\n{context}\n\nEmail received:\n{email_text}\n\nWrite a professional reply:")
	])
	chain = prompt | llm
	response = chain.invoke({})
	if hasattr(response, "content"):
		content = response.content
		if isinstance(content, str):
			return content
		elif isinstance(content, list):
			# Join list items as string
			return " ".join(str(item) for item in content)
		elif isinstance(content, dict):
			return str(content)
		else:
			return str(content)
	return str(response)
