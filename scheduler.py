from playwright.sync_api import sync_playwright
from scrapers import DRFScraper, TwinSpiresScraper
import json, time, argparse
from sampler import jsonl_to_dicts, snapshot_to_pools, run_analysis

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

def scrape_and_analyze(site: str, base_url: str, out: str, headless: bool):
    snapshot = None
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()

        if site == "drf":
            scraper = DRFScraper()
        elif site == "twinspires":
            scraper = TwinSpiresScraper()
        else:
            raise ValueError("unknown site")
        
        snapshot = scraper.scrape_race(page, base_url)
        write_jsonl(out, snapshot)
        print(f"Wrote {snapshot['track']} R{snapshot['race_number']} to {out}")
        browser.close()

    win_pool, show_pool = snapshot_to_pools(snapshot)
    print(f"Track: {snapshot['track']}, Race Number: {snapshot['race_number']}")
    run_analysis(win_pool, show_pool)


if __name__ == "__main__":
    BASE = "https://www.twinspires.com/bet/program/classic/santa-anita/sa/Thoroughbred/2/pools"

    # Twinspires requires headless=False to work properly
    scrape_and_analyze("twinspires", BASE, "live_odds_snapshots.jsonl", headless=False)