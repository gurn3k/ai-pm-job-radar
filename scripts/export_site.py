#!/usr/bin/env python3
"""Export a Jev run to site/data.json for the public radar page.

Only public posting facts and Jev's labels go out. Descriptions, the answer
cache and anything else from the run folder stay local.

    python3 scripts/export_site.py jev-runs/radar/full --scanned 8381
"""
import argparse
import datetime
import json
import re
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRICE_PER_M_INPUT = 0.042  # keep in sync with scripts/jev.py

NAMES = {
    "openai": "OpenAI", "xai": "xAI", "scaleai": "Scale AI", "gleanwork": "Glean",
    "elevenlabs": "ElevenLabs", "deepgram": "Deepgram", "supabase": "Supabase",
}

FIELDS = ["company", "title", "location", "department", "url", "pay_low", "pay_high",
          "remote_listed", "location_fit", "role_kind", "ai_scope", "seniority",
          "requires_ml_background", "requires_hands_on_ai", "requires_engineering_background"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", help="run folder with results.jsonl and summary.md")
    ap.add_argument("--scanned", type=int, help="open roles scanned before the title filter (printed by fetch.py)")
    ap.add_argument("--date", help="run date YYYY-MM-DD (default: results.jsonl modified date)")
    ap.add_argument("--out", default=str(ROOT / "site" / "data.json"))
    ap.add_argument("--force", action="store_true", help="publish even if the role count dropped by more than half")
    a = ap.parse_args()

    run = Path(a.run)
    rows = [json.loads(l) for l in (run / "results.jsonl").open(encoding="utf-8") if l.strip()]
    summary = (run / "summary.md").read_text(encoding="utf-8") if (run / "summary.md").exists() else ""
    wall = re.search(r"Wall time: ([\d.]+)s", summary)
    boards = json.loads((ROOT / "radar" / "boards.json").read_text())

    # Refuse to publish a broken run: too many failed labels, or far fewer roles than the live page.
    inp = run / "input.jsonl"
    if inp.exists():
        expected = sum(1 for l in inp.open(encoding="utf-8") if l.strip())
        if len(rows) < 0.95 * expected:
            raise SystemExit(f"Only {len(rows)} of {expected} roles labeled; not exporting.")
    if Path(a.out).exists() and not a.force:
        live = len(json.loads(Path(a.out).read_text(encoding="utf-8"))["roles"])
        if len(rows) < 0.5 * live:
            raise SystemExit(f"{len(rows)} roles vs {live} on the live page; not exporting (use --force if this is real).")

    roles = []
    for r in rows:
        out = {k: r.get(k) for k in FIELDS}
        out["company"] = NAMES.get(r["company"], r["company"].capitalize())
        out["bucket"] = r.get("_bucket")
        for k in ("requires_ml_background", "requires_hands_on_ai", "requires_engineering_background"):
            if isinstance(out[k], float):
                out[k] = round(out[k], 2)
        if not str(out["url"] or "").startswith("https://"):
            out["url"] = None
        roles.append(out)

    tokens = sum(r.get("_tokens") or 0 for r in rows)
    ms = [r["_ms"] for r in rows if r.get("_ms")]
    date = a.date or datetime.date.fromtimestamp((run / "results.jsonl").stat().st_mtime).isoformat()
    data = {
        "run": {
            "date": date,
            "model": next((r["_model"] for r in rows if r.get("_model")), None),
            "boards": sum(len(v) for v in boards.values()),
            "scanned": a.scanned,
            "labeled": len(rows),
            "seconds": float(wall.group(1)) if wall else None,
            "p50_ms": round(statistics.median(ms)) if ms else None,
            "input_tokens": tokens,
            "cost_usd": round(tokens * PRICE_PER_M_INPUT / 1e6, 3),
        },
        "roles": roles,
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    print(f"{len(roles)} roles -> {a.out} ({Path(a.out).stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
