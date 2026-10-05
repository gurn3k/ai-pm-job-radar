---
version: 1
slug: "live-site"
primary_target: "site/index.html"
---

## Scope

Persuade, then let people browse. One public page: the story at the top for hiring managers, the role explorer at the bottom for job seekers. See `PRODUCT.md`.

## Audience, job, action, proof, constraints

- **Audience:** a hiring manager or recruiter for AI PM, program or TPM roles, giving the page a minute or two, often on a phone.
- **Job:** come away believing the builder can split work between code and a model, measure the model honestly, and ship something that keeps running.
- **Action:** read the finding, then either open the source on GitHub or browse the roles.
- **Proof:** show, don't describe. The weekly run itself, drawn to scale, from 8,427 scanned roles down to the buckets. Real numbers from `data.json` and `eval/RESULTS.md` only.
- **Constraints:** everything computed from the data must stay correct after Monday's refresh. No overall accuracy claim. Strict CSP: no inline styles, no external fonts or scripts. No personal job-search data.

## Direction contract

THESIS: Code computes facts, the model judges meaning, and you can watch the split happen. This rejects both the dashboard-of-KPI-tiles default and the chat-demo default for AI portfolio pages.

OWN-WORLD: The Sorting Line, an engineering flow diagram printed in a newspaper. Warm off-white paper, graphite ink for everything code computed, one blue reserved for Jev's judgment. Serif for prose that makes a claim, system monospace for facts, stations and sources.

STORY: The visitor sees 8,427 roles enter at the top as one wide bar, sees 7,411 dropped by a title filter, sees the remaining 1,016 pass a code station (pay, remote, location) and then a Jev station (six questions), and sees them fan out into seven buckets, drawn to scale. Then they read the eval that says how far to trust it.

FIRST VIEWPORT: The headline finding, a one-line dek and the top of the flow, with the 8,427 bar visibly narrowing.

FORM: The Sorting Line, picked over The Sweep (radar scope of blips) and The Annotated Report (Tufte sidenotes). Borrowed from the declined options:
- SOURCE TAGS (from The Annotated Report): every figure ends with a mono source line naming where its numbers come from.
- SWEEP MARK (from The Sweep): a small radar-sweep mark as the brand mark in the top bar and favicon.

FINISH: unreviewed and undocumented is unfinished. This build ends with a screenshot review (desktop, phone, light, dark) and `DESIGN.md`.

## Memorable moment

The 8,427-wide bar narrowing to a 1,016 band, which turns graphite to blue at the Jev station and then splits into seven streams, one scale throughout.

## Unresolved decisions

None for this build. Week-over-week history is out of scope until `data.json` keeps more than the latest run.
