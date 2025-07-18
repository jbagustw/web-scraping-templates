# blog_scraper.py
# Template untuk scraping website blog/artikel

from bs4 import BeautifulSoup
from base_scraper import WebScraper
import logging

logger = logging.getLogger(__name__)

class BlogScraper(WebScraper):
    """
    Template untuk scraping website blog dan artikel
    Sesuaikan CSS selector dengan struktur website target
    """
    
    def __init__(self, delay_range=(1, 3)):
        super().__init__(delay_range)
        
    def scrape_article_list(self, base_url, max_pages=5, page_param='page'):
        """
        Scrape daftar artikel dari halaman utama blog
        
        Args:
            base_url (str): URL dasar blog
            max_pages (int): Maksimal halaman yang akan di-scrape
            page_param (str): Parameter untuk pagination (contoh: 'page', 'p')
            
        Returns:
            list: List berisi data artikel
        """
        articles = []
        
        for page in range(1, max_pages + 1):
            # Format URL pagination - sesuaikan dengan website target
            if '?' in base_url:
                url = f"{base_url}&{page_param}={page}"
            else:
                url = f"{base_url}?{page_param}={page}"
                
            logger.info(f"Scraping page {page}: {url}")
            
            response = self.get_page(url)
            if not response:
                logger.warning(f"Failed to fetch page {page}, skipping...")
                continue
                
            soup = BeautifulSoup(response.content, 'html.parser')
            page_articles = self._extract_articles_from_page(soup, base_url)
            
            if not page_articles:
                logger.warning(f"No articles found on page {page}, stopping...")
                break
                
            articles.extend(page_articles)
            logger.info(f"Found {len(page_articles)} articles on page {page}")
            
            # Delay antar halaman
            if page < max_pages:
                self.random_delay()
        
        logger.info(f"Total articles scraped: {len(articles)}")
        return articles
    
    def _extract_articles_from_page(self, soup, base_url):
        """
        Extract artikel dari satu halaman
        SESUAIKAN CSS SELECTOR DENGAN WEBSITE TARGET!
        
        Args:
            soup: BeautifulSoup object
            base_url (str): Base URL untuk membuat absolute link
            
        Returns:
            list: List artikel dari halaman tersebut
        """
        articles = []
        
        # CSS Selector - SESUAIKAN DENGAN WEBSITE TARGET
        # Contoh selector umum yang sering digunakan:
        possible_selectors = [
            'article',                    # HTML5 semantic
            '.post',                      # Class post
            '.article',                   # Class article  
            '.entry',                     # Class entry
            '[class*="post"]',           # Any class containing "post"
            '[class*="article"]',        # Any class containing "article"
        ]
        
        article_elements = []
        for selector in possible_selectors:
            elements = soup.select(selector)
            if elements:
                article_elements = elements
                logger.info(f"Using selector: {selector} ({len(elements)} elements found)")
                break
        
        if not article_elements:
            logger.warning("No article elements found with common selectors")
            return articles
        
        for article_elem in article_elements:
            try:
                article_data = self._extract_article_data(article_elem, base_url)
                if article_data:
                    articles.append(article_data)
            except Exception as e:
                logger.error(f"Error extracting article: {e}")
                continue
        
        return articles
    
    def _extract_article_data(self, article_elem, base_url):
        """
        Extract data dari satu element artikel
        
        Args:
            article_elem: BeautifulSoup element
            base_url (str): Base URL
            
        Returns:
            dict: Data artikel atau None jika gagal
        """
        try:
            # Title - coba berbagai selector
            title = None
            title_selectors = ['h1', 'h2', 'h3', '.title', '.post-title', '.entry-title']
            for selector in title_selectors:
                title_elem = article_elem.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break
            
            # Link - cari link utama artikel
            link = None
            link_elem = article_elem.select_one('a')
            if link_elem and link_elem.get('href'):
                link = self.get_absolute_url(base_url, link_elem['href'])
            
            # Excerpt/Summary
            excerpt = None
            excerpt_selectors = ['.excerpt', '.summary', '.post-excerpt', 'p']
            for selector in excerpt_selectors:
                excerpt_elem = article_elem.select_one(selector)
                if excerpt_elem:
                    excerpt = excerpt_elem.get_text(strip=True)
                    if len(excerpt) > 50:  # Pastikan bukan excerpt kosong
                        break
            
            # Date
            date = None
            date_selectors = ['time', '.date', '.post-date', '.published']
            for selector in date_selectors:
                date_elem = article_elem.select_one(selector)
                if date_elem:
                    # Coba ambil dari attribute datetime dulu
                    date = date_elem.get('datetime') or date_elem.get_text(strip=True)
                    break
            
            # Author
            author = None
            author_selectors = ['.author', '.post-author', '.by-author', '.writer']
            for selector in author_selectors:
                author_elem = article_elem.select_one(selector)
                if author_elem:
                    author = author_elem.get_text(strip=True)
                    break
            
            # Image
            image = None
            image_elem = article_elem.select_one('img')
            if image_elem:
                image_src = image_elem.get('src') or image_elem.get('data-src')
                if image_src:
                    image = self.get_absolute_url(base_url, image_src)
            
            # Tags/Categories
            tags = []
            tag_selectors = ['.tags a', '.categories a', '.post-tags a']
            for selector in tag_selectors:
                tag_elements = article_elem.select(selector)
                if tag_elements:
                    tags = [tag.get_text(strip=True) for tag in tag_elements]
                    break
            
            return {
                'title': title or 'N/A',
                'link': link or 'N/A',
                'excerpt': excerpt or 'N/A',
                'date': date or 'N/A',
                'author': author or 'N/A',
                'image': image or 'N/A',
                'tags': tags
            }
            
        except Exception as e:
            logger.error(f"Error extracting article data: {e}")
            return None
    
    def scrape_full_article(self, article_url):
        """
        Scrape konten lengkap dari satu artikel
        
        Args:
            article_url (str): URL artikel
            
        Returns:
            dict: Data artikel lengkap
        """
        response = self.get_page(article_url)
        if not response:
            return None
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        try:
            # Title
            title = None
            title_selectors = ['h1', '.post-title', '.entry-title', '.article-title']
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break
            
            # Content
            content = None
            content_selectors = ['.post-content', '.entry-content', '.article-content', '.content']
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem.get_text(strip=True)
                    break
            
            # Meta information
            date = None
            author = None
            
            # Date
            date_elem = soup.select_one('time, .date, .post-date')
            if date_elem:
                date = date_elem.get('datetime') or date_elem.get_text(strip=True)
            
            # Author
            author_elem = soup.select_one('.author, .post-author, .by-author')
            if author_elem:
                author = author_elem.get_text(strip=True)
            
            return {
                'url': article_url,
                'title': title or 'N/A',
                'content': content or 'N/A',
                'date': date or 'N/A',
                'author': author or 'N/A'
            }
            
        except Exception as e:
            logger.error(f"Error scraping full article {article_url}: {e}")
            return None

# Example usage
if __name__ == "__main__":
    # Contoh penggunaan
    scraper = BlogScraper(delay_range=(1, 2))
    
    # Ganti dengan URL blog yang ingin di-scrape
    blog_url = "https://example-blog.com"
    
    print("=== BLOG SCRAPER EXAMPLE ===")
    print(f"Target: {blog_url}")
    print("IMPORTANT: Sesuaikan CSS selector dengan website target!")
    
    # Scrape daftar artikel
    # articles = scraper.scrape_article_list(blog_url, max_pages=3)
    # scraper.save_to_csv(articles, "blog_articles.csv")
    # scraper.save_to_json(articles, "blog_articles.json")
    
    # Scrape artikel lengkap
    # if articles:
    #     first_article_url = articles[0]['link']
    #     full_article = scraper.scrape_full_article(first_article_url)
    #     if full_article:
    #         print(f"Full article title: {full_article['title']}")
    
    print("Blog scraper template ready!")
    print("Jangan lupa:")
    print("1. Sesuaikan CSS selector dengan website target")
    print("2. Cek robots.txt terlebih dahulu")
    print("3. Gunakan delay yang reasonable")