#!/bin/bash

# Poll Cloudflare crawl job status
# Usage: ./poll.sh <job_id>

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

if [ -z "$JOB_ID" ]; then
  echo "Usage: $0 <job_id>"
  exit 1
fi

while true; do
  RESULT=$(curl -s "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/browser-rendering/crawl/$JOB_ID?limit=1" \
    -H "Authorization: Bearer $CF_API_TOKEN")

  STATUS=$(echo "$RESULT" | jq -r '.result.status')
  TOTAL=$(echo "$RESULT" | jq -r '.result.total // 0')
  FINISHED=$(echo "$RESULT" | jq -r '.result.finished // 0')

  echo "[$(date +%H:%M:%S)] Status: $STATUS ($FINISHED/$TOTAL)"

  if [ "$STATUS" != "running" ]; then
    echo ""
    echo "Job $STATUS"
    echo "Browser seconds: $(echo "$RESULT" | jq -r '.result.browserSecondsUsed')"
    break
  fi

  sleep 5
done
