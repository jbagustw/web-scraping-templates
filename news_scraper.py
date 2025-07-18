# news_scraper.py
# Template untuk scraping website berita

from bs4 import BeautifulSoup
from base_scraper import WebScraper
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class NewsScraper(WebScraper):
    """
    Template untuk scraping website berita/media
    Mendukung berbagai format website berita
    """
    
    def __init__(self, delay_range=(1, 3)):
        super().__init__(delay_range)
    
    def scrape_news_homepage(self, base_url, categories=None):
        """
        Scrape berita dari halaman utama
        
        Args:
            base_url (str): URL website berita
            categories (list): List kategori berita (optional)
            
        Returns:
            list: List artikel berita
        """
        all_articles = []
        
        # Scrape homepage
        logger.info(f"Scraping homepage: {base_url}")
        homepage_articles = self._scrape_news_page(base_url)
        all_articles.extend(homepage_articles)
        
        # Scrape kategori jika ada
        if categories:
            for category in categories:
                category_url = f"{base_url.rstrip('/')}/{category}"
                logger.info(f"Scraping category: {category_url}")
                
                category_articles = self._scrape_news_page(category_url)
                
                # Tambah kategori info
                for article in category_articles:
                    article['category'] = category
                
                all_articles.extend(category_articles)
                self.random_delay()
        
        # Remove duplicates berdasarkan URL
        unique_articles = []
        seen_urls = set()
        
        for article in all_articles:
            if article['url'] not in seen_urls:
                unique_articles.append(article)
                seen_urls.add(article['url'])
        
        logger.info(f"Total unique articles: {len(unique_articles)}")
        return unique_articles
    
    def _scrape_news_page(self, url):
        """Scrape berita dari satu halaman"""
        response = self.get_page(url)
        if not response:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = []
        
        # CSS Selectors untuk article elements
        article_selectors = [
            'article',
            '.article',
            '.news-item',
            '.post',
            '.story',
            '[class*="article"]',
            '[class*="news"]',
            '[class*="story"]'
        ]
        
        article_elements = []
        for selector in article_selectors:
            elements = soup.select(selector)
            if elements and len(elements) >= 3:  # Minimal 3 artikel
                article_elements = elements
                logger.info(f"Using selector: {selector} ({len(elements)} articles)")
                break
        
        # Fallback: cari berdasarkan link pattern
        if not article_elements:
            # Cari link yang mengarah ke artikel
            link_patterns = [
                r'/article/',
                r'/news/',
                r'/story/',
                r'/post/',
                r'/\d{4}/\d{2}/',  # Pattern tanggal
            ]
            
            for pattern in link_patterns:
                links = soup.find_all('a', href=re.compile(pattern))
                if links and len(links) >= 5:
                    # Ambil parent element dari link
                    article_elements = [link.find_parent() for link in links[:20]]
                    article_elements = [elem for elem in article_elements if elem]
                    logger.info(f"Using link pattern: {pattern} ({len(article_elements)} elements)")
                    break
        
        if not article_elements:
            logger.warning("No article elements found")
            return articles
        
        # Extract data dari setiap artikel
        for element in article_elements:
            try:
                article_data = self._extract_news_article(element, url)
                if article_data and article_data['title'] != 'N/A':
                    articles.append(article_data)
            except Exception as e:
                logger.error(f"Error extracting article: {e}")
                continue
        
        return articles
    
    def _extract_news_article(self, element, base_url):
        """Extract data dari satu article element"""
        try:
            # Title/Headline
            title = None
            title_selectors = [
                'h1', 'h2', 'h3',
                '.title', '.headline', '.article-title',
                '.news-title', '.story-title',
                '[class*="title"]', '[class*="headline"]'
            ]
            
            for selector in title_selectors:
                title_elem = element.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if title and len(title) > 10:  # Filter title terlalu pendek
                        break
            
            # URL artikel
            url = None
            link_elem = element.select_one('a')
            if link_elem and link_elem.get('href'):
                url = self.get_absolute_url(base_url, link_elem['href'])
            
            # Summary/Excerpt
            summary = None
            summary_selectors = [
                '.summary', '.excerpt', '.description',
                '.lead', '.intro', '.teaser',
                'p'  # Fallback ke paragraph pertama
            ]
            
            for selector in summary_selectors:
                summary_elem = element.select_one(selector)
                if summary_elem:
                    summary_text = summary_elem.get_text(strip=True)
                    if summary_text and len(summary_text) > 30:
                        summary = summary_text
                        break
            
            # Author
            author = None
            author_selectors = [
                '.author', '.byline', '.writer',
                '.journalist', '.reporter',
                '[class*="author"]', '[class*="byline"]'
            ]
            
            for selector in author_selectors:
                author_elem = element.select_one(selector)
                if author_elem:
                    author = author_elem.get_text(strip=True)
                    # Clean author text
                    author = re.sub(r'^(by|oleh)\s+', '', author, flags=re.IGNORECASE)
                    if author:
                        break
            
            # Date/Time
            publish_date = None
            date_selectors = [
                'time', '.date', '.timestamp',
                '.published', '.publish-date',
                '[datetime]', '[class*="date"]'
            ]
            
            for selector in date_selectors:
                date_elem = element.select_one(selector)
                if date_elem:
                    # Coba ambil dari attribute datetime
                    publish_date = (date_elem.get('datetime') or 
                                  date_elem.get('data-time') or 
                                  date_elem.get_text(strip=True))
                    if publish_date:
                        break
            
            # Image
            image = None
            img_elem = element.select_one('img')
            if img_elem:
                image_src = (img_elem.get('src') or 
                           img_elem.get('data-src') or 
                           img_elem.get('data-lazy-src'))
                if image_src:
                    image = self.get_absolute_url(base_url, image_src)
            
            # Tags/Categories
            tags = []
            tag_selectors = [
                '.tags a', '.categories a',
                '.tag-list a', '.category-list a',
                '[class*="tag"] a', '[class*="category"] a'
            ]
            
            for selector in tag_selectors:
                tag_elements = element.select(selector)
                if tag_elements:
                    tags = [tag.get_text(strip=True) for tag in tag_elements]
                    break
            
            return {
                'title': title or 'N/A',
                'url': url or 'N/A',
                'summary': summary or 'N/A',
                'author': author or 'N/A',
                'publish_date': publish_date or 'N/A',
                'image': image or 'N/A',
                'tags': tags,
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error extracting news article: {e}")
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
            title_selectors = [
                'h1',
                '.article-title', '.news-title',
                '.post-title', '.story-title',
                '[class*="title"]'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break
            
            # Content/Body
            content = None
            content_selectors = [
                '.article-content', '.article-body',
                '.news-content', '.news-body',
                '.post-content', '.story-content',
                '.content', '.body',
                '[class*="content"]', '[class*="body"]'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Remove ads, related articles, etc.
                    for unwanted in content_elem.select('.ad, .advertisement, .related, .share, script, style'):
                        unwanted.decompose()
                    
                    content = content_elem.get_text(strip=True)
                    if content and len(content) > 200:  # Pastikan konten substansial
                        break
            
            # Meta information
            author = None
            publish_date = None
            
            # Author
            author_selectors = [
                '.author', '.byline', '.writer',
                '[class*="author"]', '[rel="author"]'
            ]
            for selector in author_selectors:
                author_elem = soup.select_one(selector)
                if author_elem:
                    author = author_elem.get_text(strip=True)
                    author = re.sub(r'^(by|oleh)\s+', '', author, flags=re.IGNORECASE)
                    break
            
            # Date
            date_elem = soup.select_one('time, .date, .published, [datetime]')
            if date_elem:
                publish_date = (date_elem.get('datetime') or 
                              date_elem.get('content') or 
                              date_elem.get_text(strip=True))
            
            # Meta tags (untuk SEO info)
            meta_description = None
            meta_keywords = None
            
            meta_desc = soup.select_one('meta[name="description"]')
            if meta_desc:
                meta_description = meta_desc.get('content')
            
            meta_key = soup.select_one('meta[name="keywords"]')
            if meta_key:
                meta_keywords = meta_key.get('content')
            
            # Images dalam artikel
            content_images = []
            if content_elem:
                img_elements = content_elem.select('img')
                for img in img_elements:
                    img_src = img.get('src') or img.get('data-src')
                    if img_src:
                        content_images.append(self.get_absolute_url(article_url, img_src))
            
            return {
                'url': article_url,
                'title': title or 'N/A',
                'content': content or 'N/A',
                'author': author or 'N/A',
                'publish_date': publish_date or 'N/A',
                'meta_description': meta_description or 'N/A',
                'meta_keywords': meta_keywords or 'N/A',
                'content_images': content_images,
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error scraping full article {article_url}: {e}")
            return None
    
    def scrape_rss_feed(self, rss_url):
        """
        Scrape dari RSS Feed (jika tersedia)
        
        Args:
            rss_url (str): URL RSS feed
            
        Returns:
            list: Articles from RSS
        """
        try:
            import feedparser
            
            feed = feedparser.parse(rss_url)
            articles = []
            
            for entry in feed.entries:
                article = {
                    'title': entry.get('title', 'N/A'),
                    'url': entry.get('link', 'N/A'),
                    'summary': entry.get('summary', 'N/A'),
                    'author': entry.get('author', 'N/A'),
                    'publish_date': entry.get('published', 'N/A'),
                    'tags': [tag.term for tag in entry.get('tags', [])],
                    'source': 'RSS',
                    'scraped_at': datetime.now().isoformat()
                }
                articles.append(article)
            
            logger.info(f"Scraped {len(articles)} articles from RSS")
            return articles
            
        except ImportError:
            logger.error("feedparser not installed. Install with: pip install feedparser")
            return []
        except Exception as e:
            logger.error(f"Error scraping RSS feed: {e}")
            return []
    
    def scrape_news_search(self, base_url, query, max_pages=3):
        """
        Search berita berdasarkan query
        
        Args:
            base_url (str): Base URL website
            query (str): Search query
            max_pages (int): Maksimal halaman hasil
            
        Returns:
            list: Search results
        """
        articles = []
        
        for page in range(1, max_pages + 1):
            # Format search URL - sesuaikan dengan website
            search_params = {
                'q': query,
                'search': query,
                'query': query,
                'page': page
            }
            
            # Coba berbagai format search URL
            search_urls = [
                f"{base_url}/search?q={query}&page={page}",
                f"{base_url}/search?search={query}&page={page}",
                f"{base_url}/?s={query}&paged={page}",  # WordPress format
            ]
            
            success = False
            for search_url in search_urls:
                logger.info(f"Trying search URL: {search_url}")
                
                response = self.get_page(search_url)
                if response and response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    page_articles = self._extract_search_results(soup, base_url, query)
                    
                    if page_articles:
                        articles.extend(page_articles)
                        success = True
                        break
            
            if not success:
                logger.warning(f"No results found for page {page}")
                break
            
            self.random_delay()
        
        return articles
    
    def _extract_search_results(self, soup, base_url, query):
        """Extract artikel dari hasil search"""
        # Search result selectors
        result_selectors = [
            '.search-result',
            '.search-item',
            '.result',
            '.search-article'
        ]
        
        search_elements = []
        for selector in result_selectors:
            elements = soup.select(selector)
            if elements:
                search_elements = elements
                break
        
        # Fallback ke article elements biasa
        if not search_elements:
            search_elements = soup.select('article, .article, .news-item')
        
        results = []
        for element in search_elements:
            try:
                article_data = self._extract_news_article(element, base_url)
                if article_data:
                    article_data['search_query'] = query
                    results.append(article_data)
            except Exception as e:
                logger.error(f"Error extracting search result: {e}")
        
        return results
    
    def analyze_news_sentiment(self, articles):
        """
        Analisis sentiment berita (requires additional libraries)
        
        Args:
            articles (list): List artikel
            
        Returns:
            list: Articles dengan sentiment score
        """
        try:
            from textblob import TextBlob
            
            for article in articles:
                # Gabungkan title dan summary untuk analisis
                text = f"{article.get('title', '')} {article.get('summary', '')}"
                
                if text.strip():
                    blob = TextBlob(text)
                    article['sentiment_polarity'] = blob.sentiment.polarity
                    article['sentiment_subjectivity'] = blob.sentiment.subjectivity
                    
                    # Kategorisasi sentiment
                    if blob.sentiment.polarity > 0.1:
                        article['sentiment_label'] = 'positive'
                    elif blob.sentiment.polarity < -0.1:
                        article['sentiment_label'] = 'negative'
                    else:
                        article['sentiment_label'] = 'neutral'
            
            logger.info("Sentiment analysis completed")
            return articles
            
        except ImportError:
            logger.warning("TextBlob not installed. Install with: pip install textblob")
            return articles
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return articles

# Example usage
if __name__ == "__main__":
    scraper = NewsScraper(delay_range=(1, 2))
    
    print("=== NEWS SCRAPER EXAMPLE ===")
    
    # Contoh scraping website berita
    news_url = "https://example-news.com"
    categories = ['politik', 'ekonomi', 'teknologi']  # Sesuaikan dengan website
    
    print(f"Target: {news_url}")
    print("SESUAIKAN CSS selector dan kategori dengan website target!")
    
    # Scrape homepage dan kategori
    # articles = scraper.scrape_news_homepage(news_url, categories)
    # print(f"Found {len(articles)} articles")
    
    # Save results
    # scraper.save_to_csv(articles, "news_articles.csv")
    # scraper.save_to_json(articles, "news_articles.json")
    
    # Scrape full article content
    # if articles:
    #     first_article = articles[0]
    #     if first_article['url'] != 'N/A':
    #         full_content = scraper.scrape_full_article(first_article['url'])
    #         if full_content:
    #             print(f"Full article: {full_content['title']}")
    
    # Search berita
    # search_results = scraper.scrape_news_search(news_url, "teknologi AI", max_pages=2)
    # print(f"Search results: {len(search_results)}")
    
    # Sentiment analysis (optional)
    # articles_with_sentiment = scraper.analyze_news_sentiment(articles)
    
    print("News scraper template ready!")
    scraper.close_session()