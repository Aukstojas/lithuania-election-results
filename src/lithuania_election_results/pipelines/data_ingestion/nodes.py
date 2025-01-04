

from lithuania_election_results.extras.scraper import Scraper

def scrape_node(static_page_root, apygarda_prefix, apygarda_location, apylinke_prefix,apylinke_pirm_prefix) -> dict:
    scraper = Scraper(static_page_root, apygarda_prefix, apygarda_location, apylinke_prefix,apylinke_pirm_prefix)
    return scraper.main()