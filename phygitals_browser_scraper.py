#!/usr/bin/env python3
"""
Phygitals Browser-Based Pokemon Scraper
Uses Selenium to handle dynamic content loading for Pokemon images and animations
"""

import os
import re
import time
import json
import requests
from pathlib import Path
from urllib.parse import urljoin, urlparse
import argparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class PhygitalsBrowserScraper:
    def __init__(self, output_dir="phygitals_dynamic_pokemon", headless=True):
        self.base_url = "https://www.phygitals.com"
        self.output_dir = Path(output_dir)
        self.headless = headless
        self.session = requests.Session()
        self.downloaded_files = set()
        self.download_stats = {
            'pokemon_images': 0,
            'animations': 0,
            'trainer_packs': 0,
            'sprites': 0,
            'failed': 0
        }
        self.failed_downloads = []
        self.lock = threading.Lock()
        
        # Setup session headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        self.create_directories()
        
    def create_directories(self):
        """Create organized directory structure"""
        directories = []
        
        for gen in range(1, 10):
            gen_dirs = [
                f"generation_{gen}/pokemon_cards",
                f"generation_{gen}/pokemon_sprites", 
                f"generation_{gen}/animations",
                f"generation_{gen}/trainer_packs",
                f"generation_{gen}/backgrounds",
                f"generation_{gen}/data"
            ]
            directories.extend(gen_dirs)
        
        directories.extend([
            "shared_assets/css",
            "shared_assets/js",
            "shared_assets/fonts",
            "shared_assets/videos"
        ])
        
        for directory in directories:
            (self.output_dir / directory).mkdir(parents=True, exist_ok=True)
    
    def setup_browser(self):
        """Setup Chrome browser with options for scraping"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        # Install and setup ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        return driver
    
    def clean_filename(self, filename):
        """Clean filename for filesystem compatibility"""
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'[^\w\-_\.]', '_', filename)
        return filename[:200]  # Limit length
    
    def download_file(self, url, local_path, file_type='other'):
        """Download file with progress tracking"""
        if url in self.downloaded_files:
            return True
            
        try:
            print(f"📥 Downloading {file_type}: {url}")
            response = self.session.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(local_path, 'wb') as f:
                if total_size > 0:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 1024 * 1024:  # Show progress for files > 1MB
                                progress = (downloaded / total_size) * 100
                                print(f"  Progress: {progress:.1f}%", end='\r')
                else:
                    f.write(response.content)
            
            with self.lock:
                self.downloaded_files.add(url)
                self.download_stats[file_type] += 1
            
            print(f"✅ Saved: {local_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to download {url}: {e}")
            with self.lock:
                self.failed_downloads.append(url)
                self.download_stats['failed'] += 1
            return False
    
    def extract_pokemon_data_from_page(self, driver, generation):
        """Extract Pokemon images and data from dynamically loaded page"""
        pokemon_data = []
        image_urls = set()
        
        print(f"🔍 Waiting for Pokemon cards to load...")
        
        try:
            # Wait for Pokemon cards to appear
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "img, [style*='background-image'], video, .pokemon-card, .card"))
            )
            
            # Let the page fully load
            time.sleep(5)
            
            # Scroll down to trigger lazy loading
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            # Look for Pokemon images with various selectors
            image_selectors = [
                "img[src*='pokemon']",
                "img[src*='pkm']", 
                "img[src*='sprite']",
                "img[alt*='pokemon']",
                "img[alt*='pkm']",
                "img",  # All images as fallback
                "video[src*='pokemon']",
                "video[src*='trainer']",
                "video",  # All videos
            ]
            
            for selector in image_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    print(f"Found {len(elements)} elements with selector: {selector}")
                    
                    for element in elements:
                        try:
                            # Get image/video source
                            src = element.get_attribute('src')
                            if src and src.startswith('http'):
                                image_urls.add(src)
                                
                                # Get additional info
                                alt_text = element.get_attribute('alt') or ''
                                title = element.get_attribute('title') or ''
                                
                                pokemon_data.append({
                                    'url': src,
                                    'alt': alt_text,
                                    'title': title,
                                    'type': 'video' if element.tag_name == 'video' else 'image',
                                    'generation': generation
                                })
                        except Exception as e:
                            continue
                            
                except Exception as e:
                    print(f"Error with selector {selector}: {e}")
                    continue
            
            # Look for background images in style attributes
            elements_with_bg = driver.find_elements(By.CSS_SELECTOR, "[style*='background-image']")
            for element in elements_with_bg:
                try:
                    style = element.get_attribute('style')
                    bg_matches = re.findall(r'background-image:\s*url\(["\']?([^)"\'\s]+)["\']?\)', style)
                    for match in bg_matches:
                        if match.startswith('http'):
                            image_urls.add(match)
                            pokemon_data.append({
                                'url': match,
                                'alt': 'background-image',
                                'title': '',
                                'type': 'background',
                                'generation': generation
                            })
                except Exception as e:
                    continue
            
            # Look for data attributes that might contain image URLs
            data_selectors = [
                "[data-src]",
                "[data-image]", 
                "[data-background]"
            ]
            
            for selector in data_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        for attr in ['data-src', 'data-image', 'data-background']:
                            src = element.get_attribute(attr)
                            if src and src.startswith('http'):
                                image_urls.add(src)
                                pokemon_data.append({
                                    'url': src,
                                    'alt': f'data-{attr}',
                                    'title': '',
                                    'type': 'data-image',
                                    'generation': generation
                                })
                except Exception as e:
                    continue
            
            print(f"📊 Found {len(image_urls)} unique media URLs for Generation {generation}")
            
        except Exception as e:
            print(f"❌ Error extracting Pokemon data: {e}")
        
        return list(image_urls), pokemon_data
    
    def categorize_and_download_media(self, media_urls, pokemon_data, generation):
        """Categorize and download media files"""
        print(f"📥 Starting download of {len(media_urls)} media files for Generation {generation}...")
        
        def download_media_item(url):
            try:
                # Determine file category and path
                url_lower = url.lower()
                
                if any(keyword in url_lower for keyword in ['trainer', 'pack', 'claw']):
                    category = 'trainer_packs'
                    subdir = 'trainer_packs'
                elif any(keyword in url_lower for keyword in ['sprite', 'icon']):
                    category = 'sprites'
                    subdir = 'pokemon_sprites'
                elif any(keyword in url_lower for keyword in ['.mp4', '.webm', '.gif']):
                    category = 'animations'
                    subdir = 'animations'
                else:
                    category = 'pokemon_images'
                    subdir = 'pokemon_cards'
                
                # Generate filename
                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path)
                if not filename or '.' not in filename:
                    filename = f"media_{abs(hash(url))}.{'mp4' if '.mp4' in url else 'png'}"
                
                filename = self.clean_filename(filename)
                local_path = self.output_dir / f"generation_{generation}" / subdir / filename
                
                return self.download_file(url, local_path, category)
            except Exception as e:
                print(f"❌ Error downloading {url}: {e}")
                return False
        
        # Download with threading
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(download_media_item, url) for url in media_urls]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"❌ Download error: {e}")
        
        # Save Pokemon data as JSON
        data_file = self.output_dir / f"generation_{generation}" / "data" / "pokemon_data.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(pokemon_data, f, indent=2, ensure_ascii=False)
    
    def scrape_generation(self, generation):
        """Scrape a specific Pokemon generation"""
        print(f"\n🎮 Scraping Pokemon Generation {generation} (Browser Mode)")
        print("=" * 70)
        
        driver = None
        try:
            driver = self.setup_browser()
            generation_url = f"{self.base_url}/pokemon/generation/{generation}"
            
            print(f"🌐 Loading: {generation_url}")
            driver.get(generation_url)
            
            # Wait for initial page load
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Extract Pokemon data and media URLs
            media_urls, pokemon_data = self.extract_pokemon_data_from_page(driver, generation)
            
            if media_urls:
                # Download all media
                self.categorize_and_download_media(media_urls, pokemon_data, generation)
            else:
                print(f"⚠️  No media found for Generation {generation}")
            
            print(f"✅ Generation {generation} scraping completed!")
            
        except Exception as e:
            print(f"❌ Error scraping Generation {generation}: {e}")
        
        finally:
            if driver:
                driver.quit()
    
    def scrape_generations(self, generations):
        """Scrape multiple Pokemon generations"""
        print(f"🚀 Starting Phygitals Browser-Based Pokemon Scraper")
        print(f"📊 Generations to scrape: {generations}")
        print(f"📁 Output directory: {self.output_dir}")
        print("=" * 80)
        
        start_time = time.time()
        
        for generation in generations:
            try:
                self.scrape_generation(generation)
                time.sleep(2)  # Brief pause between generations
            except KeyboardInterrupt:
                print(f"\n⏹️  Scraping stopped by user at Generation {generation}")
                break
            except Exception as e:
                print(f"❌ Error processing Generation {generation}: {e}")
                continue
        
        self.print_summary(time.time() - start_time)
    
    def print_summary(self, elapsed_time):
        """Print comprehensive download summary"""
        print("\n" + "=" * 80)
        print("📊 BROWSER SCRAPING SUMMARY")
        print("=" * 80)
        
        total_files = sum(self.download_stats.values()) - self.download_stats['failed']
        
        print(f"✅ Total files downloaded: {total_files}")
        print(f"🎮 Pokemon images: {self.download_stats['pokemon_images']}")
        print(f"🎬 Animations: {self.download_stats['animations']}")
        print(f"📦 Trainer packs: {self.download_stats['trainer_packs']}")
        print(f"🖼️  Sprites: {self.download_stats['sprites']}")
        print(f"❌ Failed downloads: {self.download_stats['failed']}")
        print(f"⏱️  Total time: {elapsed_time:.2f} seconds")
        print(f"📁 Files saved to: {self.output_dir}")
        
        if self.failed_downloads:
            print(f"\n⚠️  Failed URLs (first 10):")
            for url in self.failed_downloads[:10]:
                print(f"   {url}")
        
        print(f"\n🎉 Browser scraping complete!")

def main():
    parser = argparse.ArgumentParser(description="Browser-based Pokemon scraper for Phygitals.com")
    parser.add_argument("--output", "-o", default="phygitals_dynamic_pokemon",
                       help="Output directory (default: phygitals_dynamic_pokemon)")
    parser.add_argument("--generations", "-g", nargs="+", type=int,
                       help="Specific generations to scrape (e.g., -g 1 2 3)")
    parser.add_argument("--headless", action="store_true", default=True,
                       help="Run browser in headless mode (default: True)")
    parser.add_argument("--show-browser", action="store_true",
                       help="Show browser window (opposite of headless)")
    
    # Shortcuts
    parser.add_argument("--demo", action="store_true",
                       help="Quick demo - Generation 1 only")
    parser.add_argument("--classic", action="store_true",
                       help="Generations 1-3")
    parser.add_argument("--all", action="store_true",
                       help="All generations 1-9")
    
    args = parser.parse_args()
    
    # Determine generations
    if args.demo:
        generations = [1]
    elif args.classic:
        generations = [1, 2, 3]
    elif args.all:
        generations = list(range(1, 10))
    elif args.generations:
        generations = args.generations
    else:
        generations = [1]  # Default demo
    
    # Determine headless mode
    headless = args.headless and not args.show_browser
    
    # Create and run scraper
    scraper = PhygitalsBrowserScraper(args.output, headless=headless)
    scraper.scrape_generations(generations)

if __name__ == "__main__":
    main() 