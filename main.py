# main.py
# Main script untuk menjalankan berbagai scraper

import argparse
import sys
import logging
from datetime import datetime

# Import scraper classes
from blog_scraper import BlogScraper
from ecommerce_scraper import EcommerceScraper
from dynamic_scraper import DynamicScraper
from news_scraper import NewsScraper
from api_scraper import APIScraper
from utils import (
    check_robots_txt, get_website_info, analyze_page_structure,
    generate_selectors, validate_selectors, estimate_scraping_time,
    create_filename, is_scraping_allowed
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraping.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ScrapingManager:
    """
    Manager class untuk mengelola berbagai jenis scraping
    """
    
    def __init__(self):
        self.scrapers = {
            'blog': BlogScraper,
            'ecommerce': EcommerceScraper,
            'news': NewsScraper,
            'api': APIScraper,
            'dynamic': DynamicScraper
        }
    
    def run_scraping(self, scraper_type, url, **kwargs):
        """
        Run scraping berdasarkan type
        
        Args:
            scraper_type (str): Type of scraper
            url (str): Target URL
            **kwargs: Additional arguments
            
        Returns:
            list: Scraped data
        """
        if scraper_type not in self.scrapers:
            logger.error(f"Unknown scraper type: {scraper_type}")
            return []
        
        # Pre-scraping checks
        if not self._pre_scraping_checks(url):
            return []
        
        # Initialize scraper
        scraper_class = self.scrapers[scraper_type]
        
        try:
            if scraper_type == 'dynamic':
                scraper = scraper_class(headless=kwargs.get('headless', True))
            else:
                scraper = scraper_class(delay_range=kwargs.get('delay_range', (1, 3)))
            
            # Run appropriate scraping method
            data = self._execute_scraping(scraper, scraper_type, url, **kwargs)
            
            # Cleanup
            if hasattr(scraper, 'close_driver'):
                scraper.close_driver()
            elif hasattr(scraper, 'close_session'):
                scraper.close_session()
            
            return data
            
        except Exception as e:
            logger.error(f"Error in scraping: {e}")
            return []
    
    def _pre_scraping_checks(self, url):
        """Pre-scraping validation checks"""
        logger.info(f"Starting pre-scraping checks for: {url}")
        
        # Check robots.txt
        if not is_scraping_allowed(url):
            logger.warning("Scraping may not be allowed according to robots.txt")
            response = input("Continue anyway? (y/n): ")
            if response.lower() != 'y':
                return False
        
        # Get website info
        website_info = get_website_info(url)
        if 'error' in website_info:
            logger.error("Cannot access website")
            return False
        
        logger.info("Pre-scraping checks passed")
        return True
    
    def _execute_scraping(self, scraper, scraper_type, url, **kwargs):
        """Execute scraping berdasarkan type"""
        data = []
        
        try:
            if scraper_type == 'blog':
                data = scraper.scrape_article_list(
                    url,
                    max_pages=kwargs.get('max_pages', 5)
                )
                
            elif scraper_type == 'ecommerce':
                keyword = kwargs.get('keyword', 'product')
                data = scraper.search_products(
                    url,
                    keyword,
                    max_pages=kwargs.get('max_pages', 3)
                )
                
            elif scraper_type == 'news':
                categories = kwargs.get('categories', None)
                data = scraper.scrape_news_homepage(url, categories)
                
            elif scraper_type == 'api':
                if kwargs.get('paginated', False):
                    data = scraper.scrape_paginated_api(
                        url,
                        max_pages=kwargs.get('max_pages', 10)
                    )
                else:
                    result = scraper.scrape_json_api(url)
                    data = [result] if result else []
                    
            elif scraper_type == 'dynamic':
                content_selector = kwargs.get('content_selector', '.content-item')
                wait_selector = kwargs.get('wait_selector', None)
                data = scraper.scrape_spa_content(url, content_selector, wait_selector)
            
            logger.info(f"Scraped {len(data)} items")
            return data
            
        except Exception as e:
            logger.error(f"Error executing {scraper_type} scraping: {e}")
            return []

def main():
    """Main function dengan command line interface"""
    parser = argparse.ArgumentParser(description='Web Scraping Tool')
    
    parser.add_argument('--type', '-t', 
                       choices=['blog', 'ecommerce', 'news', 'api', 'dynamic'],
                       required=True,
                       help='Type of scraper to use')
    
    parser.add_argument('--url', '-u',
                       required=True,
                       help='Target URL to scrape')
    
    parser.add_argument('--output', '-o',
                       help='Output filename (without extension)')
    
    parser.add_argument('--format', '-f',
                       choices=['csv', 'json'],
                       default='csv',
                       help='Output format (default: csv)')
    
    parser.add_argument('--max-pages', '-p',
                       type=int,
                       default=5,
                       help='Maximum pages to scrape (default: 5)')
    
    parser.add_argument('--delay',
                       type=float,
                       nargs=2,
                       default=[1, 3],
                       help='Delay range in seconds (default: 1 3)')
    
    parser.add_argument('--keyword', '-k',
                       help='Search keyword (for ecommerce scraper)')
    
    parser.add_argument('--categories',
                       nargs='+',
                       help='News categories to scrape')
    
    parser.add_argument('--content-selector',
                       help='CSS selector for content (dynamic scraper)')
    
    parser.add_argument('--wait-selector',
                       help='CSS selector to wait for (dynamic scraper)')
    
    parser.add_argument('--headless',
                       action='store_true',
                       help='Run browser in headless mode (dynamic scraper)')
    
    parser.add_argument('--analyze',
                       action='store_true',
                       help='Analyze page structure before scraping')
    
    parser.add_argument('--check-robots',
                       action='store_true',
                       help='Check robots.txt only')
    
    parser.add_argument('--estimate-time',
                       action='store_true',
                       help='Estimate scraping time')
    
    args = parser.parse_args()
    
    # Quick actions
    if args.check_robots:
        check_robots_txt(args.url)
        return
    
    if args.analyze:
        analyze_page_structure(args.url)
        return
    
    if args.estimate_time:
        estimate = estimate_scraping_time(args.max_pages, tuple(args.delay))
        print(f"Estimated time: {estimate['estimated_time_human']}")
        return
    
    # Initialize scraping manager
    manager = ScrapingManager()
    
    # Prepare scraping parameters
    scraping_params = {
        'max_pages': args.max_pages,
        'delay_range': tuple(args.delay),
        'keyword': args.keyword,
        'categories': args.categories,
        'content_selector': args.content_selector,
        'wait_selector': args.wait_selector,
        'headless': args.headless
    }
    
    # Remove None values
    scraping_params = {k: v for k, v in scraping_params.items() if v is not None}
    
    print(f"Starting {args.type} scraping...")
    print(f"Target: {args.url}")
    print(f"Parameters: {scraping_params}")
    
    # Run scraping
    data = manager.run_scraping(args.type, args.url, **scraping_params)
    
    if not data:
        print("No data scraped!")
        return
    
    # Save results
    if args.output:
        filename = f"{args.output}.{args.format}"
    else:
        base_name = f"{args.type}_scraping"
        filename = create_filename(base_name, args.format)
    
    # Save based on format
    if args.format == 'json':
        import json
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    else:
        import pandas as pd
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False, encoding='utf-8')
    
    print(f"Data saved to: {filename}")
    print(f"Total items: {len(data)}")

def interactive_mode():
    """Interactive mode untuk pemula"""
    print("=== WEB SCRAPING TOOL - INTERACTIVE MODE ===")
    print()
    
    # Get basic info
    url = input("Enter website URL: ").strip()
    if not url:
        print("URL is required!")
        return
    
    print("\nSelect scraper type:")
    print("1. Blog/Article scraper")
    print("2. E-commerce scraper")
    print("3. News scraper")
    print("4. API scraper")
    print("5. Dynamic content scraper")
    
    choice = input("Choose (1-5): ").strip()
    
    scraper_types = {
        '1': 'blog',
        '2': 'ecommerce',
        '3': 'news',
        '4': 'api',
        '5': 'dynamic'
    }
    
    if choice not in scraper_types:
        print("Invalid choice!")
        return
    
    scraper_type = scraper_types[choice]
    
    # Check robots.txt
    print(f"\nChecking robots.txt for {url}...")
    robots_info = check_robots_txt(url)
    
    if not robots_info.get('can_fetch', True):
        cont = input("Scraping may not be allowed. Continue? (y/n): ")
        if cont.lower() != 'y':
            return
    
    # Get additional parameters
    max_pages = input("Max pages to scrape (default: 5): ").strip()
    max_pages = int(max_pages) if max_pages.isdigit() else 5
    
    output_format = input("Output format (csv/json, default: csv): ").strip()
    output_format = output_format if output_format in ['csv', 'json'] else 'csv'
    
    # Type-specific parameters
    scraping_params = {'max_pages': max_pages}
    
    if scraper_type == 'ecommerce':
        keyword = input("Search keyword: ").strip()
        if keyword:
            scraping_params['keyword'] = keyword
    
    elif scraper_type == 'news':
        categories = input("Categories (comma-separated, optional): ").strip()
        if categories:
            scraping_params['categories'] = [c.strip() for c in categories.split(',')]
    
    elif scraper_type == 'dynamic':
        content_selector = input("Content CSS selector (default: .content-item): ").strip()
        scraping_params['content_selector'] = content_selector or '.content-item'
        
        headless = input("Run in headless mode? (y/n, default: y): ").strip()
        scraping_params['headless'] = headless.lower() != 'n'
    
    # Run scraping
    manager = ScrapingManager()
    
    print(f"\nStarting {scraper_type} scraping...")
    data = manager.run_scraping(scraper_type, url, **scraping_params)
    
    if not data:
        print("No data scraped!")
        return
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{scraper_type}_scraping_{timestamp}.{output_format}"
    
    if output_format == 'json':
        import json
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    else:
        import pandas as pd
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False, encoding='utf-8')
    
    print(f"\nScraping completed!")
    print(f"Data saved to: {filename}")
    print(f"Total items: {len(data)}")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No arguments, run interactive mode
        interactive_mode()
    else:
        # Command line mode
        main()