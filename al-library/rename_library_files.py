#!/usr/bin/env python3
"""
Normalize ebook filenames: typos, publisher/imprint tails, mangled underscores,
optional Title - Author → Author - Title flips, and trailing junk tags.

Default: print planned renames. Use --apply to execute.

Reads file_path entries from library_inventory.json (same folder as this script)
or pass --inventory path.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_INVENTORY = SCRIPT_DIR / "library_inventory.json"

# Substrings (stem) to fix — order matters; longer/specific first where needed.
STEM_TYPO_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("Asiimov", "Asimov"),
    ("Madelein L_Engle", "Madeleine L'Engle"),
    ("Enterprenerus", "Entrepreneurs"),
    ("Continous", "Continuous"),
    ("Antoine de Saint Exupery", "Antoine de Saint-Exupéry"),
    ("4-Hours Workweek", "4-Hour Workweek"),
    ("Harry Potter and The Deadly Hallows", "Harry Potter and the Deathly Hallows"),
    ("Harry Potter and The Goblet of Fire", "Harry Potter and the Goblet of Fire"),
    ("Romance of Three Kingdoms", "Romance of the Three Kingdoms"),
)

# Removed from end of stem after typographic normalization (exact).
PUBLISHER_TAILS: tuple[str, ...] = (
    "-Springer International Publishing (2015)",
    "Springer International Publishing (2015)",
    "-Viking (2016)",
    "-Stanford University Press (1987)",
    "-Penguin (2022)",
    "-Wiley (2012)",
    "-Pkcs Media, Inc. (2019)",
)

# Short parenthetical tags (editions / language noise) stripped from end of stem.
STRIP_PAREN_TAGS: tuple[str, ...] = (
    "(Ilmuwan)",
    "(Penemu)",
    "[Independently Published]",
)

# Exact basename → new basename (full filename including extension).
EXACT_RENAMES: dict[str, str] = {
    "Dune - Frank Herbert (1965).pdf": "Frank Herbert - Dune (1965).pdf",
    "Men Are From Mars, Women Are From Venus - John Gray, Ph.D.pdf": (
        "John Gray, Ph.D. - Men Are From Mars, Women Are From Venus.pdf"
    ),
    "Independent People - Laxness, Halldor.epub": "Halldor Laxness - Independent People.epub",
    "The Rise and Fall of Modern Medicine - Le Fanu, James.epub": (
        "James Le Fanu - The Rise and Fall of Modern Medicine.epub"
    ),
    "Cash Copy - Jeffrey Lang.pdf": "Jeffrey Lang - Cash Copy.pdf",
    "The Element - Ken Robinson Ph.D.pdf": "Ken Robinson Ph.D. - The Element.pdf",
    "The 7 Habits of Highly Effective People - Stephen R. Covey.epub": (
        "Stephen R. Covey - The 7 Habits of Highly Effective People.epub"
    ),
    "The Willpower Instinct - Kelly McGonigal.epub": "Kelly McGonigal - The Willpower Instinct.epub",
    "Think Like a Futurist - Cecily Sommers.pdf": "Cecily Sommers - Think Like a Futurist.pdf",
    "The Beginning of Infinity - David Deutsch.epub": "David Deutsch - The Beginning of Infinity.epub",
    "The Fabric of Reality - David Deutsch.epub": "David Deutsch - The Fabric of Reality.epub",
    "The Hard Thing About Hard Things - Ben Horowitz.epub": (
        "Ben Horowitz - The Hard Thing About Hard Things.epub"
    ),
    # U+2019 apostrophe in source filename (macOS / iBooks)
    "L\u2019Empreinte de Dieu dans le monde quantique - Yves Dupont.epub": (
        "Yves Dupont - L'Empreinte de Dieu dans le monde quantique.epub"
    ),
    "Elon Musk - Walter Isaacson.epub": "Walter Isaacson - Elon Musk.epub",
    "Scale; The Universal Laws of Life, Growth, and Death- Geoffrey West.pdf": (
        "Geoffrey West - Scale; The Universal Laws of Life, Growth, and Death.pdf"
    ),
    "Umar bin Khattab - (Khalifah).pdf": "Umar bin Khattab.pdf",
    # U+2019 in "Person's"
    "The Sense of Style - The Thinking Person\u2019s Guide to Writing in the 21st Century by Steven Pinker (2014).epub": (
        "Steven Pinker - The Sense of Style - The Thinking Person's Guide to Writing in the 21st Century (2014).epub"
    ),
}


def expand_underscore_dashes(s: str) -> str:
    """Treat ` _ ` and `_ The ` style segments as subtitle separators (inventory pattern)."""
    s = s.replace(" _ ", " - ")
    s = re.sub(r"_\s+(The|A|An)\s", r" - \1 ", s)
    return s


def normalize_underscore_apostrophe(s: str) -> str:
    while True:
        n = re.sub(r"\b([A-Z])_([A-Z][a-z])", r"\1'\2", s)
        if n != s:
            s = n
            continue
        n = re.sub(r"(\w)n_t(?=\s|$|,|-|\)|\.)", r"\1n't", s)
        if n != s:
            s = n
            continue
        n = re.sub(r"(\w{3,})_s(?=\s|$|,|-|\)|\.)", r"\1's", s)
        if n != s:
            s = n
            continue
        break
    s = re.sub(r"_+", " ", s)
    s = re.sub(r"\s*--\s*", " - ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def strip_bracket_publisher_blocks(s: str) -> str:
    s = re.sub(r"\s*\[[^\]]+\]\s*", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def strip_auth_tag(s: str) -> str:
    s = re.sub(r"\s*\(auth\.\)\s*", " ", s, flags=re.I)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def apply_by_author_flip(stem: str) -> str:
    m = re.match(r"^(.+?)\s+by\s+(.+)$", stem, flags=re.I)
    if not m:
        return stem
    title, author = m.group(1).strip(), m.group(2).strip()
    y = re.search(r"\((19|20)\d{2}\)\s*$", author)
    if y:
        author_core = author[: y.start()].rstrip()
        year = author[y.start() :]
        return f"{author_core} - {title} {year}".strip()
    return f"{author} - {title}"


def normalize_extension(path: Path) -> str:
    ext = path.suffix
    low = ext.lower()
    return low if ext != low else ext


def compute_new_basename(original: Path) -> str:
    name = original.name
    if name in EXACT_RENAMES:
        return EXACT_RENAMES[name]

    ext = normalize_extension(original)
    stem = original.stem

    for old, new in STEM_TYPO_REPLACEMENTS:
        stem = stem.replace(old, new)

    stem = strip_auth_tag(stem)
    for tag in STRIP_PAREN_TAGS:
        stem = stem.replace(tag, " ")
    stem = strip_bracket_publisher_blocks(stem)

    for tail in sorted(PUBLISHER_TAILS, key=len, reverse=True):
        if stem.endswith(tail):
            stem = stem[: -len(tail)].rstrip(" -–")
            stem = re.sub(r"[-–]\s*$", "", stem)
            break

    stem = expand_underscore_dashes(stem)
    stem = normalize_underscore_apostrophe(stem)
    stem = apply_by_author_flip(stem)

    stem = re.sub(r"\s+", " ", stem).strip()
    stem = re.sub(r"\s+-\s*$", "", stem).strip()
    if stem != original.stem and ext != normalize_extension(Path(stem + ext)):
        pass
    return f"{stem}{ext}"


def load_paths(inventory_path: Path) -> list[Path]:
    data = json.loads(inventory_path.read_text(encoding="utf-8"))
    return [Path(e["file_path"]) for e in data.get("files", [])]


def main() -> int:
    ap = argparse.ArgumentParser(description="Rename library files to normalized names.")
    ap.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    ap.add_argument(
        "--apply",
        action="store_true",
        help="Perform renames (default is dry-run)",
    )
    args = ap.parse_args()

    if not args.inventory.is_file():
        print(f"Inventory not found: {args.inventory}", file=sys.stderr)
        return 1

    rows: list[tuple[Path, Path]] = []
    for src in load_paths(args.inventory):
        if not src.is_file():
            continue
        new_name = compute_new_basename(src)
        dst = src.with_name(new_name)
        if src.resolve() == dst.resolve():
            continue
        rows.append((src, dst))

    for src, dst in rows:
        print(f"{src}\n  -> {dst.name}\n")

    if not args.apply:
        print(f"Dry-run: {len(rows)} renames (use --apply to execute)", file=sys.stderr)
        return 0

    done = 0
    for src, dst in rows:
        if src.resolve() == dst.resolve():
            continue
        if dst.exists():
            try:
                if src.samefile(dst):
                    # Same inode (case-only or normalization); need two-step rename on APFS/HFS+.
                    tmp = src.with_name(f"{src.name}.__al_library_rename__")
                    n = 0
                    while tmp.exists():
                        n += 1
                        tmp = src.with_name(f"{src.name}.__al_library_rename_{n}__")
                    src.rename(tmp)
                    tmp.rename(dst)
                    done += 1
                    continue
            except OSError:
                pass
            print(f"Skip (target exists): {dst}", file=sys.stderr)
            continue
        src.rename(dst)
        done += 1

    print(f"Renamed {done} file(s); skipped {len(rows) - done} collision(s).", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
