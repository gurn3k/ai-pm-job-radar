#!/usr/bin/env python3
"""Score Jev's frozen answers in eval/set.jsonl against hand labels in eval/labels.csv.

    python3 eval/score.py            # prints the report and writes eval/RESULTS.md

Human buckets come from the same rules in radar/spec.json, with every human answer at
confidence 1.0, so a human row never lands in "review". Jev rows in "review" count as
misses on bucket accuracy and are also reported on their own.
"""
import collections
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from jev import bucket_for  # noqa: E402

QS = ["role_kind", "ai_scope", "seniority", "requires_ml_background", "requires_hands_on_ai",
      "requires_engineering_background"]
YN = ["requires_ml_background", "requires_hands_on_ai", "requires_engineering_background"]
# Ids 1-20 were labeled, then revised after seeing Jev's answers for them; 21-40 were labeled blind.
# requires_ml_background was relabeled to the strict definition for every row after seeing Jev's answers.
REVIEWED = set(range(1, 21))


def pct(n, d):
    return f"{n}/{d} ({n / d:.0%})" if d else "n/a"


def main():
    spec = json.loads((ROOT / "radar" / "spec.json").read_text(encoding="utf-8"))
    rows = {r["id"]: r for r in (json.loads(l) for l in (ROOT / "eval" / "set.jsonl").open(encoding="utf-8") if l.strip())}
    with (ROOT / "eval" / "labels.csv").open(newline="", encoding="utf-8-sig") as f:
        labels = {int(r["id"]): r for r in csv.DictReader(f)}

    pairs, skipped = [], []
    for i, r in rows.items():
        h = labels.get(i)
        if not h or h["url"] != r["url"] or not all(h.get(q) for q in QS):
            skipped.append(i); continue
        j = r["jev"]
        jev = {"role_kind": j["role_kind"], "ai_scope": j["ai_scope"],
               "seniority": str(round(j["seniority.score"]) + 1),
               **{q: "yes" if j[q] > 0.5 else "no" for q in YN},
               "bucket": j["_bucket"]}
        hum = {q: h[q] for q in QS}
        hum["bucket"] = bucket_for({"role_kind": hum["role_kind"], "role_kind.confidence": 1.0, "ai_scope": hum["ai_scope"],
                                    "requires_ml_background": 1.0 if hum["requires_ml_background"] == "yes" else 0.0},
                                   spec["buckets"])
        pairs.append((r, jev, hum, h.get("note", "")))

    n = len(pairs)
    model = sorted({r["jev"]["_model"] for r, *_ in pairs})
    out = [f"# Eval results", "",
           f"{n} postings labeled by hand. Model: {', '.join(model)}. Ids 21-40 were labeled blind; ids 1-20 were "
           "revised after seeing Jev's answers (originals in `labels_batch1_before_review.csv`), and "
           "`requires_ml_background` was relabeled to its strict definition after review for all rows.",
           "The set is stratified by Jev's bucket (see `make_set.py`), so these numbers describe each bucket, "
           "not the accuracy of a random posting.", ""]
    if skipped:
        out += [f"Not scored (missing or mismatched labels): ids {skipped}", ""]

    out += ["## Per question", "", "| Question | All | Ids 1-20 (revised) | Ids 21-40 (blind) |", "|---|---|---|---|"]
    for q in QS + ["bucket"]:
        cells = []
        for keep in (lambda i: True, lambda i: i in REVIEWED, lambda i: i not in REVIEWED):
            sub = [(j, h) for r, j, h, _ in pairs if keep(r["id"])]
            cells.append(pct(sum(j[q] == h[q] for j, h in sub), len(sub)))
        out.append(f"| {q} | " + " | ".join(cells) + " |")
    ai = {"ai_native", "ai_platform"}
    both = sum((j["ai_scope"] in ai) == (h["ai_scope"] in ai) for _, j, h, _ in pairs)
    out += ["", f"ai_scope as the buckets use it (AI vs not AI, native and platform merged): {pct(both, n)}."]
    scored = [(j, h) for _, j, h, _ in pairs if j["bucket"] != "review"]
    ai_b = {"ai_program_or_tpm", "ai_pm_no_ml_required", "ai_pm_ml_required"}
    out += [f"Bucket, leaving out the {n - len(scored)} rows Jev sent to review: {pct(sum(j['bucket'] == h['bucket'] for j, h in scored), len(scored))}.",
            f"In an AI bucket or not (the three AI buckets vs the rest), same rows: "
            f"{pct(sum((j['bucket'] in ai_b) == (h['bucket'] in ai_b) for j, h in scored), len(scored))}."]
    near = sum(abs(int(j["seniority"]) - int(h["seniority"])) <= 1 for _, j, h, _ in pairs)
    out += ["", f"Seniority within one level: {pct(near, n)}.", ""]

    out += ["## Per Jev bucket (precision: of the rows Jev put here, how many belong)", "",
            "| Jev bucket | Correct | Human bucket for the misses |", "|---|---|---|"]
    by = collections.defaultdict(list)
    for _, j, h, _ in pairs:
        by[j["bucket"]].append(h["bucket"])
    for b in [x["name"] for x in spec["buckets"]] + ["review"]:
        hs = by.get(b, [])
        miss = collections.Counter(x for x in hs if x != b)
        out.append(f"| {b} | {pct(len(hs) - sum(miss.values()), len(hs))} | "
                   f"{', '.join(f'{k} {v}' for k, v in miss.most_common()) or '-'} |")

    out += ["", "## Disagreements", "", "| id | Title | Question | Jev | Human | Note |", "|---|---|---|---|---|---|"]
    for r, j, h, note in pairs:
        for q in QS:
            if j[q] != h[q]:
                out.append(f"| {r['id']} | {r['title'][:50]} | {q} | {j[q]} | {h[q]} | {' '.join(note.split()).replace('|', '/')[:80]} |")

    text = "\n".join(out) + "\n"
    (ROOT / "eval" / "RESULTS.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
