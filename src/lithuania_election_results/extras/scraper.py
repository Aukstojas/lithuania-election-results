# src/lithuania_election_results/extras/scraper.py

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging
import pandas as pd
import re

logger = logging.getLogger(__name__)

class Scraper:
    def __init__(self, static_page_root, apygarda_prefix, apygarda_location, apylinke_prefix):
        self.static_page_root = static_page_root
        self.apygarda_prefix = apygarda_prefix
        self.apygarda_location = apygarda_location
        self.apylinke_prefix = apylinke_prefix
        
    def get_links_containing_phrase_from_url(self, url, phrase = None, logger = False):
        """
        1. Access the site (start_url)
        2. Find all possible links (anchor tags)
        3. Filter by link_prefix (if provided)
        4. Return the filtered list of absolute URLs
        """

        if logger: print(f"Scraping {url}.")
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        # Grab all <a> tags
        links = soup.find_all("a")
        
        valid_urls = []
        for link in links:
            href = link.get("href")

            if not href:
                continue  # skip if no href attribute
            
            # If link_prefix is set, only keep URLs that start with it
            if phrase:
                if phrase in href:
                    valid_urls.append(href)
            else:
                # No prefix filtering, keep everything
                valid_urls.append(href)

        # Remove duplicates or do further post-processing if needed
        unique_urls = list(set(valid_urls))

        if logger: print(f"Found {len(unique_urls)} links containing prefix {phrase}")
        
        return unique_urls
    
    def remove_all_before_last_slash(self, list):
        for i, item in enumerate(list):
            list[i] = re.sub(r'^.*/', '', item)
        return list
    
    def get_apylinke_links(self):

        # Get all apygarda links:
        apygarda_links_srcUrl = self.get_links_containing_phrase_from_url(self.static_page_root + self.apygarda_location, self.apygarda_prefix, logger = True)
        
        # Trim links to leave only the correct location identifying ends
        apygarda_links = self.remove_all_before_last_slash(apygarda_links_srcUrl)
        
        all_apylinke_links = {}
        
        # Get all apylinke links:
        for apygarda in apygarda_links:
            
            apylinke_links_srcUrl = self.get_links_containing_phrase_from_url(self.static_page_root + apygarda, self.apylinke_prefix)
            apylinke_links = self.remove_all_before_last_slash(apylinke_links_srcUrl)

            all_apylinke_links[apygarda] = apylinke_links

        if True:
            len_apylinkes = 0
            
            for key in all_apylinke_links:
                len_apylinkes += len(all_apylinke_links[key])
                
            print(f"In total {len_apylinkes} apylinke links found")
            
        return all_apylinke_links

    def main(self):
        return self.get_apylinke_links()