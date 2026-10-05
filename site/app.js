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

function renderHero() {
  const ml = roles.filter((r) => r.bucket === "ai_pm_ml_required").length;
  const noMl = roles.filter((r) => r.bucket === "ai_pm_no_ml_required").length;
  const total = ml + noMl;
  if (!total) return;
  $("headline").replaceChildren(
    "Only ", el("span", { class: "hl", text: `${fmt(ml)} of ${fmt(total)}` }),
    " AI product manager openings require hands-on ML experience.");

  const max = Math.max(ml, noMl);
  const bar = (label, n, muted) => {
    const b = el("div", { class: "bar" });
    b.style.width = (n / max) * 100 + "%";
    const pct = Math.round((n / total) * 100);
    const row = el("div", { class: "hrow" + (muted ? " muted" : ""), title: `${fmt(n)} roles, ${pct}% of AI PM openings` },
      el("span", { class: "lab", text: label }),
      el("span", { class: "track" }, b, el("span", { class: "val", text: fmt(n) })));
    return row;
  };
  $("hero-bars").replaceChildren(bar("No ML background required", noMl, false), bar("ML background required", ml, true));
  $("hero-note").textContent =
    `${Math.round((noMl / total) * 100)}% want product judgment about AI, not a model-building background. ` +
    `On my hand-labeled check, Jev's ML answer matched mine on 36 of 40 postings.`;
}

function renderBuckets() {
  const counts = {};
  for (const r of roles) counts[r.bucket] = (counts[r.bucket] || 0) + 1;
  const max = Math.max(...Object.values(counts));
  const box = $("buckets");
  for (const [key, [label, g]] of Object.entries(BUCKETS)) {
    const n = counts[key] || 0;
    const bar = el("span", { class: "bar" });
    bar.style.width = (n / max) * 100 + "%";
    const btn = el("button", { type: "button", class: `brow g-${g}`, title: `Show the ${fmt(n)} roles in this bucket` },
      el("span", { class: "blab", text: label }), el("span", { class: "btrack" }, bar), el("span", { class: "bcount", text: fmt(n) }));
    btn.addEventListener("click", () => {
      $("bucket").value = key;
      update();
      $("roles").scrollIntoView();
    });
    box.append(btn);
  }
  const ai = roles.filter((r) => group(r.bucket) === "ai").length;
  const target = roles.filter((r) => TARGET.has(r.bucket)).length;
  $("bucket-lede").textContent =
    `A title with "product" or "program" in it is not always a PM role. ${fmt(target)} of ${fmt(roles.length)} are real ` +
    `PM or program roles, and ${fmt(ai)} of those are on AI products. Click a bucket to see its roles.`;

  const tor = roles.filter((r) => FIT[r.location_fit]);
  const torTarget = tor.filter((r) => TARGET.has(r.bucket)).length;
  $("toronto-note").replaceChildren(
    el("strong", { text: "From Toronto: " }),
    `${fmt(tor.length)} roles can be done from Toronto or elsewhere in Canada, and ${fmt(torTarget)} of those are PM or program roles. `,
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
    renderRun(data.run);
  } catch (e) {
    $("count").textContent = "Could not load the latest run.";
    return;
  }
  renderHero();
  renderBuckets();
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
