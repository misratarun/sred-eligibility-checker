# SR&ED Eligibility Checker, Gumloop Version

A no-code port of the Python RAG app in the parent folder. Same four CRA PDFs, same five test queries, same six-section output format. The goal was to see how far a hosted agent builder could get on the same task, and where the trade-offs land.

## What I built

I built the same assistant inside Gumloop. The agent reads the four CRA SR&ED PDFs from a Google Drive folder, applies the system prompt in `agent_instructions.md`, and returns a six-section eligibility assessment: classification, confidence, criteria assessment, supporting evidence with citations, gaps or risks, and a recommendation.

I ran the five sample queries from `sample_queries.md` and saved each answer under `results/gumloop/`. For q5 the agent also produced a chat-side summary, saved separately under `results/gumloop/chat/q5_chat.txt`. For side-by-side baselines I ran the same five queries through the Python app and saved those outputs under `results/app/`.

## How long it took

About 7 minutes of agent run time across all five queries, plus a few minutes of setup. Timings from `results/gumloop/notes.md`:

| Query | Start to first working answer |
|------|-------------------------------|
| q1   | 1m 33s |
| q2   | 1m 21s |
| q3   | 1m 18s |
| q4   | 45s |
| q5   | 1m 48s |

The one friction point was the Google Drive connector. The default integration name was "google drive" and the Continue button stayed greyed out until I set a name. I uploaded the four PDFs manually since the set was small. Swapping to Claude Haiku from the model dropdown was a single click. After q1 the flow was repeatable.

## What I didn't have to build

- No ingestion script. The agent reads PDFs natively. No pdfplumber, no chunking, no overlap tuning.
- No vector store. No ChromaDB persistence, no collection config, no MMR parameters.
- No embedding step. No SentenceTransformers model to download or pin.
- No retrieval chain. No LangChain prompt template, no output parser.
- No UI. The chat window is the UI. The "copy text" button writes each assessment to a file.
- No environment wiring. No `.env`, no API key management, no `requirements.txt`.
- No deployment story. The flow runs where it was built.

## What I gave up

- Auditable retrieval. The Python app prints the exact chunks used, with document, page, and relevance score. Gumloop produces narrative citations with no visible retrieval step, so I cannot see what text the model actually read.
- Citation precision. All cited document names resolve to real PDFs, but page numbers drift. In the five test runs several citations were off by one page against the 12-page SR&ED Guidelines, one Glossary citation pointed about 30 pages away from where the quoted exclusion actually appears, and one quoted phrase ("Routine design and construction work") does not appear verbatim in any ingested PDF. Full list in `comparison.md`.
- Control over retrieval, chunking, and ranking. No knob for chunk size, no option to add a reranker, no way to force quoting over paraphrase.
- Offline operation. The code version runs fully local once ingested. Gumloop needs the service and the Drive link.
- A predictable cost model per query. The code version's cost is a sum of embedding and Claude Haiku tokens I can estimate. The Gumloop cost is per run of the flow.
- Deterministic post-processing. In the code version I can post-filter, score, or reshape output. In Gumloop I take what the agent returns.

## Results

Classification agreement against the expected labels in `sample_queries.md`:

| # | Query | Expected | App | Gumloop |
|---|-------|----------|-----|---------|
| 1 | Novel GNN for power-grid cascade failures         | ELIGIBLE                        | ELIGIBLE (High)             | ELIGIBLE (High) |
| 2 | Rust distributed tracing framework, sub-2ms       | LIKELY ELIGIBLE                 | LIKELY ELIGIBLE (Medium-High)| BORDERLINE (Medium) |
| 3 | PostgreSQL query optimization                     | BORDERLINE                      | NOT ELIGIBLE (High)         | NOT ELIGIBLE (High) |
| 4 | FastAPI CRUD REST API                             | NOT ELIGIBLE                    | NOT ELIGIBLE (High)         | NOT ELIGIBLE (Very High) |
| 5 | DBSCAN adapted to time-series anomalies           | LIKELY ELIGIBLE or BORDERLINE   | BORDERLINE (Medium)         | BORDERLINE / LIKELY ELIGIBLE (Medium) |

Scorecard:
- App: 4 of 5 match the expected label. Miss: q3 (should be BORDERLINE, called NOT ELIGIBLE).
- Gumloop: 3 of 5 match. Same q3 miss. Also one step too conservative on q2 (BORDERLINE instead of LIKELY ELIGIBLE).

Both systems cite only documents that exist in `data/`. The app's chunk-level metadata is page-accurate because the retrieval trace is printed verbatim at the bottom of each run. Gumloop's prose citations read cleaner but drift on page numbers. See `comparison.md` for the full per-query diff of expected vs app vs Gumloop, including which citations verify and which do not.

## When each version makes sense

Pick the code version when you need an auditable retrieval trace, deterministic chunking, offline operation, or the ability to swap vector store, reranker, or model under test.

Pick the Gumloop version when you want a working assessment in under 10 minutes, do not need to inspect retrieval, and are willing to trade some citation precision for setup speed.

## Folder layout

```
gumloop-version/
├── agent_instructions.md          System prompt given to the Gumloop agent
├── comparison.md                  Per-query diff: expected vs app vs Gumloop
├── results/
│   ├── app/                       CLI output from the local RAG pipeline
│   │   └── q1.md ... q5.md
│   └── gumloop/                   Agent output copied from Gumloop
│       ├── q1.md ... q5.md
│       ├── chat/q5_chat.txt       Chat-side summary for q5
│       └── notes.md               Timing and friction notes per query
└── screenshots/
    └── Copy Text Screenshot.png
```
