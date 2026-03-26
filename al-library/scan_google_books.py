#!/usr/bin/env python3
"""
List ebook files under Downloads/Lib*, search Google Books API per file,
emit JSON or CSV with paths, Google Books id/url, volume metadata, and status.

Progress is logged to stderr for each file. With -o, each result is flushed to
disk immediately (atomic replace). Re-runs reuse -o: paths with status
matched and a google_books_id are skipped; not_found and error are retried.

status values:
  matched    — API returned at least one volume and a volume id was recorded
  not_found  — API succeeded but no results (or empty items)
  error      — request/API failure (e.g. rate limit); see lookup_error
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent

DEFAULT_DOWNLOADS = Path.home() / "Downloads"
DEFAULT_GLOB = "Lib*"
DEFAULT_EXTENSIONS = frozenset({".pdf", ".epub"})
BOOKS_URL = "https://books.google.com/books"
VOLUMES_API = "https://www.googleapis.com/books/v1/volumes"


def clean_query_from_stem(stem: str) -> str:
    # Tuned from library_inventory.json: mangled apostrophes (Can_t, L_Engle),
    # underscore as space (Musk_ Tesla, Planned_ The), semicolons, bracket tags,
    # year suffixes (2015), and double-dash subtitles.
    s = stem

    def _apply(rule: str, repl: str, x: str) -> str:
        return re.sub(rule, repl, x, flags=re.UNICODE)

    while True:
        # Initial + surname: L_Engle -> L'Engle (not by_Federico)
        n = _apply(r"\b([A-Z])_([A-Z][a-z])", r"\1'\2", s)
        if n != s:
            s = n
            continue
        # n't mangled as n_t: Can_t -> Can't
        n = _apply(r"(\w)n_t(?=\s|$|,|-|\)|\.)", r"\1n't", s)
        if n != s:
            s = n
            continue
        # possessive ...s mangled: Hitchhiker_s -> Hitchhiker's
        n = _apply(r"(\w{3,})_s(?=\s|$|,|-|\)|\.)", r"\1's", s)
        if n != s:
            s = n
            continue
        break

    s = _apply(r"_+", " ", s)
    s = s.replace(".", " ")
    s = s.replace(";", " ").replace("；", " ")
    s = _apply(r"\s*--\s*", " - ", s)
    s = _apply(r"\[[^\]]*\]", " ", s)
    while True:
        n = re.sub(r"\s*\((19|20)\d{2}\)\s*$", "", s)
        if n == s:
            break
        s = n
    s = re.sub(r"\s*[\[\(].*?[\]\)]\s*", " ", s)
    s = re.sub(r"\s*-\s*[A-Z0-9]{8,}\s*$", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def epub_title_author(path: Path) -> tuple[str | None, str | None]:
    try:
        with zipfile.ZipFile(path, "r") as zf:
            try:
                container = zf.read("META-INF/container.xml")
            except KeyError:
                return None, None
            root = ET.fromstring(container)
            ns = {"ns": "urn:oasis:names:tc:opendocument:xmlns:container"}
            href = None
            for full in root.findall(".//ns:rootfile", ns):
                href = full.get("full-path")
                if href:
                    break
            if not href:
                return None, None
            try:
                opf_bytes = zf.read(href)
            except KeyError:
                return None, None
            opf = ET.fromstring(opf_bytes)
            dc_ns = {"dc": "http://purl.org/dc/elements/1.1/"}
            title_el = opf.find(".//dc:title", dc_ns)
            title = title_el.text.strip() if title_el is not None and title_el.text else None
            creators = opf.findall(".//dc:creator", dc_ns)
            authors = [c.text.strip() for c in creators if c is not None and c.text]
            author = ", ".join(authors) if authors else None
            return title, author
    except (zipfile.BadZipFile, ET.ParseError, OSError):
        return None, None


def pdf_title_author(path: Path) -> tuple[str | None, str | None]:
    try:
        from pypdf import PdfReader
    except ImportError:
        return None, None
    try:
        reader = PdfReader(str(path), strict=False)
        meta = reader.metadata
        if not meta:
            return None, None
        title = meta.get("/Title")
        author = meta.get("/Author")
        if title:
            title = str(title).strip() or None
        if author:
            author = str(author).strip() or None
        return title, author
    except Exception:
        return None, None


def build_search_query(path: Path) -> str:
    ext = path.suffix.lower()
    title = author = None
    if ext == ".epub":
        title, author = epub_title_author(path)
    elif ext == ".pdf":
        title, author = pdf_title_author(path)

    if title and author:
        return f"{title} {author}"
    if title:
        return title
    return clean_query_from_stem(path.stem)


def discover_files(roots: list[Path], extensions: frozenset[str]) -> list[Path]:
    out: list[Path] = []
    for root in roots:
        if root.is_file() and root.suffix.lower() in extensions:
            out.append(root.resolve())
        elif root.is_dir():
            for p in root.rglob("*"):
                if p.is_file() and p.suffix.lower() in extensions:
                    out.append(p.resolve())
    return sorted(set(out))


def volumes_search(
    q: str,
    api_key: str | None,
    max_results: int = 5,
    retries: int = 4,
) -> dict[str, Any] | None:
    params: list[tuple[str, str]] = [("q", q), ("maxResults", str(max_results))]
    if api_key:
        params.append(("key", api_key))
    url = f"{VOLUMES_API}?{urllib.parse.urlencode(params)}"
    last_err: str | None = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            if e.code == 429 and attempt < retries:
                wait = min(2.0 * (2**attempt), 60.0)
                time.sleep(wait)
                last_err = f"HTTP {e.code} (retrying)"
                continue
            return {"_error": f"HTTP {e.code}", "_body": body[:500]}
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            last_err = str(e)
            if attempt < retries:
                time.sleep(min(1.0 * (2**attempt), 30.0))
                continue
            return {"_error": last_err}
    return {"_error": last_err or "unknown"}


def pick_first_volume(data: dict[str, Any]) -> tuple[str | None, dict[str, Any] | None, str | None]:
    if "_error" in data:
        return None, None, data.get("_error") or data.get("_body")
    items = data.get("items") or []
    if not items:
        return None, None, "no results"
    vol = items[0]
    vid = vol.get("id")
    info = vol.get("volumeInfo") or {}
    if not vid:
        return None, None, "missing volume id"
    return vid, info, None


def row_for_file(
    path: Path,
    api_key: str | None,
    delay_s: float,
) -> dict[str, Any]:
    q = build_search_query(path)
    time.sleep(delay_s)
    data = volumes_search(q, api_key) or {}
    api_failed = bool(data.get("_error"))
    vid, info, err = pick_first_volume(data)
    url = f"{BOOKS_URL}?id={vid}" if vid else None
    if vid:
        status = "matched"
    elif api_failed:
        status = "error"
    else:
        status = "not_found"
    return {
        "file_path": str(path),
        "file_name": path.name,
        "status": status,
        "search_query": q,
        "google_books_id": vid,
        "google_books_url": url,
        "metadata": info,
        "lookup_error": err,
    }


def emit_json(rows: list[dict[str, Any]], out_fp) -> None:
    json.dump({"entries": rows}, out_fp, indent=2, ensure_ascii=False)
    out_fp.write("\n")


def atomic_write_output(path: Path, fmt: str, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / f".{path.name}.tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as fp:
        if fmt == "json":
            emit_json(rows, fp)
        else:
            emit_csv(rows, fp)
    os.replace(tmp, path)


def load_json_cache(path: Path) -> dict[str, dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for row in data.get("entries") or []:
        fp = row.get("file_path")
        if fp:
            out[fp] = copy.deepcopy(row)
    return out


def load_csv_cache(path: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    try:
        with open(path, encoding="utf-8", newline="") as fp:
            reader = csv.DictReader(fp)
            for row in reader:
                meta_s = (row.get("metadata_json") or "").strip()
                try:
                    meta = json.loads(meta_s) if meta_s else None
                except json.JSONDecodeError:
                    meta = None
                fpath = row.get("file_path")
                if not fpath:
                    continue
                gid = row.get("google_books_id") or None
                if gid == "":
                    gid = None
                gurl = row.get("google_books_url") or None
                if gurl == "":
                    gurl = None
                out[fpath] = {
                    "file_path": fpath,
                    "file_name": row.get("file_name") or "",
                    "status": row.get("status") or "",
                    "search_query": row.get("search_query") or "",
                    "google_books_id": gid,
                    "google_books_url": gurl,
                    "metadata": meta,
                    "lookup_error": row.get("lookup_error") or None,
                    "review_flag": (row.get("review_flag") or "").strip(),
                }
    except OSError:
        return {}
    return out


def load_output_cache(path: Path | None, fmt: str) -> dict[str, dict[str, Any]]:
    if not path or not path.is_file():
        return {}
    if fmt == "json":
        return load_json_cache(path)
    return load_csv_cache(path)


def cache_entry_is_complete(entry: dict[str, Any]) -> bool:
    return entry.get("status") == "matched" and bool(entry.get("google_books_id"))


def emit_csv(rows: list[dict[str, Any]], out_fp) -> None:
    fieldnames = [
        "file_path",
        "file_name",
        "status",
        "search_query",
        "google_books_id",
        "google_books_url",
        "metadata_json",
        "lookup_error",
        "review_flag",
    ]
    w = csv.DictWriter(out_fp, fieldnames=fieldnames, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        meta = r.get("metadata")
        w.writerow(
            {
                "file_path": r["file_path"],
                "file_name": r["file_name"],
                "status": r.get("status") or "",
                "search_query": r["search_query"],
                "google_books_id": r.get("google_books_id") or "",
                "google_books_url": r.get("google_books_url") or "",
                "metadata_json": json.dumps(meta, ensure_ascii=False) if meta else "",
                "lookup_error": r.get("lookup_error") or "",
                "review_flag": r.get("review_flag") or "",
            }
        )


def load_dotenv_files() -> None:
    """Populate os.environ from .env files if python-dotenv is installed."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    repo_root_env = SCRIPT_DIR.parent / ".env"
    local_env = SCRIPT_DIR / ".env"
    if repo_root_env.is_file():
        load_dotenv(repo_root_env, override=False)
    if local_env.is_file():
        load_dotenv(local_env, override=True)


def main() -> int:
    load_dotenv_files()
    p = argparse.ArgumentParser(description="Map local ebooks to Google Books metadata.")
    p.add_argument(
        "--downloads-dir",
        type=Path,
        default=DEFAULT_DOWNLOADS,
        help=f"Parent of Lib* glob (default: {DEFAULT_DOWNLOADS})",
    )
    p.add_argument(
        "--lib-glob",
        default=DEFAULT_GLOB,
        help='Glob under downloads dir (default: Lib*)',
    )
    p.add_argument(
        "--extensions",
        default="pdf,epub",
        help="Comma-separated extensions (default: pdf,epub)",
    )
    p.add_argument(
        "--format",
        choices=("json", "csv"),
        default="json",
        help="Output format",
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Write to file (default: stdout)",
    )
    p.add_argument(
        "--api-key",
        default=os.environ.get("GOOGLE_BOOKS_API_KEY"),
        help=(
            "Optional. Books API key or env GOOGLE_BOOKS_API_KEY; also read from "
            ".env in the repo root or next to this script (via python-dotenv). "
            "Recommended for larger scans (higher quota, fewer HTTP 429s)."
        ),
    )
    p.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Seconds between API calls (default: 1.0; use an API key for large scans)",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max files to process (0 = all)",
    )
    p.add_argument(
        "--no-resume",
        action="store_true",
        help="Ignore existing -o file; re-query every path (still use incremental writes if -o set).",
    )
    args = p.parse_args()

    ext_set = frozenset(
        "." + x.strip().lower().lstrip(".") for x in args.extensions.split(",") if x.strip()
    )
    roots = sorted(args.downloads_dir.glob(args.lib_glob))
    if not roots:
        print(f"No paths matched {args.downloads_dir}/{args.lib_glob}", file=sys.stderr)
        return 1

    files = discover_files(roots, ext_set)
    if args.limit and args.limit > 0:
        files = files[: args.limit]

    cache: dict[str, dict[str, Any]] = {}
    if args.output and not args.no_resume:
        cache = load_output_cache(args.output, args.format)

    n = len(files)
    rows: list[dict[str, Any]] = []

    for i, f in enumerate(files, start=1):
        key = str(f)
        if (
            not args.no_resume
            and key in cache
            and cache_entry_is_complete(cache[key])
        ):
            row = copy.deepcopy(cache[key])
            rows.append(row)
            print(
                f"[{i}/{n}] skip (cached matched) | {f.name}",
                file=sys.stderr,
                flush=True,
            )
        else:
            print(
                f"[{i}/{n}] query … | {f.name}",
                file=sys.stderr,
                flush=True,
            )
            row = row_for_file(f, args.api_key, args.delay)
            row["review_flag"] = (cache.get(key) or {}).get("review_flag") or ""
            rows.append(row)
            cache[key] = copy.deepcopy(row)
            vol_title = (row.get("metadata") or {}).get("title") or "—"
            print(
                f"[{i}/{n}] {row['status']} | {f.name} | {vol_title[:60]}",
                file=sys.stderr,
                flush=True,
            )

        if args.output:
            atomic_write_output(args.output, args.format, rows)

    if not args.output:
        if args.format == "json":
            emit_json(rows, sys.stdout)
        else:
            emit_csv(rows, sys.stdout)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
