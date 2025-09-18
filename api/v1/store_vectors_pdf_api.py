from fastapi import APIRouter, UploadFile, File, HTTPException, Form
import os
import tempfile
from langchain_community.document_loaders import (
	PyPDFLoader, CSVLoader, UnstructuredExcelLoader, UnstructuredMarkdownLoader,
	UnstructuredWordDocumentLoader, TextLoader, UnstructuredHTMLLoader,
	UnstructuredPowerPointLoader
)
from services.store_pdf_in_pgvector import store_pdf_in_pgvector

router = APIRouter(prefix="/v1", tags=["Store Document Vectors"])

@router.post("/store_document_vector")
async def store_document_vector(
	file: UploadFile = File(..., description="Supported types: PDF, CSV, Excel, Markdown, Word, Text, HTML, PPT"),
	collection_name: str = Form("hr_documents")
):
	"""
	Endpoint to store a document's vectors in PGVector.
	Accepts various document types: PDF, CSV, Excel, Markdown, Word, Text, HTML, PPT.
	Returns chunking/deduplication info.
	"""
	loader_map = {
		"application/pdf": PyPDFLoader,
		"text/csv": CSVLoader,
		"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": UnstructuredExcelLoader,
		"application/vnd.ms-excel": UnstructuredExcelLoader,  # Added support for .xls files
		"text/markdown": UnstructuredMarkdownLoader,
		"application/vnd.openxmlformats-officedocument.wordprocessingml.document": UnstructuredWordDocumentLoader,
		"application/msword": UnstructuredWordDocumentLoader,
		"text/plain": TextLoader,
		"text/html": UnstructuredHTMLLoader,
		"application/vnd.ms-powerpoint": UnstructuredPowerPointLoader,
		"application/vnd.openxmlformats-officedocument.presentationml.presentation": UnstructuredPowerPointLoader,
	}

	if file.content_type not in loader_map:
		raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

	try:
			file_bytes = await file.read()
			loader_cls = loader_map[file.content_type]
			result = store_pdf_in_pgvector(file_bytes, collection_name=collection_name, loader_cls=loader_cls)
			return {"status": "success", **result}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))
