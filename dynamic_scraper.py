# dynamic_scraper.py
# Template untuk scraping konten dinamis dengan Selenium

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import time
import logging
import chromedriver_autoinstaller

logger = logging.getLogger(__name__)

class DynamicScraper:
    """
    Scraper untuk konten dinamis yang memerlukan JavaScript
    Menggunakan Selenium WebDriver
    """
    
    def __init__(self, headless=True, wait_timeout=10):
        """
        Initialize dynamic scraper
        
        Args:
            headless (bool): Jalankan browser tanpa GUI
            wait_timeout (int): Timeout untuk WebDriverWait
        """
        self.headless = headless
        self.wait_timeout = wait_timeout
        self.driver = None
        self.wait = None
        
        # Setup Chrome options
        self.chrome_options = Options()
        if headless:
            self.chrome_options.add_argument('--headless')
        
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--window-size=1920,1080')
        self.chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        # Disable images untuk loading lebih cepat (optional)
        # prefs = {"profile.managed_default_content_settings.images": 2}
        # self.chrome_options.add_experimental_option("prefs", prefs)
    
    def start_driver(self):
        """Start Chrome WebDriver"""
        try:
            # Auto-install chromedriver jika belum ada
            chromedriver_autoinstaller.install()
            
            self.driver = webdriver.Chrome(options=self.chrome_options)
            self.wait = WebDriverWait(self.driver, self.wait_timeout)
            
            logger.info("Chrome WebDriver started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start WebDriver: {e}")
            return False
    
    def close_driver(self):
        """Close WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.wait = None
            logger.info("WebDriver closed")
    
    def get_page(self, url):
        """
        Navigate to URL
        
        Args:
            url (str): Target URL
            
        Returns:
            bool: Success status
        """
        if not self.driver:
            if not self.start_driver():
                return False
        
        try:
            self.driver.get(url)
            logger.info(f"Navigated to: {url}")
            return True
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            return False
    
    def wait_for_element(self, selector, by=By.CSS_SELECTOR):
        """
        Wait for element to be present
        
        Args:
            selector (str): Element selector
            by: Selenium By method
            
        Returns:
            WebElement or None
        """
        try:
            element = self.wait.until(
                EC.presence_of_element_located((by, selector))
            )
            return element
        except Exception as e:
            logger.error(f"Element not found: {selector} - {e}")
            return None
    
    def wait_for_elements(self, selector, by=By.CSS_SELECTOR):
        """
        Wait for multiple elements
        
        Args:
            selector (str): Element selector
            by: Selenium By method
            
        Returns:
            List of WebElements
        """
        try:
            elements = self.wait.until(
                EC.presence_of_all_elements_located((by, selector))
            )
            return elements
        except Exception as e:
            logger.error(f"Elements not found: {selector} - {e}")
            return []
    
    def scroll_to_bottom(self, pause_time=1):
        """
        Scroll ke bawah halaman untuk trigger lazy loading
        
        Args:
            pause_time (float): Jeda antar scroll
        """
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            while True:
                # Scroll ke bawah
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Tunggu loading
                time.sleep(pause_time)
                
                # Cek apakah ada konten baru
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                
            logger.info("Finished scrolling to bottom")
            
        except Exception as e:
            logger.error(f"Error scrolling: {e}")
    
    def infinite_scroll(self, max_scrolls=10, pause_time=2):
        """
        Infinite scroll untuk social media atau feed
        
        Args:
            max_scrolls (int): Maksimal jumlah scroll
            pause_time (float): Jeda antar scroll
        """
        try:
            for i in range(max_scrolls):
                # Scroll ke bawah
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                logger.info(f"Scroll {i+1}/{max_scrolls}")
                time.sleep(pause_time)
                
                # Check jika ada "Load More" button
                try:
                    load_more = self.driver.find_element(By.CSS_SELECTOR, 
                                                        'button[class*="load"], button[class*="more"]')
                    if load_more.is_displayed():
                        self.driver.execute_script("arguments[0].click();", load_more)
                        time.sleep(pause_time)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Error in infinite scroll: {e}")
    
    def click_element(self, selector, by=By.CSS_SELECTOR):
        """
        Click element dengan handling
        
        Args:
            selector (str): Element selector
            by: Selenium By method
            
        Returns:
            bool: Success status
        """
        try:
            element = self.wait_for_element(selector, by)
            if element:
                # Coba click biasa dulu
                try:
                    element.click()
                except:
                    # Jika gagal, gunakan JavaScript click
                    self.driver.execute_script("arguments[0].click();", element)
                
                logger.info(f"Clicked element: {selector}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error clicking element {selector}: {e}")
            return False
    
    def fill_form(self, field_selector, value, submit_selector=None):
        """
        Isi form dan submit
        
        Args:
            field_selector (str): Selector input field
            value (str): Value to input
            submit_selector (str): Submit button selector (optional)
            
        Returns:
            bool: Success status
        """
        try:
            # Wait for input field
            input_field = self.wait_for_element(field_selector)
            if not input_field:
                return False
            
            # Clear dan isi field
            input_field.clear()
            input_field.send_keys(value)
            
            # Submit jika ada selector submit
            if submit_selector:
                submit_btn = self.wait_for_element(submit_selector)
                if submit_btn:
                    submit_btn.click()
                else:
                    # Alternatif: tekan Enter
                    input_field.send_keys(Keys.RETURN)
            
            logger.info(f"Form filled: {field_selector} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"Error filling form: {e}")
            return False
    
    def scrape_spa_content(self, url, content_selector, wait_selector=None):
        """
        Scrape Single Page Application content
        
        Args:
            url (str): Target URL
            content_selector (str): Selector untuk content items
            wait_selector (str): Selector untuk element yang ditunggu load
            
        Returns:
            list: Scraped data
        """
        if not self.get_page(url):
            return []
        
        try:
            # Wait for specific element if provided
            if wait_selector:
                self.wait_for_element(wait_selector)
            else:
                # Default wait for content
                self.wait_for_element(content_selector)
            
            # Scroll untuk trigger lazy loading
            self.scroll_to_bottom()
            
            # Get page source dan parse dengan BeautifulSoup
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Extract content
            items = []
            content_elements = soup.select(content_selector)
            
            logger.info(f"Found {len(content_elements)} content items")
            
            for element in content_elements:
                item_data = self._extract_spa_item(element)
                if item_data:
                    items.append(item_data)
            
            return items
            
        except Exception as e:
            logger.error(f"Error scraping SPA content: {e}")
            return []
    
    def _extract_spa_item(self, element):
        """
        Extract data dari satu item SPA
        SESUAIKAN DENGAN STRUKTUR KONTEN TARGET!
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            dict: Item data
        """
        try:
            # Title
            title = None
            title_selectors = ['h1', 'h2', 'h3', '.title', '.heading']
            for selector in title_selectors:
                title_elem = element.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break
            
            # Content/Description
            content = None
            content_selectors = ['p', '.description', '.content', '.text']
            for selector in content_selectors:
                content_elem = element.select_one(selector)
                if content_elem:
                    content = content_elem.get_text(strip=True)
                    if len(content) > 20:  # Pastikan bukan content kosong
                        break
            
            # Link
            link = None
            link_elem = element.select_one('a')
            if link_elem and link_elem.get('href'):
                link = link_elem['href']
            
            # Image
            image = None
            img_elem = element.select_one('img')
            if img_elem:
                image = img_elem.get('src') or img_elem.get('data-src')
            
            # Date/Time
            date = None
            date_elem = element.select_one('time, .date, .timestamp')
            if date_elem:
                date = date_elem.get('datetime') or date_elem.get_text(strip=True)
            
            return {
                'title': title or 'N/A',
                'content': content or 'N/A',
                'link': link or 'N/A',
                'image': image or 'N/A',
                'date': date or 'N/A'
            }
            
        except Exception as e:
            logger.error(f"Error extracting SPA item: {e}")
            return None
    
    def scrape_social_media_posts(self, url, max_posts=50):
        """
        Template untuk scraping social media posts
        
        Args:
            url (str): Social media URL
            max_posts (int): Maksimal posts to scrape
            
        Returns:
            list: Posts data
        """
        if not self.get_page(url):
            return []
        
        try:
            # Wait for posts to load
            self.wait_for_element('[data-testid="tweet"], .post, article')
            
            # Infinite scroll untuk load more posts
            self.infinite_scroll(max_scrolls=10, pause_time=3)
            
            # Parse posts
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Social media post selectors (adjust sesuai platform)
            post_selectors = [
                '[data-testid="tweet"]',  # Twitter
                '.post',                   # Generic
                'article',                 # Instagram/Facebook
                '.feed-item'              # LinkedIn
            ]
            
            posts = []
            for selector in post_selectors:
                post_elements = soup.select(selector)
                if post_elements:
                    logger.info(f"Found {len(post_elements)} posts with selector: {selector}")
                    
                    for post_elem in post_elements[:max_posts]:
                        post_data = self._extract_social_post(post_elem)
                        if post_data:
                            posts.append(post_data)
                    break
            
            return posts
            
        except Exception as e:
            logger.error(f"Error scraping social media: {e}")
            return []
    
    def _extract_social_post(self, post_element):
        """Extract data dari social media post"""
        try:
            # Author/Username
            author = None
            author_selectors = ['.username', '.author', '[data-testid="User-Name"]']
            for selector in author_selectors:
                author_elem = post_element.select_one(selector)
                if author_elem:
                    author = author_elem.get_text(strip=True)
                    break
            
            # Post text
            text = None
            text_selectors = ['.tweet-text', '.post-text', '[data-testid="tweetText"]']
            for selector in text_selectors:
                text_elem = post_element.select_one(selector)
                if text_elem:
                    text = text_elem.get_text(strip=True)
                    break
            
            # Timestamp
            timestamp = None
            time_elem = post_element.select_one('time')
            if time_elem:
                timestamp = time_elem.get('datetime') or time_elem.get_text(strip=True)
            
            # Engagement metrics
            likes = self._extract_metric(post_element, ['[data-testid="like"]', '.like-count'])
            retweets = self._extract_metric(post_element, ['[data-testid="retweet"]', '.retweet-count'])
            replies = self._extract_metric(post_element, ['[data-testid="reply"]', '.reply-count'])
            
            return {
                'author': author or 'N/A',
                'text': text or 'N/A',
                'timestamp': timestamp or 'N/A',
                'likes': likes or 0,
                'retweets': retweets or 0,
                'replies': replies or 0
            }
            
        except Exception as e:
            logger.error(f"Error extracting social post: {e}")
            return None
    
    def _extract_metric(self, element, selectors):
        """Extract engagement metrics"""
        for selector in selectors:
            metric_elem = element.select_one(selector)
            if metric_elem:
                metric_text = metric_elem.get_text(strip=True)
                # Extract number from text
                import re
                numbers = re.findall(r'\d+', metric_text)
                if numbers:
                    return int(numbers[0])
        return 0

# Example usage
if __name__ == "__main__":
    scraper = DynamicScraper(headless=False)  # Set False untuk melihat browser
    
    print("=== DYNAMIC CONTENT SCRAPER EXAMPLE ===")
    print("Untuk website yang menggunakan JavaScript")
    
    try:
        # Example 1: Scrape SPA content
        # url = "https://example-spa.com"
        # content = scraper.scrape_spa_content(url, '.content-item', '.loading-complete')
        # print(f"Found {len(content)} items")
        
        # Example 2: Social media scraping
        # social_url = "https://twitter.com/username"
        # posts = scraper.scrape_social_media_posts(social_url, max_posts=20)
        # print(f"Found {len(posts)} posts")
        
        print("Dynamic scraper template ready!")
        print("SESUAIKAN selector dengan website target!")
        
    finally:
        scraper.close_driver()