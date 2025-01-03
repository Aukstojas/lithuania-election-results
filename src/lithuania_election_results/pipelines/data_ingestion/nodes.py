

from lithuania_election_results.extras.scraper import Scraper

def scrape_node(url) -> dict:
    scraper = Scraper(url)
    return scraper.access_site()