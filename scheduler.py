from playwright.sync_api import sync_playwright
from scrapers import DRFScraper, TwinSpiresScraper
import json, time, argparse


def write_jsonl(path: str, obj: dict):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def run_once(site: str, base_url: str, out: str, headless: bool):
    """Run the scraper once for the given site (drf, twinspires) and base (where all races are listed) URL, writing output to the specified file."""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()

        if site == "drf":
            scraper = DRFScraper()
        elif site == "twinspires":
            scraper = TwinSpiresScraper()
        else:
            raise ValueError("unknown site")

        # Scrape ALL races on that card
        snaps = scraper.scrape_all_races(page, base_url)
        for s in snaps:
            write_jsonl(out, s)
            print(f"Wrote {s['source']} {s['track']} R{s['race_number']} to {out}")

        browser.close()

if __name__ == "__main__":
    BASE = ""

    run_once("drf", BASE, "live_odds_snapshots.jsonl", headless=True)