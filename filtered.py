from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
import time
import os
from datetime import datetime

# Create output directory
output_dir = "momijiyama_data"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Search terms from your instructions
search_terms = [
    "朝鮮", "朝鮮刊", "朝鮮本", "明刊", "明版",
    "進上", "献上", "御分与", "御譲",
    "駿河御譲本", "元和御譲本", "家康", "御本"
]

# Base URL
base_url = "https://db2.sido.keio.ac.jp/goshojaku/index_search.html"

def setup_driver():
    """Initialize Selenium driver with options for unresponsive sites"""
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # Uncomment to run in background
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)
    return driver

def wait_for_element(driver, by, selector, timeout=15):
    """Wait for element with explicit waits"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, selector))
        )
        return element
    except TimeoutException:
        print(f"Timeout waiting for element: {selector}")
        return None

def extract_all_tables(driver):
    """Extract all 4 tables from the search results page"""
    all_data = []

    try:
        # Wait for any table to appear
        wait_for_element(driver, By.TAG_NAME, "table", timeout=20)

        # Get all tables on the page
        tables = driver.find_elements(By.TAG_NAME, "table")
        print(f"  Found {len(tables)} table(s) on this page")

        for table_idx, table in enumerate(tables):
            try:
                rows = table.find_elements(By.TAG_NAME, "tr")
                print(f"    Table {table_idx + 1}: {len(rows)} rows")

                for row_idx, row in enumerate(rows):
                    try:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) > 0:
                            # Extract all cell text
                            row_data = {
                                f"table_{table_idx + 1}_col_{col_idx}": cell.text
                                for col_idx, cell in enumerate(cells)
                            }
                            row_data["table_number"] = table_idx + 1
                            row_data["row_in_table"] = row_idx

                            # Try to extract URL if present
                            try:
                                link = row.find_element(By.TAG_NAME, "a")
                                row_data["url"] = link.get_attribute("href")
                            except NoSuchElementException:
                                row_data["url"] = None

                            all_data.append(row_data)
                    except Exception as e:
                        print(f"      Error extracting row {row_idx}: {e}")
                        continue
            except Exception as e:
                print(f"    Error processing table {table_idx}: {e}")
                continue

    except Exception as e:
        print(f"  No tables found or error extracting: {e}")

    return all_data

def search_term(driver, term):
    """Search for a single term and extract results"""
    print(f"\n--- Searching for: {term} ---")

    try:
        # Navigate to search page
        driver.get(base_url)
        print(f"Page loaded: {base_url}")

        # Wait for search box to be ready
        search_input = wait_for_element(driver, By.NAME, "q", timeout=15)
        if not search_input:
            print("Could not find search box")
            return []

        # Clear and enter search term
        search_input.clear()
        search_input.send_keys(term)
        print(f"Entered search term: {term}")

        # Find and click search button (may have various selectors)
        try:
            search_button = driver.find_element(By.XPATH, "//button[contains(@type, 'submit')]")
        except:
            try:
                search_button = driver.find_element(By.XPATH, "//input[@type='submit']")
            except:
                search_button = driver.find_element(By.NAME, "search")

        search_button.click()
        print("Search submitted")

        # Wait for results to load
        time.sleep(3)

        # Extract all tables from results
        all_results = extract_all_tables(driver)
        print(f"Extracted {len(all_results)} records")

        return all_results

    except Exception as e:
        print(f"ERROR searching for {term}: {e}")
        return []

def main():
    driver = setup_driver()
    all_combined_data = []

    try:
        for i, term in enumerate(search_terms, 1):
            print(f"\n{'='*60}")
            print(f"Search {i}/{len(search_terms)}")
            print(f"{'='*60}")

            # Search and extract
            results = search_term(driver, term)

            if results:
                # Add search term to each result
                for result in results:
                    result["search_term"] = term
                    result["search_timestamp"] = datetime.now().isoformat()

                all_combined_data.extend(results)

                # Save individual term CSV
                df_term = pd.DataFrame(results)
                term_filename = f"{output_dir}/{term}_results.csv"
                df_term.to_csv(term_filename, encoding='utf-8-sig', index=False)
                print(f"✓ Saved: {term_filename}")
            else:
                print(f"✗ No results for: {term}")

            # Rate limiting to avoid overwhelming the server
            time.sleep(2)

    except Exception as e:
        print(f"\nFATAL ERROR: {e}")

    finally:
        driver.quit()

    # Save combined CSV with all results
    if all_combined_data:
        df_all = pd.DataFrame(all_combined_data)
        combined_filename = f"{output_dir}/ALL_MOMIJIYAMA_RESULTS.csv"
        df_all.to_csv(combined_filename, encoding='utf-8-sig', index=False)
        print(f"\n✓ Saved combined file: {combined_filename}")
        print(f"Total records extracted: {len(all_combined_data)}")

    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total search terms: {len(search_terms)}")
    print(f"Total records extracted: {len(all_combined_data)}")
    print(f"Output directory: {output_dir}")
    print(f"Files created:")
    for f in os.listdir(output_dir):
        print(f"  - {f}")

if __name__ == "__main__":
    main()
