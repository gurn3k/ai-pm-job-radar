#!/usr/bin/env python3
"""jev.py - run Jev (TypeSafe System One) over a file of items. Standard library only.

  python3 jev.py setup                      create the key file and print where it is
  python3 jev.py check                      confirm the key works and list models
  python3 jev.py run SPEC INPUT --out DIR   label every item in INPUT with the questions in SPEC
        [--sample N] [--limit N] [--seed 7] [--concurrency 16] [--dry-run]

INPUT is .jsonl, .json (a list) or .csv. Each record is one item. SPEC is a JSON file:

  {
    "model": "jev-latest",
    "context": {"goal": "..."},              # optional, sent with every item
    "state_fields": ["title", "body"],        # the only record fields Jev sees
    "questions": { ... Jev questions ... },
    "buckets": [                               # optional, first match wins, else "review"
      {"name": "keep", "when": [["kind", "==", "pm"], ["kind.confidence", ">=", 0.8]]},
      {"name": "flag", "any": [["is_spam", ">", 0.7], ["is_bot", ">", 0.7]]}
    ],                                         # "when" = all must hold, "any" = at least one
    "show": ["company", "title"]               # optional, columns for the summary table
  }

Every other record field is passed through to the outputs untouched (never sent), so
you can join answers back to data Jev was not allowed to see.

Outputs in DIR: results.csv, results.jsonl, buckets/<name>.csv, summary.md, cache.jsonl.
A rerun only pays for items it has not labeled with the same questions.
"""
import argparse, csv, glob, hashlib, json, os, random, statistics, sys, time
import urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

API = "https://api.typesafe.ai/v1"
GATEWAY = "https://ai-gateway.vercel.sh/v1"   # used when only AI_GATEWAY_API_KEY is set
PRICE_PER_M_INPUT = 0.042          # dollars per million input tokens; output is free
KEY_FILE = Path("~/.config/typesafe/.env").expanduser()


# ---------- key ----------

def _find(name):
    if os.environ.get(name):
        return os.environ[name].strip(), "environment"
    root = Path(__file__).resolve().parent.parent   # repo root, so runs from jev-runs/ find the key
    candidates = [Path(".env"), Path(".env.local"), root / ".env.local", KEY_FILE] + [Path(p) for p in glob.glob(os.path.expanduser("~/.config/*/typesafe.env"))]
    for p in candidates:
        if p.is_file():
            for line in p.read_text().splitlines():
                if line.strip().startswith(name + "="):
                    v = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if v and "paste" not in v:
                        return v, str(p)
    return None, None


def find_key():
    """A native TypeSafe key wins; otherwise fall back to Vercel AI Gateway."""
    key, where = _find("TYPESAFE_API_KEY")
    if key:
        return key, where, "typesafe"
    key, where = _find("AI_GATEWAY_API_KEY")
    return key, where, ("gateway" if key else None)


def setup():
    key, where, _ = find_key()
    if key:
        print(f"A key is already set ({where}). Run: python3 jev.py check")
        return
    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not KEY_FILE.exists():
        KEY_FILE.write_text("# TypeSafe key: https://console.typesafe.ai/keys (the console may ask for a card to add credit)\n"
                            "TYPESAFE_API_KEY=paste-your-key-here\n")
        KEY_FILE.chmod(0o600)
    print(f"Key file: {KEY_FILE}\n1. Get a key at https://console.typesafe.ai/keys\n"
          f"2. Paste it after TYPESAFE_API_KEY= and save\n3. Run: python3 jev.py check")
    if sys.platform == "darwin" and not os.environ.get("JEV_NO_OPEN"):
        os.system(f"open -e '{KEY_FILE}'")


def http(method, path, key, body=None, timeout=60, base=API):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, method=method, headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": "how-to-jev/1.0"})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 529) and attempt < 5:
                time.sleep(min(2 ** attempt, 20) + random.random())
                continue
            detail = e.read().decode(errors="replace")[:300]
            raise RuntimeError(f"HTTP {e.code}: {detail}") from None
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < 5:
                time.sleep(min(2 ** attempt, 20))
                continue
            raise RuntimeError(f"network: {e}") from None


def check():
    key, where, provider = find_key()
    if not key:
        print("No TYPESAFE_API_KEY or AI_GATEWAY_API_KEY found. Run: python3 jev.py setup")
        sys.exit(1)
    if provider == "gateway":
        try:
            res = system_one(key, provider, {"model": "typesafe-ai/jev", "state": "A test.",
                             "questions": {"ok": {"type": "noul", "instructions": "Is this a test?",
                                                  "criteria": {"true": "It says it is a test", "false": "It does not"}}}})
        except RuntimeError as e:
            print(f"Gateway key found in {where} but the call failed: {e}")
            sys.exit(1)
        print(f"Gateway key OK ({where}, {len(key)} chars). Model: {res.get('model')}")
        return
    try:
        models = http("GET", "/models", key)["models"]
    except RuntimeError as e:
        print(f"Key found in {where} but the API refused it: {e}")
        sys.exit(1)
    print(f"Key OK ({where}, {len(key)} chars). Models: " + ", ".join(m["name"] for m in models))


# ---------- gateway ----------
# AI Gateway spells a Noul "boolean" and serves Jev at POST /v1/evaluate with model
# "typesafe-ai/jev". Translate on the way out and back so the rest of this file only
# ever sees the native TypeSafe shapes.

def _to_gateway(questions):
    return {k: {**q, "type": "boolean" if q["type"] == "noul" else q["type"]} for k, q in questions.items()}


def _from_gateway(answers):
    out = {}
    for k, a in answers.items():
        if a.get("type") == "boolean":
            v = a.get("boolean", a.get("probability", a.get("value")))
            out[k] = {**a, "type": "noul", "noul": v}
        else:
            out[k] = a
    return out


def system_one(key, provider, body):
    if provider == "gateway":
        body = {**body, "model": "typesafe-ai/jev" if body.get("model", "jev-latest") == "jev-latest" else body["model"],
                "questions": _to_gateway(body["questions"])}
        res = http("POST", "/evaluate", key, body, base=GATEWAY)
        res["answers"] = _from_gateway(res.get("answers", {}))
        return res
    return http("POST", "/systemone", key, body)


# ---------- data ----------

def load_records(path):
    p = Path(path)
    if p.suffix == ".jsonl":
        return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    if p.suffix == ".json":
        d = json.loads(p.read_text())
        return d if isinstance(d, list) else d.get("items") or d.get("records")
    if p.suffix == ".csv":
        with open(p, newline="", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))
    raise SystemExit(f"Unsupported input {p.suffix}: use .jsonl, .json or .csv")


def state_for(rec, spec):
    fields = spec["state_fields"]
    names = list(fields) if isinstance(fields, (list, dict)) else []
    missing = [f for f in names if f not in rec]
    if missing:
        raise KeyError(f"record is missing state field(s) {missing}")
    state = {f: rec[f] for f in names}
    if spec.get("context"):
        state = {**spec["context"], **state}
    return state


def flatten(answers):
    """One flat dict per item: q -> label or value, q.confidence, q.score, q.noul."""
    out = {}
    for q, a in answers.items():
        t = a.get("type")
        if t == "choice":
            out[q] = a["choice"]; out[f"{q}.confidence"] = round(a.get("confidence", 0), 3)
        elif t == "score":
            legend = a.get("legend", {})
            out[q] = legend.get(str(round(a["score"])), a["score"])
            out[f"{q}.score"] = round(a["score"], 3); out[f"{q}.confidence"] = round(a.get("confidence", 0), 3)
        elif t == "noul":
            out[q] = round(a["noul"], 3)
    return out


OPS = {"==": lambda a, b: a == b, "!=": lambda a, b: a != b, ">=": lambda a, b: a is not None and a >= b,
       ">": lambda a, b: a is not None and a > b, "<=": lambda a, b: a is not None and a <= b,
       "<": lambda a, b: a is not None and a < b, "in": lambda a, b: a in b, "not_in": lambda a, b: a not in b}


def bucket_for(row, rules):
    for rule in rules or []:
        ok = all(OPS[op](row.get(path), val) for path, op, val in rule.get("when", []))
        if rule.get("any"):
            ok = ok and any(OPS[op](row.get(path), val) for path, op, val in rule["any"])
        if ok:
            return rule["name"]
    return "review" if rules else ""


# ---------- run ----------

def run(a):
    spec = json.loads(Path(a.spec).read_text())
    recs = load_records(a.input)
    if a.sample and a.sample < len(recs):
        recs = random.Random(a.seed).sample(recs, a.sample)
    if a.limit:
        recs = recs[: a.limit]
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    qhash = hashlib.sha1(json.dumps([spec.get("model"), spec["questions"]], sort_keys=True).encode()).hexdigest()[:10]

    items = []
    for i, r in enumerate(recs):
        st = state_for(r, spec)
        h = hashlib.sha1((qhash + json.dumps(st, sort_keys=True, default=str)).encode()).hexdigest()
        items.append((i, r, st, h))

    approx = sum(len(json.dumps(st, default=str)) for _, _, st, _ in items) / 4 + len(items) * len(json.dumps(spec["questions"])) / 4
    if a.dry_run:
        print(f"{len(items)} items, about {approx/1e6:.2f}M input tokens, about ${approx*PRICE_PER_M_INPUT/1e6:.4f}. "
              f"Sample state:\n{json.dumps(items[0][2], indent=1, default=str)[:1500]}")
        return

    key, _, provider = find_key()
    if not key:
        raise SystemExit("No TYPESAFE_API_KEY or AI_GATEWAY_API_KEY. Run: python3 jev.py setup")
    cache_path = out / "cache.jsonl"
    cache = {}
    if cache_path.exists():
        for line in cache_path.read_text().splitlines():
            c = json.loads(line); cache[c["hash"]] = c
    todo = [it for it in items if it[3] not in cache]
    if a.max_cost is not None:
        est = (sum(len(json.dumps(it[2], default=str)) for it in todo) / 4
               + len(todo) * len(json.dumps(spec["questions"])) / 4) * PRICE_PER_M_INPUT / 1e6
        if est > a.max_cost:
            raise SystemExit(f"Estimated cost ${est:.4f} for {len(todo)} calls is over --max-cost ${a.max_cost:.2f}. Nothing was called.")
        print(f"{len(todo)} new calls, estimated ${est:.4f} (cap ${a.max_cost:.2f})")
    body_base = {"model": spec.get("model", "jev-latest"), "questions": spec["questions"]}

    def call(it):
        t0 = time.time()
        try:
            res = system_one(key, provider, {**body_base, "state": it[2]})
            return {"hash": it[3], "model": res.get("model"), "answers": res["answers"],
                    "input_tokens": res.get("usage", {}).get("input_tokens", 0), "ms": int((time.time() - t0) * 1000)}
        except Exception as e:
            return {"hash": it[3], "error": str(e)[:300], "ms": int((time.time() - t0) * 1000)}

    t0 = time.time(); errors = 0; new_tokens = 0
    with ThreadPoolExecutor(a.concurrency) as ex, open(cache_path, "a") as cf:
        futs = [ex.submit(call, it) for it in todo]
        for n, f in enumerate(as_completed(futs), 1):
            c = f.result()
            if "error" in c:
                errors += 1
                if errors <= 3:
                    print("  error:", c["error"], file=sys.stderr)
                continue
            cf.write(json.dumps(c) + "\n"); cache[c["hash"]] = c; new_tokens += c["input_tokens"]
            if n % 100 == 0 or n == len(todo):
                print(f"  {n}/{len(todo)} labeled, ${new_tokens*PRICE_PER_M_INPUT/1e6:.4f} so far", file=sys.stderr)
    wall = time.time() - t0

    rows = []
    for i, r, st, h in items:
        c = cache.get(h)
        if not c:
            continue
        row = {k: v for k, v in r.items() if not isinstance(v, (dict, list))}
        for k in list(row):
            if isinstance(row[k], str) and len(row[k]) > 300:
                row[k] = row[k][:300] + "…"
        row.update(flatten(c["answers"]))
        row["_bucket"] = bucket_for(row, spec.get("buckets"))
        row["_model"] = c.get("model"); row["_ms"] = c.get("ms"); row["_tokens"] = c.get("input_tokens")
        rows.append(row)

    cols = list(dict.fromkeys(k for r in rows for k in r))
    def write_csv(path, rs):
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(rs)
    write_csv(out / "results.csv", rows)
    with open(out / "results.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps(r, default=str) + "\n")
    if spec.get("buckets"):
        (out / "buckets").mkdir(exist_ok=True)
        for b in sorted({r["_bucket"] for r in rows}):
            write_csv(out / "buckets" / f"{b}.csv", [r for r in rows if r["_bucket"] == b])

    total_tokens = sum(r["_tokens"] or 0 for r in rows)
    ms = sorted(r["_ms"] for r in rows if r["_ms"])
    lines = [f"# Jev run: {Path(a.spec).stem}", "",
             f"- Items: {len(rows)} labeled ({len(todo) - errors} new calls, {len(items) - len(todo)} from cache, {errors} errors)",
             f"- Model: {rows[0]['_model'] if rows else '-'}",
             f"- Input tokens: {total_tokens:,}  |  cost: ${total_tokens*PRICE_PER_M_INPUT/1e6:.4f}  (output tokens are free)",
             f"- Wall time: {wall:.1f}s at concurrency {a.concurrency}" + (f"  |  per call p50 {ms[len(ms)//2]} ms, p95 {ms[int(len(ms)*.95)-1]} ms" if ms else ""),
             ""]
    if spec.get("buckets"):
        lines += ["## Buckets", ""] + [f"- **{b}**: {sum(r['_bucket']==b for r in rows)}" for b in
                                       [x["name"] for x in spec["buckets"]] + ["review"]] + [""]
    for q, qs in spec["questions"].items():
        vals = [r.get(q) for r in rows]
        if qs["type"] == "noul":
            v = [x for x in vals if isinstance(x, (int, float))]
            if v:
                lines.append(f"- `{q}` (noul): median {statistics.median(v):.2f}, share above 0.5: {sum(x>0.5 for x in v)/len(v):.0%}")
        else:
            counts = {}
            for x in vals:
                counts[x] = counts.get(x, 0) + 1
            conf = [r.get(f"{q}.confidence") or 0 for r in rows]
            lines.append(f"- `{q}`: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items(), key=lambda kv: -kv[1]))
                         + f"  |  confidence >= 0.8: {sum(c>=0.8 for c in conf)}/{len(conf)}")
    show = spec.get("show", [])
    if show:
        lines += ["", "## First 15 rows", "", "| " + " | ".join(show + ["bucket"]) + " |", "|" + "---|" * (len(show) + 1)]
        for r in rows[:15]:
            lines.append("| " + " | ".join(str(r.get(c, ""))[:60].replace("|", "/") for c in show) + f" | {r['_bucket']} |")
    (out / "summary.md").write_text("\n".join(lines) + "\n")
    cut = next((i for i, l in enumerate(lines) if l.startswith("## First")), len(lines))
    print("\n".join(l for l in lines[:cut] if l.strip()))
    print(f"Outputs: {out}/results.csv, summary.md" + (", buckets/" if spec.get("buckets") else ""))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("setup"); sub.add_parser("check")
    r = sub.add_parser("run")
    r.add_argument("spec"); r.add_argument("input"); r.add_argument("--out", required=True)
    r.add_argument("--sample", type=int); r.add_argument("--limit", type=int); r.add_argument("--seed", type=int, default=7)
    r.add_argument("--concurrency", type=int, default=16); r.add_argument("--dry-run", action="store_true")
    r.add_argument("--max-cost", type=float, help="abort before any API call if the estimated dollars for new calls exceed this")
    a = ap.parse_args()
    {"setup": lambda: setup(), "check": lambda: check(), "run": lambda: run(a)}[a.cmd]()


if __name__ == "__main__":
    main()
