"""
Hōsa Bunko Library Web Scraper
Search and extract book metadata using Momijiyama keywords
CORRECT: POST with Shift-JIS encoding
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
from urllib.parse import urljoin

# ============================================================================
# CONFIG
# ============================================================================

BASE_URL = "https://housa.city.nagoya.jp/system/search/"
SEARCH_URL = BASE_URL + "search.cgi"
OUTPUT_DIR = "hosa_library_data"

# Momijiyama keywords
KEYWORDS = [
    "朝鮮", "朝鮮刊", "朝鮮本",
    "明刊", "明版",
    "進上", "献上",
    "御分与", "御譲",
    "駿河御譲本", "元和御譲本",
    "家康", "御本"
]

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "ja,en;q=0.9",
    "Content-Type": "application/x-www-form-urlencoded; charset=Shift_JIS"
}

# ============================================================================
# SCRAPER FUNCTIONS
# ============================================================================

def search_library(keyword, page=0):
    """
    Search the library catalog with a keyword
    POST with Shift-JIS encoding
    Returns: (list of books on page, total results found)
    """

    print(f"  Searching for: '{keyword}' (page {page})")

    try:
        # Build form data and encode to Shift-JIS
        form_string = f"action=search&word={keyword}&page={page}"
        form_data = form_string.encode('shift-jis')

        response = requests.post(
            SEARCH_URL,
            data=form_data,
            headers=HEADERS,
            timeout=30
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        full_text = soup.get_text()

        # Extract result count from text
        import re
        match = re.search(r'(\d+)件見つかりました', full_text)
        total_found = int(match.group(1)) if match else 0

        # Get results on THIS page
        books_on_page = extract_results_from_page(soup)

        if len(books_on_page) > 0:
            print(f"    → Total: {total_found} | On page: {len(books_on_page)}\n")
        else:
            print(f"    → No results on this page\n")

        return books_on_page, total_found

    except Exception as e:
        print(f"    ERROR: {e}\n")
        return [], 0


def extract_results_from_page(soup):
    """
    Extract book links from search results page
    Looks for detail page links
    """

    books = []

    try:
        # Look for all links that are detail pages
        for link in soup.find_all('a'):
            href = link.get('href')
            text = link.get_text(strip=True)

            # Detail page links have action=detail_view parameter
            if href and 'action=detail_view' in href:
                full_url = urljoin(BASE_URL, href)

                # Avoid duplicates
                if not any(b['url'] == full_url for b in books):
                    books.append({
                        'title': text if text else "Unknown",
                        'url': full_url
                    })

        return books

    except Exception as e:
        print(f"    ERROR extracting results: {e}")
        return []


def extract_book_details(url):
    """
    Extract detailed information from a book's detail page
    """

    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        data = {}

        # Field mapping: Japanese label → English key
        fields = {
            '資料名': 'title',
            '資料名ヨミ': 'title_kana',
            '年代1': 'year_1',
            '年代2': 'year_2',
            '作成者': 'creator',
            '宛名': 'addressee',
            '著編者': 'author_editor',
            '出版書写地': 'place_of_publication',
            '出版書写者': 'publisher',
            '出版書写年': 'publication_year',
            '大きさ（cm）': 'size_cm',
            '叢書名': 'series_name',
            '注記その他': 'notes',
            '印記': 'stamp',
            '旧蔵': 'former_owner',
            '別書名': 'alternate_title',
            '分類': 'classification',
            'コレクション区分': 'collection_classification',
            '請求番号': 'invoice_number',
            '重要図書区分': 'important_book',
            '複写': 'copy_available',
        }

        # Extract each field
        for jp_label, en_key in fields.items():
            data[en_key] = extract_field(soup, jp_label)

        data['url'] = url

        return data

    except Exception as e:
        print(f"      ERROR extracting: {e}")
        return None


def extract_field(soup, field_label):
    """
    Extract a specific field value from the page
    Searches for label in table rows
    """

    try:
        # Find all table cells
        for row in soup.find_all('tr'):
            cells = row.find_all('td')

            if len(cells) >= 2:
                # Check if first cell contains the label
                first_cell_text = cells[0].get_text(strip=True)

                if field_label in first_cell_text:
                    # Extract value from second cell
                    value = cells[1].get_text(strip=True)
                    return value if value else "-"

        return "-"

    except Exception:
        return "-"


def process_keyword(keyword, max_results=None):
    """
    Scrape all books for a single keyword
    Handles pagination
    Returns: list of book dictionaries
    """

    print(f"\n【KEYWORD】{keyword}")
    print("-" * 70)

    all_books = []
    page = 0
    total_found = 0
    results_processed = 0

    while True:
        # Search page
        books_on_page, total_found = search_library(keyword, page=page)

        if not books_on_page:
            # No more results
            print(f"  Finished: {len(all_books)} total books extracted\n")
            break

        # Extract details from each book
        for idx, book in enumerate(books_on_page, 1):
            title_preview = book['title'][:40]
            print(f"    [{results_processed + idx}/{total_found}] {title_preview}...")

            details = extract_book_details(book['url'])

            if details:
                details['search_keyword'] = keyword
                all_books.append(details)
                print(f"        ✓\n")
            else:
                print(f"        ✗\n")

            time.sleep(0.5)  # Rate limiting

            # Check if we've hit max results
            if max_results and len(all_books) >= max_results:
                print(f"  Reached max limit ({max_results})\n")
                return all_books

        results_processed += len(books_on_page)

        # Check if there are more pages
        if results_processed >= total_found:
            print(f"  Finished: {len(all_books)} total books extracted\n")
            break

        page += 1
        time.sleep(1)  # Delay between pages

    return all_books


def process_all_keywords(keywords, max_per_keyword=None):
    """
    Scrape all keywords and collect results
    """

    all_books = []
    results_by_keyword = {}

    for kw_idx, keyword in enumerate(keywords, 1):
        print(f"\n{'='*70}")
        print(f"KEYWORD {kw_idx}/{len(keywords)}")
        print(f"{'='*70}")

        books = process_keyword(keyword, max_results=max_per_keyword)

        if books:
            all_books.extend(books)
            results_by_keyword[keyword] = len(books)

        time.sleep(1)  # Delay between keywords

    return all_books, results_by_keyword


def save_results(all_books, results_by_keyword):
    """
    Save results to CSV files
    """

    if not all_books:
        print("\nNo data to save")
        return

    # Save combined results
    df_all = pd.DataFrame(all_books)
    filepath_all = os.path.join(OUTPUT_DIR, "hosa_momijiyama_keywords_combined.csv")
    df_all.to_csv(filepath_all, encoding='utf-8-sig', index=False)

    print(f"\n✓ Combined results saved: {filepath_all}")
    print(f"  Total: {len(all_books)} books\n")

    # Save by keyword
    for keyword, count in results_by_keyword.items():
        df_kw = df_all[df_all['search_keyword'] == keyword]

        # Sanitize filename
        safe_kw = keyword.replace('/', '_').replace('\\', '_')
        filepath = os.path.join(OUTPUT_DIR, f"hosa_{safe_kw}.csv")

        df_kw.to_csv(filepath, encoding='utf-8-sig', index=False)
        print(f"✓ {keyword:15} → {count:>3} books")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import sys

    print("\n" + "="*70)
    print("HŌSA BUNKO LIBRARY SCRAPER")
    print("Searching with Momijiyama keywords")
    print("="*70)

    # Parse arguments
    keywords = KEYWORDS
    max_per_kw = None

    for arg in sys.argv[1:]:
        if arg.startswith("--limit="):
            try:
                max_per_kw = int(arg.split("=")[1])
            except ValueError:
                pass
        elif arg == "--test":
            keywords = ["朝鮮"]  # Test with just one keyword
            max_per_kw = 5

    print(f"\nKeywords to search: {len(keywords)}\n")
    for i, kw in enumerate(keywords, 1):
        print(f"  {i:>2}. {kw}")

    if max_per_kw:
        print(f"\nMax per keyword: {max_per_kw}")

    print(f"\nProceed? (y/n): ", end="")

    if input().strip().lower() != 'y':
        print("Cancelled")
        sys.exit(0)

    print()

    # Scrape all keywords
    all_books, results_by_kw = process_all_keywords(keywords, max_per_keyword=max_per_kw)

    # Save results
    if all_books:
        print("\n" + "="*70)
        print("SEARCH RESULTS")
        print("="*70)
        save_results(all_books, results_by_kw)

        print("\n" + "="*70)
        print("STATISTICS")
        print("="*70)
        print(f"Total results: {len(all_books)} books")
        print(f"By keyword:")
        for kw, count in sorted(results_by_kw.items(), key=lambda x: x[1], reverse=True):
            print(f"  {kw:15} → {count:>3}")
        print("="*70 + "\n")
    else:
        print("\nNo results found")
