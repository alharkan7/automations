# al-library — local ebook inventory, Google Books enrichment, and viewer

Small Python tools for a personal library living under **`~/Downloads/Lib*`** (or another folder you configure). They list files on disk, optionally normalize filenames, call the **Google Books API** to attach metadata and cover URLs, and serve a **macOS Books–style** HTML grid in the browser.

---

## Prerequisites

- **Python 3.10+** (recommended)
- **macOS** for “Show in Finder” (`open -R`) from the viewer; the static export still works elsewhere for browsing only
- A **Google Books API key** is *strongly* recommended for larger libraries (better quota, fewer HTTP 429 rate-limit responses)

---

## Setup

From this directory:

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Dependencies:

| Package        | Role |
|----------------|------|
| `python-dotenv`| Load `GOOGLE_BOOKS_API_KEY` from `.env` |
| `pypdf` (opt.) | Better PDF title/author extraction for search queries |

Environment variables (optional but recommended):

- Put **`GOOGLE_BOOKS_API_KEY=...`** in **`automations/.env`** or **`al-library/.env`**.  
  If both exist, **`al-library/.env` wins** for duplicate keys (local overrides repo root).

---

## Generated / hand-edited files

| File | Produced by | Purpose |
|------|-------------|---------|
| `library_inventory.json` | You: `list_library_files.py -o …` | Canonical list of paths, names, folders; input for `rename_library_files.py` |
| `google_books_scan.csv` | `scan_google_books.py -o …` | Per-file Google Books match, metadata JSON, `review_flag` for bad matches |
| `books_library.html` | `books_library_server.py --export` | Standalone viewer (no server); Finder/reveal and CSV flagging need the server |

`file-search-cost-est.md` is a separate note (cost/usage thinking), not part of the run pipeline.

---

## Scripts (what each one does)

### `list_library_files.py`

**Purpose:** Discover ebook files under a configurable **`Downloads/Lib*`** (or similar) tree and emit **JSON** (summary + file rows) or **CSV**.

**Each row includes:** absolute `file_path`, `file_name`, `file_stem`, `extension`, `rel_path`, `top_folder`, plus JSON summary counts by extension and top-level folder.

**Typical use — refresh inventory after adding or moving books:**

```bash
cd /path/to/automations/al-library
python3 list_library_files.py -o library_inventory.json
```

Useful flags:

- `--downloads-dir` — parent of the library glob (default: `~/Downloads`)
- `--lib-glob` — glob for library roots (default: `Lib*`)
- `--extensions` — comma-separated (default: `pdf,epub,mobi,azw3`)
- `--format csv` — files-only CSV instead of JSON

---

### `rename_library_files.py`

**Purpose:** Propose or apply **filename normalization** (typos, publisher tails, “Title - Author” → “Author - Title” rules, underscore cleanup, etc.) using paths from **`library_inventory.json`**.

**Default is dry-run** (prints `old → new`). Nothing is renamed until you pass **`--apply`**.

```bash
python3 rename_library_files.py              # preview
python3 rename_library_files.py --apply      # execute renames
```

- **`--inventory`** — alternate JSON path (default: `library_inventory.json` next to the script)
- Skips missing files; handles **case-only** renames on APFS with a safe two-step rename

**Suggested order:** refresh inventory → preview renames → apply → run Google scan again if names changed (so queries match the new stems).

---

### `scan_google_books.py`

**Purpose:** Walk the **same kind of disk tree** as the list script (`Lib*` under Downloads by default), build a **search query** per file (from EPUB/PDF metadata when possible, else filename cleanup), call **Google Books Volumes API**, and write **JSON or CSV** with status, IDs, URLs, and embedded metadata.

**Status values:**

| Status | Meaning |
|--------|---------|
| `matched` | At least one volume returned; a volume id was stored |
| `not_found` | API OK but no usable results |
| `error` | Network/API failure; see `lookup_error` (e.g. rate limit) |

**Progress** prints to **stderr** (`[i/n] query …`, `skip (cached matched)`, etc.).

**Typical use — full scan with incremental CSV (recommended):**

```bash
python3 scan_google_books.py --format csv -o google_books_scan.csv
```

**Resume behavior:** With **`-o`**, rows that are already **`matched`** and have a **`google_books_id`** are **skipped** on the next run. **`not_found`** and **`error`** rows are **retried**. The file is updated **incrementally** (atomic replace per flush). **`review_flag`** in the CSV is **preserved** when rescanning.

**Useful flags:**

| Flag | Effect |
|------|--------|
| `--no-resume` | Re-query every file (still writes incrementally if `-o` set) |
| `--delay SEC` | Pause between API calls (default `1.0`; increase if you see 429 without a key) |
| `--api-key` | Override key; otherwise env / `.env` |
| `--limit N` | Process only the first N files (testing) |
| `--extensions` | Default `pdf,epub` |

---

### `books_library_server.py`

**Purpose:** **HTTP server** that renders the library from **`google_books_scan.csv`**, or **`--export`** a single **`books_library.html`** for offline-ish viewing.

**Run locally (Finder + flagging work):**

```bash
python3 books_library_server.py
# http://127.0.0.1:8890  (default port)

python3 books_library_server.py --open   # macOS: open in default browser
```

**Regenerate static HTML** (no server needed to *view*; no Finder / no CSV updates):

```bash
python3 books_library_server.py --export
```

**Flags:**

- `--csv PATH` — alternate scan CSV
- `--port N` — listen port (default `8890`)

**Viewer features:** search, status filters (All / Matched / Not found / Error / Flagged), **sort by title**, cover links to Google Books, **flag incorrect match** (writes **`review_flag`** to CSV), **Show in Finder** for paths under your home directory.

---

## When you add books to the library

There is no single daemon watching the folder; **re-run the steps you care about** after copying files into `~/Downloads/Lib*` (or your configured roots).

### Minimal (metadata + viewer only)

1. **Enrich / update scan** (new files picked up automatically; existing `matched` rows skipped unless you use `--no-resume`):

   ```bash
   python3 scan_google_books.py --format csv -o google_books_scan.csv
   ```

2. **Open the viewer**

   ```bash
   python3 books_library_server.py
   ```

   Or refresh **`books_library.html`** after a scan:

   ```bash
   python3 books_library_server.py --export
   ```

### Full pipeline (inventory + optional renames + scan + viewer)

1. **Refresh inventory** (so renames and your records match disk):

   ```bash
   python3 list_library_files.py -o library_inventory.json
   ```

2. **Optional — normalize filenames**

   ```bash
   python3 rename_library_files.py
   python3 rename_library_files.py --apply
   ```

3. **Google Books scan** (same as minimal step 1).

4. **Viewer** (same as minimal step 2).

**If you only renamed files** without updating the CSV, paths inside **`google_books_scan.csv`** may be stale. Easiest fix: run **`scan_google_books.py`** with **`--no-resume`** once to rebuild rows for current paths, or delete/rename the CSV and run a full scan again (you will lose manual **`review_flag`** edits unless you merge them).

---

## Reviewing bad Google matches

The first API result is not always correct. In the **server** UI, use the **flag** control on a cover to set **`review_flag`** to **`incorrect`** in the CSV (toggle again to clear). Filter **Flagged** to review them. Those flags are kept when you resume **`scan_google_books.py`**.

---

## Troubleshooting (short)

| Issue | What to try |
|-------|-------------|
| HTTP **429** from Google | Set **`GOOGLE_BOOKS_API_KEY`**; increase **`--delay`** |
| “No paths matched …/Lib*” | Create a folder matching the glob under `Downloads`, or pass **`--downloads-dir`** / **`--lib-glob`** |
| Finder button does nothing | Use **`books_library_server.py`** (not static export); path must be a **file under your home directory** |
| PDF titles missing in queries | `pip install pypdf` and re-run scan |
| Inventory empty / wrong | Re-run **`list_library_files.py -o library_inventory.json`** with correct `--downloads-dir` |

---

## Summary cheat sheet

```bash
# Refresh file list
python3 list_library_files.py -o library_inventory.json

# Optional filename cleanup
python3 rename_library_files.py && python3 rename_library_files.py --apply

# Google metadata → CSV (resume-friendly)
python3 scan_google_books.py --format csv -o google_books_scan.csv

# Browse (live CSV + Finder + flags)
python3 books_library_server.py --open

# Or static HTML only
python3 books_library_server.py --export
```
