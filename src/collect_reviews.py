"""
collect_reviews.py
------------------
Step 1 of the MoveInSync Play Store ratings case study.

What this script does:
  1. Looks up the app listing on Google Play (title, developer, rating, etc.).
  2. Collects up to 2,000 public reviews: mostly the NEWEST reviews, plus a
     batch of "most relevant" reviews, which usually reach further back in time.
  3. Saves everything to data/raw_reviews.csv.
  4. Prints a short summary: count, date range, rating distribution, file path.

It never invents data. If a field is missing, the cell is left empty.

The app is fixed to the package ID you verified on Google Play:
  com.moveinsync.ets
"""

import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd
from google_play_scraper import Sort, app, reviews

# ----------------------------------------------------------------------------
# Settings you may want to change
# ----------------------------------------------------------------------------
APP_ID = "com.moveinsync.ets"   # Verified by you on the Google Play listing
LANGUAGE = "en"
COUNTRY = "in"         # Play Store country. "in" = India.
MAX_REVIEWS = 2000     # Upper limit for the whole sample
NEWEST_SHARE = 0.7     # 70% of the sample comes from the newest-first pass
BATCH_SIZE = 200       # Reviews requested per call
MAX_RETRIES = 3        # Tries per network call before giving up
RETRY_WAIT_SECONDS = 5
PAUSE_SECONDS = 1.0    # Polite pause between calls

# Folders are relative to the project root (the folder that contains "src").
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_CSV = DATA_DIR / "raw_reviews.csv"
LISTING_JSON = DATA_DIR / "app_listing.json"

COLUMNS = [
    "review_id",
    "rating",
    "review_text",
    "review_date",
    "app_version",
    "review_created_version",
    "thumbs_up_count",
    "developer_response",
    "developer_response_date",
    "collection_pass",
]


def call_with_retry(func, *args, **kwargs):
    """Run a network call. Retry on errors. Return (True, result) or (False, None)."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return True, func(*args, **kwargs)
        except Exception as exc:  # network errors, bad app ID, Play Store changes...
            print(f"  Attempt {attempt}/{MAX_RETRIES} failed: {type(exc).__name__}: {exc}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_WAIT_SECONDS * attempt)
    return False, None


def print_listing(app_id):
    """Fetch and print the current listing details. Returns the dict or None."""
    print(f"Fetching app listing for: {app_id}")
    ok, details = call_with_retry(app, app_id, lang=LANGUAGE, country=COUNTRY)
    if not ok or not details:
        print("  Could not fetch the listing. Check the package ID and your connection.")
        return None

    fields = [
        ("Title", "title"),
        ("Developer", "developer"),
        ("Package ID", "appId"),
        ("Current rating (score)", "score"),
        ("Total ratings", "ratings"),
        ("Total reviews", "reviews"),
        ("Installs", "installs"),
        ("Current version", "version"),
        ("Last updated", "lastUpdatedOn"),
    ]
    for label, key in fields:
        value = details.get(key)
        print(f"  {label}: {value if value not in (None, '') else 'not available'}")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(LISTING_JSON, "w", encoding="utf-8") as f:
        json.dump(details, f, indent=2, ensure_ascii=False, default=str)
    print(f"  Listing snapshot saved to: {LISTING_JSON}")
    return details


def review_to_row(raw, pass_name):
    """Turn one raw review dict into one row. Missing fields stay as None."""
    return {
        "review_id": raw.get("reviewId"),
        "rating": raw.get("score"),
        "review_text": raw.get("content"),
        "review_date": raw.get("at"),
        "app_version": raw.get("appVersion"),
        "review_created_version": raw.get("reviewCreatedVersion"),
        "thumbs_up_count": raw.get("thumbsUpCount"),
        "developer_response": raw.get("replyContent"),
        "developer_response_date": raw.get("repliedAt"),
        "collection_pass": pass_name,
    }


def collect_pass(app_id, sort_order, target, pass_name, seen_ids):
    """Collect up to `target` NEW reviews with one sort order (skips duplicates)."""
    rows = []
    token = None
    scanned = 0
    scan_limit = target * 3  # stop eventually even if most results are duplicates

    while len(rows) < target and scanned < scan_limit:
        ok, result = call_with_retry(
            reviews,
            app_id,
            lang=LANGUAGE,
            country=COUNTRY,
            sort=sort_order,
            count=BATCH_SIZE,
            continuation_token=token,
        )
        if not ok:
            print(f"  [{pass_name}] Stopping early because of repeated errors.")
            break

        batch, token = result
        if not batch:
            print(f"  [{pass_name}] No more reviews available.")
            break

        for raw in batch:
            scanned += 1
            review_id = raw.get("reviewId")
            if review_id:
                if review_id in seen_ids:
                    continue
                seen_ids.add(review_id)
            rows.append(review_to_row(raw, pass_name))
            if len(rows) >= target:
                break

        print(f"  [{pass_name}] collected {len(rows)}/{target}")
        if token is None:
            break
        time.sleep(PAUSE_SECONDS)

    return rows


def print_summary(df):
    """Print count, date range and rating distribution."""
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Reviews collected: {len(df)}")

    dates = pd.to_datetime(df["review_date"], errors="coerce").dropna()
    if dates.empty:
        print("Date range: not available (no valid dates)")
    else:
        print(f"Date range: {dates.min().date()} to {dates.max().date()}")

    ratings = pd.to_numeric(df["rating"], errors="coerce").dropna()
    print("Rating distribution:")
    if ratings.empty:
        print("  not available (no valid ratings)")
    else:
        counts = ratings.astype(int).value_counts().reindex([5, 4, 3, 2, 1], fill_value=0)
        total = counts.sum()
        for star, n in counts.items():
            print(f"  {star} stars: {n:>5}  ({n / total * 100:5.1f}%)")

    print(f"Output file: {OUTPUT_CSV}")


def main():
    parser = argparse.ArgumentParser(description="Collect Google Play reviews.")
    parser.add_argument("--max-reviews", type=int, default=MAX_REVIEWS)
    args = parser.parse_args()

    app_id = APP_ID

    # Create the output folder if it does not exist yet.
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print_listing(app_id)

    # Pass 1: newest reviews first (recent coverage).
    newest_target = int(args.max_reviews * NEWEST_SHARE)
    seen_ids = set()
    print(f"\nCollecting up to {newest_target} newest reviews...")
    rows = collect_pass(app_id, Sort.NEWEST, newest_target, "newest", seen_ids)

    # Pass 2: "most relevant" reviews (often older, adds historical coverage).
    remaining = args.max_reviews - len(rows)
    if remaining > 0:
        print(f"\nCollecting up to {remaining} additional 'most relevant' reviews...")
        rows += collect_pass(app_id, Sort.MOST_RELEVANT, remaining, "most_relevant", seen_ids)

    if not rows:
        print("\nNo reviews were collected. Nothing was saved.")
        print("Possible reasons: no internet connection, Google Play blocking requests, or no public reviews.")
        print("Check your connection and run the script again.")
        sys.exit(1)

    df = pd.DataFrame(rows, columns=COLUMNS)
    df["review_date"] = pd.to_datetime(df["review_date"], errors="coerce")
    df["developer_response_date"] = pd.to_datetime(df["developer_response_date"], errors="coerce")
    df = df.sort_values("review_date", ascending=False, na_position="last").reset_index(drop=True)

    # utf-8-sig so Excel on Windows displays non-English text correctly.
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print_summary(df)


if __name__ == "__main__":
    main()