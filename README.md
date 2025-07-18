# Web Scraping Templates

**Educational collection of web scraping templates for learning purposes**

Template lengkap untuk web scraping dengan Python yang mencakup berbagai jenis website dan teknik scraping modern.

## ⚠️ **Important Legal Notice**

**GUNAKAN DENGAN BIJAK DAN BERTANGGUNG JAWAB!**

- ✅ **Selalu check `robots.txt`** sebelum scraping
- ✅ **Patuhi Terms of Service** website target
- ✅ **Gunakan delay yang reasonable** antar request
- ✅ **Respect website's bandwidth** dan server
- ✅ **Untuk tujuan edukasi dan penelitian** yang legal

**Users bertanggung jawab memastikan aktivitas scraping mereka mematuhi:**
- Terms of Service website
- Hukum lokal dan internasional
- Undang-undang copyright
- Regulasi perlindungan data

## 📋 **Features**

### **5 Template Scraper Lengkap:**

1. **Blog Scraper** (`blog_scraper.py`)
   - Scraping artikel dan blog posts
   - Support pagination
   - Extract metadata (author, date, tags)

2. **E-commerce Scraper** (`ecommerce_scraper.py`)
   - Product search dan listing
   - Price, rating, reviews extraction
   - Product detail scraping

3. **News Scraper** (`news_scraper.py`)
   - News article scraping
   - Multi-category support
   - RSS feed support
   - Sentiment analysis (optional)

4. **Dynamic Scraper** (`dynamic_scraper.py`)
   - JavaScript-heavy websites
   - Selenium WebDriver
   - Infinite scroll handling
   - SPA (Single Page Application) support

5. **API Scraper** (`api_scraper.py`)
   - Internal API endpoints
   - AJAX/Fetch request handling
   - WordPress REST API
   - GraphQL support

###  **Utility Functions:**

- **robots.txt checker**
- **Page structure analyzer**
- **CSS selector generator**
- **️Scraping time estimator**
- **User agent rotation**
- **Multiple output formats**

##  **Quick Start**

### **Installation**

```bash
# Clone repository
git clone https://github.com/jbagustw/web-scraping-templates.git
cd web-scraping-templates

# Install dependencies
pip install -r requirements.txt

# For dynamic scraping, install ChromeDriver
# ChromeDriver akan di-install otomatis oleh chromedriver-autoinstaller
```

### **Interactive Mode (Recommended for Beginners)**

```bash
python main.py
```

Interactive mode akan guide Anda step-by-step:
1. Input URL target
2. Pilih tipe scraper
3. Configure parameters
4. Automatic robots.txt checking
5. Run scraping dan save results

### **Command Line Usage**

```bash
# Blog scraping
python main.py --type blog --url "https://example-blog.com" --max-pages 5

# E-commerce product search
python main.py --type ecommerce --url "https://shop.com/search" --keyword "laptop" --max-pages 3

# News scraping dengan categories
python main.py --type news --url "https://news-site.com" --categories "tech" "politics" "economy"

# Dynamic content scraping
python main.py --type dynamic --url "https://spa-website.com" --content-selector ".post" --headless

# API scraping
python main.py --type api --url "https://api.example.com/posts" --max-pages 10
```

### **Programmatic Usage**

```python
from blog_scraper import BlogScraper

# Initialize scraper
scraper = BlogScraper(delay_range=(1, 2))

# Scrape articles
articles = scraper.scrape_article_list("https://example-blog.com", max_pages=5)

# Save results
scraper.save_to_csv(articles, "blog_articles.csv")
scraper.save_to_json(articles, "blog_articles.json")
```

## 📁 **Project Structure**

```
web-scraping-templates/
├── 📄 requirements.txt          # Dependencies
├── 📄 README.md                 # Documentation
├── 📄 main.py                   # Main CLI interface
├── 📄 base_scraper.py           # Base scraper class
├── 📄 blog_scraper.py           # Blog/article scraper
├── 📄 ecommerce_scraper.py      # E-commerce scraper
├── 📄 news_scraper.py           # News scraper
├── 📄 dynamic_scraper.py        # Dynamic content scraper
├── 📄 api_scraper.py            # API scraper
├── 📄 utils.py                  # Utility functions
└── 📁 examples/                 # Usage examples
    ├── 📄 example_blog.py
    ├── 📄 example_ecommerce.py
    └── 📄 example_news.py
```

## 🔧 **Configuration**

### **Custom Headers & Delays**

```python
from blog_scraper import BlogScraper

# Custom delay range (min, max) in seconds
scraper = BlogScraper(delay_range=(2, 5))

# Custom headers
scraper.set_custom_headers({
    'Accept-Language': 'id-ID,id;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br'
})
```

### **CSS Selector Customization**

Template menggunakan CSS selector yang umum, tapi **HARUS disesuaikan** dengan website target:

```python
# Di dalam _extract_articles_from_page()
article_selectors = [
    'article',                    # HTML5 semantic
    '.post',                      # Class post
    '.article',                   # Class article  
    '.entry',                     # Class entry
    '[class*="post"]',           # Any class containing "post"
    '[class*="article"]',        # Any class containing "article"
]
```

## 🛠️ **Advanced Usage**

### **1. Page Structure Analysis**

```python
from utils import analyze_page_structure, validate_selectors

# Analyze struktur halaman
structure = analyze_page_structure("https://example.com")

# Generate CSS selectors
selectors = generate_selectors("https://example.com", "article")

# Validate selectors
validation = validate_selectors("https://example.com", selectors)
```

### **2. Custom Scraping Pipeline**

```python
from base_scraper import WebScraper
from bs4 import BeautifulSoup

class CustomScraper(WebScraper):
    def scrape_custom_content(self, url):
        response = self.get_page(url)
        if not response:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Custom extraction logic
        items = []
        for element in soup.select('.custom-selector'):
            item = {
                'title': element.select_one('h2').get_text(strip=True),
                'content': element.select_one('p').get_text(strip=True)
            }
            items.append(item)
        
        return items
```

### **3. Selenium Dynamic Scraping**

```python
from dynamic_scraper import DynamicScraper

scraper = DynamicScraper(headless=False)  # Show browser for debugging

# Scrape SPA content
data = scraper.scrape_spa_content(
    url="https://spa-website.com",
    content_selector=".post-item",
    wait_selector=".loading-complete"
)

# Social media scraping
posts = scraper.scrape_social_media_posts(
    url="https://social-platform.com/feed",
    max_posts=50
)

scraper.close_driver()
```

### **4. API Endpoint Discovery**

```python
from api_scraper import APIScraper

scraper = APIScraper()

# Discover API endpoints
endpoints = scraper.discover_api_endpoints("https://example.com")

# Scrape WordPress API
wp_posts = scraper.scrape_wordpress_api("https://wp-site.com")

# GraphQL API
query = """
query {
  posts(first: 10) {
    nodes {
      title
      content
      date
    }
  }
}
"""
data = scraper.scrape_graphql_api("https://site.com/graphql", query)
```

##  **Output Formats**

### **CSV Output**
```csv
title,url,author,date,content
"Article Title","https://example.com/article","John Doe","2024-01-01","Article content..."
```

### **JSON Output**
```json
[
  {
    "title": "Article Title",
    "url": "https://example.com/article",
    "author": "John Doe",
    "date": "2024-01-01",
    "content": "Article content...",
    "tags": ["tech", "programming"],
    "scraped_at": "2024-01-01T10:30:00"
  }
]
```

##  **Troubleshooting**

### **Common Issues & Solutions**

#### **1. CSS Selectors Not Working**
```bash
# Analyze page structure
python main.py --url "https://target-site.com" --analyze

# Test selectors
python -c "
from utils import validate_selectors
result = validate_selectors('https://target-site.com', ['.article', '.post'])
print(result)
"
```

#### **2. Rate Limiting / Blocked**
```python
# Increase delay
scraper = BlogScraper(delay_range=(3, 8))

# Rotate user agents
from utils import rotate_user_agent
rotate_user_agent(scraper.session)
```

#### **3. JavaScript Not Loading**
```python
# Use dynamic scraper
from dynamic_scraper import DynamicScraper
scraper = DynamicScraper(headless=False)  # Debug mode

# Wait for specific element
scraper.wait_for_element('.content-loaded', timeout=20)
```

#### **4. Memory Issues with Large Data**
```python
# Process in chunks
def scrape_in_chunks(scraper, urls, chunk_size=100):
    for i in range(0, len(urls), chunk_size):
        chunk = urls[i:i+chunk_size]
        # Process chunk
        # Save intermediate results
```

## 🔍 **Best Practices**

### **✅ Do's**
- **Always check robots.txt** sebelum scraping
- **Use reasonable delays** (1-3 seconds minimum)
- **Rotate user agents** untuk scraping besar
- **Handle errors gracefully** dengan try-catch
- **Save progress regularly** untuk scraping besar
- **Respect website resources** dan bandwidth
- **Test selectors** pada beberapa halaman

### **❌ Don'ts**
- **Jangan scrape tanpa delay** (akan di-block)
- **Jangan ignore robots.txt** dan ToS
- **Jangan overload server** dengan request bersamaan
- **Jangan scrape data personal** tanpa izin
- **Jangan distribute scraped content** tanpa hak

## 📚 **Learning Resources**

### **Understanding CSS Selectors**
```python
# Basic selectors
'.class-name'           # Class selector
'#element-id'          # ID selector
'tag-name'             # Tag selector
'[attribute="value"]'  # Attribute selector

# Advanced selectors
'.parent .child'       # Descendant
'.parent > .child'     # Direct child
'.element:nth-child(2)' # Nth child
'.element:contains("text")' # Contains text
```

### **Chrome DevTools Tips**
1. **F12** → Network tab untuk menemukan API endpoints
2. **Right-click** → Inspect → Copy selector
3. **Console tab** → Test selectors dengan `document.querySelector()`
4. **Application tab** → Check cookies dan local storage

### **Debugging Scrapers**
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Print response content
response = scraper.get_page(url)
print(response.text[:1000])  # First 1000 chars

# Save page source
with open('debug_page.html', 'w', encoding='utf-8') as f:
    f.write(response.text)
```

##  **Contributing**

Contributions welcome! Please:

1. **Fork** repository
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open Pull Request**

### **Adding New Scrapers**
```python
# Template for new scraper
from base_scraper import WebScraper

class NewScraper(WebScraper):
    def __init__(self, delay_range=(1, 3)):
        super().__init__(delay_range)
    
    def scrape_content(self, url):
        # Implementation here
        pass
```

##  **License**

MIT License - see [LICENSE](LICENSE) file for details.

## ⚖️ **Legal Disclaimer**

This project is for **educational purposes only**. Users are responsible for:

- Complying with website Terms of Service
- Respecting robots.txt files
- Following local and international laws
- Not violating copyright or data protection laws
- Using scraped data ethically and legally

The authors are not responsible for any misuse of this software.

##  **Support**

-  **Bug reports**: [Open an issue](https://github.com/jbagustw/web-scraping-templates/issues)
-  **Feature requests**: [Open an issue](https://github.com/jbagustw/web-scraping-templates/issues)
-  **Documentation**: Check [Wiki](https://github.com/jbagustw/web-scraping-templates/wiki)
-  **Discussions**: [GitHub Discussions](https://github.com/jbagustw/web-scraping-templates/discussions)

##  **Acknowledgments**

- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) - HTML parsing
- [Selenium](https://selenium.dev/) - Browser automation
- [Requests](https://requests.readthedocs.io/) - HTTP library
- [Pandas](https://pandas.pydata.org/) - Data manipulation

---

**⭐ If this project helps you, please give it a star!**

** Share dengan developer lain yang membutuhkan template web scraping!**