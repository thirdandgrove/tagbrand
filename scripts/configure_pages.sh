#!/usr/bin/env bash
# Safe to re-run before or after DNS propagation and deployment.
set -euo pipefail

repo=thirdandgrove/tagbrand
domain=brand.thirdandgrove.com
endpoint="repos/$repo/pages"
gh auth status >/dev/null

# Only create on a real 404; surface permission and network errors immediately.
if state=$(gh api "$endpoint" 2>&1); then
  gh api -X PUT "$endpoint" -f build_type=workflow >/dev/null
elif [[ "$state" == *"HTTP 404"* ]]; then
  gh api -X POST "$endpoint" -f build_type=workflow >/dev/null
else
  printf '%s\n' "$state" >&2
  exit 1
fi
gh api -X PUT "$endpoint" -f cname="$domain" >/dev/null
printf 'Pages configured: workflow deployment, custom domain %s\n' "$domain"

deadline=$((SECONDS + 1200))
while true; do
  cname=$(dig +short CNAME "$domain" || true)
  certificate=$(gh api "$endpoint" --jq '.https_certificate.state // "pending"')
  printf '%s CNAME=%s certificate=%s\n' "$(date -u +%FT%TZ)" "${cname:-pending}" "$certificate"
  if [[ "$certificate" == "approved" ]]; then
    gh api -X PUT "$endpoint" -F https_enforced=true >/dev/null
    printf 'HTTPS enforcement enabled for https://%s\n' "$domain"
    exit 0
  fi
  if (( SECONDS >= deadline )); then
    printf 'DNS or certificate still pending. After DNS propagates, re-run ./scripts/configure_pages.sh\n'
    exit 0
  fi
  # Short intervals keep the process observable and interruptible.
  remaining=$((deadline - SECONDS))
  if (( remaining < 30 )); then sleep "$remaining"; else sleep 30; fi
done
