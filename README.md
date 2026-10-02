# AI PM Job Radar

Every product, program and technical program manager opening at 36 AI and tech companies, sorted by a decision model in 15 seconds for about 11 cents.

I built this for my own search: I'm a Toronto-based program manager targeting AI program, TPM and AI product roles. Job boards can't answer the questions I actually care about: is the product itself AI, does the role require hands-on ML, is it a program role or a product role, and can I do it from Toronto. A title filter gets these wrong, and running an LLM over a thousand postings every day is slow and expensive. So the radar splits the work: code handles the facts, and [Jev](https://docs.typesafe.ai) (TypeSafe's System One model) handles the meaning.

## Latest run (2026-10-02)

| | |
|---|---|
| Open roles scanned | 8,381 across 36 public job boards |
| Product or program titles | 1,018 |
| Labeled by Jev | 1,018 in 15.0 s (p50 209 ms per call), 0 errors |
| Cost | $0.107 (2.55M input tokens at $0.042 per million; output is free) |
| Model | `jev-1.13.0` |

| Bucket | Roles |
|---|---|
| AI program / TPM | 126 |
| AI PM, no ML background required | 189 |
| AI PM, ML background required | 9 |
| Program / TPM, not AI | 141 |
| PM, not AI | 116 |
| Not a PM or program role | 403 |
| Low confidence, needs review | 34 |

Of the 1,018 roles, 56 can be done from Toronto (remote in Canada, or a Toronto, Ontario or other Canadian office), and 26 of those land in a target bucket.

**Finding:** only 9 of 198 AI PM roles list hands-on ML experience as a must-have. Most AI product roles want judgment about AI, not a model-building background.

## How it works

```
radar/boards.json   which companies (Greenhouse, Ashby, Lever slugs)
radar/fetch.py      pulls every open role, keeps product/program titles, computes facts in code
radar/spec.json     the questions Jev answers per role, plus bucket rules
scripts/jev.py      runs the spec over every role, caches answers, writes CSV + summary
```

**Code computes facts.** Pay ranges, the remote flag and where a Toronto-based person stands (`remote_canada`, `toronto_ontario_office`, `canada_other_city`, `canada_unspecified`, `outside_canada`) come from regex over the posting. The first version asked Jev for location, and it labeled four "Vancouver, BC" roles as US-only. A location string is a fact, so I moved it into code.

**Jev judges meaning.** There are five typed questions per posting, each answered with a probability:

| Question | Type | Why it can't be a keyword rule |
|---|---|---|
| `role_kind` | choice of 9 | "Product Marketing Lead" and "Fellows Program" contain "product" and "program" but aren't PM or program jobs |
| `ai_scope` | choice of 4 | Every posting at an AI company mentions AI; the question is whether *this team's* product is AI |
| `seniority` | 5-level score | Titles are inconsistent across companies |
| `requires_ml_background` | yes/no | Separates "must have shipped ML models" from "comfortable discussing AI" |
| `requires_engineering_background` | yes/no | Separates a CS-degree requirement from working with engineers |

Buckets combine the answers in code with a confidence floor of 0.6, and anything below it goes to `review`. All questions and thresholds live in `radar/spec.json`.

### Design decisions

- **Escape options on every choice** (`other`, `unclear`), so the model is never forced to guess.
- **Company boilerplate is excluded by instruction.** `ai_scope` tells Jev to ignore mission statements and benefits text that appear on every posting.
- **Iteration was measured on a sample first.** Each change was tested on a 40-role random sample (about half a cent) and a 55-role Canada set before the full run. One sample error, an "AI & LLM conversational fluency" line scored as a hard ML requirement, led to a sharper `requires_ml_background` definition.

## Evaluation status

The number of roles checked by hand is stated here; no accuracy figure is claimed. So far: a 40-role sample read by hand, with 1 clear error found and fixed, and 10 of 10 tricky location strings correct after the move to code. Next: 40 hand-labeled roles in `eval/` with per-bucket accuracy.

## Run it yourself

Python 3.9+, standard library only.

```bash
cp .env.example .env.local          # paste a TypeSafe key: https://console.typesafe.ai/keys
python3 scripts/jev.py check
mkdir -p jev-runs/radar && cd jev-runs/radar
python3 ../../radar/fetch.py --out input.jsonl
python3 ../../scripts/jev.py run ../../radar/spec.json input.jsonl --out . --sample 40   # under a cent
python3 ../../scripts/jev.py run ../../radar/spec.json input.jsonl --out .              # everything
```

`--dry-run` prints the token and cost estimate without calling the API. Reruns only pay for new postings. `jev.py` has an untested Vercel AI Gateway path that is used only when `AI_GATEWAY_API_KEY` is set and no TypeSafe key is.

## Credits

Built on the how-to-jev skill by Aakash Gupta ([product-growth.com](https://www.product-growth.com), MIT): the `jev.py` runner, validator and the original job-radar recipe. My changes: program and TPM roles, Toronto/Canada location logic, the tightened ML question, Vercel AI Gateway support, and the bucket design for my search.
