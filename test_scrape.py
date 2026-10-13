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
    # options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(60)
    return driver

def extract_tables_limited(driver, max_rows_per_table=None):
    """Extract tables with optional row limit for testing"""
    all_data = []

    try:
        # Wait for tables to load
        print("Waiting for tables to load...")
        WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "table"))
        )

        tables = driver.find_elements(By.TAG_NAME, "table")
        print(f"✓ Found {len(tables)} table(s)\n")

        for table_idx, table in enumerate(tables):
            try:
                rows = table.find_elements(By.TAG_NAME, "tr")
                rows_to_process = rows[:max_rows_per_table] if max_rows_per_table else rows

                print(f"Table {table_idx + 1}:")
                print(f"  Total rows in table: {len(rows)}")
                print(f"  Extracting: {len(rows_to_process)} rows")

                start_time = time.time()

                for row_idx, row in enumerate(rows_to_process):
                    try:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) > 0:
                            row_data = {
                                f"col_{col_idx}": cell.text.strip()
                                for col_idx, cell in enumerate(cells)
                            }
                            row_data["table_number"] = table_idx + 1
                            row_data["row_in_table"] = row_idx

                            try:
                                link = row.find_element(By.TAG_NAME, "a")
                                row_data["url"] = link.get_attribute("href")
                            except:
                                row_data["url"] = None

                            all_data.append(row_data)

                            # Progress indicator
                            if (row_idx + 1) % 10 == 0:
                                elapsed = time.time() - start_time
                                print(f"    {row_idx + 1}/{len(rows_to_process)} rows extracted ({elapsed:.1f}s)")

                    except Exception as e:
                        continue

                elapsed = time.time() - start_time
                print(f"  ✓ Table {table_idx + 1} complete in {elapsed:.1f}s\n")

            except Exception as e:
                print(f"  Error on table {table_idx}: {e}\n")
                continue

    except Exception as e:
        print(f"Error waiting for tables: {e}")

    return all_data

def scrape_test(num_rows=100):
    """Scrape limited rows for testing"""
    driver = setup_driver()
    all_records = []

    try:
        base_url = "https://db2.sido.keio.ac.jp/goshojaku/index.html"
        print(f"Loading: {base_url}")

        page_start = time.time()
        driver.get(base_url)
        page_load_time = time.time() - page_start
        print(f"✓ Page loaded in {page_load_time:.1f}s\n")

        # Extract limited rows
        extract_start = time.time()
        all_records = extract_tables_limited(driver, max_rows_per_table=num_rows)
        extract_time = time.time() - extract_start

        print(f"Total extraction time: {extract_time:.1f}s")

    except Exception as e:
        print(f"FATAL ERROR: {e}")

    finally:
        driver.quit()

    # Save results
    if all_records:
        df = pd.DataFrame(all_records)
        filename = f"{output_dir}/TEST_{num_rows}_rows.csv"
        df.to_csv(filename, encoding='utf-8-sig', index=False)

        file_size_mb = os.path.getsize(filename) / (1024*1024)

        print(f"\n{'='*60}")
        print(f"✓ SAVED: {filename}")
        print(f"{'='*60}")
        print(f"Records extracted: {len(all_records)}")
        print(f"File size: {file_size_mb:.2f} MB")
        print(f"Columns: {len(df.columns)}")

        # Extrapolate to 18K
        if len(all_records) > 0:
            avg_time_per_row = extract_time / len(all_records)
            estimated_18k_time = avg_time_per_row * 18000
            print(f"\nExtrapolation to 18,000 rows:")
            print(f"  Average time per row: {avg_time_per_row*1000:.2f}ms")
            print(f"  Estimated total time: {estimated_18k_time:.1f}s ({estimated_18k_time/60:.1f} min)")

    return all_records

if __name__ == "__main__":
    print("="*60)
    print("TEST: SCRAPING FIRST 100 ROWS")
    print("="*60 + "\n")

    scrape_test(num_rows=100)
