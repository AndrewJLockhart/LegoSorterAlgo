"""
Script to download Rebrickable CSV database files.
"""

import csv
import gzip
import io
import os
import shutil
import urllib.request
from urllib.error import URLError

# List of files to download
FILES = [
    "themes.csv",
    "colors.csv",
    "part_categories.csv",
    "parts.csv",
    "part_relationships.csv",
    "elements.csv",
    "minifigs.csv",
    "sets.csv",
    "inventories.csv",
    "inventory_parts.csv",
    "inventory_sets.csv",
    "inventory_minifigs.csv",
]

BASE_URL = "https://cdn.rebrickable.com/media/downloads/"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "RebrickableCSVs")

class ImageLibrary:
    def __init__(self):
        self.images = []
        self.image_map = {} # url -> index

    def get_key(self, url, prefix):
        if not url:
            return ""
        
        if url.startswith(prefix):
            clean_url = url[len(prefix):]
        else:
            clean_url = url
            
        if clean_url not in self.image_map:
            # Use 0-based index as the key
            self.image_map[clean_url] = len(self.images)
            self.images.append(clean_url)
            
        return str(self.image_map[clean_url])

    def save(self):
        path = os.path.join(OUTPUT_DIR, "image_paths.csv.gz")
        print(f"Writing {len(self.images)} image paths to {path}...")
        with gzip.open(path, 'wt', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['img_url'])
            for img in self.images:
                writer.writerow([img])

def process_file_with_images(filename, response, img_lib):
    """
    Process a CSV file that contains image URLs.
    Extracts URLs to ImageLibrary and replaces them with keys.
    Streams data to minimize memory usage.
    """
    print(f"Processing {filename}...")
    
    # Determine prefix
    prefix = "https://cdn.rebrickable.com/media/"
    output_path = os.path.join(OUTPUT_DIR, filename)

    try:
        # Stream decompression and text decoding
        with gzip.GzipFile(fileobj=response, mode='rb') as gz_file:
            with io.TextIOWrapper(gz_file, encoding='utf-8', newline='') as text_file:
                reader = csv.DictReader(text_file)
                fieldnames = reader.fieldnames
                
                if 'img_url' not in fieldnames:
                    print(f"Warning: img_url not found in {filename}")
                    # Fallback: write the CSV as is (re-encoding it)
                    with open(output_path, 'w', encoding='utf-8', newline='') as f_out:
                        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
                        writer.writeheader()
                        for row in reader:
                            writer.writerow(row)
                    return True
            
                new_fieldnames = [f if f != 'img_url' else 'img_key' for f in fieldnames]
                
                with open(output_path, 'w', encoding='utf-8', newline='') as f_out:
                    writer = csv.DictWriter(f_out, fieldnames=new_fieldnames)
                    writer.writeheader()
                    
                    for row in reader:
                        img_url = row.pop('img_url', '')
                        img_key = img_lib.get_key(img_url, prefix)
                        row['img_key'] = img_key
                        writer.writerow(row)
            
        return True
    except Exception as e:
        print(f"Error processing {filename}: {e}")
        return False

def download_file(filename, img_lib=None):
    url = f"{BASE_URL}{filename}.gz"
    output_path = os.path.join(OUTPUT_DIR, filename)
    
    print(f"Downloading {filename} from {url}...")
    
    try:
        with urllib.request.urlopen(url) as response:
            if filename in ["inventory_parts.csv", "sets.csv", "minifigs.csv"] and img_lib is not None:
                return process_file_with_images(filename, response, img_lib)
            
            # Stream decompression directly to file
            with gzip.GzipFile(fileobj=response, mode='rb') as gz_file:
                with open(output_path, 'wb') as out_file:
                    shutil.copyfileobj(gz_file, out_file)
            
        print(f"Successfully saved to {output_path}")
        return True
    except URLError as e:
        print(f"Failed to download {filename}: {e}")
        return False
    except Exception as e:
        print(f"Error processing {filename}: {e}")
        return False

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created directory: {OUTPUT_DIR}")
    
    print("Cleaning up existing files...")
    for filename in os.listdir(OUTPUT_DIR):
        if filename.endswith(".csv") or filename.endswith(".gz") or filename.endswith(".zip"):
            file_path = os.path.join(OUTPUT_DIR, filename)
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error deleting {filename}: {e}")

    print(f"Downloading files to: {OUTPUT_DIR}")
    
    img_lib = ImageLibrary()
    success_count = 0
    
    for filename in FILES:
        if download_file(filename, img_lib):
            success_count += 1
            
    img_lib.save()
            
    print(f"\nDownload complete. {success_count}/{len(FILES)} files downloaded.")

if __name__ == "__main__":
    main()
