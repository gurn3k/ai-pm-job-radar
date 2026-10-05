---
name: AI PM Job Radar
description: The weekly run drawn to scale, from every scanned role to seven buckets, with code's work in graphite and Jev's judgment in blue.
colors:
  paper: "#faf9f5"          # dark: #141412
  ink: "#1a1915"            # dark: #f2f0e8
  ink-soft: "#55534c"       # dark: #c2bfb3
  ink-faint: "#8a877d"      # dark: #8d8a80
  rule: "#e4e1d8"           # dark: #2f2e2a
  code: "#3b3a35"           # dark: #a3a094
  jev: "#2a78d6"            # dark: #3987e5
  jev-ink: "#1c5cab"        # dark: #86b6ef
  jev-wash: "#eaf2fc"       # dark: #172638
  other: "#9a978c"          # dark: #7d7a70
  none: "#d9d6cc"           # dark: #3d3c37
typography:
  serif: "Iowan Old Style, Charter, Source Serif Pro, Sitka Text, Cambria, Georgia (system only)"
  sans: "-apple-system, Segoe UI, Inter, Roboto (system only)"
  mono: "ui-monospace, SF Mono, Cascadia Mono, Consolas (system only)"
---

# Design System: AI PM Job Radar

Brief: `design/surfaces/live-site.md`. Product context: `PRODUCT.md`.

## Overview

**North star: "The Sorting Line."** The page shows the weekly run as one flow diagram, the way a newspaper would print an engineering figure. 8,427 scanned roles enter as a full-width bar. 7,411 are dropped by the title filter. The 1,016 that remain hang down as a graphite band, pass a CODE station and a JEV station, and fan out into seven bucket streams. Every width in the figure uses one scale (px per role), recomputed from `data.json` on each render.

It turns down two defaults: the dashboard of KPI tiles, and the AI chat demo. The figure *is* the method: you can see where code stops and the model starts.

## Colors

### Named rules

**The Graphite and Blue Rule.** Graphite (`code`) marks what code computed: the kept band, the CODE station, and facts set in mono. Blue (`jev`) marks Jev's judgment: the JEV station, AI bucket streams and chips, eval bars, and the headline's number. Blue is never used for decoration. Links use `jev-ink` because they need a link color, and that's the only exception.

**Three groups, not seven hues.** Buckets are colored by group: AI (`jev`), PM or program but not AI (`other`), not a fit or needs review (`none`). The bucket name is always written next to the color, so color never carries meaning alone.

Dark mode uses its own selected steps, not an automatic flip. `code` lightens to `#a3a094` so the band doesn't become the loudest thing on the page.

## Typography

- **Serif** for claims: the headline, dek, section heads, pull quote and the figure annotation.
- **Sans** for reading and UI: body text, labels and the table.
- **Mono** for facts and sources: every count in the figure, the station labels, the run stats, the eval numbers, pay and probabilities in the table, `Fig. n` markers and source lines.

**The Facts-in-Mono Rule.** A number that came out of the data is set in mono with tabular figures. Prose that makes a claim about it is serif or sans. (This is Redline's Cited-in-Mono rule, adapted.)

System fonts only. The CSP (`default-src 'none'`) blocks web fonts. Adding one means self-hosting it and adding `font-src 'self'`.

## Layout

The story column (masthead, Fig. 1, method, accuracy) is capped at 760px. The roles explorer uses the full 1120px. Sections are separated by a 1px ink rule at the top (`--rule-strong`), not by cards or background bands. Fig. 1 labels are HTML placed over the SVG, so they wrap and stay selectable. On phones the bucket labels switch to short names.

## Components

### Fig. 1, the Sorting Line (signature)
- Built by `renderFlow()` in `site/app.js`. It is re-rendered when the container width changes.
- Scale: `k = width / scanned`. Bucket stream width is `count × k`, with a minimum of 2px (the label carries the exact count).
- Streams peel off as concentric quarter rings sharing one center, so they never cross. The AI group is on top.
- The band is graphite until the JEV station and colored by group after it. That color change is the memorable moment.
- Hovering a stream or its label dims the others. Clicking filters the roles table.
- Entrance: the SVG reveals top to bottom and the labels fade in, staggered. Both are off under `prefers-reduced-motion`.

### Source tags (borrowed from The Annotated Report)
Every figure and stat block ends with a mono `Source:` line naming `data.json`, `eval/RESULTS.md` or the README.

### Sweep mark (borrowed from The Sweep)
A radar ring with a sweep line and one blip, drawn in `currentColor`, used in the top bar and as the favicon. No "live" claim: the data is weekly.

### Roles explorer
Filters in one row above the table. Rows show company (small caps), title (linked to the posting), team, a bucket chip, level, location (green when doable from Canada), pay, and probabilities. On phones the rows become cards.

## Do's and Don'ts

### Do
- Compute every number from `data.json`, or quote it from `eval/RESULTS.md`. The page must still be right after Monday's refresh.
- Keep one scale for the whole figure.
- Hide fields the data doesn't have yet (`requires_hands_on_ai`) instead of showing dashes.
- Set widths from JS (`el.style.width`), never with inline `style` attributes, because the CSP blocks them.
- Re-run the screenshot review (desktop and phone, light and dark) after any visual change.

### Don't
- Don't use blue for anything that isn't Jev's judgment.
- Don't give the seven buckets seven hues.
- Don't state an overall accuracy rate, or any eval number without its sample.
- Don't add week-over-week claims until `data.json` keeps history.
- Don't add external fonts, scripts or images without updating the CSP in `site/vercel.json` on purpose.
