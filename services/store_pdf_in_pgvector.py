from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_postgres import PGVector
from dotenv import load_dotenv
import hashlib
import os
import tempfile
from core.config import settings

load_dotenv()

def store_pdf_in_pgvector(file):
    """
    Store a PDF file-like object into PGVector with chunking, cleaning, and deduplication.

    Args:
        file: File-like object (e.g., from upload)

    Returns:
        dict: Information about how many chunks were added/skipped.
    """
    # Save the uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(file.read())
        temp_path = temp_file.name

    try:
        # Load PDF
        loader = PyPDFLoader(temp_path)
        docs = loader.load()

        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            add_start_index=True
        )
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
            collection_name="hr_documents",
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
