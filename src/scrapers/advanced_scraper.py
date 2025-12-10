"""
Advanced Scraper dengan Progress Bar
Mencoba scrape/download dokumen asli dari berbagai sumber

"""

import os
import json
import requests
import time
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
import sys

class ProgressBar:
    """
    """
    def __init__(self, total: int, prefix: str = "Progress"):
        self.total = total
        self.current = 0
        self.prefix = prefix
        
    def update(self, step: int = 1):
        self.current += step
        percent = (self.current / self.total) * 100
        bars = int(percent / 2)
        dots = 50 - bars
        sys.stdout.write(f'\r{self.prefix}: [{"█" * bars}{"." * dots}] {percent:.1f}% ({self.current}/{self.total})')
        sys.stdout.flush()
        
    def finish(self):
        """
        print()  # New line

class AdvancedScraper:
        """
    def __init__(self, output_dir: str = "data/raw/scraped"):
        self.output_dir = output_dir
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'id,en-US;q=0.9,en;q=0.8',
        }
        os.makedirs(output_dir, exist_ok=True)
        
    def scrape_url(self, url: str, title: str) -> Optional[Dict]:
        """
        """
        try:
            print(f"\n🔍 Mencoba: {title}")
            print(f"   URL: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=15, allow_redirects=True)
            
            # Progress indicator
            for i in range(10):
                print(".", end="", flush=True)
                time.sleep(0.1)
            print()
            
            if response.status_code != 200:
                print(f"   ❌ HTTP {response.status_code}")
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Coba berbagai selector untuk content
            content = None
            selectors = [
                'article',
                'main',
                '.content',
                '.main-content',
                '#content',
                '.post-content',
                '.entry-content',
                'body'
            ]
            
            for selector in selectors:
                content = soup.select_one(selector)
                if content:
                    break
            
            if not content:
                print(f"   ⚠️  Tidak bisa extract content")
                return None
            
            # Remove unwanted elements
            for tag in content(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
                tag.decompose()
            
            text = content.get_text(separator='\n', strip=True)
            
            if len(text) < 100:
                print(f"   ⚠️  Content terlalu pendek ({len(text)} chars)")
                return None
            
            print(f"   ✅ Berhasil! ({len(text)} chars, {len(text.split())} words)")
            
            return {
                'url': url,
                'title': title,
                'text': text,
                'scraped_at': datetime.now().isoformat(),
                'word_count': len(text.split()),
                'status': 'success'
            }
            
        except requests.exceptions.Timeout:
            print(f"   ⏱️  Timeout")
            return None
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error: {str(e)[:50]}...")
            return None
        except Exception as e:
            print(f"   ❌ Unexpected error: {str(e)[:50]}...")
            return None
    
    def process_batch(self, urls: List[Dict]) -> List[Dict]:
        results = []
        total = len(urls)
        
        print(f"\n{'='*60}")
        print(f"📚 Memproses {total} sumber")
        print(f"{'='*60}")
        
        progress = ProgressBar(total, "Overall Progress")
        
        for i, item in enumerate(urls, 1):
            print(f"\n[{i}/{total}]", end=" ")
            result = self.scrape_url(item['url'], item['title'])
            
            if result:
                result['source'] = item.get('source', 'Unknown')
                results.append(result)
            
            progress.update()
            time.sleep(2)  # Be polite
        
        progress.finish()
        return results
    
    def save_results(self, results: List[Dict], filename: str = "scraped_content.json"):
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Saved to: {filepath}")
        return filepath

def main():
    """
    print("🚀 Advanced Scraper dengan Progress Bar")
    """
    print("=" * 60)
    
    # Target URLs dari file JSON yang ada
    targets = [
        {
            'url': 'https://www.researchgate.net/publication/309202494_Complete_Guide_for_Growing_Plants_Hydroponically',
            'title': 'Complete Guide for Growing Plants Hydroponically',
            'source': 'ResearchGate'
        },
        {
            'url': 'https://pertanian.go.id',
            'title': 'Kementerian Pertanian - Hidroponik',
            'source': 'Kementerian Pertanian RI'
        },
        {
            'url': 'https://edis.ifas.ufl.edu/publication/CV266',
            'title': 'Introduction to Hydroponics - UF IFAS',
            'source': 'University of Florida'
        },
        {
            'url': 'https://extension.okstate.edu/fact-sheets/hydroponics.html',
            'title': 'Hydroponics Fact Sheet - OSU',
            'source': 'Oklahoma State University'
        }
    ]
    
    scraper = AdvancedScraper()
    results = scraper.process_batch(targets)
    
    print(f"\n{'='*60}")
    print(f"📊 HASIL:")
    print(f"   Berhasil: {len(results)}/{len(targets)}")
    print(f"   Gagal: {len(targets) - len(results)}/{len(targets)}")
    print(f"{'='*60}")
    
    if results:
        scraper.save_results(results)
        
        # Statistics
        total_words = sum(r['word_count'] for r in results)
        print(f"\n📝 Total kata: {total_words:,}")
        print(f"📄 Rata-rata per dokumen: {total_words // len(results):,} kata")
    
    print("\n✨ Selesai!")

if __name__ == "__main__":
    main()
