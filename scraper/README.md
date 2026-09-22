# The Polite Scraper (Assignment A9)

## Target Classification
- **Site:** Books to Scrape (https://books.toscrape.com/)
- **Why:** It is a public practice sandbox explicitly built for scraping practice.
- **Scope:** First 3 catalogue pages only (60 books total).
- **Robots Check:** `curl` returned 404 (No robots file found). 
- **Ethics:** I will not reuse this code on another site without checking its rules and terms first. I will use an official API when one exists, never bypass logins/paywalls, and collect only what I need.

## Setup & Run
```bash
uv run src/main.py