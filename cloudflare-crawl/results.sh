#!/bin/bash

# View crawl job results
# Usage: ./results.sh <job_id> [format]
#   format: summary | urls | markdown | json (default: summary)

set -e

# Load credentials from .env file
if [ -f .env ]; then
  source .env
fi

if [ -z "$CF_ACCOUNT_ID" ] || [ -z "$CF_API_TOKEN" ]; then
  echo "Error: CF_ACCOUNT_ID and CF_API_TOKEN must be set"
  echo "Create a .env file from .env.example"
  exit 1
fi

JOB_ID="$1"
FORMAT="${2:-summary}"

if [ -z "$JOB_ID" ]; then
  echo "Usage: $0 <job_id> [format]"
  echo "Formats: summary, urls, markdown, json"
  exit 1
fi

RESULT=$(curl -s "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/browser-rendering/crawl/$JOB_ID" \
  -H "Authorization: Bearer $CF_API_TOKEN")

case "$FORMAT" in
  summary)
    echo "$RESULT" | jq '{
      status: .result.status,
      total: .result.total,
      finished: .result.finished,
      completed: (.result.records | map(select(.status == "completed")) | length),
      skipped: (.result.records | map(select(.status == "skipped")) | length),
      errored: (.result.records | map(select(.status == "errored")) | length),
      browserSecondsUsed: .result.browserSecondsUsed
    }'
    ;;
  urls)
    echo "$RESULT" | jq -r '.result.records[] | "\(.status) | \(.url)"'
    ;;
  markdown)
    echo "$RESULT" | jq -r '.result.records[] | select(.status == "completed") | "# \(.metadata.title)\n\n\(.markdown)\n\n---\n"'
    ;;
  json)
    echo "$RESULT" | jq '.result'
    ;;
  *)
    echo "Unknown format: $FORMAT"
    exit 1
    ;;
esac
