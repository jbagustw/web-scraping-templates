# base_scraper.py
# Base class untuk semua web scraper

import requests
import pandas as pd
import time
import random
import json
import logging
from urllib.parse import urljoin

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WebScraper:
    """
    Base class untuk web scraping
    Menyediakan fungsi-fungsi dasar yang dibutuhkan semua scraper
    """
    
    def __init__(self, delay_range=(1, 3)):
        """
        Initialize scraper
        Args:
            delay_range (tuple): Range untuk random delay antar request (min, max) dalam detik
        """
        self.session = requests.Session()
        self.delay_range = delay_range
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        self.session.headers.update(self.headers)
    
    def get_page(self, url, **kwargs):
        """
        Safe GET request dengan error handling
        Args:
            url (str): URL yang akan di-request
            **kwargs: Additional arguments untuk requests.get()
        Returns:
            requests.Response object atau None jika error
        """
        try:
            response = self.session.get(url, timeout=30, **kwargs)
            response.raise_for_status()
            logger.info(f"Successfully fetched: {url}")
            return response
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def post_request(self, url, data=None, json_data=None, **kwargs):
        """
        Safe POST request dengan error handling
        Args:
            url (str): URL untuk POST request
            data: Form data
            json_data: JSON data
            **kwargs: Additional arguments
        Returns:
            requests.Response object atau None jika error
        """
        try:
            if json_data:
                response = self.session.post(url, json=json_data, timeout=30, **kwargs)
            else:
                response = self.session.post(url, data=data, timeout=30, **kwargs)
            response.raise_for_status()
            logger.info(f"Successfully posted to: {url}")
            return response
        except requests.RequestException as e:
            logger.error(f"Error posting to {url}: {e}")
            return None
    
    def random_delay(self):
        """Random delay untuk menghindari rate limiting"""
        delay = random.uniform(*self.delay_range)
        logger.info(f"Waiting {delay:.2f} seconds...")
        time.sleep(delay)
    
    def save_to_csv(self, data, filename, index=False):
        """
        Save data to CSV file
        Args:
            data (list): List of dictionaries
            filename (str): Output filename
            index (bool): Whether to include index
        """
        try:
            df = pd.DataFrame(data)
            df.to_csv(filename, index=index, encoding='utf-8')
            logger.info(f"Data saved to {filename} ({len(data)} records)")
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
    
    def save_to_json(self, data, filename, indent=2):
        """
        Save data to JSON file
        Args:
            data: Data to save
            filename (str): Output filename
            indent (int): JSON indentation
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=indent)
            logger.info(f"Data saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
    
    def load_from_json(self, filename):
        """
        Load data from JSON file
        Args:
            filename (str): Input filename
        Returns:
            Loaded data atau None jika error
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Data loaded from {filename}")
            return data
        except Exception as e:
            logger.error(f"Error loading from JSON: {e}")
            return None
    
    def set_custom_headers(self, headers):
        """
        Set custom headers untuk session
        Args:
            headers (dict): Custom headers
        """
        self.session.headers.update(headers)
        logger.info("Custom headers updated")
    
    def add_cookies(self, cookies):
        """
        Add cookies to session
        Args:
            cookies (dict): Cookies to add
        """
        self.session.cookies.update(cookies)
        logger.info("Cookies added to session")
    
    def get_absolute_url(self, base_url, relative_url):
        """
        Convert relative URL to absolute URL
        Args:
            base_url (str): Base URL
            relative_url (str): Relative URL
        Returns:
            str: Absolute URL
        """
        return urljoin(base_url, relative_url)
    
    def close_session(self):
        """Close the requests session"""
        self.session.close()
        logger.info("Session closed")