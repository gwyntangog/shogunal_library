from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd
import time
import os
from datetime import datetime

output_dir = "momijiyama_data"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

def setup_driver():
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # Uncomment to run in background
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(60)
    return driver

def extract_all_tables(driver):
    """Extract all 4 tables from the page"""
    all_data = []

    try:
        # Wait for tables to load
        WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "table"))
        )

        tables = driver.find_elements(By.TAG_NAME, "table")
        print(f"\nFound {len(tables)} table(s)")

        for table_idx, table in enumerate(tables):
            try:
                rows = table.find_elements(By.TAG_NAME, "tr")
                print(f"  Table {table_idx + 1}: extracting {len(rows)} rows...")

                for row_idx, row in enumerate(rows):
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
                    except Exception as e:
                        continue

                print(f"    ✓ Table {table_idx + 1} complete: {len([d for d in all_data if d['table_number'] == table_idx + 1])} records")

            except Exception as e:
                print(f"  Error on table {table_idx}: {e}")
                continue

    except Exception as e:
        print(f"Error waiting for tables: {e}")

    return all_data

def scrape_all_unfiltered():
    """Scrape all 18,000 entries from one page"""
    driver = setup_driver()
    all_records = []

    try:
        base_url = "https://db2.sido.keio.ac.jp/goshojaku/index.html"
        print(f"Loading: {base_url}")
        print("(This will take a minute... 18K records is a lot of HTML)")

        driver.get(base_url)
        print("✓ Page loaded")

        # Extract all tables
        all_records = extract_all_tables(driver)

    except Exception as e:
        print(f"FATAL ERROR: {e}")

    finally:
        driver.quit()

    # Save results
    if all_records:
        df = pd.DataFrame(all_records)
        filename = f"{output_dir}/ALL_18K_UNFILTERED.csv"
        df.to_csv(filename, encoding='utf-8-sig', index=False)
        print(f"\n{'='*60}")
        print(f"✓ SAVED: {filename}")
        print(f"{'='*60}")
        print(f"Total records: {len(all_records)}")
        print(f"Columns: {list(df.columns)}")
        print(f"File size: {os.path.getsize(filename) / (1024*1024):.2f} MB")

    return all_records

if __name__ == "__main__":
    print("="*60)
    print("SCRAPING ALL 18,000 UNFILTERED ENTRIES")
    print("="*60)
    scrape_all_unfiltered()
