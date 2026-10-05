#!/usr/bin/env python3
"""Draw the hand-label eval set from a Jev run and build a blind labeling page.

    python3 eval/make_set.py jev-runs/weekly

Writes eval/set.jsonl (posting facts + Jev's frozen answers, no descriptions; committed)
and jev-runs/eval/labeler.html (full descriptions, Jev's answers hidden; local only).
The sample is stratified by Jev's bucket so rare buckets get enough rows to measure,
which means overall accuracy here is not the accuracy of a random posting.
"""
import argparse
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PER_BUCKET = {"ai_program_or_tpm": 8, "ai_pm_no_ml_required": 7, "ai_pm_ml_required": 4,
              "program_or_tpm_non_ai": 6, "pm_non_ai": 5, "not_a_fit": 6, "review": 4}
FACTS = ["company", "title", "location", "department", "url", "location_fit"]
JEV = ["role_kind", "role_kind.confidence", "ai_scope", "ai_scope.confidence", "seniority.score",
       "requires_ml_background", "requires_hands_on_ai", "requires_engineering_background", "_bucket", "_model"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", help="run folder with results.jsonl and input.jsonl")
    ap.add_argument("--seed", type=int, default=20261004)
    ap.add_argument("--force", action="store_true", help="overwrite an existing eval/set.jsonl")
    a = ap.parse_args()

    out = ROOT / "eval" / "set.jsonl"
    if out.exists() and not a.force:
        raise SystemExit(f"{out} exists; the set is frozen once labeling starts. Use --force to redraw.")
    run = Path(a.run)
    rows = [json.loads(l) for l in (run / "results.jsonl").open(encoding="utf-8") if l.strip()]
    full = {r["url"]: r["description"] for r in
            (json.loads(l) for l in (run / "input.jsonl").open(encoding="utf-8") if l.strip())}

    rng = random.Random(a.seed)
    picked = []
    for bucket, n in PER_BUCKET.items():
        pool = sorted((r for r in rows if r["_bucket"] == bucket), key=lambda r: r["url"])
        picked += rng.sample(pool, min(n, len(pool)))
    rng.shuffle(picked)  # labeling order carries no hint of the bucket

    with out.open("w", encoding="utf-8") as f:
        for i, r in enumerate(picked, 1):
            f.write(json.dumps({"id": i, **{k: r.get(k) for k in FACTS},
                                "jev": {k: r.get(k) for k in JEV}}) + "\n")

    items = [{"id": i, **{k: r.get(k) for k in FACTS}, "description": full.get(r["url"], r["description"])}
             for i, r in enumerate(picked, 1)]
    spec = json.loads((ROOT / "radar" / "spec.json").read_text(encoding="utf-8"))["questions"]
    page = (ROOT / "eval" / "labeler_template.html").read_text(encoding="utf-8")
    page = page.replace("/*ITEMS*/[]", json.dumps(items)).replace("/*SPEC*/{}", json.dumps(spec))
    local = ROOT / "jev-runs" / "eval"
    local.mkdir(parents=True, exist_ok=True)
    (local / "labeler.html").write_text(page, encoding="utf-8")
    print(f"{len(picked)} rows -> {out}\nLabel them in {local / 'labeler.html'}, then save labels.csv to eval/")


if __name__ == "__main__":
    main()
