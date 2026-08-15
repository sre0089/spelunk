#!/usr/bin/env bash
set -euo pipefail

if rg -n \
  --glob '!.git/**' \
  --glob '!.internal/**' \
  --glob '!dist/**' \
  --glob '!build/**' \
  --glob '!*.pyc' \
  --glob '!*.whl' \
  --glob '!*.tar.gz' \
  --glob '!scripts/privacy_scan.sh' \
  '(/Users/|/private/|/tmp/|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|API[_ -]?key|password|secret|token|BEGIN [A-Z ]*PRIVATE|sk-[A-Za-z0-9]{20,})' \
  .; then
  echo "Privacy scan found possible private material."
  exit 1
else
  status=$?
  if [[ "${status}" -eq 1 ]]; then
    echo "No private patterns found."
    exit 0
  fi
  exit "${status}"
fi
