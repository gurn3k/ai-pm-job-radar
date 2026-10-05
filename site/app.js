// Renders site/data.json. Every value from the data goes in through textContent, never innerHTML.
"use strict";

const BUCKETS = {
  ai_program_or_tpm: ["AI program / TPM", "--b-ai-prog"],
  ai_pm_no_ml_required: ["AI PM, no ML background required", "--b-ai-pm"],
  ai_pm_ml_required: ["AI PM, ML background required", "--b-ai-pm-ml"],
  program_or_tpm_non_ai: ["Program / TPM, not AI", "--b-prog"],
  pm_non_ai: ["PM, not AI", "--b-pm"],
  not_a_fit: ["Not a PM or program role", "--b-none"],
  review: ["Low confidence, needs review", "--b-review"],
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
  for (const c of kids) if (c) n.append(c);
  return n;
};
const fmt = (n) => n.toLocaleString("en-US");
const money = (n) => (n >= 1000 ? "$" + Math.round(n / 1000) + "k" : "$" + n);
const level = (s) => (s || "").replace(/\s*\(.*$/, "").replace(/,? (head of a function|principal or group lead).*$/i, "");

let roles = [];
let shown = PAGE;

function dot(bucket) {
  const d = el("span", { class: "dot" });
  d.style.background = `var(${(BUCKETS[bucket] || ["", "--b-none"])[1]})`;
  return d;
}

function renderRun(run) {
  const set = (k, v) => document.querySelectorAll(`[data-run="${k}"]`).forEach((n) => (n.textContent = v));
  set("boards", run.boards);
  set("scanned", run.scanned ? fmt(run.scanned) : "—");
  set("labeled", fmt(run.labeled));
  set("seconds", run.seconds ? run.seconds.toFixed(1) + " s" : "—");
  set("cost", "$" + run.cost_usd.toFixed(2));
  set("date", run.date);
  set("model", run.model || "—");
  set("p50", run.p50_ms ? run.p50_ms + " ms" : "—");
}

function renderFinding() {
  const aiPm = roles.filter((r) => r.bucket === "ai_pm_ml_required" || r.bucket === "ai_pm_no_ml_required");
  const ml = aiPm.filter((r) => r.bucket === "ai_pm_ml_required").length;
  const tor = roles.filter((r) => FIT[r.location_fit]);
  const torTarget = tor.filter((r) => TARGET.has(r.bucket)).length;
  $("finding").textContent =
    `Only ${ml} of ${aiPm.length} AI PM roles list hands-on ML experience as a must-have. ` +
    `Most AI product roles want judgment about AI, not a model-building background. ` +
    `${tor.length} roles can be done from Toronto, and ${torTarget} of those are PM or program roles.`;
}

function renderBuckets() {
  const counts = {};
  for (const r of roles) counts[r.bucket] = (counts[r.bucket] || 0) + 1;
  const max = Math.max(...Object.values(counts));
  const box = $("buckets");
  for (const [key, [label]] of Object.entries(BUCKETS)) {
    const n = counts[key] || 0;
    const btn = el("button", { type: "button", text: label, title: "Show these roles" });
    btn.addEventListener("click", () => {
      $("bucket").value = key;
      update();
      $("roles-h").scrollIntoView({ behavior: "smooth" });
    });
    const bar = el("div", { class: "bar" });
    bar.style.width = (n / max) * 100 + "%";
    bar.style.background = `var(${BUCKETS[key][1]})`;
    box.append(el("div", { class: "brow" }, btn, bar, el("span", { class: "bcount", text: fmt(n) })));
  }
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
  return roles.filter((r) => {
    if (bucket === "" && !TARGET.has(r.bucket)) return false;
    if (bucket && bucket !== "*" && r.bucket !== bucket) return false;
    if (company && r.company !== company) return false;
    if (toronto && !FIT[r.location_fit]) return false;
    if (aiSkills && !(r.requires_hands_on_ai > 0.5 && r.requires_ml_background <= 0.5)) return false;
    if (q && !`${r.title} ${r.company} ${r.location} ${r.department}`.toLowerCase().includes(q)) return false;
    return true;
  });
}

function row(r) {
  const title = r.url
    ? el("a", { href: r.url, target: "_blank", rel: "noopener noreferrer", text: r.title })
    : document.createTextNode(r.title);
  const loc = el("td", {}, el("span", { text: r.location || "—" }));
  if (FIT[r.location_fit]) loc.append(el("span", { class: "sub can", text: FIT[r.location_fit] }));
  else if (r.remote_listed) loc.append(el("span", { class: "sub", text: "Remote listed" }));
  const pay = r.pay_low && r.pay_high ? `${money(r.pay_low)}–${money(r.pay_high)}` : r.pay_low ? money(r.pay_low) : "—";
  const pctOf = (v) => (typeof v === "number" ? Math.round(v * 100) + "%" : "—");
  return el("tr", {},
    el("td", { class: "co", text: r.company }),
    el("td", {}, title, r.department ? el("span", { class: "sub", text: r.department }) : null),
    el("td", {}, el("span", { class: "chip" }, dot(r.bucket), document.createTextNode((BUCKETS[r.bucket] || [r.bucket])[0]))),
    el("td", { text: level(r.seniority) || "—" }),
    loc,
    el("td", { class: "r", text: pay }),
    el("td", { class: "r", text: pctOf(r.requires_ml_background) }),
    el("td", { class: "r", text: pctOf(r.requires_hands_on_ai) }));
}

function update(resetPage = true) {
  if (resetPage) shown = PAGE;
  const list = filtered();
  const body = $("rows");
  body.replaceChildren(...list.slice(0, shown).map(row));
  if (!list.length) body.append(el("tr", {}, el("td", { colspan: "8", text: "No roles match these filters." })));
  $("count").textContent = `${fmt(list.length)} role${list.length === 1 ? "" : "s"}` + (list.length > shown ? `, showing ${fmt(shown)}` : "");
  $("more").hidden = list.length <= shown;
}

async function main() {
  try {
    const res = await fetch("data.json", { cache: "no-cache" });
    if (!res.ok) throw new Error(res.status);
    const data = await res.json();
    roles = data.roles;
    renderRun(data.run);
  } catch (e) {
    $("finding").textContent = "Could not load the latest run.";
    return;
  }
  renderFinding();
  renderBuckets();
  fillSelects();
  // The AI-skills question was added after the first runs; hide its filter until the data has it.
  if (!roles.some((r) => typeof r.requires_hands_on_ai === "number")) $("aiskills").closest("label").hidden = true;
  for (const id of ["q", "bucket", "company", "toronto", "aiskills"]) $(id).addEventListener("input", () => update());
  $("filters").addEventListener("submit", (e) => e.preventDefault());
  $("more").addEventListener("click", () => { shown += PAGE; update(false); });
  update();
}

main();
