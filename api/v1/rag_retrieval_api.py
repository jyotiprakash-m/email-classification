from fastapi import APIRouter, Query
from services.rag_retrieval import retrieve_from_pgvector

router = APIRouter(prefix="/v1/rag", tags=["RAG Retrieval"])

@router.get("/retrieve")
async def rag_retrieve(
	query: str = Query(..., description="Search query for retrieval"),
	collection_name: str = Query(..., description="PGVector collection name"),
	k: int = Query(3, description="Number of top results to return")
):
	"""
	Retrieve top-k most similar documents from PGVector for a given query and collection name.
	"""
	output = retrieve_from_pgvector(query, collection_name, k)
	# Format results for API response
	return {
		"llm_answer": output["llm_answer"],
		"results": [
			{
				"content": doc.page_content,
				"metadata": doc.metadata
			}
			for doc in output["results"]
		]
	}
