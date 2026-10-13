"""
Search the Momijiyama Bunko catalogue for text movement terms
Saves results organized by category folders with individual term CSVs
(Only saves CSVs with non-empty results)
"""

import pandas as pd
import os
from datetime import datetime
from searchterms import (
    SEARCH_TERM_CATEGORIES,
    get_all_terms,
    get_category_for_term,
    get_priority_rank,
)

# ============================================================================
# CONFIG
# ============================================================================

CATALOGUE_FILE = "momijiyama_data/ALL_ENTRIES.csv"
OUTPUT_DIR = "momijiyama_data/search_results"

# ============================================================================
# SETUP / DIRECTORY FUNCTIONS
# ============================================================================

def setup_output_structure():
    """Create output directory structure with folders per category"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"✓ Created output directory: {OUTPUT_DIR}\n")

    # Create subfolder per category
    for category in SEARCH_TERM_CATEGORIES.keys():
        category_dir = os.path.join(OUTPUT_DIR, category)
        if not os.path.exists(category_dir):
            os.makedirs(category_dir)
            print(f"✓ Created category folder: {category_dir}")

    print()

def get_category_dir(category):
    """Get path to category folder"""
    return os.path.join(OUTPUT_DIR, category)

def get_term_csv_path(category, term):
    """Get path to CSV file for a specific term"""
    category_dir = get_category_dir(category)
    # Replace problematic filename characters
    safe_term = term.replace("/", "_").replace("\\", "_")
    filename = f"{safe_term}.csv"
    return os.path.join(category_dir, filename)

# ============================================================================
# CORE SEARCH FUNCTIONS
# ============================================================================

def load_catalogue(filepath=CATALOGUE_FILE):
    """Load the full catalogue CSV"""
    if not os.path.exists(filepath):
        print(f"ERROR: Catalogue file not found: {filepath}")
        return None

    print(f"Loading catalogue: {filepath}")
    df = pd.read_csv(filepath)
    print(f"✓ Loaded {len(df)} records\n")
    return df

def search_term(df, term):
    """
    Search for a single term across all columns
    Returns: DataFrame of matching records
    """
    # Convert all to strings and search
    matches = df[df.astype(str).apply(
        lambda x: x.str.contains(term, na=False, regex=False, case=False)
    ).any(axis=1)]

    return matches

def search_all_terms(df, verbose=True):
    """
    Search for all terms in the catalogue
    Returns: DataFrame with results ranked by frequency
    """
    results = []
    all_terms = get_all_terms()
    total = len(all_terms)

    print("="*70)
    print(f"SEARCHING {total} TERMS")
    print("="*70 + "\n")

    for idx, term in enumerate(all_terms, 1):
        hits = search_term(df, term)
        hit_count = len(hits)

        # Get metadata
        categories = get_category_for_term(term)
        priority_rank = get_priority_rank(term)

        result = {
            "term": term,
            "hit_count": hit_count,
            "categories": "|".join(categories),
            "is_priority": "YES" if priority_rank else "NO",
            "priority_rank": priority_rank if priority_rank else "-",
        }
        results.append(result)

        # Progress indicator
        if verbose and idx % 10 == 0:
            print(f"[{idx:>3}/{total}] Processed {idx} terms...")

    # Convert to DataFrame and sort
    df_results = pd.DataFrame(results)
    df_results = df_results.sort_values("hit_count", ascending=False)

    return df_results

def search_by_category(df, category, verbose=True):
    """
    Search for all terms in a specific category
    Returns: DataFrame of results for that category
    """
    if category not in SEARCH_TERM_CATEGORIES:
        print(f"ERROR: Category not found: {category}")
        print(f"Available categories: {list(SEARCH_TERM_CATEGORIES.keys())}")
        return None

    terms = SEARCH_TERM_CATEGORIES[category]
    results = []

    if verbose:
        print(f"\n{'='*70}")
        print(f"SEARCHING CATEGORY: {category}")
        print(f"{'='*70}\n")

    for term in terms:
        hits = search_term(df, term)
        hit_count = len(hits)

        result = {
            "term": term,
            "hit_count": hit_count,
            "category": category,
        }
        results.append(result)

        if verbose:
            if hit_count > 0:
                print(f"✓ {term:20} → {hit_count:>5} hits")
            else:
                print(f"✗ {term:20} → {hit_count:>5} hits")

    df_results = pd.DataFrame(results)
    df_results = df_results.sort_values("hit_count", ascending=False)

    return df_results

def get_records_for_term(df, term):
    """
    Get all records matching a specific term
    Returns: DataFrame of matching records
    """
    return search_term(df, term)

# ============================================================================
# SAVING FUNCTIONS
# ============================================================================

def save_term_results(df_catalogue, category, term, verbose=True):
    """
    Search for a term and save results to category folder
    ONLY saves if hit_count > 0
    Returns: (filepath, hit_count) or (None, 0) if empty
    """
    hits = get_records_for_term(df_catalogue, term)
    hit_count = len(hits)

    if hit_count == 0:
        if verbose:
            print(f"  ✗ {term:20} (0 hits) [skipped]")
        return None, 0

    filepath = get_term_csv_path(category, term)
    hits.to_csv(filepath, encoding='utf-8-sig', index=False)

    if verbose:
        print(f"  ✓ {term:20} ({hit_count:>5} hits) → {os.path.basename(filepath)}")

    return filepath, hit_count

def save_category_csvs(df_catalogue, category, verbose=True):
    """
    Search all terms in a category and save individual CSVs
    ONLY saves non-empty results
    Returns: list of (filepath, hit_count) tuples
    """
    if category not in SEARCH_TERM_CATEGORIES:
        print(f"ERROR: Category not found: {category}")
        return []

    terms = SEARCH_TERM_CATEGORIES[category]
    results = []

    if verbose:
        print(f"\nSaving results for category: {category}")
        print("-" * 70)

    for term in terms:
        filepath, hit_count = save_term_results(df_catalogue, category, term, verbose=verbose)
        if filepath is not None:  # Only add if saved
            results.append((filepath, hit_count))

    return results

def save_all_category_csvs(df_catalogue, verbose=True):
    """
    Save individual CSVs for every term in every category
    ONLY saves non-empty results
    Returns: summary dictionary
    """
    summary = {}

    print("\n" + "="*70)
    print("SAVING ALL SEARCH RESULTS (non-empty only)")
    print("="*70)

    for category in SEARCH_TERM_CATEGORIES.keys():
        results = save_category_csvs(df_catalogue, category, verbose=verbose)
        summary[category] = results

    return summary

def save_summary_csv(df_results, filename="search_summary.csv"):
    """Save ranked search results to CSV (root of search_results)"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    df_results.to_csv(filepath, encoding='utf-8-sig', index=False)
    print(f"\n✓ Saved summary: {filepath}\n")
    return filepath

# ============================================================================
# ANALYSIS / REPORTING
# ============================================================================

def print_results_summary(df_results, top_n=20):
    """Print summary of search results"""
    print("="*70)
    print(f"TOP {top_n} TERMS BY HIT COUNT")
    print("="*70 + "\n")

    for idx, row in df_results.head(top_n).iterrows():
        term = row["term"]
        hits = row["hit_count"]
        categories = row["categories"]
        priority = row["is_priority"]

        priority_marker = "⭐" if priority == "YES" else "  "

        print(f"{priority_marker} {term:20} | {hits:>5} hits | {categories}")

    print("\n" + "="*70)
    print("STATISTICS")
    print("="*70)
    total_terms = len(df_results)
    terms_with_hits = len(df_results[df_results["hit_count"] > 0])
    total_hits = df_results["hit_count"].sum()

    print(f"Total unique terms searched: {total_terms}")
    print(f"Terms with at least 1 hit: {terms_with_hits} ({100*terms_with_hits/total_terms:.1f}%)")
    print(f"Total hits across all searches: {total_hits}")
    print(f"Terms with 0 hits: {total_terms - terms_with_hits}")
    print()

def print_category_stats(df_results):
    """Print statistics by category"""
    print("="*70)
    print("HITS BY CATEGORY")
    print("="*70 + "\n")

    categories = df_results["categories"].str.split("|").explode()
    category_counts = categories.value_counts()

    for category, count in category_counts.items():
        print(f"{category:30} → {count:>3} terms")
    print()

def print_priority_results(df_results):
    """Print only Wiebke's priority terms"""
    print("="*70)
    print("WIEBKE'S PRIORITY TERMS - RESULTS")
    print("="*70 + "\n")

    priority_results = df_results[df_results["is_priority"] == "YES"].sort_values("priority_rank")

    for idx, row in priority_results.iterrows():
        term = row["term"]
        hits = row["hit_count"]
        rank = row["priority_rank"]
        status = "✓" if hits > 0 else "✗"

        print(f"[{rank:>2}] {status} {term:20} → {hits:>5} hits")
    print()

def print_directory_structure():
    """Print the created directory structure"""
    print("\n" + "="*70)
    print("OUTPUT DIRECTORY STRUCTURE (non-empty CSVs only)")
    print("="*70 + "\n")

    total_files = 0
    for root, dirs, files in os.walk(OUTPUT_DIR):
        level = root.replace(OUTPUT_DIR, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f'{indent}{os.path.basename(root)}/')

        subindent = ' ' * 2 * (level + 1)
        for file in sorted(files):
            print(f'{subindent}{file}')
            total_files += 1

    print(f"\nTotal files created: {total_files}")
    print()

# ============================================================================
# MAIN WORKFLOW
# ============================================================================

def run_full_analysis():
    """Run complete search and analysis"""
    print("\n" + "="*70)
    print("MOMIJIYAMA BUNKO - TEXT MOVEMENT CATALOGUE SEARCH")
    print("="*70 + "\n")

    # Setup directory structure
    setup_output_structure()

    # Load catalogue
    df_catalogue = load_catalogue()
    if df_catalogue is None:
        return

    # Search all terms and get summary
    df_results = search_all_terms(df_catalogue, verbose=True)

    # Save summary to root
    save_summary_csv(df_results, "search_summary.csv")

    # Print initial analysis
    print_results_summary(df_results, top_n=30)
    print_category_stats(df_results)
    print_priority_results(df_results)

    # Save individual CSVs per term in category folders (non-empty only)
    save_all_category_csvs(df_catalogue, verbose=True)

    # Print final structure
    print_directory_structure()

    print("="*70)
    print("✓ ANALYSIS COMPLETE")
    print("="*70 + "\n")
    print(f"All results saved to: {OUTPUT_DIR}\n")

    return df_results, df_catalogue

# ============================================================================
# INTERACTIVE FUNCTIONS
# ============================================================================

def search_term_interactive(df_catalogue, term):
    """Search for a term and display top results"""
    hits = get_records_for_term(df_catalogue, term)

    print(f"\n{'='*70}")
    print(f"SEARCH RESULTS FOR: {term}")
    print(f"{'='*70}")
    print(f"Found {len(hits)} matching records\n")

    if len(hits) > 0:
        # Display first 5 results
        print("First 5 results:")
        print("-" * 70)
        for idx, (i, row) in enumerate(hits.head(5).iterrows(), 1):
            print(f"\n[{idx}]")
            for col in hits.columns:
                if hits[col].dtype == 'object':  # String column
                    val = str(row[col])[:80]  # Truncate long strings
                    print(f"  {col}: {val}")

    return hits

def open_category_results(category):
    """Open a category folder in file explorer (MacOS/Linux/Windows)"""
    import subprocess
    import platform

    category_dir = get_category_dir(category)

    if not os.path.exists(category_dir):
        print(f"ERROR: Category directory not found: {category_dir}")
        return

    system = platform.system()

    if system == "Darwin":  # MacOS
        subprocess.Popen(["open", category_dir])
    elif system == "Windows":
        os.startfile(category_dir)
    elif system == "Linux":
        subprocess.Popen(["xdg-open", category_dir])

    print(f"Opened: {category_dir}")

if __name__ == "__main__":
    # Run full analysis
    df_results, df_catalogue = run_full_analysis()

    # Optional: search a specific term interactively
    # hits = search_term_interactive(df_catalogue, "進上")

    # Optional: open a category folder
    # open_category_results("PRIORITY")
