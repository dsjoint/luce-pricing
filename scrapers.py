from playwright.sync_api import sync_playwright, Page
from datetime import datetime, timezone
from abc import ABC, abstractmethod
import json
import re
import logging

URL = "https://www.drf.com/live_odds/winodds/track/KEE/USA/6/D"

# Helper functions
def to_int_or_none(s):
    s = s.strip().replace(",", "")
    return int(s) if s.isdigit() else None

def write_jsonl(path: str, obj: dict):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


class baseScraper(ABC):
    source: str = "base"

    @abstractmethod
    def scrape_race(self, page: Page, url: str | None = None) -> dict:
        """Returns a snapshot dictionary containing race data for the given URL."""
        
    @abstractmethod
    def return_race_urls(self, page: Page, base_url: str | None = None) -> list[str]:
        """Returns a list of race URLs from the given page."""
    
    def scrape_all_races(self, page: Page, base_url: str | None = None) -> list[dict]:
        """Returns a list of snapshot dictionaries for all races found on the given page."""
        if base_url:
            page.goto(base_url, wait_until="domcontentloaded")
        
        race_urls = self.return_race_urls(page)
        snapshots = []
        for url in race_urls:
            snapshot = self.scrape_race(page, url)
            snapshots.append(snapshot)
        
        return snapshots


class DRFScraper(baseScraper):
    source: str = "drf"

    def scrape_race(self, page: Page, url: str | None = None) -> dict:
        if url:
            page.goto(url, wait_until="domcontentloaded")
        # else assume that the page is already at the correct URL

        # Wait for the main data table to be visible
        ul = page.locator("ul.dataTable.listBody:visible").first
        ul.wait_for(state="visible", timeout=10000)

        # Select the track name and race number
        track = page.locator("span.titleTrack").first
        number  = page.locator("span.titleTrack.raceNo").first

        # Process the entries
        track_text = track.inner_text().strip()
        track_only = track_text.split("\n")[0].strip()
        number_text = track_text.split("\n")[1].strip() if "\n" in track_text else ""

        # Select the number from number_text
        number_search = re.search(r'Race\s*[-–—]?\s*(\d+)', number_text, re.IGNORECASE)
        race_num = int(number_search.group(1)) if number_search else None

        # Dictionary for the jsonl entry
        snapshot = {
            "time_utc": datetime.now(timezone.utc).isoformat(), # set fixed timezone so it doesn't depend on local machine timezone
            "track": track_only,
            "race_number": race_num,
            "entries": []
        }

        # Process each row in the data table
        rows = ul.locator("li")
        for i in range(rows.count()):
            row = rows.nth(i).inner_text() # select the text in the i-th row

            parts = re.split(r"\s{2,}|\t+", row.strip()) # split by 2+ spaces or tabs as each row is spaced like a table

            if len(parts) == 7:
                entry = {
                    "horse_number": parts[0],
                    "horse": parts[1],
                    "jockey": parts[2],
                    "trainer": parts[3],
                    "win_pool":  to_int_or_none(parts[4]),
                    "place_pool":to_int_or_none(parts[5]),
                    "show_pool": to_int_or_none(parts[6]),
                }
                snapshot["entries"].append(entry)
            else:
                logging.warning(f"Unexpected number of parts ({len(parts)}) in row: {row}")
            
        return snapshot

    
    def return_race_urls(self, page: Page, base_url: str | None = None) -> list[str]:
        if base_url:
            page.goto(base_url, wait_until="domcontentloaded")
        # else assume that the page is already at the correct URL

        
        pass # finish implementation


class TwinSpiresScraper(baseScraper):
    source: str = "twinspires"

    def scrape_race(self, page: Page, url: str | None = None) -> dict:
        pass # finish implementation

    def return_race_urls(self, page: Page, base_url: str | None = None) -> list[str]:
        pass # finish implementation
    

