"""
Smart Downloader & Scraper for Hydroponic Knowledge Base
Downloads PDFs and intelligently scrapes content from target URLs.

"""

import os
import json
import requests
import time
import logging
from typing import List, Dict
from urllib.parse import urlparse
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SmartDownloader:
    """
    """
    def __init__(self, download_dir: str = "data/raw/downloads", targets_file: str = "data/raw/download_targets.json"):
        self.download_dir = download_dir
        self.targets_file = targets_file
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        # Create download directory
        os.makedirs(download_dir, exist_ok=True)

    def load_targets(self) -> List[Dict]:
        """
        """
        if not os.path.exists(self.targets_file):
            logger.error(f"Targets file not found: {self.targets_file}")
            return []
        
        with open(self.targets_file, 'r') as f:
            return json.load(f)

    def download_file(self, url: str, filename: str = None) -> str:
        """
        """
        try:
            if not filename:
                # Extract filename from URL
                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path)
                if not filename:
                    filename = f"download_{int(time.time())}.pdf"
            
            # Ensure filename ends with .pdf if it's a PDF
            if not filename.lower().endswith('.pdf') and '.pdf' in url.lower():
                filename += '.pdf'

            filepath = os.path.join(self.download_dir, filename)
            
            # Skip if already exists
            if os.path.exists(filepath):
                logger.info(f"File already exists: {filename}")
                return filepath

            logger.info(f"Downloading: {url}")
            response = requests.get(url, headers=self.headers, stream=True, timeout=30)
            response.raise_for_status()

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"✅ Successfully downloaded: {filename}")
            return filepath

        except Exception as e:
            logger.error(f"❌ Failed to download {url}: {e}")
            return None

    def process_targets(self):
        targets = self.load_targets()
        logger.info(f"Found {len(targets)} targets to process")
        
        results = []
        
        for target in targets:
            url = target.get('url')
            title = target.get('title', 'Untitled')
            
            if not url:
                continue
                
            logger.info(f"Processing target: {title}")
            
            # Generate a safe filename
            safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_')]).strip().replace(' ', '_')
            filename = f"{safe_title}.pdf"
            
            filepath = self.download_file(url, filename)
            
            if filepath:
                results.append({
                    'title': title,
                    'url': url,
                    'local_path': filepath,
                    'downloaded_at': datetime.now().isoformat(),
                    'type': target.get('type', 'unknown')
                })
            
            # Be polite
            time.sleep(2)
            
        # Save results log
        log_file = os.path.join(self.download_dir, "download_log.json")
        with open(log_file, 'w') as f:
            json.dump(results, f, indent=2)
            
        logger.info(f"Download complete. Log saved to {log_file}")

def main():
    """
    print("🚀 Starting Smart Downloader...")
    """
    downloader = SmartDownloader()
    downloader.process_targets()
    print("\n✨ All tasks completed!")

if __name__ == "__main__":
    main()
