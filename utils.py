# utils.py
# Utility functions untuk web scraping

import requests
import time
import random
import re
import json
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import logging

logger = logging.getLogger(__name__)

def check_robots_txt(base_url, user_agent='*'):
    """
    Check robots.txt file untuk memastikan scraping diizinkan
    
    Args:
        base_url (str): Base URL website
        user_agent (str): User agent string
        
    Returns:
        dict: Robots.txt information
    """
    robots_url = urljoin(base_url, '/robots.txt')
    
    try:
        response = requests.get(robots_url, timeout=10)
        
        if response.status_code == 200:
            print(f"Robots.txt found at: {robots_url}")
            print("-" * 50)
            print(response.text)
            print("-" * 50)
            
            # Parse robots.txt
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            return {
                'exists': True,
                'content': response.text,
                'can_fetch': rp.can_fetch(user_agent, base_url),
                'crawl_delay': rp.crawl_delay(user_agent),
                'request_rate': rp.request_rate(user_agent)
            }
        else:
            print(f"No robots.txt found (Status: {response.status_code})")
            return {'exists': False, 'can_fetch': True}
            
    except Exception as e:
        logger.error(f"Error checking robots.txt: {e}")
        return {'exists': False, 'can_fetch': True, 'error': str(e)}

def get_website_info(url):
    """
    Get basic information tentang website
    
    Args:
        url (str): Website URL
        
    Returns:
        dict: Website information
    """
    try:
        response = requests.head(url, timeout=10)
        
        info = {
            'url': url,
            'status_code': response.status_code,
            'server': response.headers.get('server', 'N/A'),
            'content_type': response.headers.get('content-type', 'N/A'),
            'content_length': response.headers.get('content-length', 'N/A'),
            'last_modified': response.headers.get('last-modified', 'N/A'),
            'cache_control': response.headers.get('cache-control', 'N/A'),
            'x_powered_by': response.headers.get('x-powered-by', 'N/A')
        }
        
        print("Website Information:")
        print("-" * 30)
        for key, value in info.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
        
        return info
        
    except Exception as e:
        logger.error(f"Error getting website info: {e}")
        return {'error': str(e)}

def analyze_page_structure(url, max_elements=20):
    """
    Analyze struktur halaman untuk membantu identifikasi selector
    
    Args:
        url (str): Page URL
        max_elements (int): Max elements to analyze per type
        
    Returns:
        dict: Page structure analysis
    """
    try:
        from bs4 import BeautifulSoup
        
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        analysis = {
            'title': soup.title.string if soup.title else 'N/A',
            'meta_description': '',
            'headings': {},
            'common_classes': [],
            'common_ids': [],
            'forms': [],
            'links_count': len(soup.find_all('a')),
            'images_count': len(soup.find_all('img')),
            'scripts_count': len(soup.find_all('script')),
        }
        
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            analysis['meta_description'] = meta_desc.get('content', '')
        
        # Headings analysis
        for i in range(1, 7):
            headings = soup.find_all(f'h{i}')
            if headings:
                analysis['headings'][f'h{i}'] = [h.get_text(strip=True)[:100] for h in headings[:5]]
        
        # Common classes
        all_elements = soup.find_all(True)
        class_counter = {}
        id_counter = {}
        
        for element in all_elements:
            # Count classes
            classes = element.get('class', [])
            for cls in classes:
                class_counter[cls] = class_counter.get(cls, 0) + 1
            
            # Count IDs
            element_id = element.get('id')
            if element_id:
                id_counter[element_id] = id_counter.get(element_id, 0) + 1
        
        # Sort by frequency
        analysis['common_classes'] = sorted(class_counter.items(), key=lambda x: x[1], reverse=True)[:max_elements]
        analysis['common_ids'] = sorted(id_counter.items(), key=lambda x: x[1], reverse=True)[:max_elements]
        
        # Forms analysis
        forms = soup.find_all('form')
        for form in forms[:5]:
            form_info = {
                'action': form.get('action', 'N/A'),
                'method': form.get('method', 'GET'),
                'inputs': []
            }
            
            inputs = form.find_all(['input', 'textarea', 'select'])
            for inp in inputs:
                form_info['inputs'].append({
                    'type': inp.get('type', inp.name),
                    'name': inp.get('name', 'N/A'),
                    'id': inp.get('id', 'N/A'),
                    'placeholder': inp.get('placeholder', 'N/A')
                })
            
            analysis['forms'].append(form_info)
        
        print("Page Structure Analysis:")
        print("-" * 40)
        print(f"Title: {analysis['title']}")
        print(f"Links: {analysis['links_count']}")
        print(f"Images: {analysis['images_count']}")
        print(f"Scripts: {analysis['scripts_count']}")
        
        print("\nMost Common Classes:")
        for cls, count in analysis['common_classes'][:10]:
            print(f"  .{cls}: {count} elements")
        
        print("\nHeadings Structure:")
        for heading, texts in analysis['headings'].items():
            print(f"  {heading.upper()}: {len(texts)} found")
            for text in texts[:3]:
                print(f"    - {text}")
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing page structure: {e}")
        return {'error': str(e)}

def generate_selectors(url, target_content="article"):
    """
    Generate possible CSS selectors untuk target content
    
    Args:
        url (str): Page URL
        target_content (str): Type of content to target
        
    Returns:
        list: Suggested selectors
    """
    selectors = {
        'article': [
            'article', '.article', '.post', '.entry',
            '.news-item', '.story', '.content-item',
            '[class*="article"]', '[class*="post"]'
        ],
        'product': [
            '.product', '.item', '.product-item',
            '.product-card', '.listing', '.card',
            '[class*="product"]', '[data-testid*="product"]'
        ],
        'news': [
            '.news-item', '.article', '.story',
            '.headline', '.news-article',
            '[class*="news"]', '[class*="story"]'
        ],
        'blog': [
            '.post', '.blog-post', '.entry',
            '.article', '.content',
            '[class*="post"]', '[class*="blog"]'
        ]
    }
    
    return selectors.get(target_content, [])

def validate_selectors(url, selectors):
    """
    Validate CSS selectors pada halaman
    
    Args:
        url (str): Page URL
        selectors (list): List of CSS selectors to test
        
    Returns:
        dict: Validation results
    """
    try:
        from bs4 import BeautifulSoup
        
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        results = {}
        
        for selector in selectors:
            try:
                elements = soup.select(selector)
                results[selector] = {
                    'found': len(elements),
                    'valid': len(elements) > 0,
                    'sample_text': elements[0].get_text(strip=True)[:100] if elements else 'N/A'
                }
            except Exception as e:
                results[selector] = {
                    'found': 0,
                    'valid': False,
                    'error': str(e)
                }
        
        print("Selector Validation Results:")
        print("-" * 50)
        for selector, result in results.items():
            status = "✓" if result['valid'] else "✗"
            print(f"{status} {selector}: {result['found']} elements")
            if result.get('sample_text'):
                print(f"   Sample: {result['sample_text']}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error validating selectors: {e}")
        return {'error': str(e)}

def clean_text(text):
    """
    Clean dan normalize text dari scraping
    
    Args:
        text (str): Raw text
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ''
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', text)
    
    # Remove multiple newlines
    text = re.sub(r'\n+', '\n', text)
    
    return text.strip()

def extract_domain(url):
    """
    Extract domain dari URL
    
    Args:
        url (str): Full URL
        
    Returns:
        str: Domain name
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except:
        return url

def is_valid_url(url):
    """
    Check apakah URL valid
    
    Args:
        url (str): URL to check
        
    Returns:
        bool: True if valid
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def create_filename(base_name, extension='csv', timestamp=True):
    """
    Create safe filename untuk output
    
    Args:
        base_name (str): Base filename
        extension (str): File extension
        timestamp (bool): Include timestamp
        
    Returns:
        str: Safe filename
    """
    # Clean base name
    safe_name = re.sub(r'[^\w\-_.]', '_', base_name)
    
    if timestamp:
        import datetime
        ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = f"{safe_name}_{ts}"
    
    return f"{safe_name}.{extension}"

def rate_limit_decorator(delay_range=(1, 3)):
    """
    Decorator untuk rate limiting
    
    Args:
        delay_range (tuple): Min and max delay in seconds
        
    Returns:
        decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Execute function
            result = func(*args, **kwargs)
            
            # Random delay
            delay = random.uniform(*delay_range)
            time.sleep(delay)
            
            return result
        return wrapper
    return decorator

def retry_on_failure(max_retries=3, delay=1):
    """
    Decorator untuk retry failed requests
    
    Args:
        max_retries (int): Maximum retry attempts
        delay (int): Delay between retries
        
    Returns:
        decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed")
            
            raise last_exception
        return wrapper
    return decorator

def estimate_scraping_time(total_pages, delay_range=(1, 3), items_per_page=20):
    """
    Estimate waktu yang dibutuhkan untuk scraping
    
    Args:
        total_pages (int): Total pages to scrape
        delay_range (tuple): Delay range between requests
        items_per_page (int): Average items per page
        
    Returns:
        dict: Time estimates
    """
    avg_delay = sum(delay_range) / 2
    total_requests = total_pages
    
    total_seconds = total_requests * avg_delay
    total_minutes = total_seconds / 60
    total_hours = total_minutes / 60
    
    total_items = total_pages * items_per_page
    
    return {
        'total_pages': total_pages,
        'total_items_estimated': total_items,
        'total_requests': total_requests,
        'avg_delay_seconds': avg_delay,
        'estimated_time_seconds': total_seconds,
        'estimated_time_minutes': round(total_minutes, 2),
        'estimated_time_hours': round(total_hours, 2),
        'estimated_time_human': f"{int(total_hours)}h {int(total_minutes % 60)}m {int(total_seconds % 60)}s"
    }

def save_config(config, filename='scraping_config.json'):
    """
    Save scraping configuration to file
    
    Args:
        config (dict): Configuration data
        filename (str): Config filename
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        logger.info(f"Configuration saved to {filename}")
    except Exception as e:
        logger.error(f"Error saving config: {e}")

def load_config(filename='scraping_config.json'):
    """
    Load scraping configuration from file
    
    Args:
        filename (str): Config filename
        
    Returns:
        dict: Configuration data
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info(f"Configuration loaded from {filename}")
        return config
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {}

def create_user_agents_list():
    """
    Create list of user agents untuk rotation
    
    Returns:
        list: List of user agent strings
    """
    return [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59'
    ]

def rotate_user_agent(session, user_agents=None):
    """
    Rotate user agent untuk session
    
    Args:
        session: Requests session object
        user_agents (list): List of user agents (optional)
    """
    if not user_agents:
        user_agents = create_user_agents_list()
    
    new_ua = random.choice(user_agents)
    session.headers.update({'User-Agent': new_ua})
    logger.info(f"User agent rotated")

def check_content_type(url):
    """
    Check content type dari URL
    
    Args:
        url (str): URL to check
        
    Returns:
        str: Content type
    """
    try:
        response = requests.head(url, timeout=10)
        return response.headers.get('content-type', 'unknown')
    except:
        return 'unknown'

def is_scraping_allowed(url, user_agent='*'):
    """
    Quick check apakah scraping diizinkan
    
    Args:
        url (str): Website URL
        user_agent (str): User agent
        
    Returns:
        bool: True if allowed
    """
    robots_info = check_robots_txt(url, user_agent)
    return robots_info.get('can_fetch', True)

# Example usage
if __name__ == "__main__":
    print("=== WEB SCRAPING UTILITIES ===")
    
    # Example website
    test_url = "https://example.com"
    
    print(f"\nTesting utilities with: {test_url}")
    
    # Check robots.txt
    print("\n1. Checking robots.txt...")
    # robots_info = check_robots_txt(test_url)
    
    # Get website info
    print("\n2. Getting website info...")
    # website_info = get_website_info(test_url)
    
    # Analyze page structure
    print("\n3. Analyzing page structure...")
    # structure = analyze_page_structure(test_url)
    
    # Generate selectors
    print("\n4. Generating selectors...")
    article_selectors = generate_selectors(test_url, 'article')
    print("Suggested article selectors:")
    for selector in article_selectors:
        print(f"  - {selector}")
    
    # Validate selectors
    print("\n5. Validating selectors...")
    # validation = validate_selectors(test_url, article_selectors[:3])
    
    # Estimate scraping time
    print("\n6. Estimating scraping time...")
    time_estimate = estimate_scraping_time(10, (1, 3), 20)
    print(f"Estimated time for 10 pages: {time_estimate['estimated_time_human']}")
    
    print("\nUtilities ready to use!")