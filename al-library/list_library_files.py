#!/usr/bin/env python3
"""
List ebook files under Downloads/Lib* (configurable): path, name, extension,
relative path, top-level folder — plus summary counts by extension and folder.

Outputs JSON (summary + files) or CSV (files only).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

DEFAULT_DOWNLOADS = Path.home() / "Downloads"
DEFAULT_GLOB = "Lib*"


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


def rel_under_any_root(path: Path, roots: list[Path]) -> str:
    path = path.resolve()
    for r in sorted(roots, key=lambda p: len(p.parts), reverse=True):
        r = r.resolve()
        try:
            return str(path.relative_to(r))
        except ValueError:
            continue
    return ""


def top_bucket(rel: str) -> str:
    if not rel or rel == ".":
        return ""
    return rel.split("/", 1)[0]


def main() -> int:
    p = argparse.ArgumentParser(description="List ebook files under Lib* paths.")
    p.add_argument(
        "--downloads-dir",
        type=Path,
        default=DEFAULT_DOWNLOADS,
        help=f"Parent of Lib* glob (default: {DEFAULT_DOWNLOADS})",
    )
    p.add_argument("--lib-glob", default=DEFAULT_GLOB, help="Glob under downloads (default: Lib*)")
    p.add_argument(
        "--extensions",
        default="pdf,epub,mobi,azw3",
        help="Comma-separated extensions (default: pdf,epub,mobi,azw3)",
    )
    p.add_argument("--format", choices=("json", "csv"), default="json")
    p.add_argument("-o", "--output", type=Path, default=None, help="Write to file (default: stdout)")
    args = p.parse_args()

    ext_set = frozenset(
        "." + x.strip().lower().lstrip(".") for x in args.extensions.split(",") if x.strip()
    )
    roots = sorted(args.downloads_dir.glob(args.lib_glob))
    if not roots:
        print(f"No paths matched {args.downloads_dir}/{args.lib_glob}", file=sys.stderr)
        return 1

    files = discover_files(roots, ext_set)
    by_ext = Counter(f.suffix.lower() for f in files)
    by_bucket = Counter()
    rows: list[dict[str, str]] = []
    for f in files:
        rel = rel_under_any_root(f, roots)
        b = top_bucket(rel)
        if b:
            by_bucket[b] += 1
        rows.append(
            {
                "file_path": str(f),
                "file_name": f.name,
                "file_stem": f.stem,
                "extension": f.suffix.lower(),
                "rel_path": rel,
                "top_folder": b,
            }
        )

    summary = {
        "downloads_dir": str(args.downloads_dir.resolve()),
        "lib_glob": args.lib_glob,
        "roots_matched": [str(r.resolve()) for r in roots],
        "total_files": len(files),
        "by_extension": dict(sorted(by_ext.items())),
        "by_top_folder": dict(sorted(by_bucket.items(), key=lambda x: (-x[1], x[0]))),
    }

    out = open(args.output, "w", encoding="utf-8", newline="") if args.output else sys.stdout
    try:
        if args.format == "json":
            json.dump({"summary": summary, "files": rows}, out, indent=2, ensure_ascii=False)
            out.write("\n")
        else:
            fieldnames = [
                "file_path",
                "file_name",
                "file_stem",
                "extension",
                "rel_path",
                "top_folder",
            ]
            w = csv.DictWriter(out, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(rows)
    finally:
        if args.output:
            out.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
