# AI PM Job Radar

Every product, program and technical program manager opening at 36 AI and tech companies, sorted by a decision model in 15 seconds for about 11 cents.

I built this for my own search: I'm a Toronto-based program manager targeting AI program, TPM and AI product roles. Job boards can't answer the questions I actually care about: is the product itself AI, does the role require hands-on ML, is it a program role or a product role, and can I do it from Toronto. A title filter gets these wrong, and running an LLM over a thousand postings every day is slow and expensive. So the radar splits the work: code handles the facts, and [Jev](https://docs.typesafe.ai) (TypeSafe's System One model) handles the meaning.

**Live:** [ai-pm-job-radar.vercel.app](https://ai-pm-job-radar.vercel.app), every labeled role with filters for bucket, company and Toronto fit.

## First full run (2026-10-02)

The live page refreshes every Monday (see `scripts/weekly_refresh.sh`); these are the numbers from the first run.

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
scripts/export_site.py  writes site/data.json (posting facts + labels only, no descriptions)
site/               static page on Vercel: no server, no API key, strict CSP
eval/               40 hand-labeled postings, the scorer, and RESULTS.md
```

**Code computes facts.** Pay ranges, the remote flag and where a Toronto-based person stands (`remote_canada`, `toronto_ontario_office`, `canada_other_city`, `canada_unspecified`, `outside_canada`) come from regex over the posting. The first version asked Jev for location, and it labeled four "Vancouver, BC" roles as US-only. A location string is a fact, so I moved it into code.

**Jev judges meaning.** There are six typed questions per posting, each answered with a probability:

| Question | Type | Why it can't be a keyword rule |
|---|---|---|
| `role_kind` | choice of 9 | "Product Marketing Lead" and "Fellows Program" contain "product" and "program" but aren't PM or program jobs |
| `ai_scope` | choice of 4 | Every posting at an AI company mentions AI; the question is whether *this team's* product is AI |
| `seniority` | 5-level score | Titles are inconsistent across companies |
| `requires_ml_background` | yes/no | Separates "must have shipped ML models" from "comfortable discussing AI" |
| `requires_hands_on_ai` | yes/no | Catches roles that screen for building with AI tools or agents, or required AI fluency, without asking for an ML background |
| `requires_engineering_background` | yes/no | Separates a CS-degree requirement from working with engineers |

Buckets combine the answers in code with a confidence floor of 0.6, and anything below it goes to `review`. All questions and thresholds live in `radar/spec.json`.

### Design decisions

- **Escape options on every choice** (`other`, `unclear`), so the model is never forced to guess.
- **Company boilerplate is excluded by instruction.** `ai_scope` tells Jev to ignore mission statements and benefits text that appear on every posting.
- **Iteration was measured on a sample first.** Each change was tested on a 40-role random sample (about half a cent) and a 55-role Canada set before the full run. One sample error, an "AI & LLM conversational fluency" line scored as a hard ML requirement, led to a sharper `requires_ml_background` definition.

## Evaluation

I labeled 40 postings by hand and scored Jev's answers against mine (`eval/`, full results in [`eval/RESULTS.md`](eval/RESULTS.md)). The sample takes a fixed number of postings from each bucket, so rare buckets get enough rows to check. These are per-bucket numbers, not the accuracy on a random posting.

| | All 40 | Labeled blind (21-40) |
|---|---|---|
| In an AI target bucket or not (rows not sent to review) | 32/36 | 15/18 |
| Exact bucket (rows not sent to review) | 26/36 | 11/18 |
| AI vs not AI (`ai_scope`, native and platform merged) | 33/40 | 16/20 |
| `role_kind` | 31/40 | 15/20 |
| Seniority within one level | 40/40 | 20/20 |
| `requires_ml_background` (strict) | 36/40 | 17/20 |
| `requires_hands_on_ai` | 31/40 | 14/20 |
| `requires_engineering_background` | 34/40 | 17/20 |

Model `jev-1.13.0`. Answers come from the 2026-10-04 run, except `requires_hands_on_ai`, which comes from a 2026-10-05 re-run on the same 40 postings ($0.005).

**How the labels were made.** Postings 21-40 were labeled without seeing Jev's answers. Postings 1-20 were labeled the same way, then 9 of their labels were revised after I saw Jev's answers and settled what "AI scope" means: *this team builds AI*, not *this is an AI company*. The originals are kept in `eval/labels_batch1_before_review.csv`. Treat the blind column as the honest one.

**What the eval changed.** On `requires_ml_background`, 12 of the first disagreements were me saying yes where Jev said no. The posting text showed I was answering a broader question: does the role need hands-on AI skills? That's a different question from whether it needs an ML background, so the spec now asks both. `requires_hands_on_ai` was added after this, and its wording was written after I had seen my own labels, so treat its 31/40 as a first read rather than a held-out score. I then relabeled the strict ML question for the 16 postings where I'd said yes.

**Where Jev and I still disagree.** Most misses don't change the bucket. They're TPM vs program manager, AI-native vs AI-platform, and seniority off by one level. The ones that do change the bucket are borderline AI-scope calls and 4 strict-ML calls that move a posting between the two AI PM buckets, plus the 4 postings Jev sent to review, which the table leaves out.

**Repeatability.** Re-running Jev on the same 40 postings gave the same `role_kind` and `ai_scope` on all 40, and the same bucket on 38. Both changes were near a cutoff: an ML score of 0.53 became 0.49, and a confidence of 0.63 became 0.54.

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

The site refreshes every Monday from the owner's machine (Windows Task Scheduler runs `scripts/weekly_refresh.sh`): fetch, label (capped at $0.30), export, push, and Vercel redeploys. The API key never leaves that machine. The export refuses to publish if more than 5% of labels failed or the role count halves. To refresh by hand, export and push:

```bash
python3 scripts/export_site.py jev-runs/radar/full --scanned <total printed by fetch.py>
git add site/data.json && git commit -m "Refresh radar data" && git push
```

`--dry-run` prints the token and cost estimate without calling the API. Reruns only pay for new postings. `jev.py` has an untested Vercel AI Gateway path that is used only when `AI_GATEWAY_API_KEY` is set and no TypeSafe key is.

## Credits

Built on the how-to-jev skill by Aakash Gupta ([product-growth.com](https://www.product-growth.com), MIT): the `jev.py` runner, validator and the original job-radar recipe. My changes: program and TPM roles, Toronto/Canada location logic, the tightened ML question, Vercel AI Gateway support, and the bucket design for my search.
