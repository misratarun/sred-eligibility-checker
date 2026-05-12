# SR&ED Eligibility Checker 🍁

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3-green?logo=chainlink)](https://www.langchain.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-0.6-orange)](https://www.trychroma.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.45-red?logo=streamlit)](https://streamlit.io/)
[![Claude](https://img.shields.io/badge/Claude-Haiku-blueviolet?logo=anthropic)](https://www.anthropic.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A production-quality Retrieval-Augmented Generation (RAG) application that assesses
whether engineering work qualifies for Canada's SR&ED tax credit program, with cited
reasoning drawn directly from CRA's official policy documents.

---

## What Is SR&ED?

SR&ED (Scientific Research & Experimental Development) is Canada's largest federal
tax incentive program. It provides tax credits for eligible R&D work under the
Income Tax Act. Eligibility hinges on three criteria: **technological uncertainty**,
**systematic investigation**, and **technological advancement**.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        INGESTION PIPELINE                       │
│                                                                 │
│   ./data/*.pdf                                                  │
│       │                                                         │
│       ▼                                                         │
│   pdfplumber  ──► RecursiveCharacterTextSplitter                │
│   (extract)        (chunk_size=800, overlap=100)                │
│                         │                                       │
│                         ▼                                       │
│               SentenceTransformers                              │
│               (all-MiniLM-L6-v2, local)                        │
│                         │                                       │
│                         ▼                                       │
│                   ChromaDB (./chroma_db/)                       │
│                   persisted vector store                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         QUERY PIPELINE                          │
│                                                                 │
│   User Input (Streamlit / CLI)                                  │
│       │                                                         │
│       ▼                                                         │
│   SentenceTransformers embed query                              │
│       │                                                         │
│       ▼                                                         │
│   ChromaDB MMR retrieval (top 5 diverse chunks)                 │
│       │                                                         │
│       ▼                                                         │
│   LangChain RAG Chain                                           │
│       │                                                         │
│       ▼                                                         │
│   Claude Haiku (claude-haiku-4-5-20251001)                      │
│       │                                                         │
│       ▼                                                         │
│   Structured Assessment + Source Citations                      │
│       │                                                         │
│       ▼                                                         │
│   Streamlit UI (two tabs)                                       │
│   ├── Tab 1: Classification + Full Assessment                   │
│   └── Tab 2: Source Evidence with relevance scores             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Architecture Decisions

### Why ChromaDB over Pinecone or Weaviate

ChromaDB's local persistence mode is a natural fit for a single-tenant compliance use
case: data never leaves the machine, there is no network dependency, and costs remain
zero during development and testing. Retrieval latency is also lower without a round
trip to a cloud API. ChromaDB exposes a nearly identical interface to Pinecone's Python
client, making a future migration to Pinecone straightforward when the application
needs to scale to multi-tenant or cloud deployment.

### Chunking Strategy

A chunk size of 800 tokens was chosen to preserve the full context of a regulatory
clause or sub-criterion without exceeding the relevance window where retrieval quality
degrades. The 100-token overlap prevents a criterion definition from being split across
two chunks and losing its qualifying language. CRA SR&ED documents use a hierarchical
numbered structure (e.g., "2.1.1 Technological Uncertainty"), so larger chunks reduce
the risk of fragmenting a single policy point across multiple retrieved passages.

### Retrieval Approach — Why MMR over Similarity Search

Maximum Marginal Relevance (MMR) penalizes redundancy alongside similarity, which is
critical for regulatory documents where multiple chunks from the same CRA section often
score nearly identically. Without MMR, the LLM would receive five near-duplicate
passages about the same criterion, leaving entire parts of the eligibility framework
unrepresented in the prompt. MMR trades a small amount of peak similarity for much
greater evidence diversity, which produces more balanced and defensible assessments.

### What I Would Do Differently at Production Scale

At production scale I would swap ChromaDB for Pinecone with namespace-per-client
isolation so assessments across different companies remain fully separated. I would
add a reranking step between retrieval and generation — either Cohere Rerank or a
local cross-encoder — to improve precision on the final passages sent to Claude.
The pipeline would benefit from chunk-level confidence scoring so the UI can surface
which citations are high-confidence versus marginal. I would implement an evaluation
suite using RAGAS to continuously measure faithfulness (are the citations accurate?)
and answer relevance (does the answer address the query?). Finally, at scale I would
separate the ingestion service from the query service, processing large document sets
through an async job queue (e.g., Celery + Redis) rather than blocking the request path.

---

## Setup

### Prerequisites

- Python 3.11+
- An Anthropic API key ([get one here](https://console.anthropic.com/))
- CRA SR&ED PDF documents (see below)

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/sred-eligibility-checker.git
cd sred-eligibility-checker
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your Anthropic API key
```

### 4. Download CRA SR&ED Documents

Place PDF files into the `./data/` directory. The recommended CRA documents are:

| Document | CRA Page |
|---|---|
| Basic Concepts of SR&ED | [cra-arc.gc.ca](https://www.canada.ca/en/revenue-agency/services/scientific-research-experimental-development-tax-incentive-program/policies-procedures-guidelines.html) |
| Eligibility of Work for SR&ED Tax Incentives | same page above |
| SR&ED Filing Requirements | same page above |
| Overhead and Other Expenditures | same page above |

Navigate to the CRA SR&ED Policies, Procedures, and Guidelines page and download the
policy documents as PDFs. Add them all to `./data/`.

### 5. Ingest Documents

```bash
python ingest.py
```

Expected output:
```
Found 4 PDF file(s):
  • BasicConcepts_SR&ED.pdf
  • EligibilityWork_SR&ED.pdf
  ...
Extracted 312 page(s) across all PDFs.
Created 1847 chunk(s) (size=800, overlap=100).
✓ Ingestion complete. 1847 chunks persisted to ./chroma_db/
```

### 6. Run the App

```bash
streamlit run app.py
```

---

## CLI Demo

```bash
python query.py "We developed a custom neural network architecture to solve a problem where no existing solution existed"
```

Output includes a structured eligibility assessment followed by the top 3 source
chunks with filename, page number, and relevance score.

---

## Sample Queries

See [`sample_queries.md`](sample_queries.md) for five realistic test cases. Quick summary:

| # | Scenario | Expected Classification |
|---|---|---|
| 1 | Novel GNN architecture for power grid failure prediction | ELIGIBLE |
| 2 | Custom low-latency distributed tracing framework in Rust | LIKELY ELIGIBLE |
| 3 | PostgreSQL query optimization using standard techniques | BORDERLINE |
| 4 | REST API built with FastAPI following established patterns | NOT ELIGIBLE |
| 5 | DBSCAN adapted to network traffic with custom distance metric | LIKELY ELIGIBLE / BORDERLINE |

---

## Project Structure

```
sred-eligibility-checker/
├── README.md              ← This file
├── requirements.txt       ← Pinned dependencies
├── .env.example           ← API key template
├── .gitignore             ← Excludes chroma_db/, data/, .env
├── ingest.py              ← PDF loading, chunking, embedding, ChromaDB persistence
├── rag_chain.py           ← LangChain RAG chain + Claude generation
├── query.py               ← CLI demo (< 50 lines)
├── app.py                 ← Streamlit frontend (two tabs)
└── sample_queries.md      ← 5 test queries with expected classifications
```

---

## Built to Demonstrate

This project is a portfolio artifact built to demonstrate:

- **RAG pipeline architecture** — end-to-end ingestion, retrieval, and generation with real regulatory documents
- **LangChain orchestration** — retrieval chains, prompt templates, and output parsers
- **ChromaDB** — local vector store with MMR retrieval
- **Local embeddings** — SentenceTransformers running without any API dependency
- **Structured LLM output** — prompt engineering for consistent, citation-grounded assessments
- **Production patterns** — separation of concerns across ingest / chain / UI layers, graceful error handling, environment variable management

> Replace this section with your own context as needed.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Orchestration | LangChain 0.3 |
| Vector Store | ChromaDB (local) |
| Embeddings | SentenceTransformers `all-MiniLM-L6-v2` |
| PDF Ingestion | pdfplumber |
| LLM | Anthropic Claude Haiku (`claude-haiku-4-5-20251001`) |
| Environment | python-dotenv |

---

## License

MIT
