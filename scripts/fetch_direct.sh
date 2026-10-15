#!/usr/bin/env bash
# Download the reports that have stable, directly fetchable URLs:
# X (from its India index page), Google (predictable file names) and
# Roblox (one page per month that embeds the PDF link).
# Existing files are skipped, so this can be re-run to pick up new months.
set -euo pipefail
cd "$(dirname "$0")/.."
UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36'
mkdir -p reports/x reports/google reports/roblox

# X: every PDF linked from the India country page.
curl -sSL -A "$UA" https://transparency.x.com/en/reports/countries/in \
  | grep -oE 'https://transparency.x.com/content/dam/transparency-twitter/country-reports/india/[^"]*\.pdf' \
  | sort -u | while read -r u; do
      f="reports/x/$(basename "$u")"
      [ -s "$f" ] || curl -sSL -A "$UA" --retry 3 -o "$f" "$u"
    done

# Google: india-intermediary-guidelines_YYYY-M-1_YYYY-M-<last>_en_v1.pdf
G=https://storage.googleapis.com/transparencyreport/report-downloads
for y in $(seq 2021 "$(date +%Y)"); do
  for m in $(seq 1 12); do
    o=$(printf 'reports/google/google_india_%d-%02d.pdf' "$y" "$m")
    [ -s "$o" ] && continue
    last=$(date -d "$y-$m-01 +1 month -1 day" +%-d)
    u="$G/india-intermediary-guidelines_${y}-${m}-1_${y}-${m}-${last}_en_v1.pdf"
    [ "$(curl -sS -o "$o" -w '%{http_code}' "$u")" = 200 ] || rm -f "$o"
  done
done

# Roblox: about.roblox.com/pdf/<month>-<year>-india-information-technology-rules-report
for y in $(seq 2025 "$(date +%Y)"); do
  for m in january february march april may june july august september october november december; do
    o="reports/roblox/roblox_india_$(date -d "$m 1 $y" +%Y-%m).pdf"
    [ -s "$o" ] && continue
    page=$(curl -sS -A "$UA" "https://about.roblox.com/pdf/$m-$y-india-information-technology-rules-report" || true)
    pdf=$(grep -oE 'https://cms-media.roblox.com/assets/[^"\\]*\.pdf' <<<"$page" | head -1 || true)
    [ -n "$pdf" ] && curl -sSL -A "$UA" -o "$o" "$pdf"
  done
done
echo done
