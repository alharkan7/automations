#!/usr/bin/env python3
"""
macOS Books-style viewer for google_books_scan.csv.

  python3 books_library_server.py              # http://127.0.0.1:8890
  python3 books_library_server.py --export   # write books_library.html (view only; Finder needs server)

Cover → opens Google Books in a new tab. File badge → POST /reveal → opens Finder with
the file selected (paths must live under your home directory).

Flag button on each cover → POST /flag → sets column `review_flag` to `incorrect` in the
CSV (toggle again to clear). Use the "Flagged" filter to review them.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CSV = SCRIPT_DIR / "google_books_scan.csv"
DEFAULT_EXPORT = SCRIPT_DIR / "books_library.html"
DEFAULT_PORT = 8890
REVIEW_FLAG_COL = "review_flag"


def read_scan_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows: list[dict[str, str]] = [dict(r) for r in reader]
    if REVIEW_FLAG_COL not in fieldnames:
        fieldnames.append(REVIEW_FLAG_COL)
        for r in rows:
            r[REVIEW_FLAG_COL] = ""
    else:
        for r in rows:
            if REVIEW_FLAG_COL not in r or r[REVIEW_FLAG_COL] is None:
                r[REVIEW_FLAG_COL] = ""
    return rows, fieldnames


def write_scan_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    tmp = path.parent / f".{path.name}.tmp"
    with tmp.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: (r.get(k) if r.get(k) is not None else "") for k in fieldnames})
    os.replace(tmp, path)


def apply_review_flag(csv_path: Path, file_path: str, value: str) -> tuple[bool, str]:
    if value not in ("", "incorrect"):
        return False, "review_flag must be '' or 'incorrect'"
    try:
        target = Path(file_path).expanduser().resolve()
    except OSError:
        return False, "bad file path"
    if not path_is_under_home(target):
        return False, "Path must be under your home directory"
    if not target.is_file():
        return False, "Not a file"
    rows, fieldnames = read_scan_csv(csv_path)
    found = False
    for r in rows:
        fp = (r.get("file_path") or "").strip()
        if not fp:
            continue
        try:
            if Path(fp).expanduser().resolve() == target:
                r[REVIEW_FLAG_COL] = value
                found = True
                break
        except OSError:
            continue
    if not found:
        return False, "file_path not found in CSV"
    write_scan_csv(csv_path, rows, fieldnames)
    return True, "ok"


def load_books(csv_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with csv_path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            meta: dict[str, Any] = {}
            mj = (row.get("metadata_json") or "").strip()
            if mj:
                try:
                    meta = json.loads(mj)
                except json.JSONDecodeError:
                    meta = {}
            il = meta.get("imageLinks") or {}
            thumb = il.get("thumbnail") or il.get("smallThumbnail") or ""
            if isinstance(thumb, str) and thumb.startswith("http://"):
                thumb = "https://" + thumb[7:]
            title = (meta.get("title") or "").strip()
            subtitle = (meta.get("subtitle") or "").strip()
            authors = meta.get("authors") or []
            if isinstance(authors, list):
                author_str = ", ".join(str(a) for a in authors if a)
            else:
                author_str = str(authors) if authors else ""
            display_title = title or Path(row.get("file_name", "")).stem
            rows.append(
                {
                    "file_path": row.get("file_path") or "",
                    "file_name": row.get("file_name") or "",
                    "status": row.get("status") or "",
                    "search_query": row.get("search_query") or "",
                    "google_books_id": (row.get("google_books_id") or "").strip() or None,
                    "google_books_url": (row.get("google_books_url") or "").strip() or None,
                    "cover_url": thumb or None,
                    "display_title": display_title,
                    "display_subtitle": subtitle,
                    "display_author": author_str,
                    "lookup_error": row.get("lookup_error") or "",
                    "review_flag": (row.get(REVIEW_FLAG_COL) or "").strip(),
                }
            )
    return rows


def path_is_under_home(p: Path) -> bool:
    try:
        rp = p.resolve()
        home = Path.home().resolve()
        return rp == home or home in rp.parents
    except (OSError, ValueError):
        return False


def reveal_in_finder(abs_path: str) -> tuple[bool, str]:
    p = Path(abs_path).expanduser()
    if not p.is_file():
        return False, "Not a file"
    if not path_is_under_home(p):
        return False, "Path must be under your home directory"
    try:
        subprocess.run(["/usr/bin/open", "-R", str(p.resolve())], check=True)
        return True, "ok"
    except subprocess.CalledProcessError as e:
        return False, str(e)


def build_html_payload(books: list[dict[str, Any]], *, standalone_fetch_reveal: bool) -> str:
    data_json = json.dumps(books, ensure_ascii=False).replace("</", "<\\/")
    reveal_note = ""
    if standalone_fetch_reveal:
        reveal_note = (
            "<p class='banner'>Finder buttons need the local server. Run: "
            "<code>python3 books_library_server.py</code> and open the URL it prints.</p>"
        )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Library</title>
  <style>
    :root {{
      --bg0: #e8eaed;
      --bg1: #f2f3f5;
      --card: #ffffff;
      --text: #1d1d1f;
      --text2: #6e6e73;
      --accent: #007aff;
      --shadow: 0 2px 8px rgba(0,0,0,.08), 0 1px 2px rgba(0,0,0,.06);
      --radius: 12px;
      --cover-radius: 6px;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif;
      color: var(--text);
      background: linear-gradient(165deg, var(--bg0) 0%, var(--bg1) 45%, #dfe3e8 100%);
    }}
    .toolbar {{
      position: sticky;
      top: 0;
      z-index: 20;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 12px 20px;
      padding: 16px 28px 14px;
      background: rgba(242,243,245,.82);
      backdrop-filter: blur(16px);
      border-bottom: 1px solid rgba(0,0,0,.06);
    }}
    h1 {{
      margin: 0;
      font-size: 1.35rem;
      font-weight: 600;
      letter-spacing: -0.02em;
    }}
    .counts {{ font-size: .85rem; color: var(--text2); }}
    .search {{
      flex: 1;
      min-width: 200px;
      max-width: 360px;
      padding: 8px 14px;
      border: 1px solid rgba(0,0,0,.12);
      border-radius: 10px;
      font-size: .95rem;
      background: var(--card);
    }}
    .sort-wrap {{
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: .85rem;
      color: var(--text2);
      white-space: nowrap;
    }}
    .sort-wrap label {{ cursor: pointer; }}
    .sort-select {{
      padding: 8px 12px;
      border-radius: 10px;
      border: 1px solid rgba(0,0,0,.12);
      font-size: .9rem;
      background: var(--card);
      color: var(--text);
      cursor: pointer;
      min-width: 9.5rem;
    }}
    .sort-select:focus {{
      outline: 2px solid var(--accent);
      outline-offset: 2px;
    }}
    .chips {{ display: flex; flex-wrap: wrap; gap: 8px; }}
    .chip {{
      border: none;
      padding: 6px 12px;
      border-radius: 20px;
      font-size: .8rem;
      background: rgba(0,0,0,.06);
      cursor: pointer;
      color: var(--text);
    }}
    .chip.on {{ background: var(--text); color: #fff; }}
    .banner {{
      margin: 0 28px 0;
      padding: 10px 14px;
      font-size: .85rem;background: #fff3cd;
      border-radius: var(--radius);
      color: #664d03;
    }}
    .banner code {{ font-size: .8rem; }}
    .shelf {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(152px, 1fr));
      gap: 28px 20px;
      padding: 28px;
      max-width: 1600px;
      margin: 0 auto;
    }}
    .book {{
      display: flex;
      flex-direction: column;
      align-items: stretch;
    }}
    .cover-wrap {{
      position: relative;
      aspect-ratio: 2 / 3;
      border-radius: var(--cover-radius);
      box-shadow: var(--shadow);
      overflow: hidden;
      background: linear-gradient(145deg, #d4d4d8, #a8a8ae);
    }}
    .cover-link {{
      display: block;
      width: 100%;
      height: 100%;
      outline: none;
    }}
    .cover-link:focus-visible {{ box-shadow: inset 0 0 0 3px var(--accent); }}
    .cover-img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }}
    .cover-placeholder {{
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 12px;
      text-align: center;
      font-size: .72rem;
      font-weight: 500;
      color: #3a3a3d;
      line-height: 1.35;
      word-break: break-word;
    }}
    .cover-badges {{
      position: absolute;
      bottom: 8px;
      left: 8px;
      z-index: 3;
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      gap: 4px;
      max-width: calc(100% - 16px);
      pointer-events: none;
    }}
    .cover-badges .badge {{
      font-size: .58rem;
      padding: 3px 7px;
      border-radius: 6px;
      font-weight: 600;
      box-shadow: 0 1px 4px rgba(0,0,0,.22);
      line-height: 1.2;
    }}
    .finder-btn {{
      position: absolute;
      top: 8px;
      right: 8px;
      z-index: 5;
      width: 32px;
      height: 32px;
      border: none;
      border-radius: 8px;
      background: rgba(255,255,255,.92);
      box-shadow: 0 1px 4px rgba(0,0,0,.15);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 0;
      opacity: 0;
      pointer-events: none;
      transition: opacity .15s ease, transform .12s, background .12s;
    }}
    .cover-wrap:hover .finder-btn {{
      opacity: 1;
      pointer-events: auto;
    }}
    .finder-btn:hover {{ background: #fff; transform: scale(1.06); }}
    .finder-btn:focus-visible {{
      opacity: 1;
      pointer-events: auto;
      outline: 2px solid var(--accent);
      outline-offset: 2px;
    }}
    .finder-btn svg {{ width: 18px; height: 18px; opacity: .85; }}
    .flag-btn {{
      position: absolute;
      top: 8px;
      left: 8px;
      z-index: 5;
      width: 32px;
      height: 32px;
      border: none;
      border-radius: 8px;
      background: rgba(255,255,255,.92);
      box-shadow: 0 1px 4px rgba(0,0,0,.15);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 0;
      opacity: 0;
      pointer-events: none;
      transition: opacity .15s ease, transform .12s, background .12s;
    }}
    .cover-wrap:hover .flag-btn {{
      opacity: 1;
      pointer-events: auto;
    }}
    .flag-btn:hover {{ background: #fff; transform: scale(1.06); }}
    .flag-btn:focus-visible {{
      opacity: 1;
      pointer-events: auto;
      outline: 2px solid var(--accent);
      outline-offset: 2px;
    }}
    .flag-btn svg {{ width: 18px; height: 18px; opacity: .85; }}
    .flag-btn.flagged {{
      background: #fef2f2;
      color: #b91c1c;
    }}
    .flag-btn.flagged svg {{ opacity: 1; }}
    .cover-wrap.is-flagged {{
      box-shadow: var(--shadow), 0 0 0 2px #dc2626;
    }}
    .meta {{
      margin-top: 10px;
      padding: 0 2px;
    }}
    .t {{
      font-size: .82rem;
      font-weight: 600;
      line-height: 1.3;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }}
    .st {{
      font-size: .72rem;
      color: var(--text2);
      margin-top: 2px;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }}
    .au {{
      font-size: .72rem;
      color: var(--text2);
      margin-top: 4px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .fname {{
      font-size: .65rem;
      color: #888;
      margin-top: 6px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .badge {{
      display: inline-block;
      font-weight: 500;
    }}
    .matched {{ background: #d1fae5; color: #047857; }}
    .not_found {{ background: #fee2e2; color: #b91c1c; }}
    .error {{ background: #fef3c7; color: #a16207; }}
    .review-incorrect {{ background: #fecaca; color: #991b1b; }}
    .toast {{
      position: fixed;
      bottom: 24px;
      left: 50%;
      transform: translateX(-50%) translateY(80px);
      background: #1d1d1f;
      color: #fff;
      padding: 10px 18px;
      border-radius: 10px;
      font-size: .85rem;
      opacity: 0;
      transition: transform .25s, opacity .25s;
      z-index: 100;
      pointer-events: none;
    }}
    .toast.show {{
      opacity: 1;
      transform: translateX(-50%) translateY(0);
    }}
  </style>
</head>
<body>
  {reveal_note}
  <header class="toolbar">
    <h1>Library</h1>
    <span class="counts" id="counts"></span>
    <input type="search" class="search" id="q" placeholder="Search title, author, filename…" autocomplete="off"/>
    <div class="sort-wrap">
      <label for="sort-title">Sort by title</label>
      <select id="sort-title" class="sort-select" aria-label="Sort books by title">
        <option value="original">Original order</option>
        <option value="asc">Title A → Z</option>
        <option value="desc">Title Z → A</option>
      </select>
    </div>
    <div class="chips" id="chips">
      <button type="button" class="chip on" data-f="all">All</button>
      <button type="button" class="chip" data-f="matched">Matched</button>
      <button type="button" class="chip" data-f="not_found">Not found</button>
      <button type="button" class="chip" data-f="error">Error</button>
      <button type="button" class="chip" data-f="flagged">Flagged</button>
    </div>
  </header>
  <main class="shelf" id="shelf"></main>
  <div class="toast" id="toast"></div>
  <script id="book-data" type="application/json">{data_json}</script>
  <script>
    const STANDALONE = {json.dumps(standalone_fetch_reveal)};
    const books = JSON.parse(document.getElementById('book-data').textContent);
    const shelf = document.getElementById('shelf');
    const qEl = document.getElementById('q');
    const sortEl = document.getElementById('sort-title');
    const countsEl = document.getElementById('counts');
    let filter = 'all';
    let query = '';
    let sortTitle = 'original';
    const titleCollator = new Intl.Collator(undefined, {{ sensitivity: 'base', numeric: true }});

    function sortByTitle(arr) {{
      if (sortTitle === 'original') return arr;
      const out = arr.slice();
      const mul = sortTitle === 'asc' ? 1 : -1;
      out.sort((a, b) => {{
        const c = titleCollator.compare(a.display_title || '', b.display_title || '');
        if (c !== 0) return mul * c;
        return titleCollator.compare(a.file_path || '', b.file_path || '');
      }});
      return out;
    }}

    const fileIcon = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M12 18v-6M9 15l3 3 3-3"/></svg>`;
    const flagIcon = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/></svg>`;

    function toast(msg) {{
      const t = document.getElementById('toast');
      t.textContent = msg;
      t.classList.add('show');
      clearTimeout(t._h);
      t._h = setTimeout(() => t.classList.remove('show'), 2600);
    }}

    async function reveal(path) {{
      if (STANDALONE) {{
        toast('Run python3 books_library_server.py and use the browser URL for Finder reveal.');
        return;
      }}
      try {{
        const r = await fetch('/reveal', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ path }})
        }});
        const j = await r.json();
        if (j.ok) toast('Revealed in Finder');
        else toast(j.error || 'Could not reveal');
      }} catch (e) {{
        toast('Server error — is books_library_server running?');
      }}
    }}

    async function toggleIncorrectFlag(filePath, makeIncorrect) {{
      if (STANDALONE) {{
        toast('Run books_library_server.py to save flags to the CSV.');
        return;
      }}
      const review_flag = makeIncorrect ? 'incorrect' : '';
      try {{
        const r = await fetch('/flag', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ file_path: filePath, review_flag }})
        }});
        const j = await r.json();
        if (!j.ok) {{
          toast(j.error || 'Could not update CSV');
          return;
        }}
        const b = books.find(x => x.file_path === filePath);
        if (b) b.review_flag = review_flag;
        toast(makeIncorrect ? 'Marked incorrect in CSV' : 'Flag cleared in CSV');
        render();
      }} catch (e) {{
        toast('Server error — could not write CSV');
      }}
    }}

    function matches(b) {{
      if (filter === 'flagged') return b.review_flag === 'incorrect';
      if (filter !== 'all' && b.status !== filter) return false;
      if (!query) return true;
      const s = (query.toLowerCase());
      const hay = [
        b.display_title, b.display_subtitle, b.display_author, b.file_name, b.file_path, b.search_query
      ].join(' ').toLowerCase();
      return hay.includes(s);
    }}

    function render() {{
      const vis = sortByTitle(books.filter(matches));
      countsEl.textContent = vis.length + ' shown · ' + books.length + ' total';
      shelf.innerHTML = vis.map(b => {{
        const gb = b.google_books_url || (b.google_books_id
          ? 'https://books.google.com/books?id=' + encodeURIComponent(b.google_books_id) : null);
        const cover = b.cover_url
          ? `<a class="cover-link" href="${{gb || '#'}}" target="_blank" rel="noopener" ${{!gb ? 'onclick="return false"' : ''}}><img class="cover-img" src="${{b.cover_url}}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.style.opacity=.35;this.alt=''"></a>`
          : `<div class="cover-placeholder">${{esc(b.display_title)}}</div>`;
        const sub = b.display_subtitle ? `<div class="st">${{esc(b.display_subtitle)}}</div>` : '';
        const au = b.display_author ? `<div class="au">${{esc(b.display_author)}}</div>` : '';
        const cls = b.status === 'matched' ? 'matched' : (b.status === 'not_found' ? 'not_found' : 'error');
        const flagged = b.review_flag === 'incorrect';
        const wrapCls = flagged ? 'cover-wrap is-flagged' : 'cover-wrap';
        const flagCls = flagged ? 'flag-btn flagged' : 'flag-btn';
        const flagTitle = flagged ? 'Clear incorrect flag (updates CSV)' : 'Mark match as incorrect (updates CSV)';
        const badges = `<span class="badge ${{cls}}">${{esc(b.status)}}</span>` +
          (flagged ? `<span class="badge review-incorrect">incorrect match</span>` : '');
        return `<article class="book">
          <div class="${{wrapCls}}">
            ${{cover}}
            <div class="cover-badges">${{badges}}</div>
            <button type="button" class="${{flagCls}}" title="${{flagTitle}}" aria-label="${{flagTitle}}" data-path="${{escAttr(b.file_path)}}" data-flagged="${{flagged ? '1' : '0'}}">${{flagIcon}}</button>
            <button type="button" class="finder-btn" title="Show in Finder" aria-label="Show in Finder" data-path="${{escAttr(b.file_path)}}">${{fileIcon}}</button>
          </div>
          <div class="meta">
            <div class="t">${{esc(b.display_title)}}</div>
            ${{sub}}
            ${{au}}
            <div class="fname">${{esc(b.file_name)}}</div>
          </div>
        </article>`;
      }}).join('');

      shelf.querySelectorAll('.finder-btn').forEach(btn => {{
        btn.addEventListener('click', (e) => {{
          e.preventDefault();
          e.stopPropagation();
          reveal(btn.getAttribute('data-path'));
        }});
      }});
      shelf.querySelectorAll('.flag-btn').forEach(btn => {{
        btn.addEventListener('click', (e) => {{
          e.preventDefault();
          e.stopPropagation();
          const p = btn.getAttribute('data-path');
          const cur = btn.getAttribute('data-flagged') === '1';
          toggleIncorrectFlag(p, !cur);
        }});
      }});
    }}

    function esc(s) {{
      const d = document.createElement('div');
      d.textContent = s || '';
      return d.innerHTML;
    }}
    function escAttr(s) {{
      return (s || '').replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;');
    }}

    document.getElementById('chips').addEventListener('click', (e) => {{
      const b = e.target.closest('.chip');
      if (!b) return;
      document.querySelectorAll('.chip').forEach(c => c.classList.toggle('on', c === b));
      filter = b.getAttribute('data-f');
      render();
    }});
    qEl.addEventListener('input', () => {{ query = qEl.value.trim(); render(); }});
    sortEl.addEventListener('change', () => {{ sortTitle = sortEl.value; render(); }});
    render();
  </script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    books: list[dict[str, Any]] = []
    csv_path: Path = DEFAULT_CSV

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urllib.parse.urlparse(self.path).path
        if path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        if path in ("/", "/index.html"):
            html = build_html_payload(self.books, standalone_fetch_reveal=False).encode("utf-8")
            self._send(200, html, "text/html; charset=utf-8")
            return
        self.send_error(404)

    def do_POST(self) -> None:
        up = urllib.parse.urlparse(self.path)
        if up.path not in ("/reveal", "/flag"):
            self.send_error(404)
            return
        ln = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(ln).decode("utf-8")
        try:
            data = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            self._send(400, b'{"ok":false,"error":"invalid json"}', "application/json; charset=utf-8")
            return

        if up.path == "/reveal":
            p = data.get("path") or ""
            ok, err = reveal_in_finder(p)
            out = json.dumps({"ok": ok, **({} if ok else {"error": err})}, ensure_ascii=False).encode(
                "utf-8"
            )
            self._send(200 if ok else 400, out, "application/json; charset=utf-8")
            return

        fp = data.get("file_path") or ""
        flag = (data.get("review_flag") or "").strip()
        ok, err = apply_review_flag(Handler.csv_path, fp, flag)
        if ok:
            Handler.books = load_books(Handler.csv_path)
        payload: dict[str, Any] = {"ok": ok}
        if ok:
            payload["review_flag"] = flag
        else:
            payload["error"] = err
        self._send(200 if ok else 400, json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Books-style viewer for google_books_scan.csv")
    ap.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--export", type=Path, nargs="?", const=DEFAULT_EXPORT, default=None)
    ap.add_argument("--open", action="store_true", help="Open default browser (macOS)")
    args = ap.parse_args()

    if not args.csv.is_file():
        print(f"CSV not found: {args.csv}", file=sys.stderr)
        return 1

    books = load_books(args.csv)
    if args.export is not None:
        html = build_html_payload(books, standalone_fetch_reveal=True)
        args.export.write_text(html, encoding="utf-8")
        print(f"Wrote {args.export} (open in browser; Finder icon needs the server).", file=sys.stderr)
        return 0

    Handler.books = books
    Handler.csv_path = args.csv.resolve()
    server = HTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}/"
    print(f"Serving {len(books)} books at {url}", file=sys.stderr)
    print("Ctrl+C to stop.", file=sys.stderr)
    if args.open and sys.platform == "darwin":
        subprocess.Popen(["/usr/bin/open", url])
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
