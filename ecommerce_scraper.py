# ecommerce_scraper.py
# Template untuk scraping website e-commerce

from bs4 import BeautifulSoup
from base_scraper import WebScraper
import re
import logging

logger = logging.getLogger(__name__)

class EcommerceScraper(WebScraper):
    """
    Template untuk scraping website e-commerce
    PENTING: Patuhi robots.txt dan Terms of Service website!
    """
    
    def __init__(self, delay_range=(2, 5)):
        super().__init__(delay_range)
        # E-commerce sites biasanya lebih sensitif, gunakan delay lebih lama
        
    def search_products(self, search_url, keyword, max_pages=3, sort_by=None):
        """
        Search produk berdasarkan keyword
        
        Args:
            search_url (str): URL search endpoint
            keyword (str): Kata kunci pencarian
            max_pages (int): Maksimal halaman
            sort_by (str): Parameter sorting (optional)
            
        Returns:
            list: List produk
        """
        products = []
        
        for page in range(1, max_pages + 1):
            # Format URL search - sesuaikan dengan website target
            params = {
                'q': keyword,
                'page': page
            }
            
            if sort_by:
                params['sort'] = sort_by
            
            # Buat URL dengan parameter
            url = f"{search_url}?"
            url += "&".join([f"{k}={v}" for k, v in params.items()])
            
            logger.info(f"Searching products on page {page}: {url}")
            
            response = self.get_page(url)
            if not response:
                logger.warning(f"Failed to fetch page {page}")
                continue
                
            soup = BeautifulSoup(response.content, 'html.parser')
            page_products = self._extract_products_from_page(soup, search_url)
            
            if not page_products:
                logger.warning(f"No products found on page {page}, stopping...")
                break
                
            products.extend(page_products)
            logger.info(f"Found {len(page_products)} products on page {page}")
            
            # Delay antar halaman
            if page < max_pages:
                self.random_delay()
        
        logger.info(f"Total products found: {len(products)}")
        return products
    
    def _extract_products_from_page(self, soup, base_url):
        """
        Extract produk dari satu halaman
        SESUAIKAN CSS SELECTOR DENGAN WEBSITE TARGET!
        """
        products = []
        
        # CSS Selector untuk product items - SESUAIKAN!
        possible_selectors = [
            '.product-item',
            '.product',
            '.item',
            '[class*="product"]',
            '[data-testid*="product"]',
            '.card',
            '.listing'
        ]
        
        product_elements = []
        for selector in possible_selectors:
            elements = soup.select(selector)
            if elements and len(elements) > 3:  # Minimal 3 elements untuk validasi
                product_elements = elements
                logger.info(f"Using selector: {selector} ({len(elements)} products)")
                break
        
        if not product_elements:
            logger.warning("No product elements found")
            return products
        
        for product_elem in product_elements:
            try:
                product_data = self._extract_product_data(product_elem, base_url)
                if product_data:
                    products.append(product_data)
            except Exception as e:
                logger.error(f"Error extracting product: {e}")
                continue
        
        return products
    
    def _extract_product_data(self, product_elem, base_url):
        """
        Extract data dari satu product element
        """
        try:
            # Product Name
            name = None
            name_selectors = [
                'h3', 'h2', 'h4',
                '.product-name', '.product-title', '.title',
                '[class*="name"]', '[class*="title"]'
            ]
            for selector in name_selectors:
                name_elem = product_elem.select_one(selector)
                if name_elem:
                    name = name_elem.get_text(strip=True)
                    if name and len(name) > 3:
                        break
            
            # Price
            price = None
            price_raw = None
            price_selectors = [
                '.price', '.cost', '.amount',
                '[class*="price"]', '[class*="cost"]',
                '[data-testid*="price"]'
            ]
            for selector in price_selectors:
                price_elem = product_elem.select_one(selector)
                if price_elem:
                    price_raw = price_elem.get_text(strip=True)
                    price = self._clean_price(price_raw)
                    if price:
                        break
            
            # Rating
            rating = None
            rating_selectors = [
                '.rating', '.stars', '.score',
                '[class*="rating"]', '[class*="star"]'
            ]
            for selector in rating_selectors:
                rating_elem = product_elem.select_one(selector)
                if rating_elem:
                    # Coba ambil dari berbagai attribute
                    rating = (rating_elem.get('data-rating') or 
                             rating_elem.get('title') or 
                             rating_elem.get_text(strip=True))
                    rating = self._clean_rating(rating)
                    if rating:
                        break
            
            # Image
            image = None
            image_elem = product_elem.select_one('img')
            if image_elem:
                image_src = (image_elem.get('src') or 
                           image_elem.get('data-src') or 
                           image_elem.get('data-lazy'))
                if image_src:
                    image = self.get_absolute_url(base_url, image_src)
            
            # Product Link
            link = None
            link_elem = product_elem.select_one('a')
            if link_elem and link_elem.get('href'):
                link = self.get_absolute_url(base_url, link_elem['href'])
            
            # Reviews Count
            reviews_count = None
            review_selectors = [
                '.reviews-count', '.review-count',
                '[class*="review"]'
            ]
            for selector in review_selectors:
                review_elem = product_elem.select_one(selector)
                if review_elem:
                    reviews_text = review_elem.get_text(strip=True)
                    reviews_count = self._extract_number(reviews_text)
                    if reviews_count:
                        break
            
            # Discount/Sale
            discount = None
            discount_selectors = [
                '.discount', '.sale', '.off',
                '[class*="discount"]', '[class*="sale"]'
            ]
            for selector in discount_selectors:
                discount_elem = product_elem.select_one(selector)
                if discount_elem:
                    discount = discount_elem.get_text(strip=True)
                    break
            
            # Stock Status
            stock = None
            stock_selectors = [
                '.stock', '.availability',
                '[class*="stock"]', '[class*="available"]'
            ]
            for selector in stock_selectors:
                stock_elem = product_elem.select_one(selector)
                if stock_elem:
                    stock = stock_elem.get_text(strip=True)
                    break
            
            return {
                'name': name or 'N/A',
                'price': price or 'N/A',
                'price_raw': price_raw or 'N/A',
                'rating': rating or 'N/A',
                'reviews_count': reviews_count or 'N/A',
                'image': image or 'N/A',
                'link': link or 'N/A',
                'discount': discount or 'N/A',
                'stock': stock or 'N/A'
            }
            
        except Exception as e:
            logger.error(f"Error extracting product data: {e}")
            return None
    
    def _clean_price(self, price_text):
        """Clean dan extract harga dari text"""
        if not price_text:
            return None
            
        # Remove whitespace dan normalize
        price_text = re.sub(r'\s+', ' ', price_text.strip())
        
        # Extract angka dan simbol mata uang
        # Pattern untuk berbagai format harga
        patterns = [
            r'[\d,.]+',  # Angka dengan koma/titik
            r'\$[\d,.]+',  # Dollar
            r'Rp[\d,.]+',  # Rupiah
            r'€[\d,.]+',   # Euro
        ]
        
        for pattern in patterns:
            match = re.search(pattern, price_text)
            if match:
                return match.group()
        
        return price_text
    
    def _clean_rating(self, rating_text):
        """Clean dan extract rating"""
        if not rating_text:
            return None
            
        # Extract angka rating (biasanya format 4.5, 4/5, dll)
        rating_pattern = r'(\d+(?:\.\d+)?)'
        match = re.search(rating_pattern, rating_text)
        
        if match:
            return float(match.group(1))
        
        return rating_text
    
    def _extract_number(self, text):
        """Extract angka dari text"""
        if not text:
            return None
            
        # Cari angka dalam text
        numbers = re.findall(r'\d+', text)
        if numbers:
            return int(numbers[0])
        
        return None
    
    def scrape_product_detail(self, product_url):
        """
        Scrape detail lengkap dari satu produk
        
        Args:
            product_url (str): URL produk
            
        Returns:
            dict: Detail produk
        """
        response = self.get_page(product_url)
        if not response:
            return None
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        try:
            # Product name
            name = None
            name_selectors = ['h1', '.product-name', '.product-title']
            for selector in name_selectors:
                name_elem = soup.select_one(selector)
                if name_elem:
                    name = name_elem.get_text(strip=True)
                    break
            
            # Description
            description = None
            desc_selectors = [
                '.product-description', '.description',
                '.product-details', '.details'
            ]
            for selector in desc_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    description = desc_elem.get_text(strip=True)
                    break
            
            # Specifications
            specs = {}
            spec_selectors = [
                '.specifications table tr',
                '.specs table tr',
                '.product-specs tr'
            ]
            for selector in spec_selectors:
                spec_rows = soup.select(selector)
                if spec_rows:
                    for row in spec_rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            key = cells[0].get_text(strip=True)
                            value = cells[1].get_text(strip=True)
                            specs[key] = value
                    break
            
            # Images
            images = []
            image_selectors = [
                '.product-images img',
                '.gallery img',
                '.product-gallery img'
            ]
            for selector in image_selectors:
                img_elements = soup.select(selector)
                if img_elements:
                    for img in img_elements:
                        img_src = img.get('src') or img.get('data-src')
                        if img_src:
                            images.append(self.get_absolute_url(product_url, img_src))
                    break
            
            return {
                'url': product_url,
                'name': name or 'N/A',
                'description': description or 'N/A',
                'specifications': specs,
                'images': images
            }
            
        except Exception as e:
            logger.error(f"Error scraping product detail {product_url}: {e}")
            return None

# Example usage
if __name__ == "__main__":
    scraper = EcommerceScraper(delay_range=(2, 4))
    
    print("=== E-COMMERCE SCRAPER EXAMPLE ===")
    print("IMPORTANT: Patuhi robots.txt dan ToS website!")
    
    # Contoh search produk
    search_url = "https://example-shop.com/search"
    keyword = "laptop"
    
    print(f"Searching for: {keyword}")
    print("SESUAIKAN URL dan CSS selector dengan website target!")
    
    # products = scraper.search_products(search_url, keyword, max_pages=2)
    # scraper.save_to_csv(products, "products.csv")
    # scraper.save_to_json(products, "products.json")
    
    # Scrape detail produk
    # if products:
    #     first_product_url = products[0]['link']
    #     if first_product_url != 'N/A':
    #         detail = scraper.scrape_product_detail(first_product_url)
    #         if detail:
    #             print(f"Product detail: {detail['name']}")
    
    print("E-commerce scraper template ready!")
    scraper.close_session()