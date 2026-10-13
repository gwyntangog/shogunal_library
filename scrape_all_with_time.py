from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import os
from datetime import datetime

output_dir = "momijiyama_data"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(90)
    return driver

def extract_tables(driver, test_mode=False, test_rows=100):
    """Extract tables. If test_mode=True, only extract first N rows per table"""
    all_data = []

    try:
        print("Waiting for tables to load...")
        WebDriverWait(driver, 45).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "table"))
        )

        tables = driver.find_elements(By.TAG_NAME, "table")
        print(f"✓ Found {len(tables)} table(s)\n")

        for table_idx, table in enumerate(tables):
            try:
                rows = table.find_elements(By.TAG_NAME, "tr")

                # If test mode, limit rows
                if test_mode:
                    rows_to_process = rows[:test_rows]
                    print(f"Table {table_idx + 1}: {len(rows)} total rows (TEST: extracting {len(rows_to_process)})")
                else:
                    rows_to_process = rows
                    print(f"Table {table_idx + 1}: extracting {len(rows_to_process)} rows...")

                start_time = time.time()
                table_records = 0

                for row_idx, row in enumerate(rows_to_process):
                    try:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) > 0:
                            row_data = {
                                f"col_{col_idx}": cell.text.strip()
                                for col_idx, cell in enumerate(cells)
                            }
                            row_data["table_number"] = table_idx + 1

                            # Try to extract URL if present
                            try:
                                link = row.find_element(By.TAG_NAME, "a")
                                row_data["url"] = link.get_attribute("href")
                            except:
                                row_data["url"] = None

                            all_data.append(row_data)
                            table_records += 1

                            # Progress indicator every 10 rows
                            if (row_idx + 1) % 10 == 0:
                                elapsed = time.time() - start_time
                                rate = (row_idx + 1) / elapsed
                                remaining = (len(rows_to_process) - row_idx - 1) / rate if rate > 0 else 0
                                print(f"  [{row_idx + 1:>6}/{len(rows_to_process):<6}] {rate:>6.1f} rows/sec | {elapsed:>6.1f}s elapsed | {remaining:>6.1f}s remaining")

                    except Exception as e:
                        continue

                elapsed = time.time() - start_time
                print(f"  ✓ Table {table_idx + 1}: {table_records} records in {elapsed:.1f}s\n")

            except Exception as e:
                print(f"  Error on table {table_idx}: {e}\n")
                continue

    except Exception as e:
        print(f"Error: {e}")

    return all_data

def scrape_all(test_mode=False, test_rows=100):
    """Scrape all data from index page"""
    driver = setup_driver()
    all_records = []

    try:
        base_url = "https://db2.sido.keio.ac.jp/goshojaku/index.html"

        if test_mode:
            print("="*80)
            print(f"TEST MODE: First {test_rows} rows per table")
            print("="*80 + "\n")
        else:
            print("="*80)
            print("SCRAPING ALL 18,000+ ENTRIES")
            print("="*80 + "\n")

        print(f"Loading: {base_url}")
        page_start = time.time()
        driver.get(base_url)
        page_load_time = time.time() - page_start
        print(f"✓ Page loaded in {page_load_time:.1f}s\n")

        # Extract
        extract_start = time.time()
        all_records = extract_tables(driver, test_mode=test_mode, test_rows=test_rows)
        extract_time = time.time() - extract_start

    except Exception as e:
        print(f"FATAL ERROR: {e}")

    finally:
        driver.quit()

    # Save results
    if all_records:
        df = pd.DataFrame(all_records)

        if test_mode:
            filename = f"{output_dir}/TEST_{test_rows}rows.csv"
        else:
            filename = f"{output_dir}/ALL_ENTRIES.csv"

        df.to_csv(filename, encoding='utf-8-sig', index=False)

        file_size_mb = os.path.getsize(filename) / (1024*1024)

        print("\n" + "="*80)
        print(f"✓ SAVED: {filename}")
        print("="*80)
        print(f"Records: {len(all_records)}")
        print(f"File size: {file_size_mb:.2f} MB")
        print(f"Columns: {len(df.columns)}")
        print(f"Total extraction time: {extract_time:.1f}s ({extract_time/60:.1f} min)")

        # Extrapolate to 18K if in test mode
        if test_mode and len(all_records) > 0:
            avg_time_per_row = extract_time / len(all_records)
            estimated_total = avg_time_per_row * 18000
            print(f"\nExtrapolation to 18,000 rows:")
            print(f"  Estimated time: {estimated_total:.0f}s ({estimated_total/60:.1f} min)")

    return df if all_records else None

if __name__ == "__main__":
    import sys

    # Check command line args
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test with first 100 rows
        scrape_all(test_mode=True, test_rows=100)
    else:
        # Full scrape
        scrape_all(test_mode=False)
