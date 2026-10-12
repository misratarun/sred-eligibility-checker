# App vs Gumloop — SR&ED Eligibility Results Comparison

Compares `results/app/qN.md` (local RAG pipeline) and `results/gumloop/qN.md` (Gumloop agent) against the expected classifications in `sample_queries.md`. Citation column checks whether each system's cited document and page point to a real file/page in `data/`.

Documents in `data/`:
- `Guidelines on the eligibility of work for scientific research and experimental development (SR&ED) tax incentives - Canada.ca.pdf` (12 pages)
- `Guidelines on the eligibility of work for scientific research and experimental development (SRED) tax incentives - Canadaca.pdf` (5 pages, condensed variant)
- `SR&ED Glossary - Canada.ca.pdf` (46 pages)
- `T4088 – Scientific Research and Experimental Development (SR&ED) Expenditures Claim – Guide to Form T661 - Canada.ca.pdf` (93 pages)

## Results Table

| # | Query (short) | Expected | App result | Gumloop result | App citations → real doc & page? | Gumloop citations → real doc & page? |
|---|---------------|----------|------------|----------------|----------------------------------|--------------------------------------|
| 1 | Novel GNN for power-grid cascade failures | ELIGIBLE | **ELIGIBLE** (High) ✓ | **ELIGIBLE** (High) ✓ | Doc ✓ (all 4 PDFs). The `TOP SOURCE CHUNKS` block prints the exact retrieved chunks with real metadata; pages verified (e.g., T4088 p.79, SRED-Guidelines p.3, Glossary p.29/8/16). However top-ranked chunk (T4088 p.79, "Physical sciences subcategories") is irrelevant to the query, and the LLM leans on Source 2 instead. | Doc ✓ (cites the 12-page SR&ED Guidelines). Pages mostly correct: p.4 "circumvent…workaround" ✓, p.4 "recognition that…uncertainty exists" ✓, p.2 formal definition w/ "systematic investigation or search" ✓ (clause (d) with "computer programming" actually spans p.2–p.3). |
| 2 | Rust distributed tracing framework (sub-2ms) | LIKELY ELIGIBLE | **LIKELY ELIGIBLE** (Medium-High) ✓ | **BORDERLINE** (Medium) ✗ (one step too conservative) | Doc ✓. Pages verified against indexed chunks (T4088 p.79, Glossary p.9, SRED-Guidelines p.3, SR&ED-Guidelines p.7, T4088 p.91). Narrative quotes "psychological research" oddly but it is in the real p.2 definition. | Doc ✓. Page 2 "incremental improvements thereto" ✓. Page 4 "How requirement" — **off by one** (the "How requirement" header and the quoted sentence are on **p.5** of the PDF). Page 5 "Routine design and construction work" — **not found verbatim** in the PDF (closest excluded-work list is on p.3/p.10). |
| 3 | PostgreSQL query optimization | BORDERLINE | **NOT ELIGIBLE** (High) ✗ | **NOT ELIGIBLE** (High) ✗ | Doc ✓. Chunks real (Glossary p.10, T4088 p.91/79/33). Narrative citations use Glossary p.10 which is topically relevant (Directly engaged in SR&ED). Retrieval relevance is low (scores −22% to −27%). | Doc ✓. Page 3 "unknown (or uncertain)…" — **off** (actual page 4). Page 4 "distinguish between a systematic approach…" — **off by one** (actual p.5). Pages 3/7 Why/Experimental Development — Why section is on p.4, Experimental Development p.6–7, so p.7 is close. Page 10 "quality control or routine testing" ✓, p.10 "key feature that can help you distinguish" — **off** (actual p.11). |
| 4 | FastAPI CRUD REST API | NOT ELIGIBLE | **NOT ELIGIBLE** (High) ✓ | **NOT ELIGIBLE** (Very High) ✓ | Doc ✓. Chunks real (T4088 p.79/91, Glossary p.9/3, SR&ED-Guidelines p.2). The "style changes" quote is accurate CRA language (appears on p.3 and p.10 of the 12-page PDF). | Doc ✓. Page 3 uncertainty definition — **off** (actual p.4). Page 4 "How requirement" — **off** (actual p.5). Page 2 "(i) the commercial production…" — **off by one** (clause (i) list is on p.3). Page 10 exclusions ✓. |
| 5 | DBSCAN adapted to time-series anomalies | LIKELY ELIGIBLE **or** BORDERLINE | **BORDERLINE** (Medium) ✓ | **BORDERLINE / LIKELY ELIGIBLE WITH CONDITIONS** (Medium) ✓ | Doc ✓. Chunks real (Glossary p.9, SRED-Guidelines p.1/4/2, T4088 p.79). Pages verified against indexed metadata. | Doc ✓ (cites Glossary). Page 2 "Advancement of scientific knowledge" header ✓. Page 3 "Analysis is an integral part of the systematic investigation" ✓. Page 2 uncertainty definition — **not on p.2** of the Glossary (uncertainty definition appears later; Glossary p.2 is about adjusted service cost). Page 4 "commercial production of a new or improved…" — **wrong** (actual page is p.38 in Glossary; also appears in SR&ED Guidelines p.3/p.10). |

Legend: ✓ = matches expected / verifiable; ✗ = disagrees with expected / miscited.

## Meaningful Differences

**Classification agreement with expected labels**
- App matches on Q1, Q2, Q4, Q5 (4/5). Misses Q3 (says NOT ELIGIBLE where expected is BORDERLINE).
- Gumloop matches on Q1, Q4, Q5 (3/5). Misses Q3 (same miss as the app) and is one step more conservative on Q2 (BORDERLINE vs. LIKELY ELIGIBLE).
- Both systems converge on NOT ELIGIBLE for Q3 and ignore the "non-obvious join reordering" novelty hook that `sample_queries.md` says should pull it toward BORDERLINE.

**Citation fidelity**
- App surfaces an auditable `TOP SOURCE CHUNKS` block at the bottom of every answer. Document names, pages, and chunk text are directly checkable against the indexed PDFs — nothing is fabricated. The weakness is retrieval quality: the top-ranked chunk is often an off-topic page from T4088 (p.79 physical-sciences subcategories, p.91 lab-notebooks list), with negative relevance scores (−10% to −27%). The LLM compensates by citing Source 2/3 (which happen to be the relevant SRED-Guidelines p.3 chunk).
- Gumloop produces narrative citations with cleaner prose but no retrieval trace. Document names always resolve to a real PDF, but **page numbers drift**: in Q2–Q4 several "p.3 / p.4" citations are off-by-one against the actual 12-page SR&ED Guidelines (correct pages are p.4 / p.5 respectively). In Q5, a "Glossary p.4" citation for the commercial-production exclusion is far off — that quote actually appears on Glossary p.38 (or on p.3 of the SR&ED Guidelines). In Q2 the phrase "Routine design and construction work" is quoted but does not appear verbatim in any of the ingested PDFs.

**Content & tone**
- Gumloop answers are substantially longer and include extra scaffolding — hypothetical rewrites of borderline projects, cross-project comparisons ("How This Differs From Your GNN Project"), and critical questions back to the user. Across q3/q4 it even references the user's other projects.
- App answers are tighter and tabular (criterion/evidence tables, gap lists, 1–2 recommendations). They avoid cross-contaminating one query's reasoning with another.
- App outputs include noisy stderr at the top (LangChain deprecation warnings, Chroma telemetry errors, relevance-score warning). Gumloop output is clean except for q5 where a chat `Summary` is captured separately in `results/gumloop/chat/q5_chat.txt`.

**Retrieval architecture signal**
- The app's negative relevance scores on every query suggest the vectorstore's cosine similarity is routinely producing poor matches on this corpus. Despite that, the final classifications match expected labels more often than Gumloop's — because the model falls back on general SR&ED knowledge rather than the specific irrelevant chunks it was handed.
- Gumloop reads whole PDFs natively (per `notes.md`: "agent read the PDFs without any chunking or embedding setup"), so it has access to broader context, but its page attributions are less reliable than the app's chunk-level metadata.

**Where Gumloop is stricter than the app**
- Q2 (Rust tracing): Gumloop downgrades to BORDERLINE primarily because of the phrase "informed by published systems research papers" and the lack of ablation/hypothesis documentation. The app weighs the same signal but keeps LIKELY ELIGIBLE, flagging documentation gaps as the risk rather than the classification driver. The expected label is LIKELY ELIGIBLE, so the app is more faithful here.

**Where the two agree against the expected label**
- Q3 (Postgres optimization): both call it NOT ELIGIBLE with High confidence. The expected label is BORDERLINE, specifically because of the one "non-obvious join reordering" novelty. Both systems treat the user's self-description ("standard database tuning practice") as dispositive and discount the novelty hook — a shared failure mode.
