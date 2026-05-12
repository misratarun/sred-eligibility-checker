"""
rag_chain.py — LangChain RAG chain: ChromaDB retrieval + Claude generation.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain_anthropic import ChatAnthropic
from langchain_chroma import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

load_dotenv()

CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "sred_guidelines"
EMBED_MODEL = "all-MiniLM-L6-v2"
CLAUDE_MODEL = "claude-haiku-4-5-20251001"
TOP_K = 5

SYSTEM_PROMPT = """You are a CRA SR&ED eligibility specialist. Given a description of engineering work
and retrieved sections from CRA's official SR&ED guidelines, assess whether the work
qualifies as SR&ED under Canada's Income Tax Act.

Classify the work as one of:
- ELIGIBLE — clearly meets SR&ED criteria
- LIKELY ELIGIBLE — meets most criteria, minor gaps
- BORDERLINE — partial alignment, needs more information
- NOT ELIGIBLE — does not meet core SR&ED criteria

Your response must include:
1. CLASSIFICATION: (one of the four above)
2. CONFIDENCE: (High / Medium / Low)
3. CRITERIA ASSESSMENT: Which of the three core SR&ED criteria are met:
   - Technological uncertainty (was there a knowledge gap?)
   - Systematic investigation (was there a structured process?)
   - Technological advancement (did it advance general knowledge?)
4. SUPPORTING EVIDENCE: Direct citations from the retrieved CRA source sections
5. GAPS OR RISKS: What is missing or could weaken the claim
6. RECOMMENDATION: One concrete suggestion to strengthen eligibility documentation

Be specific, conservative, and cite your sources precisely. Do not speculate
beyond what the CRA documentation supports."""

RAG_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        (
            "human",
            "Retrieved CRA guideline sections:\n\n{context}\n\n"
            "Engineering work description:\n{question}\n\n"
            "Provide your SR&ED eligibility assessment.",
        ),
    ]
)


@dataclass
class RAGResult:
    answer: str
    source_chunks: list[dict]


def _format_docs(docs) -> str:
    parts = []
    for i, doc in enumerate(docs, start=1):
        src = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page", "?")
        parts.append(f"[Source {i}: {src}, p.{page}]\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


def load_vectorstore() -> Chroma:
    if not Path(CHROMA_DIR).exists():
        raise FileNotFoundError(
            f"ChromaDB not found at {CHROMA_DIR}/. Run: python ingest.py"
        )
    embeddings = SentenceTransformerEmbeddings(model_name=EMBED_MODEL)
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )


def build_chain(vectorstore: Chroma):
    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": TOP_K, "fetch_k": 20, "lambda_mult": 0.5},
    )
    llm = ChatAnthropic(
        model=CLAUDE_MODEL,
        anthropic_api_key=os.environ["ANTHROPIC_API_KEY"],
        max_tokens=2048,
    )
    chain = (
        {"context": retriever | _format_docs, "question": RunnablePassthrough()}
        | RAG_PROMPT_TEMPLATE
        | llm
        | StrOutputParser()
    )
    return chain, retriever


def run_query(question: str) -> RAGResult:
    """Run a query through the full RAG pipeline. Returns answer + source chunks."""
    vectorstore = load_vectorstore()
    chain, retriever = build_chain(vectorstore)

    # Retrieve source docs separately so we can return them with scores
    docs_with_scores = vectorstore.similarity_search_with_relevance_scores(
        question, k=TOP_K
    )
    answer = chain.invoke(question)

    source_chunks = [
        {
            "text": doc.page_content,
            "source": doc.metadata.get("source", "unknown"),
            "page": doc.metadata.get("page", "?"),
            "score": round(score, 4),
        }
        for doc, score in docs_with_scores
    ]
    source_chunks.sort(key=lambda x: x["score"], reverse=True)

    return RAGResult(answer=answer, source_chunks=source_chunks)


def get_collection_info() -> dict:
    """Return metadata about the persisted collection (for sidebar display)."""
    try:
        vs = load_vectorstore()
        collection = vs._collection
        count = collection.count()
        # Get unique source filenames
        results = collection.get(include=["metadatas"])
        sources = sorted(
            {m.get("source", "unknown") for m in (results["metadatas"] or [])}
        )
        return {"chunk_count": count, "sources": sources}
    except Exception:
        return {"chunk_count": 0, "sources": []}
