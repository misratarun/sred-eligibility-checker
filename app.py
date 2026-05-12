"""
app.py — Streamlit frontend for the SR&ED Eligibility Checker.

Run with:
    streamlit run app.py
"""

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="SR&ED Eligibility Checker",
    page_icon="🍁",
    layout="wide",
)

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🍁 SR&ED Checker")

    st.subheader("About")
    st.markdown(
        "SR&ED (Scientific Research & Experimental Development) is Canada's largest "
        "federal tax incentive program, providing credits for qualifying R&D work. "
        "The CRA defines eligibility based on technological uncertainty, systematic "
        "investigation, and advancement of general knowledge."
    )

    st.subheader("How It Works")
    st.markdown(
        "- **Retrieve:** Your description is embedded and matched against CRA guideline chunks stored in ChromaDB\n"
        "- **Rank:** Maximum Marginal Relevance selects the 5 most diverse, relevant sections\n"
        "- **Generate:** Claude synthesizes a structured eligibility assessment grounded in those sections"
    )

    st.subheader("Knowledge Base")
    chroma_ready = Path("./chroma_db").exists() and any(Path("./chroma_db").iterdir())
    if chroma_ready:
        try:
            from rag_chain import get_collection_info
            info = get_collection_info()
            st.success(f"{info['chunk_count']} chunks indexed")
            if info["sources"]:
                st.markdown("**Source documents:**")
                for src in info["sources"]:
                    st.markdown(f"  • `{src}`")
        except Exception as e:
            st.warning(f"Could not load collection info: {e}")
    else:
        st.error("Knowledge base not found.")
        st.code("python ingest.py", language="bash")

# ── Classification color map ──────────────────────────────────────────────────

CLASSIFICATION_COLORS = {
    "ELIGIBLE": "#1a7a4a",
    "LIKELY ELIGIBLE": "#1565c0",
    "BORDERLINE": "#e65100",
    "NOT ELIGIBLE": "#b71c1c",
}

CLASSIFICATION_BG = {
    "ELIGIBLE": "#e8f5e9",
    "LIKELY ELIGIBLE": "#e3f2fd",
    "BORDERLINE": "#fff3e0",
    "NOT ELIGIBLE": "#ffebee",
}


def detect_classification(answer: str) -> str:
    upper = answer.upper()
    for label in ["NOT ELIGIBLE", "LIKELY ELIGIBLE", "BORDERLINE", "ELIGIBLE"]:
        if label in upper:
            return label
    return "BORDERLINE"


def render_classification_badge(label: str):
    color = CLASSIFICATION_COLORS.get(label, "#555")
    bg = CLASSIFICATION_BG.get(label, "#f5f5f5")
    st.markdown(
        f"""<div style="
            background-color:{bg};
            border-left: 6px solid {color};
            padding: 16px 20px;
            border-radius: 6px;
            margin-bottom: 16px;
        ">
        <span style="font-size:1.4rem; font-weight:700; color:{color};">{label}</span>
        </div>""",
        unsafe_allow_html=True,
    )


# ── Main tabs ─────────────────────────────────────────────────────────────────

tab1, tab2 = st.tabs(["Eligibility Assessment", "Source Evidence"])

# Store results in session state so both tabs can access them
if "result" not in st.session_state:
    st.session_state.result = None

with tab1:
    st.header("SR&ED Eligibility Checker")
    st.subheader("Based on CRA's official SR&ED guidelines")

    if not chroma_ready:
        st.error(
            "Knowledge base not found. Please run: `python ingest.py` "
            "after adding CRA PDF documents to the `data/` folder."
        )
        st.stop()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        st.error(
            "ANTHROPIC_API_KEY not set. Add it to your `.env` file and restart the app."
        )
        st.stop()

    work_description = st.text_area(
        "Describe the engineering work or project activity",
        height=200,
        placeholder=(
            "Example: We attempted to build a real-time anomaly detection model "
            "for IoT sensor streams. Existing statistical methods failed under "
            "non-stationary conditions, so we designed and tested three novel "
            "neural architectures over six months of iterative experimentation..."
        ),
    )

    company_context = st.text_input(
        "Company / project context (optional)",
        placeholder="e.g., SaaS company building predictive maintenance for industrial equipment",
    )

    submitted = st.button("Assess Eligibility", type="primary", use_container_width=True)

    if submitted:
        if not work_description.strip():
            st.warning("Please enter a description of the engineering work.")
        else:
            query = work_description.strip()
            if company_context.strip():
                query = f"[Context: {company_context.strip()}]\n\n{query}"

            with st.spinner("Retrieving CRA guidelines and generating assessment..."):
                try:
                    from rag_chain import run_query
                    st.session_state.result = run_query(query)
                except FileNotFoundError as e:
                    st.error(str(e))
                    st.stop()
                except Exception as e:
                    st.error(f"An error occurred during assessment: {e}")
                    st.stop()

    if st.session_state.result:
        result = st.session_state.result
        classification = detect_classification(result.answer)
        render_classification_badge(classification)

        st.markdown("### Assessment")
        st.markdown(result.answer)

        st.info(
            f"Assessment grounded in {len(result.source_chunks)} retrieved CRA document sections. "
            "See the **Source Evidence** tab for full citations."
        )

with tab2:
    st.title("Retrieved Source Chunks")
    st.markdown("*These CRA document sections informed the assessment*")

    if not st.session_state.result:
        st.info("Run an assessment in the **Eligibility Assessment** tab first.")
    else:
        chunks = st.session_state.result.source_chunks

        for i, chunk in enumerate(chunks, start=1):
            score = chunk["score"]
            score_pct = max(0.0, min(1.0, score))

            st.markdown(f"**Chunk {i}** — `{chunk['source']}` | Page {chunk['page']}")
            col1, col2 = st.columns([3, 1])
            with col1:
                st.progress(score_pct, text=f"Relevance: {score_pct * 100:.1f}%")
            with col2:
                pass

            with st.expander(f"View text — {chunk['source']}, p.{chunk['page']}"):
                st.text(chunk["text"])

            st.divider()
