# ---
# Approach Summary: PDF Chunking & Vector Storage (for Interview)
#
# 1. Accept PDF file as bytes and save to a temporary file.
# 2. Use PyPDFLoader to extract text from the PDF.
# 3. Apply RecursiveCharacterTextSplitter to split text into overlapping chunks (chunk_size=1000, chunk_overlap=200).
#    - This preserves semantic boundaries and ensures context continuity for retrieval/LLM tasks.
# 4. Clean each chunk and generate a content hash for deduplication.
# 5. Use OpenAIEmbeddings to embed each chunk.
# 6. Store chunks in PGVector (Postgres vector DB), skipping duplicates based on content hash.
# 7. Return stats on added chunks and skipped duplicates.
#
# This approach is robust for semantic search, RAG, and LLM pipelines, balancing chunk size, context, and deduplication.
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_postgres import PGVector
from dotenv import load_dotenv
import hashlib
import os
import tempfile
from core.config import settings
from models.request_response import StorePDFRequest

load_dotenv()

def store_pdf_in_pgvector(file_or_path, collection_name="hr_documents", loader_cls=None):
    """
    Store a document (bytes or file path) into PGVector with chunking, cleaning, and deduplication.

    Args:
        file_or_path: bytes (file content) or str (file path)
        collection_name: Name of the PGVector collection to store chunks in.
        loader_cls: Document loader class to use (from langchain_community.document_loaders)

    Returns:
        dict: Information about how many chunks were added/skipped.
    """
    # If bytes, save to temp file
    if isinstance(file_or_path, bytes):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as temp_file:
            temp_file.write(file_or_path)
            temp_path = temp_file.name
    else:
        temp_path = file_or_path

    try:
        # Use provided loader class, default to PyPDFLoader
        loader = loader_cls(temp_path) if loader_cls else PyPDFLoader(temp_path)
        docs = loader.load()

        # Split into chunks
        # Recommended: RecursiveCharacterTextSplitter (used below)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            add_start_index=True
        )
    # Alternative splitters for learning/experimentation:
    #
    # 1. CharacterTextSplitter: Splits text into fixed-size character chunks. Simple, but may break sentences/words.
    #    from langchain_text_splitters import CharacterTextSplitter
    #    char_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    #    chunks = char_splitter.split_documents(docs)
    #
    # 2. SentenceTextSplitter: Splits at sentence boundaries. Preserves meaning, but chunk sizes may vary.
    #    from langchain_text_splitters import SentenceTextSplitter
    #    sentence_splitter = SentenceTextSplitter(chunk_size=1000, chunk_overlap=200)
    #    chunks = sentence_splitter.split_documents(docs)
    #
    # 3. TokenTextSplitter: Splits by token count (model-compatible). Useful for LLM context management.
    #    from langchain_text_splitters import TokenTextSplitter
    #    token_splitter = TokenTextSplitter(chunk_size=256, chunk_overlap=32)
    #    chunks = token_splitter.split_documents(docs)
    #
    # 4. MarkdownTextSplitter: Splits markdown docs by headers. Good for structured markdown files.
    #    from langchain_text_splitters import MarkdownTextSplitter
    #    md_splitter = MarkdownTextSplitter(chunk_size=1000, chunk_overlap=200)
    #    chunks = md_splitter.split_documents(docs)
    #
    # 5. SpacyTextSplitter: Uses spaCy for sentence boundaries. More accurate for complex text.
    #    from langchain_text_splitters import SpacyTextSplitter
    #    spacy_splitter = SpacyTextSplitter(chunk_size=1000, chunk_overlap=200)
    #    chunks = spacy_splitter.split_documents(docs)
    #
    # 6. NLTKTextSplitter: Uses NLTK for sentence boundaries. Similar to spaCy, but uses NLTK.
    #    from langchain_text_splitters import NLTKTextSplitter
    #    nltk_splitter = NLTKTextSplitter(chunk_size=1000, chunk_overlap=200)
    #    chunks = nltk_splitter.split_documents(docs)
    #
    # 7. HTMLHeaderTextSplitter: Splits HTML docs by header tags (h1, h2, etc.).
    #    from langchain_text_splitters import HTMLHeaderTextSplitter
    #    html_splitter = HTMLHeaderTextSplitter(chunk_size=1000, chunk_overlap=200)
    #    chunks = html_splitter.split_documents(docs)
    #
    # 8. Language-specific splitters: For code, splits by function/class (e.g., PythonCodeTextSplitter).
    #    from langchain_text_splitters import PythonCodeTextSplitter
    #    py_splitter = PythonCodeTextSplitter(chunk_size=1000, chunk_overlap=200)
    #    chunks = py_splitter.split_documents(docs)
    #
    # You can experiment by swapping out the splitter above to see how chunking affects downstream tasks.
        chunks = text_splitter.split_documents(docs)

        # Clean chunks and add content hash
        for chunk in chunks:
            chunk.page_content = chunk.page_content.replace('\x00', '')
            content_hash = hashlib.sha256(chunk.page_content.encode('utf-8')).hexdigest()
            chunk.metadata['content_hash'] = content_hash

        # Embeddings
        embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

        # PGVector store
        vector_store = PGVector(
            embeddings=embeddings,
            collection_name=collection_name,
            connection=settings.DATABASE_URL,
        )

        # Deduplication
        unique_chunks = []
        duplicate_count = 0

        try:
            test_docs = vector_store.similarity_search("test", k=1000)
            existing_hashes = {doc.metadata['content_hash'] for doc in test_docs if 'content_hash' in doc.metadata}

            for chunk in chunks:
                if chunk.metadata['content_hash'] not in existing_hashes:
                    unique_chunks.append(chunk)
                else:
                    duplicate_count += 1
        except Exception as e:
            print(f"Could not check database for duplicates: {e}")
            unique_chunks = chunks

        # Add unique chunks to PGVector
        if unique_chunks:
            vector_store.add_documents(unique_chunks)
            print(f"Added {len(unique_chunks)} new documents, skipped {duplicate_count} duplicates.")
        else:
            print("No new documents to add - all already exist.")

        return {
            "added_chunks": len(unique_chunks),
            "skipped_duplicates": duplicate_count
        }

    finally:
        # Clean up temporary file
        os.remove(temp_path)


