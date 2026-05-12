"""
query.py — CLI demo for the SR&ED RAG pipeline.

Usage:
    python query.py "your query here"
    python query.py "We developed a custom neural network architecture to solve a problem
                     where no existing solution existed"
"""

import sys

from rag_chain import run_query


def main():
    if len(sys.argv) < 2:
        print("Usage: python query.py \"<your engineering work description>\"")
        sys.exit(1)

    question = " ".join(sys.argv[1:])
    print(f"\nQuery: {question}\n")
    print("=" * 70)
    print("Running SR&ED eligibility assessment...")
    print("=" * 70)

    result = run_query(question)

    print("\n" + result.answer)

    print("\n" + "─" * 70)
    print("TOP SOURCE CHUNKS (ranked by relevance)")
    print("─" * 70)
    for i, chunk in enumerate(result.source_chunks[:3], start=1):
        score_pct = f"{chunk['score'] * 100:.1f}%"
        print(f"\n[{i}] {chunk['source']} — Page {chunk['page']} | Score: {score_pct}")
        print("-" * 50)
        print(chunk["text"][:400] + ("..." if len(chunk["text"]) > 400 else ""))


if __name__ == "__main__":
    main()
