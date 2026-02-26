# LinkedIn Connection Remover

Automatically removes LinkedIn connections marked as "Remove" in your CSV file.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Set credentials (optional):**
   ```bash
   export LINKEDIN_EMAIL="your@email.com"
   export LINKEDIN_PASSWORD="your-password"
   ```
   Or enter them when prompted.

## Usage

```bash
python linkedin_remover.py
```

## Features

- **Resumable**: If interrupted, it will skip already processed connections
- **Safe delays**: Random human-like delays between actions (3-8 seconds)
- **Batch pauses**: Pauses 30 seconds after every 10 removals
- **Progress tracking**: Updates CSV with `Removal Status`, `Removal Error`, and `Removal Date` columns
- **Auto backup**: Creates `LinkedIn Connections_backup.csv` before running

## CSV Status Values

| Status | Meaning |
|--------|---------|
| `Removed` | Successfully removed |
| `Failed` | Error occurred (see Removal Error column) |
| `Skipped` | Manually skipped |

## Configuration

Edit these in `linkedin_remover.py`:

```python
HEADLESS = False  # Set True to run in background
MIN_DELAY = 3     # Min seconds between actions
MAX_DELAY = 8     # Max seconds between actions
```

## Risk Mitigation

- Uses non-headless browser by default (less suspicious)
- Random delays and mouse movements
- Removes automation indicators
- Pauses after batches of 10

## Troubleshooting

If LinkedIn challenges you:
1. Stop the script
2. Complete any security verification in the browser
3. Run the script again (it will resume from where it left off)
