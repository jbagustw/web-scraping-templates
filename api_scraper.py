# api_scraper.py
# Template untuk scraping website yang menggunakan API/AJAX

from base_scraper import WebScraper
import json
import logging

logger = logging.getLogger(__name__)

class APIScraper(WebScraper):
    """
    Template untuk scraping website yang menggunakan internal API
    Berguna untuk website modern yang load data via AJAX/Fetch
    """
    
    def __init__(self, delay_range=(1, 3)):
        super().__init__(delay_range)
        
        # Headers khusus untuk API requests
        api_headers = {
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
        self.session.headers.update(api_headers)
    
    def discover_api_endpoints(self, base_url):
        """
        Coba temukan API endpoints umum
        GUNAKAN NETWORK TAB di DevTools untuk menemukan endpoint yang tepat!
        
        Args:
            base_url (str): Base URL website
            
        Returns:
            dict: Status setiap endpoint
        """
        common_endpoints = [
            '/api/posts',
            '/api/articles',
            '/api/products',
            '/api/search',
            '/api/data',
            '/wp-json/wp/v2/posts',  # WordPress REST API
            '/api/v1/',
            '/api/v2/',
            '/graphql',  # GraphQL endpoint
        ]
        
        endpoint_status = {}
        
        for endpoint in common_endpoints:
            full_url = f"{base_url.rstrip('/')}{endpoint}"
            
            try:
                response = self.session.head(full_url, timeout=10)
                endpoint_status[endpoint] = {
                    'status_code': response.status_code,
                    'accessible': response.status_code < 400,
                    'content_type': response.headers.get('content-type', 'N/A')
                }
                
                if response.status_code < 400:
                    logger.info(f"Found accessible endpoint: {full_url}")
                
            except Exception as e:
                endpoint_status[endpoint] = {
                    'status_code': None,
                    'accessible': False,
                    'error': str(e)
                }
            
            self.random_delay()
        
        return endpoint_status
    
    def scrape_json_api(self, api_url, params=None, method='GET', data=None):
        """
        Scrape data dari JSON API
        
        Args:
            api_url (str): URL API endpoint
            params (dict): Query parameters
            method (str): HTTP method (GET/POST)
            data (dict): POST data untuk request
            
        Returns:
            dict: Response data
        """
        try:
            if method.upper() == 'POST':
                response = self.post_request(api_url, json_data=data, params=params)
            else:
                response = self.get_page(api_url, params=params)
            
            if not response:
                return None
            
            # Parse JSON response
            try:
                json_data = response.json()
                logger.info(f"Successfully parsed JSON from: {api_url}")
                return json_data
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON response from {api_url}: {e}")
                # Coba parse sebagai text jika bukan JSON
                return {'raw_content': response.text}
                
        except Exception as e:
            logger.error(f"Error fetching API data from {api_url}: {e}")
            return None
    
    def scrape_paginated_api(self, api_url, max_pages=10, page_param='page', per_page_param='per_page', per_page=20):
        """
        Scrape API dengan pagination
        
        Args:
            api_url (str): Base API URL
            max_pages (int): Maksimal halaman
            page_param (str): Parameter nama halaman
            per_page_param (str): Parameter jumlah item per halaman
            per_page (int): Jumlah item per halaman
            
        Returns:
            list: Semua data dari semua halaman
        """
        all_data = []
        
        for page in range(1, max_pages + 1):
            params = {
                page_param: page,
                per_page_param: per_page
            }
            
            logger.info(f"Fetching page {page} from API: {api_url}")
            
            response_data = self.scrape_json_api(api_url, params=params)
            
            if not response_data:
                logger.warning(f"No data received for page {page}")
                break
            
            # Extract data dari response (struktur bisa bervariasi)
            page_items = self._extract_items_from_api_response(response_data)
            
            if not page_items:
                logger.info(f"No more items found at page {page}, stopping...")
                break
            
            all_data.extend(page_items)
            logger.info(f"Page {page}: Found {len(page_items)} items")
            
            # Check jika ini halaman terakhir
            if self._is_last_page(response_data, page_items, per_page):
                logger.info("Reached last page")
                break
            
            self.random_delay()
        
        logger.info(f"Total items collected: {len(all_data)}")
        return all_data
    
    def _extract_items_from_api_response(self, response_data):
        """
        Extract items dari API response
        SESUAIKAN dengan struktur response API target!
        
        Args:
            response_data (dict): Raw API response
            
        Returns:
            list: Extracted items
        """
        items = []
        
        # Common API response structures
        possible_keys = [
            'data',           # Standard REST API
            'items',          # Common format
            'results',        # Search API format
            'posts',          # Blog/CMS API
            'articles',       # News API
            'products',       # E-commerce API
            'content',        # Generic content
            'entries',        # Feed format
        ]
        
        # Try to find data in nested structure
        for key in possible_keys:
            if key in response_data:
                data = response_data[key]
                
                if isinstance(data, list):
                    items = data
                    logger.info(f"Found data in '{key}' field ({len(items)} items)")
                    break
                elif isinstance(data, dict) and 'items' in data:
                    items = data['items']
                    logger.info(f"Found data in '{key}.items' field ({len(items)} items)")
                    break
        
        # If no standard structure found, return the whole response if it's a list
        if not items and isinstance(response_data, list):
            items = response_data
            logger.info(f"Using root array ({len(items)} items)")
        
        return items
    
    def _is_last_page(self, response_data, page_items, expected_per_page):
        """
        Check apakah ini halaman terakhir
        
        Args:
            response_data (dict): API response
            page_items (list): Items di halaman ini
            expected_per_page (int): Expected items per halaman
            
        Returns:
            bool: True jika halaman terakhir
        """
        # Method 1: Check jumlah items kurang dari expected
        if len(page_items) < expected_per_page:
            return True
        
        # Method 2: Check pagination metadata
        pagination_keys = ['pagination', 'meta', 'page_info']
        
        for key in pagination_keys:
            if key in response_data:
                pagination = response_data[key]
                
                # Check various pagination indicators
                if isinstance(pagination, dict):
                    # Has next page indicator
                    if 'has_next' in pagination:
                        return not pagination['has_next']
                    
                    # Total pages
                    if 'total_pages' in pagination and 'current_page' in pagination:
                        return pagination['current_page'] >= pagination['total_pages']
                    
                    # Next page URL
                    if 'next_page' in pagination:
                        return pagination['next_page'] is None
        
        return False
    
    def scrape_wordpress_api(self, wp_site_url, post_type='posts', max_posts=100):
        """
        Scrape WordPress site menggunakan REST API
        
        Args:
            wp_site_url (str): URL WordPress site
            post_type (str): Jenis post (posts, pages, etc.)
            max_posts (int): Maksimal post yang di-scrape
            
        Returns:
            list: WordPress posts data
        """
        api_url = f"{wp_site_url.rstrip('/')}/wp-json/wp/v2/{post_type}"
        
        # Test if WordPress API is available
        test_response = self.get_page(api_url + "?per_page=1")
        if not test_response or test_response.status_code != 200:
            logger.error("WordPress API not accessible")
            return []
        
        # Calculate pages needed
        per_page = 100  # WordPress default max
        max_pages = (max_posts // per_page) + 1
        
        all_posts = []
        
        for page in range(1, max_pages + 1):
            params = {
                'per_page': min(per_page, max_posts - len(all_posts)),
                'page': page
            }
            
            posts_data = self.scrape_json_api(api_url, params=params)
            
            if not posts_data or not isinstance(posts_data, list):
                break
            
            # Process WordPress posts
            for post in posts_data:
                processed_post = self._process_wordpress_post(post)
                all_posts.append(processed_post)
            
            logger.info(f"Page {page}: {len(posts_data)} posts")
            
            if len(posts_data) < per_page or len(all_posts) >= max_posts:
                break
            
            self.random_delay()
        
        return all_posts[:max_posts]
    
    def _process_wordpress_post(self, post_data):
        """Process WordPress post data"""
        try:
            return {
                'id': post_data.get('id'),
                'title': post_data.get('title', {}).get('rendered', 'N/A'),
                'content': post_data.get('content', {}).get('rendered', 'N/A'),
                'excerpt': post_data.get('excerpt', {}).get('rendered', 'N/A'),
                'author_id': post_data.get('author'),
                'date': post_data.get('date'),
                'modified': post_data.get('modified'),
                'slug': post_data.get('slug'),
                'status': post_data.get('status'),
                'url': post_data.get('link'),
                'categories': post_data.get('categories', []),
                'tags': post_data.get('tags', []),
                'featured_media': post_data.get('featured_media')
            }
        except Exception as e:
            logger.error(f"Error processing WordPress post: {e}")
            return post_data
    
    def scrape_graphql_api(self, graphql_url, query, variables=None):
        """
        Scrape GraphQL API
        
        Args:
            graphql_url (str): GraphQL endpoint URL
            query (str): GraphQL query string
            variables (dict): Query variables
            
        Returns:
            dict: GraphQL response data
        """
        payload = {
            'query': query,
            'variables': variables or {}
        }
        
        try:
            response = self.post_request(graphql_url, json_data=payload)
            
            if not response:
                return None
            
            graphql_data = response.json()
            
            # Check for GraphQL errors
            if 'errors' in graphql_data:
                logger.error(f"GraphQL errors: {graphql_data['errors']}")
                return None
            
            return graphql_data.get('data')
            
        except Exception as e:
            logger.error(f"Error with GraphQL request: {e}")
            return None
    
    def search_api_endpoints(self, base_url, search_term):
        """
        Search data menggunakan API endpoints
        
        Args:
            base_url (str): Base URL
            search_term (str): Search query
            
        Returns:
            list: Search results
        """
        search_endpoints = [
            f"/api/search?q={search_term}",
            f"/api/search?query={search_term}",
            f"/search.json?q={search_term}",
            f"/wp-json/wp/v2/search?search={search_term}",
        ]
        
        for endpoint in search_endpoints:
            full_url = f"{base_url.rstrip('/')}{endpoint}"
            
            logger.info(f"Trying search endpoint: {full_url}")
            
            search_data = self.scrape_json_api(full_url)
            
            if search_data:
                # Extract results
                results = self._extract_items_from_api_response(search_data)
                if results:
                    logger.info(f"Found {len(results)} search results")
                    return results
        
        logger.warning("No search results found from any endpoint")
        return []

# Example usage
if __name__ == "__main__":
    scraper = APIScraper(delay_range=(1, 2))
    
    print("=== API SCRAPER EXAMPLE ===")
    print("Untuk website yang menggunakan API/AJAX")
    
    base_url = "https://example-site.com"
    
    # Discover API endpoints
    print("Discovering API endpoints...")
    # endpoints = scraper.discover_api_endpoints(base_url)
    # for endpoint, status in endpoints.items():
    #     if status['accessible']:
    #         print(f"✓ {endpoint}: {status['status_code']}")
    
    # Scrape API data
    # api_url = f"{base_url}/api/posts"
    # data = scraper.scrape_paginated_api(api_url, max_pages=5)
    # scraper.save_to_json(data, "api_data.json")
    
    # WordPress API example
    # wp_posts = scraper.scrape_wordpress_api("https://example-wp-site.com")
    # scraper.save_to_csv(wp_posts, "wordpress_posts.csv")
    
    print("API scraper template ready!")
    print("GUNAKAN Network tab di DevTools untuk menemukan API endpoints!")
    
    scraper.close_session()