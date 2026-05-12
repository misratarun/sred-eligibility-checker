"""
ingest.py — Load CRA SR&ED PDFs, chunk, embed, and persist to ChromaDB.

Usage:
    python ingest.py
"""

import os
import sys
from pathlib import Path

import pdfplumber
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings

DATA_DIR = Path("./data")
CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "sred_guidelines"
EMBED_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


def load_pdfs(data_dir: Path) -> list[Document]:
    """Extract text from all PDFs under data_dir, returning LangChain Documents."""
    documents: list[Document] = []
    pdf_files = sorted(data_dir.rglob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in {data_dir}/")
        sys.exit(1)

    print(f"Found {len(pdf_files)} PDF file(s):")
    for pdf_path in pdf_files:
        print(f"  • {pdf_path.name}")

    for pdf_path in pdf_files:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text()
                    if not text or not text.strip():
                        continue
                    documents.append(
                        Document(
                            page_content=text.strip(),
                            metadata={
                                "source": pdf_path.name,
                                "page": page_num,
                            },
                        )
                    )
        except Exception as exc:
            print(f"  WARNING: Could not read {pdf_path.name}: {exc}")

    return documents


def chunk_documents(documents: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_documents(documents)


def chroma_exists() -> bool:
    return Path(CHROMA_DIR).exists() and any(Path(CHROMA_DIR).iterdir())


def ingest():
    if not DATA_DIR.exists():
        print(f"Error: {DATA_DIR}/ directory not found.")
        print("Create the directory and add CRA SR&ED PDF files to it.")
        sys.exit(1)

    if chroma_exists():
        answer = input(
            f"ChromaDB already exists at {CHROMA_DIR}/. Re-ingest? [y/N]: "
        ).strip().lower()
        if answer != "y":
            print("Skipping ingestion. Existing knowledge base will be used.")
            return

    print("\n── Loading PDFs ──────────────────────────────────────")
    raw_docs = load_pdfs(DATA_DIR)
    print(f"Extracted {len(raw_docs)} page(s) across all PDFs.")

    print("\n── Chunking ──────────────────────────────────────────")
    chunks = chunk_documents(raw_docs)
    print(f"Created {len(chunks)} chunk(s) (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP}).")

    print("\n── Embedding & Persisting ────────────────────────────")
    print(f"Loading embedding model: {EMBED_MODEL} (this may take a moment on first run)...")
    embeddings = SentenceTransformerEmbeddings(model_name=EMBED_MODEL)

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_DIR,
    )

    print(f"\n✓ Ingestion complete. {len(chunks)} chunks persisted to {CHROMA_DIR}/")
    print(f"  Collection: {COLLECTION_NAME}")


if __name__ == "__main__":
    ingest()
