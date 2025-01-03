# src/lithuania_election_results/extras/scraper.py

import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

ROOT_URL = "https://www.vrk.lt/2024-seimo/rezultatai?srcUrl=/rinkimai/1544/1/2150/rezultatai/lt/rezultataiDaugmVrt.html"

class Scraper:
    def __init__(self, root_url = ROOT_URL):
        self.root_url = root_url
        
    def access_site(self) -> dict:
        logger.info(f"Scraping {self.root_url} ...")
        
        response = requests.get(self.root_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "lxml")

        # Suppose there's a table with id "results_table"
        table = soup.find("table", {"id": "results_table"})

        data = {}
        
        data['raw'] = table
        
        return data