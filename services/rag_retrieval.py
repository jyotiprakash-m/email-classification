from core import settings
from langchain.chat_models import init_chat_model
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
import os

def retrieve_from_pgvector(query: str, collection_name: str, k: int = 3):
	# Initialize LLM
	# Retrieve results
	embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
	vector_store = PGVector(
		embeddings=embeddings,
		collection_name=collection_name,
		connection=os.getenv("DATABASE_URL"),
	)
	retriever = vector_store.as_retriever(
		search_type="similarity",
		search_kwargs={"k": k},
	)
	results = retriever.invoke(query)

	# Initialize LLM
	llm = init_chat_model(
		model="gpt-4o-mini",
		temperature=0,
		api_key=settings.OPENAI_API_KEY
	)

	# Aggregate retrieved docs for context
	context = "\n\n".join([doc.page_content for doc in results])
	prompt = f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"
	llm_response = llm.invoke(prompt)

	return {
		"results": results,
		"llm_answer": llm_response.content if hasattr(llm_response, 'content') else str(llm_response)
	}

