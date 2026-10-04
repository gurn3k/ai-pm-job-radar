#!/usr/bin/env bash
# Weekly radar refresh, run on the owner's machine by Windows Task Scheduler (Mondays).
# Fetch, label with Jev (capped at $0.30), export, push; Vercel deploys the push.
# The API key stays in the local .env.local. Log: jev-runs/weekly/refresh.log
set -euo pipefail
cd "$(dirname "$0")/.."
run=jev-runs/weekly
mkdir -p "$run"
exec >>"$run/refresh.log" 2>&1
echo "=== $(date -Is)"

git pull --ff-only origin main
python3 radar/fetch.py --out "$run/input.jsonl" | tee "$run/fetch.log"
rm -f "$run/cache.jsonl"   # full relabel each week so the page's time and cost stats are a real full run
python3 scripts/jev.py run radar/spec.json "$run/input.jsonl" --out "$run" --max-cost 0.30
scanned=$(grep -oE '^[0-9,]+ open roles' "$run/fetch.log" | tr -dc 0-9)
python3 scripts/export_site.py "$run" --scanned "$scanned" --date "$(date +%F)"

git add site/data.json
if git diff --cached --quiet; then echo "No changes"; exit 0; fi
git commit -m "Weekly radar refresh $(date +%F) (automated)"
git push origin main
echo "=== done $(date -Is)"
