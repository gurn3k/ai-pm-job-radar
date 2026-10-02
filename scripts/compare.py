#!/usr/bin/env python3
"""Join Jev's labels to a number Jev never saw, and rank the labels by it.

  python3 compare.py results.jsonl --metric engagement --by archetype,pillar
        [--min-confidence 0.5] [--normalize-by-month date] [--min-n 10]

--normalize-by-month divides each item's metric by the median of its calendar month, so
audience growth over time does not make recent labels look better (1.00 = a typical item
that month). Labels below --min-confidence are grouped as "low-confidence", not dropped.
"""
import argparse, collections, json, statistics as st


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results"); ap.add_argument("--metric", required=True); ap.add_argument("--by", required=True)
    ap.add_argument("--min-confidence", type=float, default=0.5); ap.add_argument("--normalize-by-month")
    ap.add_argument("--min-n", type=int, default=10)
    a = ap.parse_args()
    rows = [json.loads(l) for l in open(a.results) if l.strip()]
    rows = [r for r in rows if isinstance(r.get(a.metric), (int, float)) or str(r.get(a.metric, "")).replace(".", "", 1).isdigit()]
    for r in rows:
        r["_m"] = float(r[a.metric])
    if a.normalize_by_month:
        months = collections.defaultdict(list)
        for r in rows:
            months[str(r[a.normalize_by_month])[:7]].append(r["_m"])
        med = {k: st.median(v) or 1 for k, v in months.items()}
        for r in rows:
            r["_m"] = r["_m"] / med[str(r[a.normalize_by_month])[:7]]
    q3 = sorted(r["_m"] for r in rows)[int(len(rows) * 0.75)]
    label = "x monthly median" if a.normalize_by_month else a.metric
    print(f"{len(rows)} items. Top quartile starts at {q3:.2f}.\n")
    for key in a.by.split(","):
        groups = collections.defaultdict(list)
        for r in rows:
            v = r.get(key)
            if isinstance(v, float):  # noul: split at 0.5
                v = f"{key} yes" if v > 0.5 else f"{key} no"
            elif (r.get(f"{key}.confidence") or 1) < a.min_confidence:
                v = "low-confidence"
            groups[v].append(r["_m"])
        print(f"{key:30} {'n':>5} {'median ' + label:>22} {'in top quartile':>16}")
        for v, ms in sorted(groups.items(), key=lambda kv: -st.median(kv[1])):
            if len(ms) >= a.min_n:
                print(f"  {str(v):28} {len(ms):5} {st.median(ms):22.2f} {sum(m >= q3 for m in ms) / len(ms):16.0%}")
        print()


if __name__ == "__main__":
    main()
