#!/usr/bin/env python3
"""
Open LinkedIn connection URLs in batches of 30.

Usage:
    python3 open_urls.py --1    # Opens URLs 1-30
    python3 open_urls.py --2    # Opens URLs 31-60
    python3 open_urls.py --3    # Opens URLs 61-90
    ...
"""

import csv
import webbrowser
import argparse
import os
import time
import random

BATCH_SIZE = 20
CSV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "LinkedIn Connections.csv")


def main():
    parser = argparse.ArgumentParser(
        description="Open LinkedIn connection URLs in batches of 30."
    )
    parser.add_argument(
        "batch",
        type=str,
        help="Batch number prefixed with '--', e.g. --1 for the first 30 URLs, --2 for the next 30, etc."
    )
    
    # Custom parsing to handle --1, --2, etc.
    import sys
    args = sys.argv[1:]
    
    if not args:
        print("Usage: python3 open_urls.py --<batch_number>")
        print("  e.g. python3 open_urls.py --1   (opens URLs 1-30)")
        print("       python3 open_urls.py --2   (opens URLs 31-60)")
        sys.exit(1)
    
    # Extract batch number from --N format
    batch_arg = args[0]
    if not batch_arg.startswith("--"):
        print(f"Error: Expected --<number>, got '{batch_arg}'")
        sys.exit(1)
    
    try:
        batch_num = int(batch_arg[2:])
    except ValueError:
        print(f"Error: '{batch_arg[2:]}' is not a valid number.")
        sys.exit(1)
    
    if batch_num < 1:
        print("Error: Batch number must be 1 or greater.")
        sys.exit(1)
    
    # Read URLs from CSV (only "Remove" connections)
    urls = []
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get("URL", "").strip()
            connection = row.get("Connection", "").strip()
            if url and connection == "Remove":
                urls.append(url)
    
    total_urls = len(urls)
    total_batches = (total_urls + BATCH_SIZE - 1) // BATCH_SIZE
    
    if batch_num > total_batches:
        print(f"Error: Batch {batch_num} doesn't exist. There are only {total_batches} batches ({total_urls} URLs total).")
        sys.exit(1)
    
    start = (batch_num - 1) * BATCH_SIZE
    end = min(start + BATCH_SIZE, total_urls)
    batch_urls = urls[start:end]
    
    print(f"Opening batch {batch_num} of {total_batches} — URLs {start + 1} to {end} (of {total_urls} total)")
    print("-" * 60)
    
    for i, url in enumerate(batch_urls, start=start + 1):
        print(f"  [{i}] {url}")
        webbrowser.open(url)
        if i < end:  # No delay after the last URL
            delay = random.uniform(2, 5)
            print(f"       ⏳ Waiting {delay:.1f}s...")
            time.sleep(delay)
    
    print("-" * 60)
    print(f"Done! Opened {len(batch_urls)} URLs in your default browser.")


if __name__ == "__main__":
    main()
