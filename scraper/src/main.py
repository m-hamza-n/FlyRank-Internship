import os
import json
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timezone
from pydantic import BaseModel, ValidationError, Field
from typing import Optional

# --- Configuration ---
BASE_URL = "https://books.toscrape.com/"
HEADERS = {
    "User-Agent": "FlyRankInternship-A9/1.0 (+https://github.com/yourusername/backend-ai-flyrank)"
}
DELAY = 0.5
TIMEOUT = 10
CACHE_DIR = "cache"
OUTPUT_DIR = "output"
MAX_PAGES = 3

# Ensure directories exist
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Pydantic Schema (Stage 4) ---
class BookSchema(BaseModel):
    title: str
    product_url: str
    price_text: str
    price_gbp: float
    availability_text: str
    rating_text: str
    description: Optional[str] = None
    source_page: str
    fetched_at: str

# --- Helper: Polite Fetch with Cache (Stage 1, 3, 5) ---
def fetch_page(url, cache_key):
    cache_path = os.path.join(CACHE_DIR, cache_key)
    if os.path.exists(cache_path):
        print(f"CACHE HIT: {url}")
        with open(cache_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    print(f"FETCH: {url}")
    try:
        time.sleep(DELAY)
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        with open(cache_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"ERROR fetching {url}: {e}")
        return None

# --- Helper: Extract Book Details (Stage 3) ---
def extract_book_data(html, url, source_page):
    soup = BeautifulSoup(html, 'html.parser')
    product_area = soup.find('div', class_='product_main')
    
    if not product_area:
        return None
        
    title = product_area.find('h1').text.strip()
    price_text = product_area.find('p', class_='price_color').text.strip()
    availability_text = product_area.find('p', class_='instock availability').text.strip()
    rating_text = product_area.find('p', class_='star-rating')['class'][1]
    
    desc_tag = soup.find('div', id='product_description')
    description = desc_tag.find_next_sibling('p').text.strip() if desc_tag else None
    
    # Normalization (Stage 4)
    clean_price = float(price_text.replace('£', ''))
    
    raw_record = {
        "title": title,
        "product_url": url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }
    
    return raw_record, clean_price

# --- Main Execution ---
def main():
    start_time = time.time()
    print("Starting the polite scraper...")
    
    # Tracking variables for run report (Stage 5)
    report = {
        "start_time": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": 0,
        "pages_fetched": 0,
        "cache_hits": 0,
        "valid_records": 0,
        "invalid_records": 0,
        "failed_pages": 0
    }
    
    all_books = {}
    errors = []
    
    # Step 1: Discover catalogue pages and book URLs (Stage 2)
    book_urls = []
    current_page_url = BASE_URL
    
    for i in range(1, MAX_PAGES + 1):
        cache_key = f"catalogue-page-{i}.html"
        html = fetch_page(current_page_url, cache_key)
        
        if not html:
            report["failed_pages"] += 1
            break
            
        soup = BeautifulSoup(html, 'html.parser')
        books = soup.find_all('article', class_='product_pod')
        
        for book in books:
            href = book.find('h3').find('a')['href']
            absolute_url = urljoin(current_page_url, href)
            book_urls.append((absolute_url, current_page_url))
            
        next_btn = soup.find('li', class_='next')
        if next_btn and i < MAX_PAGES:
            current_page_url = urljoin(current_page_url, next_btn.find('a')['href'])
        else:
            break

    # Remove duplicates (Stage 2)
    unique_book_urls = list(dict.fromkeys(book_urls))
    print(f"catalogue_pages={MAX_PAGES}, discovered={len(book_urls)}, unique_urls={len(unique_book_urls)}")

    # Step 2: Extract and Validate (Stage 3 & 4)
    for idx, (url, source_page) in enumerate(unique_book_urls, 1):
        cache_key = f"book-{idx}.html"
        html = fetch_page(url, cache_key)
        
        if not html:
            report["failed_pages"] += 1
            errors.append({"url": url, "error": "Failed to fetch"})
            continue
            
        try:
            raw_record, clean_price = extract_book_data(html, url, source_page)
            
            # Validate with Pydantic (Stage 4)
            validated_record = BookSchema(
                **raw_record, 
                price_gbp=clean_price
            )
            
            # Idempotency: use URL as identity (Stage 4)
            all_books[validated_record.product_url] = validated_record.model_dump()
            report["valid_records"] += 1
            
        except Exception as e:
            report["invalid_records"] += 1
            errors.append({"url": url, "error": str(e)})

    # Step 3: Output results (Stage 4 & 5)
    with open(os.path.join(OUTPUT_DIR, "books.json"), 'w', encoding='utf-8') as f:
        json.dump(list(all_books.values()), f, indent=2)
        
    with open(os.path.join(OUTPUT_DIR, "errors.json"), 'w', encoding='utf-8') as f:
        json.dump(errors, f, indent=2)

    report["duration_seconds"] = round(time.time() - start_time, 2)
    report["pages_fetched"] = len(unique_book_urls) + MAX_PAGES
    with open(os.path.join(OUTPUT_DIR, "run-report.json"), 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"Finished! Valid records: {report['valid_records']}, Failed: {report['failed_pages']}")
    print(f"Report written to {OUTPUT_DIR}/run-report.json")

if __name__ == "__main__":
    main()