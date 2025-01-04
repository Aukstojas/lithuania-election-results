# src/lithuania_election_results/extras/scraper.py

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging
import pandas as pd
import numpy as np
import re
from io import StringIO

logger = logging.getLogger(__name__)

class Scraper:
    def __init__(self, static_page_root, apygarda_prefix, apygarda_location, apylinke_prefix, apylinke_pirm_prefix):
        self.static_page_root = static_page_root
        self.apygarda_prefix = apygarda_prefix
        self.apygarda_location = apygarda_location
        self.apylinke_prefix = apylinke_prefix
        self.apylinke_pirm_prefix = apylinke_pirm_prefix
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)
    
    def contains_phrases(self, href: str, phrase) -> bool:
        """
        Check if the href contains all the specified phrases.

        Parameters:
            href (str): The string to search within.
            phrases (str or list of str): The phrase(s) to search for.

        Returns:
            bool: True if all phrases are found in href, False otherwise.
        """
        if isinstance(phrase, list):
            return all(p in href for p in phrase)
        elif isinstance(phrase, str):
            return phrase in href
        else:
            raise TypeError("phrases must be a string or a list of strings")
    
    def get_links_containing_phrase_from_url(self, url, phrase=None, log=False):
        """
        Fetches and filters links from a given URL containing a specific phrase.
        """
        if log:
            self.logger.info(f"Scraping {url}.")
        try:
            response = self.session.get(url)
            response.raise_for_status()
        except requests.RequestException as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return []

        soup = BeautifulSoup(response.text, "lxml")
        links = soup.find_all("a")
        
        valid_urls = []
        for link in links:
            href = link.get("href")
            if not href:
                continue  # Skip if no href attribute

            # Check if the href contains the specified phrase
            if phrase:
                if self.contains_phrases(href, phrase):
                    full_url = urljoin(self.static_page_root, href)
                    valid_urls.append(full_url)
            else:
                # No filtering by phrase
                full_url = urljoin(self.static_page_root, href)
                valid_urls.append(full_url)

        unique_urls = list(set(valid_urls))
        if log:
            self.logger.info(f"Found {len(unique_urls)} links containing phrase '{phrase}'")
        return unique_urls
    
    def remove_all_before_last_slash(self, list):
        """
        Removes all characters before the last slash in each string of the list.
        """
        for i, item in enumerate(list):
            list[i] = re.sub(r'^.*/', '', item)
        return list
    
    def get_apylinke_links(self):

        # Get all apygarda links:
        apygarda_links_srcUrl = self.get_links_containing_phrase_from_url(self.static_page_root + self.apygarda_location, self.apygarda_prefix, log = True)
        
        # Trim links to leave only the correct location identifying ends
        apygarda_links = self.remove_all_before_last_slash(apygarda_links_srcUrl)
        
        all_apylinke_links = {}
        
        # Get all apylinke links:
        for apygarda in apygarda_links:
            
            apylinke_links_srcUrl = self.get_links_containing_phrase_from_url(self.static_page_root + apygarda, self.apylinke_prefix)
            apylinke_links = self.remove_all_before_last_slash(apylinke_links_srcUrl)

            all_apylinke_links[apygarda] = apylinke_links

        total_apylinkes = 0
        for key in all_apylinke_links:
            total_apylinkes += len(all_apylinke_links[key])
                
        self.logger.info(f"In total {total_apylinkes} apylinke links found")
            
        return all_apylinke_links

    def extract_partydata_table(self, url) -> pd.DataFrame:
        """
        Extracts the 'partydata' table from the given URL and returns it as a pandas DataFrame.
        """

        try:
            response = self.session.get(url)
            response.raise_for_status()
        except requests.RequestException as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return pd.DataFrame()  # Return empty DataFrame on failure

        soup = BeautifulSoup(response.text, "lxml")
        
        # Step 1: Find the <h2>Balsavimo rezultatai</h2> heading
        target_heading = soup.find("h2", string=re.compile(r"Balsavimo rezultatai", re.IGNORECASE))
        if not target_heading:
            self.logger.warning(f"<h2>Balsavimo rezultatai</h2> heading not found at {url}")
            return None  # Return None if the heading is not found
        
        # Step 2: Find the next <table> with class 'partydata' after the heading
        # Using .find_next() to traverse the siblings after the heading
        partydata_table = target_heading.find_next("table", class_="partydata")
        if not partydata_table:
            self.logger.warning(f"No 'partydata' table found after the heading at {url}")
            return None  # Return None if the table is not found

        # Extract tables
        tables = pd.read_html(StringIO(str(partydata_table)))

        # Access the first table
        df = tables[0]

        return df  # Return the BeautifulSoup object representing the table
        
    def process_apylinke_partydata_table(self, df: pd.DataFrame) -> pd.DataFrame:
        df.columns = df.columns.droplevel(0)
        df = df.iloc[:, [0, 1, 5]]
        df.columns = ['VRK_nr', 'party_name', 'total_apylinke_votes']
        df = df[~df['VRK_nr'].isna()]
        df['VRK_nr'] = df['VRK_nr'].astype(int)
        #df = df.set_index(['VRK_nr']).sort_index()
        return df
    
    def get_pirm_votes_and_party_name(self, url: str, party_names: list):
        '''
        A function to access a site with individual votes from one apylinke with party name somehwere in the html and return that party name from a list and the individual votes
        url: site with individual votes from one apylinke with party name somehwere in the html
        party_names: a list with all possible party names
        '''
        try:
            response = self.session.get(url)
            response.raise_for_status()
        except requests.RequestException as e:
            self.logger.error(f"Error fetching {url}: {e}")
            raise LookupError(f'webpage {url} not found')
        
        soup = BeautifulSoup(response.text, "lxml")
        html_text = soup.get_text(separator=' ', strip=True)  # Extract all text from the HTML

        # Step 1: Find the party names present in the HTML
        found_parties = [party for party in party_names if party in html_text]

        # Step 2: Validate the number of parties found
        if len(found_parties) == 0:
            error_msg = f"No party names from the provided list were found in the HTML of {url}."
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        elif len(found_parties) > 1:
            error_msg = f"Multiple party names found in the HTML of {url}: {found_parties}. Expected only one."
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Exactly one party name found
        identified_party = found_parties[0]
        
        partydata_table = soup.find("table", class_="partydata")
        if not partydata_table:
            error_msg = f"No 'partydata' table found in the HTML of {url}."
            self.logger.error(error_msg)
            raise ValueError(error_msg)
         
        table = pd.read_html(StringIO(str(partydata_table)))[0]
        
        return table, identified_party


    def main(self):
        
        all_apylinke_links = self.get_apylinke_links()
        all_total_pirm_votes_by_apylinke = {}
        records = []
        
        total_apylinkes = 0
        for key in all_apylinke_links:
            total_apylinkes += len(all_apylinke_links[key])
        
        processed = 0
        log_step = 0.01
        
        for apygarda_link in list(all_apylinke_links.keys()):
            for apylinke_link in all_apylinke_links[apygarda_link]:
                
                # Get full apylinke results
                full_apylinke_result_table = self.extract_partydata_table(self.static_page_root + apylinke_link)
                apylinke_result_table = self.process_apylinke_partydata_table(full_apylinke_result_table)

                # Get all pirm links 
                pirm_links = self.get_links_containing_phrase_from_url(self.static_page_root + apylinke_link, phrase= self.apylinke_pirm_prefix)
                pirm_links = self.remove_all_before_last_slash(pirm_links)
                
                # Start pirm votes analysis
                final_apylinke_table = apylinke_result_table.copy()
                final_apylinke_table['total_pirm_votes'] = np.nan
                
                party_names = list(apylinke_result_table['party_name'])
                for pirm_link in pirm_links:
                    
                    pirm_df, party_name = self.get_pirm_votes_and_party_name(self.static_page_root + pirm_link, party_names)
                    
                    total_pirm_votes = pirm_df['Pirmumo balsai'].max().astype(int)
                    
                    # Check if total is correct
                    if total_pirm_votes != pirm_df['Pirmumo balsai'].sum() / 2:
                        raise ValueError("total number of votes calculated incorrectly for one apylinke one party")
                    
                    final_apylinke_table.loc[final_apylinke_table['party_name'] == party_name, 'total_pirm_votes'] = total_pirm_votes

                # Add data to records
                for _, row in final_apylinke_table.iterrows():
                    records.append({
                        'apygarda': apygarda_link,
                        'apylinke': apylinke_link,
                        'VRK_nr': row['VRK_nr'],
                        'party_name': row['party_name'],
                        'total_apylinke_votes': row['total_apylinke_votes'],
                        'total_pirm_votes': row['total_pirm_votes']
                    })

                # Update progress
                processed += 1
                percent = processed/total_apylinkes
                if percent > log_step:
                    self.logger.info(f"Progress: {percent*100:.2f}% of apylinkes processed.")
                    log_step += log_step
                if processed > 50: break
            if processed > 50: break
            
        df = pd.DataFrame(records)
        return df