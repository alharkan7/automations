# Cloudflare Browser Rendering /crawl Endpoint

Automated web crawling using Cloudflare's Browser Rendering API.

## Setup

### Credentials

```bash
# Source .env file (create from .env.example)
source .env

# Or set manually
export CF_ACCOUNT_ID="your_account_id"
export CF_API_TOKEN="your_api_token"
```

### Create API Token

1. Go to https://dash.cloudflare.com/profile/api-tokens
2. Click "Create Token" -> "Create Custom Token"
3. Add permission: **Account - Browser Rendering - Edit**
4. Save the token

## Usage

### Basic Crawl

```bash
curl -X POST "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/browser-rendering/crawl" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "limit": 10,
    "formats": ["markdown"]
  }'
```

Response includes a job ID:
```json
{
  "success": true,
  "result": "c8e066ba-f9e4-4453-b2cb-d2110d060cee"
}
```

### Check Job Status

```bash
curl "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/browser-rendering/crawl/$JOB_ID" \
  -H "Authorization: Bearer $CF_API_TOKEN"
```

### Get Results

```bash
# Full results
curl "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/browser-rendering/crawl/$JOB_ID" \
  -H "Authorization: Bearer $CF_API_TOKEN" | jq '.result.records'

# Just URLs and status
curl "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/browser-rendering/crawl/$JOB_ID" \
  -H "Authorization: Bearer $CF_API_TOKEN" | jq '.result.records[] | {url, status, title: .metadata.title}'

# Just markdown content
curl "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/browser-rendering/crawl/$JOB_ID" \
  -H "Authorization: Bearer $CF_API_TOKEN" | jq -r '.result.records[] | .markdown'
```

## Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | string | required | Starting URL |
| `limit` | number | 10 | Max pages to crawl (max 100,000) |
| `depth` | number | 100,000 | Max link depth |
| `formats` | array | `["html"]` | Output formats: `html`, `markdown`, `json` |
| `render` | boolean | `true` | Execute JavaScript (false = faster static fetch) |
| `source` | string | `all` | URL discovery: `all`, `sitemaps`, `links` |
| `maxAge` | number | 86400 | Cache TTL in seconds (max 604,800) |

### Include/Exclude Patterns

```bash
curl -X POST "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/browser-rendering/crawl" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/docs",
    "limit": 100,
    "options": {
      "includePatterns": ["https://example.com/docs/**"],
      "excludePatterns": ["https://example.com/docs/changelog/**", "https://example.com/docs/archive/**"]
    }
  }'
```

### JSON Format (AI Extraction)

```bash
curl -X POST "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/browser-rendering/crawl" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://shop.example.com/products",
    "limit": 50,
    "formats": ["json"],
    "jsonOptions": {
      "prompt": "Extract product name, price, description, and availability",
      "response_format": {
        "type": "json_schema",
        "json_schema": {
          "name": "product",
          "properties": {
            "name": "string",
            "price": "number",
            "currency": "string",
            "description": "string",
            "inStock": "boolean"
          }
        }
      }
    }
  }'
```

### Static Mode (No JavaScript)

```bash
curl -X POST "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/browser-rendering/crawl" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "limit": 100,
    "render": false,
    "formats": ["html", "markdown"]
  }'
```

## Polling Script

```bash
#!/bin/bash

JOB_ID="$1"

while true; do
  RESULT=$(curl -s "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/browser-rendering/crawl/$JOB_ID?limit=1" \
    -H "Authorization: Bearer $CF_API_TOKEN")

  STATUS=$(echo "$RESULT" | jq -r '.result.status')

  if [ "$STATUS" != "running" ]; then
    echo "Job $STATUS"
    echo "$RESULT" | jq '.result'
    break
  fi

  echo "Status: $STATUS..."
  sleep 5
done
```

## Job Statuses

| Status | Description |
|--------|-------------|
| `running` | Crawl in progress |
| `completed` | Finished successfully |
| `cancelled_due_to_timeout` | Exceeded 7-day limit |
| `cancelled_due_to_limits` | Hit account limits |
| `cancelled_by_user` | Manually cancelled |
| `errored` | Encountered an error |

## Cancel a Job

```bash
curl -X DELETE "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/browser-rendering/crawl/$JOB_ID" \
  -H "Authorization: Bearer $CF_API_TOKEN"
```

## Pricing

- Free plan: 10 minutes of browser time per day
- Paid plan: Higher limits
- `render: false` crawls run on Workers (no browser time, currently free in beta)

## References

- Documentation: https://developers.cloudflare.com/browser-rendering/rest-api/crawl-endpoint/
- Changelog: https://developers.cloudflare.com/changelog/post/2026-03-10-br-crawl-endpoint/
