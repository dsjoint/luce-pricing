from playwright.sync_api import sync_playwright, Page
from datetime import datetime, timezone
from abc import ABC, abstractmethod
import json
import re
import logging

# Helper functions
def to_int_or_none(s):
    s = s.strip().replace(",", "")
    return int(s) if s.isdigit() else None

def money_to_int_or_none(s: str | None):
    if not s:
        return None
    s = s.strip().replace("$", "").replace(",", "")
    return int(s) if s.isdigit() else None

def clean(t): 
    return (t or "").strip().replace("\n", " ")

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

        # Select the track name and race number
        track = page.locator("span.titleTrack").first
        number  = page.locator("span.titleTrack.raceNo").first

        # Process the entries
        track_text = track.inner_text(timeout=5000).strip()
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
            row = rows.nth(i).inner_text(timeout=5000) # select the text in the i-th row

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
            
        snapshot["entries"].sort(key=lambda x: x["horse_number"])

        return snapshot

    
    def return_race_urls(self, page: Page, base_url: str | None = None) -> list[str]:
        if base_url:
            page.goto(base_url, wait_until="domcontentloaded")
        # else assume that the page is already at the correct URL

        
        return [] # finish implementation


class TwinSpiresScraper(baseScraper): # twinspires needs headless=False to work properly
    source: str = "twinspires"

    def scrape_race(self, page: Page, url: str | None = None) -> dict:
        url_head = ""
        if url:
            last_path = url.split("/")[-1] # get the last path component
            url_head = url.rsplit("/", 1)[0] # get the base URL without the last path component
            if last_path != "pools":
                url = url_head + "/pools"

            page.goto(url, wait_until="domcontentloaded")
        else:
            logging.error("URL must be provided for TwinSpiresScraper.scrape_race")
            return {}
        
        # Select the track name and race TODO: change to less hacky way
        race_num = to_int_or_none(url_head.split("/")[-1])
        track_only = clean(url_head.split("/")[-4])

        # Dictionary for the jsonl entry
        snapshot = {
            "time_utc": datetime.now(timezone.utc).isoformat(), # set fixed timezone so it doesn't depend on local machine timezone
            "track": track_only,
            "race_number": race_num,
            "entries": []
        }

        # Wait for the main data table to be visible
        ul = page.locator("ul.pools-basic:visible").first ### TODO: this selection should be done in a cleaner way as below

        raw_data = ul.inner_text(timeout=5000)

        entries = []
        lines = [line.strip() for line in raw_data.split("\n") if line.strip()]
        i = 0
        while i < len(lines):
            if i + 4 >= len(lines):
                logging.warning(f"Unexpected partial block while processing line {i}: {lines[i:]}")
                break

            horse_number = to_int_or_none(lines[i])
            win_odds = lines[i + 1]
            win_pool = money_to_int_or_none(lines[i + 2])
            place_pool = money_to_int_or_none(lines[i + 3])
            show_pool = money_to_int_or_none(lines[i + 4])
            i += 5

            entry = {
                "horse_number": horse_number,
                "horse": None, # to be entered below
                "jockey": None, # to be entered below
                "trainer": None, # to be entered below
                "win_pool":  win_pool,
                "place_pool":place_pool,
                "show_pool": show_pool,
            }
            entries.append(entry)
        
        entries.sort(key=lambda x: x["horse_number"])
        
        page.goto(url_head + "/advanced", wait_until="load")

        container = page.locator("div.program-container").first
        page.wait_for_selector("div.program-container", state="attached", timeout=5000)

        cards = container.locator("div.program-container cdux-program-entry")
        page.wait_for_selector("div.program-container cdux-program-entry", state="attached", timeout=5000)
        total_cards = cards.count()

        for i in range(total_cards):
            card = cards.nth(i)

            # code for checking if scratched
            row = card.locator("div.entry").first
            classes = (row.get_attribute("class") or "").split()
            scratched = "is-scratched" in classes
            # horse number
            number  = to_int_or_none(card.locator(".program-number").first.text_content())

            if number != i+1:
                logging.warning(f"Mismatch in horse number: expected {i+1}, got {number}")

            horse = clean(card.locator(".entry-runner-name").first.text_content())
            jockey = clean(card.locator(".entry_col_jockey .entry-jockey-name").first.text_content())
            trainer = clean(card.locator(".entry_col_trainer .entry-trainer-name").first.text_content())

            entries[i]["horse"] = horse
            entries[i]["jockey"] = jockey
            entries[i]["trainer"] = trainer
        
        snapshot["entries"] = entries

        return snapshot



    def return_race_urls(self, page: Page, base_url: str | None = None) -> list[str]:
        return [] # finish implementation
    

# For testing
if __name__ == "__main__":
    URL = "https://www.twinspires.com/bet/program/classic/keeneland/kee/Thoroughbred/5/advanced"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        scraper = TwinSpiresScraper()
        snapshot = scraper.scrape_race(page, URL)

        write_jsonl("live_odds_snapshots.jsonl", snapshot)

        browser.close()