"""
Fill translations by iterating through CSV files in evidence_raw folder
WITH TIME ESTIMATION
"""

import pandas as pd
import os
import time
import requests
import json
import glob
from datetime import datetime, timedelta

# ============================================================================
# CONFIG
# ============================================================================

EVIDENCE_RAW_DIR = "momijiyama_data/evidence_raw"
OUTPUT_DIR = "momijiyama_data/translations_parley"

def load_secrets():
    """Load API key from secrets.txt"""
    secrets_file = "secrets.txt"

    if not os.path.exists(secrets_file):
        print(f"ERROR: {secrets_file} not found")
        return None

    with open(secrets_file, 'r') as f:
        api_key = f.readline().strip()

    return api_key if api_key else None


ANTHROPIC_API_KEY = load_secrets()
ANTHROPIC_BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://parley.api.mit.edu")
ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"

# RETRY CONFIG
MAX_RETRIES = 3
INITIAL_BACKOFF = 1
BACKOFF_MULTIPLIER = 2

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# ============================================================================
# TIME ESTIMATION
# ============================================================================

class TimeEstimator:
    """Track and estimate remaining time"""

    def __init__(self, total_items):
        self.total_items = total_items
        self.processed = 0
        self.start_time = time.time()
        self.times = []

    def record_item(self, duration):
        """Record time for one item"""
        self.processed += 1
        self.times.append(duration)

    def get_avg_time(self):
        """Get average time per item"""
        if not self.times:
            return 0
        return sum(self.times) / len(self.times)

    def get_elapsed(self):
        """Get elapsed time"""
        return time.time() - self.start_time

    def get_remaining(self):
        """Estimate remaining time"""
        if self.processed == 0:
            return 0
        avg = self.get_avg_time()
        remaining_items = self.total_items - self.processed
        return avg * remaining_items

    def format_time(self, seconds):
        """Format seconds to human readable"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            mins = seconds / 60
            return f"{mins:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"

    def get_status(self):
        """Get status string"""
        elapsed = self.format_time(self.get_elapsed())
        remaining = self.format_time(self.get_remaining())
        avg = self.format_time(self.get_avg_time())

        return f"[{self.processed}/{self.total_items}] ⏱ Avg: {avg} | Remaining: {remaining} | Elapsed: {elapsed}"


# ============================================================================
# API CALL WITH RETRY
# ============================================================================

def call_claude_with_retry(japanese_text, record_id="", max_retries=MAX_RETRIES):
    """Call Claude with automatic retry"""

    if not ANTHROPIC_API_KEY:
        print("ERROR: API key not loaded")
        return None

    if not japanese_text or japanese_text.strip() == "":
        return None

    backoff = INITIAL_BACKOFF

    for attempt in range(1, max_retries + 1):
        try:
            print(f"    Attempt {attempt}/{max_retries}...", end=" ", flush=True)

            headers = {
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }

            system_prompt = """You are an expert in Classical Japanese and Early Modern Japanese (Edo period). Provide a literal translation and one-sentence summary."""

            user_message = f"""Analyze this archival provenance text:

{japanese_text}

Provide:
1. WORD-FOR-WORD TRANSLATION: Literal clause-by-clause translation
2. SUMMARY: One-sentence summary of book movement/acquisition

Format exactly like this:
---
WORD-FOR-WORD TRANSLATION:
[translation]

SUMMARY:
[summary]
---"""

            payload = {
                "model": ANTHROPIC_MODEL,
                "max_tokens": 4096,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_message}],
            }

            url = f"{ANTHROPIC_BASE_URL}/v1/messages"
            response = requests.post(url, json=payload, headers=headers, timeout=30)

            if response.status_code != 200:
                print(f"HTTP {response.status_code}")

                if attempt < max_retries:
                    print(f"      Retrying in {backoff}s...")
                    time.sleep(backoff)
                    backoff *= BACKOFF_MULTIPLIER
                    continue
                else:
                    return None

            response.raise_for_status()
            result = response.json()

            if "error" in result:
                if attempt < max_retries:
                    print(f"API ERROR, retrying...")
                    time.sleep(backoff)
                    backoff *= BACKOFF_MULTIPLIER
                    continue
                else:
                    return None

            if "content" not in result or len(result.get("content", [])) == 0:
                if attempt < max_retries:
                    print(f"BAD RESPONSE, retrying...")
                    time.sleep(backoff)
                    backoff *= BACKOFF_MULTIPLIER
                    continue
                else:
                    return None

            response_text = result["content"][0]["text"]
            print("✓")
            return parse_response(response_text)

        except Exception as e:
            print(f"ERROR")
            if attempt < max_retries:
                print(f"      Retrying in {backoff}s...")
                time.sleep(backoff)
                backoff *= BACKOFF_MULTIPLIER
                continue
            else:
                return None

    return None


def parse_response(response_text):
    """Parse Claude response"""
    try:
        word_for_word = ""
        summary = ""

        if "WORD-FOR-WORD TRANSLATION:" in response_text:
            start = response_text.find("WORD-FOR-WORD TRANSLATION:") + len("WORD-FOR-WORD TRANSLATION:")
            end = response_text.find("SUMMARY:") if "SUMMARY:" in response_text else len(response_text)
            word_for_word = response_text[start:end].strip()

        if "SUMMARY:" in response_text:
            start = response_text.find("SUMMARY:") + len("SUMMARY:")
            summary = response_text[start:].strip()

        return {
            "word_for_word": word_for_word or "[Parse error]",
            "summary": summary or "[Parse error]",
        }

    except Exception:
        return {"word_for_word": "[Parse error]", "summary": "[Parse error]"}


# ============================================================================
# FILE PROCESSING
# ============================================================================

def get_csv_files():
    """Get all CSV files in evidence_raw folder (except combined)"""
    csv_files = glob.glob(os.path.join(EVIDENCE_RAW_DIR, "*.csv"))

    # Filter out evidence_sheet_combined.csv
    csv_files = [f for f in csv_files if not f.endswith("evidence_sheet_combined.csv")]

    # Sort by filename
    csv_files.sort()

    return csv_files


def load_and_prepare_csv(filepath):
    """Load CSV and prepare for translation"""
    df = pd.read_csv(filepath)

    # Convert translation columns to object type
    if 'Literal_English_Translation' not in df.columns:
        df['Literal_English_Translation'] = ""
    else:
        df['Literal_English_Translation'] = df['Literal_English_Translation'].astype('object').fillna("")

    if 'Summary' not in df.columns:
        df['Summary'] = ""
    else:
        df['Summary'] = df['Summary'].astype('object').fillna("")

    return df


def process_csv_file(filepath, limit=None):
    """
    Process a single CSV file
    Returns: (df_updated, successful, failed, elapsed_time)
    """

    filename = os.path.basename(filepath)
    print(f"\nProcessing: {filename}")
    print("-"*70)

    file_start = time.time()
    df = load_and_prepare_csv(filepath)

    # Filter records needing translation
    mask = (
        (df['Exact_Provenance_Language_JP'].notna()) &
        (df['Exact_Provenance_Language_JP'] != '') &
        ((df['Literal_English_Translation'].isna()) | (df['Literal_English_Translation'] == ''))
    )

    needs = df[mask].copy()

    if len(needs) == 0:
        print(f"  No records need translation")
        return df, 0, 0, 0

    if limit:
        needs = needs.iloc[:limit]

    print(f"  Found {len(needs)} records needing translation\n")

    successful = 0
    failed = 0

    # Time estimator
    estimator = TimeEstimator(len(needs))

    for idx, (i, row) in enumerate(needs.iterrows(), 1):
        record_start = time.time()

        record_id = row['Record_ID']
        title = str(row['Title_and_Author'])[:40] if pd.notna(row['Title_and_Author']) else "(no title)"

        jp_text = row['Exact_Provenance_Language_JP']

        print(f"  [{idx:>3}] {record_id:>6} | {title}...")

        result = call_claude_with_retry(str(jp_text), record_id=record_id)

        record_duration = time.time() - record_start
        estimator.record_item(record_duration)

        if result:
            df.loc[i, 'Literal_English_Translation'] = result.get("word_for_word", "")
            df.loc[i, 'Summary'] = result.get("summary", "")
            successful += 1
        else:
            failed += 1

        # Print time estimation
        print(f"         {estimator.get_status()}\n")

        time.sleep(0.3)

    file_elapsed = time.time() - file_start

    return df, successful, failed, file_elapsed


def get_output_filename(input_filename):
    """Generate output filename"""
    name, ext = os.path.splitext(input_filename)
    return f"{name}_translated{ext}"


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import sys

    if not ANTHROPIC_API_KEY:
        print("ERROR: API key not loaded from secrets.txt")
        sys.exit(1)

    print("\n" + "="*70)
    print("MOMIJIYAMA - TRANSLATE CSV FILES")
    print("="*70 + "\n")

    # Get CSV files
    csv_files = get_csv_files()

    if not csv_files:
        print(f"ERROR: No CSV files found in {EVIDENCE_RAW_DIR}")
        sys.exit(1)

    print(f"Found {len(csv_files)} CSV files to process:\n")

    for idx, filepath in enumerate(csv_files, 1):
        filename = os.path.basename(filepath)
        print(f"  [{idx}] {filename}")

    print()

    # Parse args
    limit = None
    for arg in sys.argv[1:]:
        if arg.startswith("--limit="):
            try:
                limit = int(arg.split("=")[1])
            except ValueError:
                pass

    if limit:
        print(f"Processing max {limit} records per file\n")

    # Confirm
    print("Process all files? (y/n): ", end="")
    if input().strip().lower() != 'y':
        print("Cancelled")
        sys.exit(0)

    print()

    # Process each CSV
    total_success = 0
    total_failed = 0
    total_time = 0
    processed_files = []

    overall_start = time.time()

    for file_idx, filepath in enumerate(csv_files, 1):
        print(f"\n{'='*70}")
        print(f"FILE {file_idx}/{len(csv_files)}")
        print(f"{'='*70}")

        df_updated, success, failed, elapsed = process_csv_file(filepath, limit=limit)

        total_success += success
        total_failed += failed
        total_time += elapsed

        # Save output
        input_filename = os.path.basename(filepath)
        output_filename = get_output_filename(input_filename)
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        df_updated.to_csv(output_path, encoding='utf-8-sig', index=False)

        # Format elapsed time
        if elapsed < 60:
            time_str = f"{int(elapsed)}s"
        elif elapsed < 3600:
            time_str = f"{elapsed/60:.1f}m"
        else:
            time_str = f"{elapsed/3600:.1f}h"

        print(f"\n  ✓ Success: {success}")
        print(f"  ✗ Failed: {failed}")
        print(f"  ⏱ Time: {time_str}")
        print(f"  ✓ Saved: {output_path}")

        processed_files.append((input_filename, success, failed, time_str))

    # Summary
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)
    print()

    for input_file, success, failed, time_str in processed_files:
        total = success + failed
        if total > 0:
            print(f"  {input_file:35} | ✓ {success:>3}  ✗ {failed:>3}  |  {time_str:>6}")

    print()

    # Format total time
    if total_time < 60:
        total_time_str = f"{int(total_time)}s"
    elif total_time < 3600:
        total_time_str = f"{total_time/60:.1f}m"
    else:
        total_time_str = f"{total_time/3600:.1f}h"

    print(f"  TOTAL: ✓ {total_success:>3}  ✗ {total_failed:>3}  |  {total_time_str:>6}")
    print("="*70 + "\n")
