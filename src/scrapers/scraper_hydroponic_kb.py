"""
NFT Hydroponic Knowledge Base Scraper

Script untuk mengumpulkan data dari sumber-sumber valid di internet
untuk membangun knowledge base chatbot NFT hydroponic.

Sumber data:
1. University Extension Programs (USDA, UF, OSU)
2. Hydroponic guides & tutorials
3. Forums & FAQ sections
4. Scientific articles (open access)

Dependencies:
    pip install beautifulsoup4 requests lxml markdown html2text

"""

import requests
from bs4 import BeautifulSoup
import json
import time
import os
from typing import List, Dict
from urllib.parse import urljoin, urlparse
import html2text
import re

class HydroponicScraper:
    
    def __init__(self, output_dir: str = "scraped_data"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # HTML to Markdown converter
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = True
        self.h2t.body_width = 0
    
    def clean_text(self, text: str) -> str:
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:()\-"\'°%]', '', text)
        return text.strip()
    
    def save_json(self, data: List[Dict], filename: str):
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Saved {len(data)} items to {filepath}")
    
    def delay(self, seconds: float = 1.0):
        """Polite delay between requests"""
        time.sleep(seconds)

class UniversityScraper(HydroponicScraper):
    """Scraper for university extension programs"""
    SOURCES = {
        "uf_ifas": {
            "base_url": "https://edis.ifas.ufl.edu",
            "search_query": "hydroponics NFT",
            "note": "University of Florida IFAS Extension - peer-reviewed publications"
        },
        "cornell": {
            "base_url": "https://cea.cals.cornell.edu",
            "note": "Cornell Controlled Environment Agriculture"
        }
    }
    
    def scrape_article(self, url: str) -> Dict:
        """Scrape a single article from university extension"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Extract title
            title = soup.find('h1')
            title_text = title.get_text(strip=True) if title else "Untitled"
            
            # Extract main content
            # Try common content containers
            content = None
            for selector in ['article', '.content', '.main-content', '#main-content']:
                content = soup.select_one(selector)
                if content:
                    break
            
            if not content:
                content = soup.find('body')
            
            # Convert to markdown
            content_html = str(content) if content else ""
            content_md = self.h2t.handle(content_html)
            content_clean = self.clean_text(content_md)
            
            return {
                "url": url,
                "title": title_text,
                "content": content_clean,
                "source": "university_extension",
                "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            print(f"❌ Error scraping {url}: {str(e)}")
            return None

class HydroponicGuideScraper(HydroponicScraper):
    
    GUIDE_URLS = [
        "https://www.hydragarden.com/nft-hydroponics/",
        "https://www.forkfarms.com/resources/",
        "https://www.greenlivingoffgrid.com/hydroponic-troubleshooting-guide/",
    ]
    
    def scrape_guide(self, url: str) -> Dict:
        """Scrape a hydroponic guide/tutorial"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Extract title
            title = soup.find('h1') or soup.find('title')
            title_text = title.get_text(strip=True) if title else "Guide"
            
            # Extract all text content
            paragraphs = soup.find_all(['p', 'li', 'h2', 'h3'])
            content_parts = []
            
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 20:  # Filter out very short snippets
                    content_parts.append(text)
            
            content = "\n\n".join(content_parts)
            content_clean = self.clean_text(content)
            
            return {
                "url": url,
                "title": title_text,
                "content": content_clean,
                "source": "tutorial_guide",
                "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            print(f"❌ Error scraping guide {url}: {str(e)}")
            return None
    
    def scrape_all_guides(self) -> List[Dict]:
        results = []
        
        for url in self.GUIDE_URLS:
            print(f"🔍 Scraping guide: {url}")
            data = self.scrape_guide(url)
            if data:
                results.append(data)
            self.delay(2.0)  # Be polite
        
        return results

class RedditScraper(HydroponicScraper):
    """
    Scrape Reddit r/Hydroponics for FAQs and troubleshooting
    
    Note: For production, use Reddit API with proper authentication.
    This basic scraper is for demonstration purposes.
    """
    
    def scrape_reddit_thread(self, thread_url: str) -> Dict:
        """
        Scrape a single Reddit thread
        
        WARNING: Reddit blocks scrapers. Use official API for production.
        This is just a template.
        """
        print("⚠️ Reddit scraping requires API authentication.")
        print("Please use Reddit API (PRAW) with proper credentials.")
        print("Example: https://praw.readthedocs.io/")
        
        return {
            "note": "Use Reddit API (PRAW) for actual implementation",
            "example_topics": [
                "NFT system setup",
                "pH troubleshooting",
                "TDS adjustment",
                "Common beginner mistakes"
            ]
        }

class FAQScraper(HydroponicScraper):
    
    FAQ_URLS = [
        "https://www.sylvane.com/blog/hydroponic-gardening-faq",
        # Add more FAQ URLs here
    ]
    
    def scrape_faq(self, url: str) -> List[Dict]:
        """
        Scrape FAQ page and extract Q&A pairs
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'lxml')
            
            qa_pairs = []
            
            # Try to find FAQ structure
            # Common patterns: h3/h4 for questions, p for answers
            questions = soup.find_all(['h3', 'h4', 'strong'])
            
            for q in questions:
                question_text = q.get_text(strip=True)
                
                # Get next paragraph as answer
                answer_elem = q.find_next(['p', 'div'])
                answer_text = answer_elem.get_text(strip=True) if answer_elem else ""
                
                if len(question_text) > 10 and len(answer_text) > 20:
                    qa_pairs.append({
                        "question": self.clean_text(question_text),
                        "answer": self.clean_text(answer_text),
                        "source_url": url,
                        "type": "faq"
                    })
            
            return qa_pairs
            
        except Exception as e:
            print(f"❌ Error scraping FAQ {url}: {str(e)}")
            return []

class DatasetDownloader:
    """
    Download open datasets for hydroponic research
    
    Datasets:
    1. Kaggle: Hydroponics IoT Data
    2. Mendeley: HydroGrowNet Dataset
    
    """
    def __init__(self, output_dir: str = "datasets"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def download_kaggle_dataset(self, dataset_id: str):
        """
        Download dataset from Kaggle
        
        Requires: kaggle API credentials (~/.kaggle/kaggle.json)
        Install: pip install kaggle
        
        Example:
            dataset_id = "dataengineer21/hydroponics-iot-data"
        """
        print("📦 Kaggle dataset download requires:")
        print("1. Install: pip install kaggle")
        print("2. Setup API key: https://www.kaggle.com/docs/api")
        print(f"3. Run: kaggle datasets download -d {dataset_id}")
        print(f"   Output: {self.output_dir}/")
        
        # Uncomment below if kaggle is installed and configured
        # import kaggle
        # kaggle.api.dataset_download_files(dataset_id, path=self.output_dir, unzip=True)

# MAIN EXECUTION

def main():
    """
    Main scraping pipeline
    """
    print("=" * 70)
    print("NFT HYDROPONIC KNOWLEDGE BASE SCRAPER")
    print("=" * 70)
    print()
    
    # 1. Scrape University Extensions
    print("📚 Step 1: Scraping University Extension Programs")
    print("⚠️  Note: Many sites block automated scraping.")
    print("    Manually download PDFs from these sources instead:")
    print()
    
    uni_sources = [
        "https://edis.ifas.ufl.edu (Search: 'hydroponics NFT')",
        "https://extension.okstate.edu (Search: 'hydroponics')",
        "https://cea.cals.cornell.edu (Browse publications)",
        "https://www.usda.gov/nal (USDA National Agricultural Library)"
    ]
    
    for source in uni_sources:
        print(f"   • {source}")
    print()
    
    # 2. Scrape Guides
    print("📖 Step 2: Scraping Tutorial Guides")
    guide_scraper = HydroponicGuideScraper()
    guides = guide_scraper.scrape_all_guides()
    if guides:
        guide_scraper.save_json(guides, "tutorial_guides.json")
    print()
    
    # 3. Scrape FAQs
    print("❓ Step 3: Scraping FAQ Pages")
    faq_scraper = FAQScraper()
    all_faqs = []
    for faq_url in faq_scraper.FAQ_URLS:
        print(f"🔍 Scraping FAQ: {faq_url}")
        faqs = faq_scraper.scrape_faq(faq_url)
        all_faqs.extend(faqs)
        faq_scraper.delay(2.0)
    
    if all_faqs:
        faq_scraper.save_json(all_faqs, "faqs.json")
    print()
    
    # 4. Reddit (requires API)
    print("💬 Step 4: Reddit Data Collection")
    print("⚠️  Use Reddit API (PRAW) for this:")
    print("   pip install praw")
    print("   Subreddits: r/Hydroponics, r/hydro")
    print()
    
    # 5. Datasets
    print("📊 Step 5: Download Open Datasets")
    downloader = DatasetDownloader()
    print("   Kaggle: hydroponics-iot-data")
    print("   Mendeley: HydroGrowNet Dataset")
    print()
    
    # Summary
    print("=" * 70)
    print("✅ SCRAPING COMPLETE")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Review and clean scraped data in ./scraped_data/")
    print("2. Manually download university PDFs and extract text")
    print("3. Setup Reddit API for community Q&A")
    print("4. Combine all sources into unified knowledge base")
    print("5. Chunk documents for embedding (512-1024 tokens)")
    print("6. Upload to Qdrant vector database")
    print()
    print("⚠️  IMPORTANT: Always respect robots.txt and rate limits!")
    print("    For production, contact website owners for API access.")

if __name__ == "__main__":
    main()
