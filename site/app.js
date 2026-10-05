// Renders site/data.json. Every value from the data goes in through textContent, never innerHTML.
"use strict";

// [label, color group]. Groups: ai = AI roles, other = PM/program not AI, none = not a fit or review.
const BUCKETS = {
  ai_pm_no_ml_required: ["AI PM, no ML background required", "ai"],
  ai_program_or_tpm: ["AI program / TPM", "ai"],
  ai_pm_ml_required: ["AI PM, ML background required", "ai"],
  program_or_tpm_non_ai: ["Program / TPM, not AI", "other"],
  pm_non_ai: ["PM, not AI", "other"],
  not_a_fit: ["Not a PM or program role", "none"],
  review: ["Low confidence, needs review", "none"],
};
const TARGET = new Set(["ai_program_or_tpm", "ai_pm_no_ml_required", "ai_pm_ml_required", "program_or_tpm_non_ai", "pm_non_ai"]);
const FIT = {
  remote_canada: "Remote in Canada",
  toronto_ontario_office: "Toronto / Ontario office",
  canada_other_city: "Other Canadian city",
  canada_unspecified: "Canada",
};
const PAGE = 100;

const $ = (id) => document.getElementById(id);
const el = (tag, props = {}, ...kids) => {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k === "text") n.textContent = v;
    else if (k === "class") n.className = v;
    else n.setAttribute(k, v);
  }
  for (const c of kids) if (c) n.append(typeof c === "string" ? document.createTextNode(c) : c);
  return n;
};
const fmt = (n) => n.toLocaleString("en-US");
const money = (n) => (n >= 1000 ? "$" + Math.round(n / 1000) + "k" : "$" + n);
const level = (s) => (s || "").replace(/\s*\(.*$/, "").replace(/,? (head of a function|principal or group lead).*$/i, "");
const group = (b) => (BUCKETS[b] || ["", "none"])[1];
const hasAiSkills = (r) => typeof r.requires_hands_on_ai === "number";

let roles = [];
let run = null;
let shown = PAGE;

function renderRun(run) {
  const set = (k, v) => document.querySelectorAll(`[data-run="${k}"]`).forEach((n) => (n.textContent = v));
  set("boards", run.boards);
  set("scanned", run.scanned ? fmt(run.scanned) : "—");
  set("labeled", fmt(run.labeled));
  set("seconds", run.seconds ? run.seconds.toFixed(1) + " s" : "—");
  set("cost", "$" + run.cost_usd.toFixed(2));
  const d = new Date(run.date + "T12:00:00");
  set("date", isNaN(d) ? run.date : d.toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" }));
  set("model", run.model || "—");
  set("p50", run.p50_ms ? run.p50_ms + " ms" : "—");
}

const SVGNS = "http://www.w3.org/2000/svg";
const svgEl = (tag, attrs) => {
  const n = document.createElementNS(SVGNS, tag);
  for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
  return n;
};
const SHORT = {
  ai_pm_no_ml_required: "AI PM, no ML required", ai_pm_ml_required: "AI PM, ML required",
  ai_program_or_tpm: "AI program / TPM", program_or_tpm_non_ai: "Program / TPM, not AI",
  pm_non_ai: "PM, not AI", review: "Needs review", not_a_fit: "Not PM or program",
};
// Streams left to right in the band. They peel off right to left, so the last one is the top row.
const LANES = ["not_a_fit", "review", "pm_non_ai", "program_or_tpm_non_ai", "ai_program_or_tpm", "ai_pm_ml_required", "ai_pm_no_ml_required"];

function renderHero() {
  const ml = roles.filter((r) => r.bucket === "ai_pm_ml_required").length;
  const noMl = roles.filter((r) => r.bucket === "ai_pm_no_ml_required").length;
  const total = ml + noMl;
  if (!total) return;
  $("headline").replaceChildren(
    "Only ", el("span", { class: "hl", text: `${fmt(ml)} of ${fmt(total)}` }),
    " AI product manager openings require hands-on ML experience.");
  $("flow-note").textContent =
    `The other ${Math.round((noMl / total) * 100)}% of AI PM openings want product judgment about AI, not a model-building background. ` +
    `Jev's ML answer matched my hand labels on 36 of 40 postings.`;
}

// Fig. 1: the run drawn to one scale, from every scanned role down to the buckets.
let flowW = 0;
function renderFlow(run, animate) {
  const box = $("flow");
  const W = box.clientWidth;
  if (!W || W === flowW) return;
  flowW = W;
  const narrow = W < 560;
  const scanned = run.scanned || roles.length;
  const k = W / scanned;
  $("flow-scale").textContent = fmt(Math.round(scanned / W));

  const counts = {};
  for (const r of roles) counts[r.bucket] = (counts[r.bucket] || 0) + 1;
  const t = LANES.map((b) => Math.max((counts[b] || 0) * k, 2));
  const band = t.reduce((a, b) => a + b, 0);

  const step = narrow ? 58 : 46;
  const barY = 36, barH = 10;
  const yDrop = barY + barH + 24, yKept = yDrop + step, yCode = yKept + step, yJev = yCode + step;
  const yP = yJev + 72, gap = narrow ? 26 : 24, R0 = narrow ? 20 : 28;
  const xs = [];
  LANES.forEach((_, i) => xs.push(i ? xs[i - 1] + t[i - 1] + gap : 0));
  const last = LANES.length - 1;
  const cx = xs[last] + t[last] + R0, cy = yP, xEnd = cx + 20;
  const radius = (i) => cx - (xs[i] + t[i]);
  const H = cy + radius(0) + t[0] + 18;
  box.style.height = H + "px";

  const s = svgEl("svg", { width: W, height: H, viewBox: `0 0 ${W} ${H}`, "aria-hidden": "true" });
  if (animate) s.classList.add("reveal");
  s.append(svgEl("rect", { class: "s-drop", x: 0, y: barY, width: W, height: barH, rx: 2 }));
  s.append(svgEl("rect", { class: "s-code", x: 0, y: barY, width: band, height: yJev - barY }));
  s.append(svgEl("line", { class: "tick-code", x1: -6, x2: band + 12, y1: yCode, y2: yCode }));
  s.append(svgEl("line", { class: "tick-jev", x1: -6, x2: band + 12, y1: yJev, y2: yJev }));

  const labels = [];
  const label = (y, cls, kids, delay, top) => {
    const n = el("div", { class: `fl ${cls}${top ? " top" : ""}` }, ...kids);
    n.style.top = y + "px";
    n.style.left = (top ? 0 : band + 18) + "px";
    n.style.maxWidth = (W - (top ? 0 : band + 18)) + "px";
    n.style.setProperty("--d", delay + "s");
    labels.push(n);
  };
  const num = (v) => el("span", { class: "num", text: v });
  label(4, "head", [num(fmt(scanned)), ` open roles on ${run.boards} public careers boards`], 0, true);
  label(yDrop, "muted", [`${fmt(scanned - roles.length)} dropped by the title filter in code: not a product, program or TPM title`], 0.2);
  label(yKept, "head", [num(fmt(roles.length)), " product, program and TPM titles kept"], 0.35);
  label(yCode, "station code", [el("b", { text: "CODE" }), "pay range · remote flag · Toronto/Canada fit"], 0.5);
  label(yJev, "station jev", [el("b", { text: "JEV" }), `6 questions per role · ${run.seconds ? run.seconds.toFixed(1) + " s" : "—"} · $${run.cost_usd.toFixed(2)}`], 0.65);

  const ym = (yJev + yP) / 2;
  let c = 0;
  const streams = {};
  LANES.forEach((b, i) => {
    const w = t[i], x = xs[i], R = radius(i), n = counts[b] || 0;
    const d = `M${c},${yJev} C${c},${ym} ${x},${ym} ${x},${cy} ` +
      `A${R + w},${R + w} 0 0 0 ${cx},${cy + R + w} L${xEnd},${cy + R + w} L${xEnd},${cy + R} L${cx},${cy + R} ` +
      `A${R},${R} 0 0 1 ${x + w},${cy} C${x + w},${ym} ${c + w},${ym} ${c + w},${yJev} Z`;
    c += w;
    const p = svgEl("path", { class: `stream s-${group(b)}`, d });
    p.append(svgEl("title", {}));
    p.firstChild.textContent = `${BUCKETS[b][0]}: ${fmt(n)} roles`;
    s.append(p);
    streams[b] = p;

    const name = narrow || W - xEnd < 330 ? SHORT[b] : BUCKETS[b][0];
    const btn = el("button", { type: "button", class: `fl g-${group(b)}`, title: `Show the ${fmt(n)} roles in this bucket` }, name, num(fmt(n)));
    btn.style.top = cy + R + w / 2 + "px";
    btn.style.left = xEnd + 10 + "px";
    btn.style.setProperty("--d", 0.85 + (last - i) * 0.06 + "s");
    const on = (v) => { box.classList.toggle("hovering", v); p.classList.toggle("on", v); btn.classList.toggle("on", v); };
    const pick = () => { $("bucket").value = b; update(); $("roles").scrollIntoView(); };
    for (const n2 of [btn, p]) {
      n2.addEventListener("mouseenter", () => on(true));
      n2.addEventListener("mouseleave", () => on(false));
      n2.addEventListener("click", pick);
    }
    btn.addEventListener("focus", () => on(true));
    btn.addEventListener("blur", () => on(false));
    labels.push(btn);
  });
  box.replaceChildren(s, ...labels);
}

function renderToronto() {
  const tor = roles.filter((r) => FIT[r.location_fit]);
  const torTarget = tor.filter((r) => TARGET.has(r.bucket)).length;
  $("toronto-note").replaceChildren(
    el("strong", { text: "From Toronto: " }),
    `${fmt(tor.length)} roles can be done from Toronto or elsewhere in Canada, and ${fmt(torTarget)} of those are PM or program roles. ` +
    `Most of these companies hire in the US.`);
}

function renderEval() {
  document.querySelectorAll(".erow .fill").forEach((f) => (f.style.width = f.dataset.v + "%"));
}

function fillSelects() {
  const b = $("bucket");
  for (const [key, [label]] of Object.entries(BUCKETS)) b.append(el("option", { value: key, text: label }));
  const c = $("company");
  for (const name of [...new Set(roles.map((r) => r.company))].sort()) c.append(el("option", { value: name, text: name }));
}

function filtered() {
  const q = $("q").value.trim().toLowerCase();
  const bucket = $("bucket").value;
  const company = $("company").value;
  const toronto = $("toronto").checked;
  const aiSkills = $("aiskills").checked;
  const list = roles.filter((r) => {
    if (bucket === "" && !TARGET.has(r.bucket)) return false;
    if (bucket && bucket !== "*" && r.bucket !== bucket) return false;
    if (company && r.company !== company) return false;
    if (toronto && !FIT[r.location_fit]) return false;
    if (aiSkills && !(r.requires_hands_on_ai > 0.5 && r.requires_ml_background <= 0.5)) return false;
    if (q && !`${r.title} ${r.company} ${r.location} ${r.department}`.toLowerCase().includes(q)) return false;
    return true;
  });
  const sort = $("sort").value;
  if (sort === "pay") list.sort((a, b) => (b.pay_high || b.pay_low || 0) - (a.pay_high || a.pay_low || 0));
  else if (sort === "company") list.sort((a, b) => a.company.localeCompare(b.company) || a.title.localeCompare(b.title));
  return list;
}

function row(r) {
  const title = r.url
    ? el("a", { class: "ttl", href: r.url, target: "_blank", rel: "noopener noreferrer", text: r.title })
    : el("span", { class: "ttl", text: r.title });
  const loc = el("td", {}, el("span", { text: r.location || "—" }));
  if (FIT[r.location_fit]) loc.append(el("span", { class: "sub can", text: FIT[r.location_fit] }));
  else if (r.remote_listed) loc.append(el("span", { class: "sub", text: "Remote listed" }));
  const pay = r.pay_low && r.pay_high ? `${money(r.pay_low)}–${money(r.pay_high)}` : r.pay_low ? money(r.pay_low) : "—";
  const pctOf = (v) => (typeof v === "number" ? Math.round(v * 100) + "%" : "—");
  const lvl = level(r.seniority);
  return el("tr", {},
    el("td", {}, el("span", { class: "co", text: r.company }), title, r.department ? el("span", { class: "sub", text: r.department }) : null),
    el("td", {}, el("span", { class: "chip" }, el("span", { class: `dot g-${group(r.bucket)}` }), (BUCKETS[r.bucket] || [r.bucket])[0])),
    el("td", { class: lvl ? "" : "empty-sm", text: lvl || "—" }),
    loc,
    el("td", { class: "r" + (pay === "—" ? " empty-sm" : ""), "data-label": "Pay", text: pay }),
    el("td", { class: "r", "data-label": "ML required", text: pctOf(r.requires_ml_background) }),
    el("td", { class: "r col-ai", "data-label": "AI skills required", text: pctOf(r.requires_hands_on_ai) }));
}

function update(resetPage = true) {
  if (resetPage) shown = PAGE;
  const list = filtered();
  const body = $("rows");
  body.replaceChildren(...list.slice(0, shown).map(row));
  if (!list.length) body.append(el("tr", {}, el("td", { colspan: "7", text: "No roles match these filters." })));
  $("count").textContent = `${fmt(list.length)} role${list.length === 1 ? "" : "s"}` + (list.length > shown ? `, showing ${fmt(shown)}` : "");
  $("more").hidden = list.length <= shown;
}

async function main() {
  renderEval();
  try {
    const res = await fetch("data.json", { cache: "no-cache" });
    if (!res.ok) throw new Error(res.status);
    const data = await res.json();
    roles = data.roles;
    run = data.run;
    renderRun(run);
  } catch (e) {
    $("count").textContent = "Could not load the latest run.";
    $("flow").textContent = "Could not load the latest run.";
    return;
  }
  renderHero();
  renderFlow(run, true);
  new ResizeObserver(() => renderFlow(run, false)).observe($("flow"));
  renderToronto();
  fillSelects();
  // The AI-skills question was added after the first runs; hide its filter and column until the data has it.
  if (!roles.some(hasAiSkills)) {
    $("aiskills").closest("label").hidden = true;
    $("table").classList.add("no-ai");
  }
  for (const id of ["q", "bucket", "company", "sort", "toronto", "aiskills"]) $(id).addEventListener("input", () => update());
  $("filters").addEventListener("submit", (e) => e.preventDefault());
  $("more").addEventListener("click", () => { shown += PAGE; update(false); });
  update();
}

main();
