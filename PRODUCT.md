# Product

## Platform

web (one static page)

## Stack

A static page in `site/` (HTML, CSS, vanilla JS, no build step, no dependencies), rendered from `site/data.json`, which `scripts/export_site.py` writes after each Jev run. Hosted on Vercel with Root Directory `site`, auto-deployed on every push to main. A local scheduled job refreshes it every Monday. No API key on Vercel. The page runs under a strict content security policy (`site/vercel.json`): scripts, styles and data from the same origin only, no inline styles, no third-party fonts or scripts.

## Users

Primary: a hiring manager or recruiter for AI product, program or technical program manager roles, who reaches the page from a resume, LinkedIn or the GitHub README and gives it a minute or two. They are judging the builder, not looking for a job.

Secondary: someone job hunting in AI PM, program or TPM roles who wants to browse the roles. They are served by the explorer at the bottom of the page, not by the story above it.

## Product Purpose

Show, with real numbers, that the builder can define an AI product, split work between code and a model, evaluate the model honestly, and ship something that keeps running. The page does that by publishing the radar's output: every PM, program and TPM opening at 36 AI and tech companies, labeled by Jev and refreshed weekly.

Success means a hiring manager leaves able to repeat the finding (few AI PM roles require hands-on ML), the method (code computes facts, the model judges meaning), and the eval result (32 of 36 on AI bucket or not), and knows where the code is.

## Positioning

Most AI portfolio projects are a chat demo with no measurement. This one is a working pipeline over live public data, with a published cost per run, a hand-labeled eval with its limits stated, and a weekly refresh that needs no manual steps.

## Operating Context

Read once, quickly, often on a phone, often from a link in an application. The data changes every Monday, so the headline, counts and charts are computed from `data.json` and must never be hard-coded. The eval numbers come from `eval/RESULTS.md` and change only when the eval is re-run.

## Capabilities and Constraints

- Every number on the page is either computed from `data.json` or quoted from `eval/RESULTS.md`. No estimates, no rounding up.
- Labels are model judgments and the page says so.
- Eval numbers are quoted as measured ("32 of 36 on a 40-posting hand-labeled eval"), never as a general accuracy rate. The set is stratified by bucket, which the page states.
- Only public posting facts and Jev's labels are published. No job descriptions, no personal job-search data, no API keys.
- Fields added to Jev's questions after the first runs (for example `requires_hands_on_ai`) are hidden until the data has them.
- CSP: no inline `style` attributes (set widths from JS), no external fonts unless `font-src 'self'` is added and the font files are self-hosted.

## Brand Commitments

Product name: AI PM Job Radar. Jev is TypeSafe's model and is named as such. Credit Aakash Gupta's how-to-jev skill (MIT).

Terms: **bucket** (where a role lands), **role** (one posting), **run** (one weekly fetch and label). The seven bucket names in `site/app.js` are the canonical labels.

Voice: plain and measured. State the finding, then the evidence, then the limits. Built "with AI coding agents"; never claim hand-written code.

## Evidence on Hand

- Weekly run stats (roles scanned, labeled, seconds, cost, p50 latency) in `data.json`.
- `eval/RESULTS.md`: 40 hand-labeled postings, per-question and per-bucket agreement, disagreements listed.
- README: first-run numbers, design decisions (location moved to code after Jev mislabeled Vancouver roles as US-only).

Explicit absences the page must not fabricate:
- No visitor, usage or traffic data.
- No overall accuracy figure (the eval is stratified, 40 postings).
- No week-over-week history yet: `data.json` holds only the latest run.
- No users or testimonials.

## Product Principles

1. Code computes facts; the model judges meaning. The page should make that split visible.
2. Every claim sits next to its evidence or a link to it.
3. Limits are stated, not hidden.
4. The page refreshes itself; nothing on it may go stale on Monday.
