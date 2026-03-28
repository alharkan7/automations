#!/usr/bin/env python3
"""
Apply local github_stars_categorized.json to GitHub Star Lists via GraphQL.

Requires GITHUB_TOKEN (or GH_TOKEN) with GraphQL access. For star **Lists** mutations,
GitHub requires classic PAT scope **`user`** (in addition to **`repo`** if you star
private repos). Without `user`, you will see: updateUserListsForItem requires scope
`user`. Enable it at https://github.com/settings/tokens and regenerate the token.
`gh auth token` only works if the gh login OAuth app was granted equivalent access.

Usage:
  export GITHUB_TOKEN=ghp_...
  python3 sync_lists.py --dry-run              # summary only
  python3 sync_lists.py --dry-run --verbose    # print every assignment
  python3 sync_lists.py                        # create missing lists + assign all repos
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from typing import Any, TypeVar

_T = TypeVar("_T")

GRAPHQL_URL = "https://api.github.com/graphql"

# Stay under typical GraphQL alias / payload limits; tune if needed.
REPO_LOOKUP_BATCH = 20
MUTATION_PAUSE_SEC = 0.05


def gql_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def graphql(token: str, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {"query": query}
    if variables is not None:
        body["variables"] = variables
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        GRAPHQL_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
            "User-Agent": "github-stars-sync-lists",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {err_body}") from e

    if "errors" in payload and payload["errors"]:
        msgs = "; ".join(
            e.get("message", str(e)) for e in payload["errors"]
        )
        raise RuntimeError(f"GraphQL errors: {msgs}")
    if "data" not in payload:
        raise RuntimeError(f"Unexpected response: {payload!r}")
    if payload.get("data") is None:
        raise RuntimeError(f"GraphQL returned data: null (full payload: {payload!r})")
    return payload["data"]


def chunked(items: list[_T], n: int) -> Iterator[list[_T]]:
    for i in range(0, len(items), n):
        yield items[i : i + n]


def load_categorized(path: str) -> dict[str, list[dict[str, Any]]]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def parse_repo(full: str) -> tuple[str, str]:
    parts = full.split("/", 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(f"Invalid repo full name: {full!r}")
    return parts[0], parts[1]


def fetch_viewer_login(token: str) -> str:
    q = "query { viewer { login } }"
    return str(graphql(token, q)["viewer"]["login"])


def fetch_list_stats(token: str) -> list[dict[str, Any]]:
    """Name, slug, and item counts for each star list (for verification)."""
    q = """
    query {
      viewer {
        lists(first: 100) {
          nodes {
            name
            slug
            items { totalCount }
          }
        }
      }
    }
    """
    data = graphql(token, q)
    nodes = data["viewer"]["lists"]["nodes"]
    return [
        {
            "name": n["name"],
            "slug": n["slug"],
            "totalCount": n["items"]["totalCount"],
        }
        for n in nodes
    ]


def fetch_viewer_lists(token: str) -> dict[str, str]:
    """Map list name -> GraphQL node id."""
    q = """
    query {
      viewer {
        lists(first: 100) {
          nodes { id name }
        }
      }
    }
    """
    data = graphql(token, q)
    nodes = data["viewer"]["lists"]["nodes"]
    out: dict[str, str] = {}
    for n in nodes:
        name = n["name"]
        if name in out:
            raise RuntimeError(f"Duplicate list name on GitHub: {name!r}")
        out[name] = n["id"]
    return out


def create_user_list(token: str, name: str, is_private: bool) -> str:
    m = """
    mutation ($input: CreateUserListInput!) {
      createUserList(input: $input) {
        list { id name }
      }
    }
    """
    data = graphql(
        token,
        m,
        variables={
            "input": {
                "name": name,
                "isPrivate": is_private,
            }
        },
    )
    lst = data["createUserList"]["list"]
    if not lst:
        raise RuntimeError(f"createUserList returned no list for {name!r}")
    return lst["id"]


def ensure_lists(
    token: str,
    wanted_names: list[str],
    is_private: bool,
    dry_run: bool,
) -> dict[str, str]:
    existing = fetch_viewer_lists(token)
    for name in wanted_names:
        if name not in existing:
            if dry_run:
                print(f"[dry-run] would create list: {name!r}")
                existing[name] = f"DRY_RUN_LIST_ID_{name}"
            else:
                print(f"Creating list: {name}")
                lid = create_user_list(token, name, is_private=is_private)
                existing[name] = lid
                time.sleep(MUTATION_PAUSE_SEC)
    return {n: existing[n] for n in wanted_names}


def batch_repository_lookup(
    token: str, pairs: list[tuple[str, str]]
) -> list[dict[str, Any] | None]:
    """Return list of {id, viewerHasStarred} or None per pair, same order."""
    lines = []
    for i, (owner, repo) in enumerate(pairs):
        eo, er = gql_escape(owner), gql_escape(repo)
        lines.append(
            f'  _r{i}: repository(owner: "{eo}", name: "{er}") '
            f"{{ id viewerHasStarred }}"
        )
    query = "query {\n" + "\n".join(lines) + "\n}"
    data = graphql(token, query)
    out: list[dict[str, Any] | None] = []
    for i in range(len(pairs)):
        node = data.get(f"_r{i}")
        out.append(node)
    return out


def update_user_lists_for_item(
    token: str, item_id: str, list_ids: list[str]
) -> None:
    m = """
    mutation ($input: UpdateUserListsForItemInput!) {
      updateUserListsForItem(input: $input) {
        lists { id name }
      }
    }
    """
    data = graphql(
        token,
        m,
        variables={"input": {"itemId": item_id, "listIds": list_ids}},
    )
    payload = data.get("updateUserListsForItem")
    if payload is None:
        raise RuntimeError(
            "updateUserListsForItem returned null (often: token cannot write star lists; "
            "try a classic PAT with scope `repo` and full `user` / account access)"
        )
    lists_out = payload.get("lists")
    if not lists_out:
        raise RuntimeError(
            f"updateUserListsForItem returned no lists (response: {payload!r})"
        )
    returned_ids = {x["id"] for x in lists_out}
    for lid in list_ids:
        if lid not in returned_ids:
            raise RuntimeError(
                f"List id {lid!r} not in mutation response lists {returned_ids!r}"
            )
    # `item` may be null per schema even when lists update; membership is what we verify above.


def add_star(token: str, starrable_id: str) -> None:
    m = """
    mutation ($input: AddStarInput!) {
      addStar(input: $input) { starrable { id } }
    }
    """
    graphql(token, m, variables={"input": {"starrableId": starrable_id}})


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--json",
        default=os.path.join(os.path.dirname(__file__), "github_stars_categorized.json"),
        help="Path to categorized JSON",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions only; no API writes",
    )
    ap.add_argument(
        "--private-lists",
        action="store_true",
        help="When creating missing lists, set isPrivate=true",
    )
    ap.add_argument(
        "--star-if-missing",
        action="store_true",
        help="If a repo is not starred, star it before assigning lists",
    )
    ap.add_argument(
        "--verbose",
        action="store_true",
        help="With --dry-run, print every repo assignment (default is summary only)",
    )
    ap.add_argument(
        "--limit",
        type=int,
        metavar="N",
        help="Only process the first N repos (after JSON order); for testing",
    )
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token and not args.dry_run:
        print("Set GITHUB_TOKEN (or GH_TOKEN) in the environment.", file=sys.stderr)
        return 1

    data = load_categorized(args.json)
    list_names = list(data.keys())
    work: list[tuple[str, str]] = []
    for lst_name, repos in data.items():
        for entry in repos:
            work.append((entry["name"], lst_name))

    if args.limit is not None:
        work = work[: max(0, args.limit)]
        print(f"Lists: {len(list_names)}  Repos (limited): {len(work)}  (--limit {args.limit})")
    else:
        print(f"Lists: {len(list_names)}  Repos: {len(work)}")

    if args.dry_run and not token:
        print(
            "No GITHUB_TOKEN: printing assignments from JSON only (no API calls).",
            file=sys.stderr,
        )
        name_to_list_id = {n: "" for n in list_names}
    else:
        assert token is not None
        login = fetch_viewer_login(token)
        print(f"Authenticated as: {login}", flush=True)
        print(
            f"View star lists: https://github.com/{login}?tab=stars "
            '(open "Lists" in the left sidebar on the Stars page)',
            flush=True,
        )
        name_to_list_id = ensure_lists(
            token,
            list_names,
            is_private=args.private_lists,
            dry_run=args.dry_run,
        )
        print("Target list IDs (JSON category name → GraphQL list id):", flush=True)
        for n in list_names:
            print(f"  {n!r} → {name_to_list_id[n]}", flush=True)

    failures: list[str] = []
    ok = 0

    # Flatten repo lookups in batches
    pairs = [parse_repo(full) for full, _ in work]
    id_by_full: dict[str, dict[str, Any] | None] = {}

    if not args.dry_run:
        assert token is not None
        n_lookup = 0
        n_total = len(work)
        for batch in chunked(list(zip([w[0] for w in work], pairs, strict=True)), REPO_LOOKUP_BATCH):
            full_batch = [b[0] for b in batch]
            pbatch = [b[1] for b in batch]
            results = batch_repository_lookup(token, pbatch)
            for full, meta in zip(full_batch, results, strict=True):
                id_by_full[full] = meta
            n_lookup += len(batch)
            print(f"Fetching repository metadata: {n_lookup}/{n_total}", flush=True)
            time.sleep(MUTATION_PAUSE_SEC)
        print("Assigning repos to lists (GraphQL mutations)…", flush=True)

    for i, (full, lst_name) in enumerate(work):
        list_id = name_to_list_id[lst_name]
        if args.dry_run:
            if args.verbose:
                print(f"[dry-run] would assign {full} -> {lst_name!r}")
            ok += 1
            continue

        meta = id_by_full.get(full)
        if meta is None:
            failures.append(f"{full}: repository not found (deleted or renamed?)")
            continue
        rid = meta.get("id")
        if not rid:
            failures.append(f"{full}: no id in response")
            continue
        if not meta.get("viewerHasStarred"):
            if args.star_if_missing:
                print(f"Starring (not previously starred): {full}")
                add_star(token, rid)
                time.sleep(MUTATION_PAUSE_SEC)
            else:
                failures.append(f"{full}: not starred (use --star-if-missing or star in UI)")
                continue

        try:
            update_user_lists_for_item(token, rid, [list_id])
            ok += 1
        except Exception as e:
            failures.append(f"{full}: {e}")

        time.sleep(MUTATION_PAUSE_SEC)
        if (i + 1) % 25 == 0 or (i + 1) == len(work):
            print(f"Progress: {i + 1}/{len(work)}", flush=True)

    if args.dry_run and not args.verbose:
        print(f"[dry-run] summary: would assign {ok} repos to {len(list_names)} lists")
    print(f"Done. OK: {ok}  Failed: {len(failures)}")
    if not args.dry_run and token:
        stats = fetch_list_stats(token)
        print("Star list item counts on GitHub (from API):", flush=True)
        for row in sorted(stats, key=lambda r: r["name"]):
            print(
                f"  {row['name']!r}: {row['totalCount']} repos "
                f"(slug: {row['slug']})",
                flush=True,
            )
    if failures:
        print("--- Failures ---")
        for line in failures[:80]:
            print(line)
        if len(failures) > 80:
            print(f"... and {len(failures) - 80} more")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
