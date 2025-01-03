

from lithuania_election_results.extras.scraper import Scraper

def scrape_node() -> dict:
    scraper = Scraper
    return scraper.access_site()