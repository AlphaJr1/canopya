import os
import json
import pdfplumber
import re
from datetime import datetime
from typing import List, Dict, Tuple

class PDFProcessor:
    """
    """
    def __init__(self, raw_dir="data/raw"):
        self.raw_dir = raw_dir
        self.downloads_dir = os.path.join(raw_dir, "downloads")
        self.output_file = os.path.join(raw_dir, "processed_pdfs.json")
        self.metadata_file = os.path.join(raw_dir, "sources_metadata.json")
        self.images_dir = os.path.join("data", "processed", "images")
        
        # Ensure image directory exists
        os.makedirs(self.images_dir, exist_ok=True)
        
    def load_metadata(self):
        """
        """
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {}

    def clean_text(self, text: str) -> str:
        """
        """
        if not text:
            return ""
        
        # Remove common header/footer patterns (e.g., "Page 1", "Chapter 5")
        # This is a basic regex, can be improved based on specific document patterns
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE) # Standalone numbers
        text = re.sub(r'^\s*Page\s+\d+\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
        
        return text.strip()

    def extract_tables_to_markdown(self, page) -> str:
        tables = page.extract_tables()
        markdown_tables = []
        
        for table in tables:
            if not table:
                continue
                
            # Filter out empty rows/cols
            cleaned_table = [[cell if cell else "" for cell in row] for row in table if any(row)]
            
            if not cleaned_table:
                continue

            # Create Markdown Table
            try:
                headers = cleaned_table[0]
                rows = cleaned_table[1:]
                
                # Header row
                md_table = "| " + " | ".join(str(h).replace("\n", " ") for h in headers) + " |\n"
                # Separator row
                md_table += "| " + " | ".join(["---"] * len(headers)) + " |\n"
                # Data rows
                for row in rows:
                    md_table += "| " + " | ".join(str(c).replace("\n", " ") for c in row) + " |\n"
                
                markdown_tables.append(md_table)
            except Exception as e:
                # print(f"      ⚠️ Error formatting table: {e}")
                continue
                
        return "\n\n".join(markdown_tables)

    def extract_images(self, page, pdf_filename, page_num) -> List[str]:
        image_paths = []
        images = page.images
        
        for i, img in enumerate(images):
            # Filter small icons/lines (width or height < 50px)
            if img['width'] < 50 or img['height'] < 50:
                continue
                
            try:
                # Get image object
                # Note: pdfplumber extracts image metadata. To get the actual image, 
                # we often need to crop the page or use the stream. 
                # For simplicity and reliability with pdfplumber, we crop the page area.
                bbox = (img['x0'], img['top'], img['x1'], img['bottom'])
                cropped_page = page.crop(bbox)
                im = cropped_page.to_image(resolution=150) # 150 DPI is good balance
                
                # Generate filename
                safe_name = pdf_filename.replace(".pdf", "").replace(" ", "_")
                img_filename = f"{safe_name}_p{page_num}_img{i}.png"
                img_path = os.path.join(self.images_dir, img_filename)
                
                # Save image
                im.save(img_path, format="PNG")
                image_paths.append(img_path)
                
            except Exception as e:
                # Image extraction can be flaky depending on PDF structure
                # print(f"      ⚠️ Failed to extract image {i}: {e}")
                pass
                
        return image_paths

    def process_pdf(self, file_path, filename):
        """
        print(f"\nProcessing: {filename}")
        """
        full_content = ""
        all_images = []
        total_pages = 0
        
        try:
            with pdfplumber.open(file_path) as pdf:
                total_pages = len(pdf.pages)
                print(f"   📄 Processing {total_pages} pages...")
                
                for i, page in enumerate(pdf.pages):
                    page_num = i + 1
                    
                    # 1. Extract Text
                    text = page.extract_text()
                    text = self.clean_text(text)
                    
                    # 2. Extract Tables (and append to text)
                    tables_md = self.extract_tables_to_markdown(page)
                    
                    # 3. Extract Images
                    images = self.extract_images(page, filename, page_num)
                    all_images.extend(images)
                    
                    # Combine content
                    page_content = f"\n\n[Page {page_num}]\n"
                    page_content += text if text else ""
                    
                    if tables_md:
                        page_content += "\n\n### Tables extracted from Page {}:\n{}".format(page_num, tables_md)
                    
                    if images:
                        page_content += "\n\n[Images found on Page {}: {}]".format(page_num, ", ".join([os.path.basename(img) for img in images]))
                    
                    full_content += page_content
                    
                    # Progress dot
                    if i % 10 == 0:
                        print(".", end="", flush=True)
                        
            print(f"\n   ✅ Success! Extracted {len(full_content)} chars and {len(all_images)} images.")
            return full_content, total_pages, all_images
            
        except Exception as e:
            print(f"   ❌ Error processing PDF: {e}")
            return None, 0, []

    def process_all(self):
        """
        print(f"🚀 Starting Multimodal PDF Processing...")
        """
        metadata_map = self.load_metadata()
        processed_data = []
        
        # List all PDF files
        pdf_files = [f for f in os.listdir(self.downloads_dir) if f.endswith('.pdf')]
        print(f"📚 Found {len(pdf_files)} PDF files.")
        
        for filename in pdf_files:
            file_path = os.path.join(self.downloads_dir, filename)
            
            # Get metadata
            meta = metadata_map.get(filename, {})
            
            # Process
            content, pages, images = self.process_pdf(file_path, filename)
            
            if content:
                doc_record = {
                    "filename": filename,
                    "title": meta.get("title", filename.replace("_", " ").replace(".pdf", "")),
                    "url": meta.get("url", ""),
                    "source": meta.get("source", "Local PDF"),
                    "content": content,
                    "images": images, # List of absolute paths to images
                    "total_pages": pages,
                    "processed_at": datetime.now().isoformat(),
                    "type": "pdf"
                }
                processed_data.append(doc_record)
            else:
                print("   ⚠️ Skipped (No content extracted)")

        # Save results
        with open(self.output_file, 'w') as f:
            json.dump(processed_data, f, indent=2, ensure_ascii=False)
            
        print(f"\n✨ Finished! Processed content saved to: {self.output_file}")
        print(f"📊 Total Documents: {len(processed_data)}")
        print(f"🖼️  Total Images Extracted: {sum(len(d['images']) for d in processed_data)}")

if __name__ == "__main__":
    processor = PDFProcessor()
    processor.process_all()
