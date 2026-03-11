#!/bin/bash

# Cloudflare Browser Rendering Crawl Script
# Usage: ./crawl.sh <url> [limit]

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

URL="$1"
LIMIT="${2:-10}"
FORMATS="${FORMATS:-markdown}"

if [ -z "$URL" ]; then
  echo "Usage: $0 <url> [limit]"
  exit 1
fi

echo "Starting crawl: $URL (limit: $LIMIT)"

# Start crawl
RESPONSE=$(curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/browser-rendering/crawl" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"url\": \"$URL\",
    \"limit\": $LIMIT,
    \"formats\": [\"$FORMATS\"]
  }")

SUCCESS=$(echo "$RESPONSE" | jq -r '.success')

if [ "$SUCCESS" != "true" ]; then
  echo "Error starting crawl:"
  echo "$RESPONSE" | jq '.errors'
  exit 1
fi

JOB_ID=$(echo "$RESPONSE" | jq -r '.result')
echo "Job ID: $JOB_ID"

# Poll for completion
echo "Waiting for completion..."
while true; do
  sleep 3

  RESULT=$(curl -s "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/browser-rendering/crawl/$JOB_ID?limit=1" \
    -H "Authorization: Bearer $CF_API_TOKEN")

  STATUS=$(echo "$RESULT" | jq -r '.result.status')
  TOTAL=$(echo "$RESULT" | jq -r '.result.total // 0')
  FINISHED=$(echo "$RESULT" | jq -r '.result.finished // 0')

  echo "Status: $STATUS ($FINISHED/$TOTAL)"

  if [ "$STATUS" != "running" ]; then
    echo ""
    echo "Crawl $STATUS"
    echo "Browser seconds used: $(echo "$RESULT" | jq -r '.result.browserSecondsUsed')"
    break
  fi
done

# Get full results
echo "Fetching results..."
curl -s "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/browser-rendering/crawl/$JOB_ID" \
  -H "Authorization: Bearer $CF_API_TOKEN" | jq '.result' > "crawl_${JOB_ID}.json"

echo "Results saved to: crawl_${JOB_ID}.json"

# Show summary
echo ""
echo "Crawled pages:"
jq -r '.records[] | select(.status == "completed") | "  - \(.url) (\(.metadata.title))"' "crawl_${JOB_ID}.json"
