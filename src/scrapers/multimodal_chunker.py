"""
Multimodal Document Chunker
Chunks PDF documents with text, images, and tables for RAG pipeline

"""

import json
import os
import re
from typing import List, Dict, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultimodalChunker:
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        """
        Args:
            chunk_size: Target characters per chunk (not tokens)
            overlap: Overlap characters between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def load_processed_pdfs(self, filepath: str = "data/raw/processed_pdfs.json") -> List[Dict]:
        """Load processed PDFs from JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def extract_page_info(self, text: str) -> List[Dict]:
        """
        Split content by pages and extract page-specific information
        
        Returns: List of {page_num, content, images}
        """
        pages = []
        page_pattern = r'\[Page (\d+)\]'
        
        # Find all page markers
        splits = list(re.finditer(page_pattern, text))
        
        for i, match in enumerate(splits):
            page_num = int(match.group(1))
            start_pos = match.end()
            
            # End position is start of next page or end of text
            end_pos = splits[i + 1].start() if i + 1 < len(splits) else len(text)
            
            page_content = text[start_pos:end_pos].strip()
            
            # Extract image references from this page
            images = self._extract_image_refs(page_content, page_num)
            
            # Clean image references from text
            page_content = re.sub(r'\[Images found on Page \d+:.*?\]', '', page_content)
            
            pages.append({
                'page': page_num,
                'content': page_content,
                'images': images
            })
        
        return pages
    
    def _extract_image_refs(self, page_content: str, page_num: int) -> List[str]:
        images = []
        # Pattern: [Images found on Page X: img1.png, img2.png]
        pattern = rf'\[Images found on Page {page_num}: (.*?)\]'
        match = re.search(pattern, page_content)
        
        if match:
            img_names = match.group(1).split(', ')
            # Construct full paths
            for img_name in img_names:
                img_path = os.path.join("data", "processed", "images", img_name.strip())
                images.append(img_path)
        
        return images
    
    def extract_section_title(self, text: str) -> Optional[str]:
        # Look for patterns like "Chapter X:", "Section X.Y:", numbered headers
        patterns = [
            r'^(Chapter\s+\d+[:\.\s]+.*?)(?:\n|$)',
            r'^(CHAPTER\s+\d+[:\.\s]+.*?)(?:\n|$)',
            r'^(\d+\.\s+[A-Z][^\n]{5,50})(?:\n|$)',
            r'^([A-Z][A-Z\s]{10,50})(?:\n|$)',  # ALL CAPS titles
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def smart_split(self, text: str, max_size: int) -> List[str]:
        """
        Smart text splitting with priority: paragraph > sentence > word
        """
        if len(text) <= max_size:
            return [text]
        
        chunks = []
        
        # Try splitting by paragraphs first
        paragraphs = re.split(r'\n\n+', text)
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # If adding this paragraph exceeds max, save current and start new
            if len(current_chunk) + len(para) + 2 > max_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    # Add overlap from end of previous chunk
                    overlap_text = current_chunk[-self.overlap:] if len(current_chunk) > self.overlap else current_chunk
                    current_chunk = overlap_text + "\n\n" + para
                else:
                    # Paragraph itself is too long, need to split further
                    if len(para) > max_size:
                        sub_chunks = self._split_by_sentences(para, max_size)
                        chunks.extend(sub_chunks[:-1])
                        current_chunk = sub_chunks[-1] if sub_chunks else ""
                    else:
                        current_chunk = para
            else:
                current_chunk += ("\n\n" if current_chunk else "") + para
        
        # Add remaining
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_by_sentences(self, text: str, max_size: int) -> List[str]:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current = ""
        
        for sentence in sentences:
            if len(current) + len(sentence) + 1 > max_size:
                if current:
                    chunks.append(current.strip())
                    overlap = current[-self.overlap:] if len(current) > self.overlap else current
                    current = overlap + " " + sentence
                else:
                    # Single sentence too long, just add it
                    chunks.append(sentence.strip())
            else:
                current += (" " if current else "") + sentence
        
        if current:
            chunks.append(current.strip())
        
        return chunks
    
    def has_table(self, text: str) -> bool:
        return bool(re.search(r'\|.*\|.*\|', text))
    
    def chunk_document(self, doc: Dict) -> List[Dict]:
        """
        Chunk a single processed PDF document
        
        Returns: List of chunk objects with metadata
        """
        logger.info(f"Chunking: {doc['filename']}")
        
        filename = doc['filename']
        title = doc['title']
        source = doc['source']
        content = doc['content']
        
        # Extract page-by-page information
        pages = self.extract_page_info(content)
        
        all_chunks = []
        chunk_counter = 0
        
        for page_info in pages:
            page_num = page_info['page']
            page_content = page_info['content']
            page_images = page_info['images']
            
            if not page_content or len(page_content) < 50:
                continue
            
            # Extract section title if present
            section = self.extract_section_title(page_content)
            
            # Split page content into chunks
            text_chunks = self.smart_split(page_content, self.chunk_size)
            
            for chunk_text in text_chunks:
                if len(chunk_text) < 100:  # Skip very small chunks
                    continue
                
                chunk_obj = {
                    "chunk_id": f"{filename.replace('.pdf', '')}_p{page_num}_c{chunk_counter}",
                    "text": chunk_text,
                    "metadata": {
                        "source_file": filename,
                        "source_title": title,
                        "source": source,
                        "page": page_num,
                        "section": section,
                        "images": page_images,  # All images from this page
                        "has_table": self.has_table(chunk_text),
                        "char_count": len(chunk_text),
                        "processed_at": datetime.now().isoformat()
                    }
                }
                
                all_chunks.append(chunk_obj)
                chunk_counter += 1
        
        logger.info(f"  → Created {len(all_chunks)} chunks from {doc['filename']}")
        return all_chunks
    
    def chunk_all(self, input_file: str = "data/raw/processed_pdfs.json", 
                   output_file: str = "data/processed/chunks.json") -> List[Dict]:
        """Process all documents and save chunks"""
        docs = self.load_processed_pdfs(input_file)
        logger.info(f"Loaded {len(docs)} documents from {input_file}")
        
        all_chunks = []
        
        for doc in docs:
            try:
                chunks = self.chunk_document(doc)
                all_chunks.extend(chunks)
            except Exception as e:
                logger.error(f"Error chunking {doc.get('filename', 'unknown')}: {e}")
        
        # Save to JSON
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_chunks, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n✅ Chunking complete!")
        logger.info(f"   Total chunks: {len(all_chunks)}")
        logger.info(f"   Saved to: {output_file}")
        
        # Calculate statistics
        self._print_statistics(all_chunks)
        
        return all_chunks
    
    def _print_statistics(self, chunks: List[Dict]):
        total = len(chunks)
        avg_chars = sum(c['metadata']['char_count'] for c in chunks) / total if total > 0 else 0
        chunks_with_images = sum(1 for c in chunks if c['metadata']['images'])
        chunks_with_tables = sum(1 for c in chunks if c['metadata']['has_table'])
        
        sources = set(c['metadata']['source_file'] for c in chunks)
        
        print("\n📊 Chunking Statistics:")
        print(f"   - Total chunks: {total}")
        print(f"   - Avg chars/chunk: {avg_chars:.0f}")
        print(f"   - Chunks with images: {chunks_with_images} ({chunks_with_images/total*100:.1f}%)")
        print(f"   - Chunks with tables: {chunks_with_tables} ({chunks_with_tables/total*100:.1f}%)")
        print(f"   - Source documents: {len(sources)}")

def main():
    """Main function untuk chunking"""
    print("🔪 Starting Multimodal Document Chunking\n")
    
    chunker = MultimodalChunker(chunk_size=1000, overlap=200)
    
    # Check if processed_pdfs.json exists
    input_file = "data/raw/processed_pdfs.json"
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        print("   Run pdf_processor.py first!")
        return
    
    # Process all documents
    chunks = chunker.chunk_all(
        input_file=input_file,
        output_file="data/processed/chunks.json"
    )
    
    print("\n✨ Done! Chunks ready for embedding.")

if __name__ == "__main__":
    main()
