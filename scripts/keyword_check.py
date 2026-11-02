#!/usr/bin/env python3
"""Compare two plain keyword rules with Jev on this week's labeled postings.

    python3 scripts/keyword_check.py jev-runs/weekly

Prints a short markdown report. It never changes site/data.json. Jev is not ground truth here:
the numbers show where a free rule and the model disagree, so those rows can be hand-checked
and added to the next eval set.
"""
import json
import re
import sys
from pathlib import Path

AI_RE = re.compile(r"\bAI\b|\bA\.I\.|machine learning|\bLLMs?\b|large language|generative|\bGenAI\b|"
                   r"artificial intelligence|\bML\b", re.I)
ML_RE = re.compile(r"(experience|background|degree|knowledge|expertise|proficien\w*|understanding)[^.\n]{0,80}"
                   r"(machine learning|\bML\b|deep learning|data science)|"
                   r"(machine learning|\bML\b)[^.\n]{0,40}(experience|background|degree|required)", re.I)
AI_CUTOFF = 5  # matches of AI terms in title, department and description
AI_SCOPES = {"ai_native", "ai_platform"}


def main():
    out = Path(sys.argv[1])
    rows = [json.loads(l) for l in (out / "results.jsonl").open(encoding="utf-8") if l.strip()]
    rows = [r for r in rows if r.get("ai_scope") and r.get("requires_ml_background") not in (None, "")]
    n = len(rows)
    ai_agree = ml_agree = 0
    ml_kw_only, ml_jev_only = [], []
    for r in rows:
        text = f"{r['title']} {r.get('department', '')} {r.get('description', '')}"
        k_ai = len(AI_RE.findall(text)) >= AI_CUTOFF
        ai_agree += k_ai == (r["ai_scope"] in AI_SCOPES)
        k_ml = bool(ML_RE.search(text))
        j_ml = float(r["requires_ml_background"]) > 0.5
        ml_agree += k_ml == j_ml
        if k_ml and not j_ml:
            ml_kw_only.append(r)
        if j_ml and not k_ml:
            ml_jev_only.append(r)
    print(f"## Keyword rule against Jev, {n} postings")
    print(f"- AI or not: agree on {ai_agree}/{n} ({ai_agree / n:.0%}).")
    print(f"- Strict ML: agree on {ml_agree}/{n}. Rule only: {len(ml_kw_only)}. Jev only: {len(ml_jev_only)}.")
    print("\n### Strict ML, rule says yes and Jev says no (hand-check these first)")
    for r in ml_kw_only[:25]:
        print(f"- {r['company']}: {r['title']} ({r['url']})")


if __name__ == "__main__":
    main()
