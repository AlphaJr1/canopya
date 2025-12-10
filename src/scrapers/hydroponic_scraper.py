"""
Hydroponic Knowledge Scraper
Scrapes valid agricultural extension services and research sources for NFT hydroponic knowledge

"""

import requests
from bs4 import BeautifulSoup
import json
import time
from typing import List, Dict
from datetime import datetime
import logging
from urllib.parse import urljoin, urlparse
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HydroponicScraper:
    
    def __init__(self, output_dir: str = "data/raw"):
        self.output_dir = output_dir
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Educational Research Bot - Hydroponic Knowledge Collection)'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
    
    def check_robots_txt(self, base_url: str) -> bool:
        """
        """
        try:
            robots_url = urljoin(base_url, '/robots.txt')
            response = self.session.get(robots_url, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Robots.txt found for {base_url}")
                # Simple check - in production should use robotparser
                return True
            return True  # If no robots.txt, assume allowed for educational use
        except Exception as e:
            logger.warning(f"Could not check robots.txt for {base_url}: {e}")
            return True
    
    def scrape_page(self, url: str) -> Dict:
        """
        """
        try:
            logger.info(f"Scraping: {url}")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract main content - try common selectors
            content = (
                soup.find('article') or 
                soup.find('main') or 
                soup.find('div', class_='content') or
                soup.find('div', class_='main-content') or
                soup.find('body')
            )
            
            # Extract text
            if content:
                # Remove script and style elements
                for script in content(['script', 'style', 'nav', 'header', 'footer']):
                    script.decompose()
                
                text = content.get_text(separator='\n', strip=True)
            else:
                text = ""
            
            # Extract metadata
            title = soup.find('title')
            title_text = title.get_text() if title else ""
            
            meta_desc = soup.find('meta', {'name': 'description'})
            description = meta_desc.get('content') if meta_desc else ""
            
            return {
                'url': url,
                'title': title_text,
                'description': description,
                'text': text,
                'scraped_at': datetime.now().isoformat(),
                'word_count': len(text.split())
            }
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None
    
    def scrape_multiple(self, urls: List[str], delay: float = 2.0) -> List[Dict]:
        results = []
        
        for url in urls:
            result = self.scrape_page(url)
            if result:
                results.append(result)
            
            # Be respectful - add delay
            time.sleep(delay)
        
        return results
    
    def save_results(self, results: List[Dict], filename: str):
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(results)} pages to {filepath}")

class UniversityExtensionScraper(HydroponicScraper):
    
    SOURCES = {
        'okstate': {
            'name': 'Oklahoma State University Extension',
            'urls': [
                'https://extension.okstate.edu/fact-sheets/hydroponics.html',
                'https://extension.okstate.edu/fact-sheets/commercial-hydroponic-vegetable-production.html'
            ]
        },
        'ufl': {
            'name': 'University of Florida IFAS Extension',
            'urls': [
                'https://edis.ifas.ufl.edu/publication/CV266',  # Introduction to Hydroponics
                'https://edis.ifas.ufl.edu/publication/HS1215',  # Hydroponic Lettuce Production
            ]
        },
        'psu': {
            'name': 'Penn State Extension',
            'urls': [
                'https://extension.psu.edu/hydroponics',
                'https://extension.psu.edu/hydroponic-greenhouse-vegetable-production'
            ]
        }
    }
    
    def scrape_all_sources(self):
        """
        """
        for source_key, source_data in self.SOURCES.items():
            logger.info(f"\n{'='*50}")
            logger.info(f"Scraping: {source_data['name']}")
            logger.info(f"{'='*50}\n")
            
            results = self.scrape_multiple(source_data['urls'], delay=3.0)
            
            # Save results
            filename = f"{source_key}_hydroponics_{datetime.now().strftime('%Y%m%d')}.json"
            self.save_results(results, filename)

class ResearchPaperScraper(HydroponicScraper):
    
    def scrape_mdpi(self, doi: str) -> Dict:
        # MDPI papers are open access
        url = f"https://www.mdpi.com/{doi}"
        
        try:
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract paper content
            article = soup.find('div', class_='article-content') or soup.find('article')
            
            if article:
                # Remove references, figures etc for cleaner text
                for elem in article(['script', 'style', 'figure', 'table']):
                    elem.decompose()
                
                text = article.get_text(separator='\n', strip=True)
            else:
                text = ""
            
            title = soup.find('h1', class_='title')
            title_text = title.get_text() if title else ""
            
            abstract = soup.find('div', class_='art-abstract')
            abstract_text = abstract.get_text() if abstract else ""
            
            return {
                'url': url,
                'doi': doi,
                'title': title_text,
                'abstract': abstract_text,
                'full_text': text,
                'source': 'MDPI',
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error scraping MDPI paper {doi}: {e}")
            return None

def main():
    """
    print("🌱 Hydroponic Knowledge Scraper 🌱\n")
    
    # Scrape university extensions
    print("Phase 1: Scraping University Extension Services...")
    """
    ext_scraper = UniversityExtensionScraper()
    ext_scraper.scrape_all_sources()
    
    print("\n✅ Scraping complete! Check the data/raw directory for results.")
    print("\nNext steps:")
    print("1. Run pdf_processor.py to process any PDF guides")
    print("2. Run data_processor.py to clean and chunk the data")
    print("3. Run embedding_generator.py to create embeddings")

if __name__ == "__main__":
    main()
