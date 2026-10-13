"""
Build evidence sheet from Momijiyama catalogue
Version 2 CLEAN: NO TEXT MODIFICATION - preserve everything exactly as-is

Catalogue columns:
番号, 参照, 書誌, 題目(主目録), 巻数・附録等, 刊写・来歴等, 員数, 撰者等, 備考, 種別, 冊, link
col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11
"""

import pandas as pd
import os
from datetime import datetime

# ============================================================================
# CONFIG
# ============================================================================

CATALOGUE_FILE = "momijiyama_data/ALL_ENTRIES.csv"
SEARCH_RESULTS_DIR = "momijiyama_data/search_results"
OUTPUT_DIR = "momijiyama_data/evidence_v2"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# ============================================================================
# EVIDENCE SHEET COLUMNS
# ============================================================================

EVIDENCE_SHEET_COLUMNS = [
    "Record_ID",                        # From: col_0 (番号) - NO CHANGE
    "Library",                          # Constant: "Momijiyama"
    "Title_and_Author",                 # From: col_3 (題目) + col_7 (撰者) - CONCATENATE ONLY
    "Volume_Info",                      # From: col_4 (巻数・附録等) - NO CHANGE
    "Exact_Provenance_Language_JP",     # From: col_5 (刊写・来歴等) - **NO CHANGE - PRESERVE EXACTLY**
    "Remarks_Notes",                    # From: col_8 (備考) - NO CHANGE
    "Type_Category",                    # From: col_9 (種別) - NO CHANGE
    "Fascicle_Count",                   # From: col_10 (冊) - NO CHANGE
    "Keywords_Present",                 # FLAG ONLY: what keywords appear in col_5
    "Search_Term_Hit",                  # Which search term found this
    "Search_Category",                  # Which category
    "Source_URL",                       # From: col_11 (link) - NO CHANGE
    "Literal_English_Translation",      # EMPTY - for human translation
    "Confidence_Level",                 # EMPTY - for human to rate
    "Notes_and_Uncertainty",            # EMPTY - for human to flag
    "Extraction_Date",                  # When extracted
]

# ============================================================================
# KEYWORD FLAGGING (reference only - does not modify text)
# ============================================================================

KEYWORDS = {
    "edition_type": ["刊", "写", "版", "板", "活字", "刊本", "写本", "版本"],
    "transregional": ["朝鮮", "明", "宋", "元", "唐", "清"],
    "provenance_actions": ["進上", "献上", "御譲", "御分与", "賜", "献", "给"],
    "ownership": ["蔵書印", "御本", "家康", "秀忠", "吉宗", "旧蔵", "所蔵"],
    "institutional": ["駿河", "駿府", "江戸", "御文庫", "御庫", "五山", "足利学"],
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def safe_extract(value):
    """
    Extract text field - NO MODIFICATION
    """
    if pd.isna(value) or value == "":
        return ""

    return str(value).strip()

def flag_keywords_present(text):
    """
    FLAG keywords present in text - does NOT extract or modify text
    Returns: comma-separated list of keyword categories found
    """
    if not text:
        return ""

    flags = []

    for category, terms in KEYWORDS.items():
        for term in terms:
            if term in text:
                flags.append(category)
                break  # Just flag each category once

    return "|".join(flags) if flags else ""

def build_evidence_record(catalogue_row, search_term="", search_category=""):
    """
    Build one evidence record - PRESERVE EVERYTHING EXACTLY
    Only action: concatenate title + author, flag keywords, copy fields
    """

    # Extract fields - NO MODIFICATION
    record_id = safe_extract(catalogue_row.get("col_0"))
    title = safe_extract(catalogue_row.get("col_3"))
    author = safe_extract(catalogue_row.get("col_7"))
    volume_info = safe_extract(catalogue_row.get("col_4"))
    provenance_text = safe_extract(catalogue_row.get("col_5"))
    remarks = safe_extract(catalogue_row.get("col_8"))
    type_category = safe_extract(catalogue_row.get("col_9"))
    fascicle_count = safe_extract(catalogue_row.get("col_10"))
    url = safe_extract(catalogue_row.get("col_11"))

    # ONLY ACTION: Concatenate title + author
    if title and author:
        title_and_author = f"{title} / {author}"
    elif title:
        title_and_author = title
    elif author:
        title_and_author = author
    else:
        title_and_author = ""

    # FLAG keywords present (reference only, does not modify provenance_text)
    keywords_flagged = flag_keywords_present(provenance_text)

    # Build record
    record = {
        "Record_ID": record_id if record_id else "?",
        "Library": "Momijiyama",
        "Title_and_Author": title_and_author,
        "Volume_Info": volume_info,
        "Exact_Provenance_Language_JP": provenance_text,  # EXACTLY AS-IS
        "Remarks_Notes": remarks,  # EXACTLY AS-IS
        "Type_Category": type_category,
        "Fascicle_Count": fascicle_count,
        "Keywords_Present": keywords_flagged,  # FLAG ONLY
        "Search_Term_Hit": search_term,
        "Search_Category": search_category,
        "Source_URL": url,
        "Literal_English_Translation": "",  # EMPTY - FOR HUMAN
        "Confidence_Level": "",  # EMPTY - FOR HUMAN
        "Notes_and_Uncertainty": "",  # EMPTY - FOR HUMAN
        "Extraction_Date": datetime.now().isoformat(),
    }

    return record

# ============================================================================
# MAIN BUILDING FUNCTION
# ============================================================================

def build_evidence_sheet():
    """
    Extract all search results into evidence sheet
    ZERO TEXT MODIFICATION
    """

    print("="*70)
    print("BUILDING EVIDENCE SHEET V2 CLEAN")
    print("NO TEXT MODIFICATION - Preserving everything exactly as-is")
    print("="*70 + "\n")

    # Load catalogue
    print(f"Loading catalogue: {CATALOGUE_FILE}")
    if not os.path.exists(CATALOGUE_FILE):
        print(f"ERROR: Catalogue not found!")
        return None

    df_catalogue = pd.read_csv(CATALOGUE_FILE)
    print(f"✓ Loaded {len(df_catalogue)} records\n")

    # Process search results if they exist
    all_records = []
    record_counter = 1

    search_dir_exists = os.path.exists(SEARCH_RESULTS_DIR)

    if search_dir_exists:
        print("="*70)
        print("PROCESSING SEARCH RESULTS")
        print("="*70 + "\n")

        for category_dir in sorted(os.listdir(SEARCH_RESULTS_DIR)):
            category_path = os.path.join(SEARCH_RESULTS_DIR, category_dir)

            if not os.path.isdir(category_path):
                continue

            print(f"Category: {category_dir}")
            csv_files = [f for f in os.listdir(category_path) if f.endswith('.csv')]

            for csv_file in sorted(csv_files):
                search_term = csv_file.replace('.csv', '')
                csv_path = os.path.join(category_path, csv_file)

                # Load search result
                try:
                    df_hits = pd.read_csv(csv_path)
                except:
                    print(f"  [ERROR] Could not read {csv_file}")
                    continue

                if len(df_hits) == 0:
                    continue

                print(f"  {search_term}: {len(df_hits)} hits")

                # Extract each hit
                for idx, row in df_hits.iterrows():
                    record = build_evidence_record(
                        row.to_dict(),
                        search_term=search_term,
                        search_category=category_dir
                    )
                    all_records.append(record)

    else:
        print("Search results directory not found - extracting all records with provenance text\n")

        for idx, row in df_catalogue.iterrows():
            record = build_evidence_record(row.to_dict())
            provenance = record["Exact_Provenance_Language_JP"]

            # Only include if there's provenance text
            if provenance:
                all_records.append(record)

            if (idx + 1) % 500 == 0:
                print(f"  Processed {idx + 1} records...")

    # Create DataFrame
    df_evidence = pd.DataFrame(all_records)

    print(f"\n✓ Extracted {len(df_evidence)} records total\n")

    return df_evidence

# ============================================================================
# SAVING & REPORTING
# ============================================================================

def save_evidence_sheet(df_evidence):
    """Save the evidence sheet"""

    print("="*70)
    print("SAVING EVIDENCE SHEET")
    print("="*70 + "\n")

    # Save combined
    filepath = os.path.join(OUTPUT_DIR, "evidence_sheet_combined.csv")
    df_evidence.to_csv(filepath, encoding='utf-8-sig', index=False)
    print(f"✓ Saved combined: {filepath}")
    print(f"  Records: {len(df_evidence)}")
    print(f"  Columns: {len(df_evidence.columns)}\n")

    # Save by category (if available)
    if "Search_Category" in df_evidence.columns:
        categories = df_evidence['Search_Category'].unique()
        if len(categories) > 1 or categories[0] != "":
            print("Saving by category:")
            for category in sorted(categories):
                if category == "" or category == "[all]":
                    continue
                df_cat = df_evidence[df_evidence['Search_Category'] == category]
                cat_filepath = os.path.join(OUTPUT_DIR, f"evidence_{category}.csv")
                df_cat.to_csv(cat_filepath, encoding='utf-8-sig', index=False)
                print(f"  ✓ {category}: {len(df_cat)} records")

    print()

def print_summary(df_evidence):
    """Print summary statistics"""

    print("\n" + "="*70)
    print("EVIDENCE SHEET SUMMARY")
    print("="*70 + "\n")

    print(f"Total records: {len(df_evidence)}")

    with_provenance = len(df_evidence[df_evidence['Exact_Provenance_Language_JP'] != ''])
    print(f"Records with provenance text: {with_provenance}")

    with_keywords = len(df_evidence[df_evidence['Keywords_Present'] != ''])
    print(f"Records with flagged keywords: {with_keywords}\n")

    if "Keywords_Present" in df_evidence.columns and with_keywords > 0:
        print("Keyword categories found:")
        all_keywords = "|".join(df_evidence['Keywords_Present'].dropna())
        keyword_counts = {}
        for kw in all_keywords.split("|"):
            if kw:
                keyword_counts[kw] = keyword_counts.get(kw, 0) + 1

        for kw, count in sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {kw}: {count} records")

def print_sample_records(df_evidence, n=3):
    """Print sample records with original Japanese text"""

    print("\n" + "="*70)
    print(f"SAMPLE RECORDS (first {n})")
    print("="*70 + "\n")

    for idx, (i, row) in enumerate(df_evidence.head(n).iterrows(), 1):
        print(f"\n[{idx}] {row['Record_ID']}")
        print("-" * 70)
        print(f"Title: {row['Title_and_Author']}")
        print(f"Keywords flagged: {row['Keywords_Present'] if row['Keywords_Present'] else '(none)'}")
        print(f"\n[EXACT JAPANESE]")
        print(row['Exact_Provenance_Language_JP'][:300])
        if len(row['Exact_Provenance_Language_JP']) > 300:
            print("... [truncated for display]")
        print()

# ============================================================================
# MAIN
# ============================================================================

def run():
    """Run complete build"""

    df_evidence = build_evidence_sheet()

    if df_evidence is None or len(df_evidence) == 0:
        print("ERROR: No records extracted!")
        return

    print_summary(df_evidence)
    print_sample_records(df_evidence, n=5)
    save_evidence_sheet(df_evidence)

    print("="*70)
    print("✓ EVIDENCE SHEET BUILD COMPLETE")
    print("="*70 + "\n")
    print(f"Output directory: {OUTPUT_DIR}\n")

    return df_evidence

if __name__ == "__main__":
    run()
