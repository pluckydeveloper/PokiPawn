#!/usr/bin/env python3
"""
Phygitals Image Fix Scraper - Focused on proper image extraction
"""

import os
import requests
import json
import time
from urllib.parse import urljoin, urlparse
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import hashlib

class PhygitalsImageFixScraper:
    def __init__(self, output_dir="phygitals_with_images"):
        self.base_url = "https://www.phygitals.com"
        self.output_dir = Path(output_dir)
        self.session = requests.Session()
        
        self.stats = {
            'pokemon_found': 0,
            'images_downloaded': 0,
            'animations_downloaded': 0,
            'total_size_mb': 0
        }
        
        self.output_dir.mkdir(exist_ok=True)
        (self.output_dir / "pokemon_images").mkdir(exist_ok=True)
        (self.output_dir / "pokemon_animations").mkdir(exist_ok=True)
        (self.output_dir / "metadata").mkdir(exist_ok=True)
        
        self.setup_selenium()
        
    def setup_selenium(self):
        """Setup Selenium"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 30)
        
    def download_asset(self, url, local_path, asset_type="image"):
        """Download asset with proper error handling"""
        try:
            if local_path.exists():
                return True
                
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': self.base_url,
                'Accept': 'image/*,*/*;q=0.9'
            }
            
            response = self.session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            file_size_mb = len(response.content) / (1024 * 1024)
            self.stats['total_size_mb'] += file_size_mb
            
            if asset_type == "animation":
                self.stats['animations_downloaded'] += 1
            else:
                self.stats['images_downloaded'] += 1
            
            print(f"✅ Downloaded {asset_type}: {os.path.basename(local_path)} ({file_size_mb:.2f}MB)")
            return True
            
        except Exception as e:
            print(f"❌ Failed to download {url}: {e}")
            return False
    
    def extract_pokemon_images_enhanced(self, generation_num):
        """Enhanced image extraction for a generation"""
        print(f"\n🎮 Enhanced scraping for Generation {generation_num}...")
        
        generation_url = f"{self.base_url}/pokemon/generation/{generation_num}"
        
        try:
            self.driver.get(generation_url)
            time.sleep(5)
            
            # Wait for page load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Scroll to load all images
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            # Get all images on the page
            all_images = self.driver.find_elements(By.CSS_SELECTOR, "img")
            print(f"  📷 Total images found: {len(all_images)}")
            
            pokemon_images = []
            unique_urls = set()
            
            for i, img in enumerate(all_images):
                try:
                    # Get all possible image sources
                    img_src = img.get_attribute('src')
                    img_data_src = img.get_attribute('data-src')
                    img_srcset = img.get_attribute('srcset')
                    img_alt = img.get_attribute('alt') or ''
                    
                    # Check each potential source
                    for src in [img_src, img_data_src]:
                        if src and src.startswith('http') and src not in unique_urls:
                            # Filter for Pokemon-related images
                            if any(term in src.lower() for term in ['pokemon', 'sprite', 'card', 'pkmn']):
                                unique_urls.add(src)
                                
                                img_type = 'animation' if '.gif' in src.lower() else 'image'
                                
                                pokemon_images.append({
                                    'url': src,
                                    'alt': img_alt,
                                    'type': img_type,
                                    'generation': generation_num
                                })
                                
                                print(f"  🎯 Found Pokemon {img_type}: {src.split('/')[-1]}")
                
                except Exception as e:
                    continue
            
            print(f"  ✅ Total unique Pokemon images: {len(pokemon_images)}")
            
            # Download all found images
            downloaded = 0
            for img_data in pokemon_images:
                url = img_data['url']
                img_type = img_data['type']
                
                # Generate filename
                url_path = urlparse(url).path
                original_filename = os.path.basename(url_path)
                
                if not original_filename or '.' not in original_filename:
                    ext = '.gif' if img_type == 'animation' else '.png'
                    original_filename = f"gen{generation_num}_{hashlib.md5(url.encode()).hexdigest()[:8]}{ext}"
                
                # Organize by type
                if img_type == 'animation':
                    local_path = self.output_dir / f"pokemon_animations/gen_{generation_num}_{original_filename}"
                else:
                    local_path = self.output_dir / f"pokemon_images/gen_{generation_num}_{original_filename}"
                
                if self.download_asset(url, local_path, img_type):
                    downloaded += 1
            
            # Save metadata
            metadata = {
                'generation': generation_num,
                'url': generation_url,
                'images_found': len(pokemon_images),
                'images_downloaded': downloaded,
                'pokemon_images': pokemon_images,
                'scraped_at': datetime.now().isoformat()
            }
            
            with open(self.output_dir / f"metadata/generation_{generation_num}.json", 'w') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            self.stats['pokemon_found'] += len(pokemon_images)
            
            print(f"✅ Generation {generation_num}: {len(pokemon_images)} images found, {downloaded} downloaded")
            return pokemon_images
            
        except Exception as e:
            print(f"❌ Error scraping Generation {generation_num}: {e}")
            return []
    
    def test_specific_generations(self, generations=[1, 2, 3]):
        """Test specific generations to verify the fix works"""
        print("🧪 TESTING IMAGE EXTRACTION FIX")
        print("="*50)
        
        start_time = datetime.now()
        all_images = []
        
        try:
            for gen in generations:
                gen_images = self.extract_pokemon_images_enhanced(gen)
                all_images.extend(gen_images)
                time.sleep(2)
            
            # Create summary
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds() / 60
            
            summary = {
                'test_summary': {
                    'generations_tested': generations,
                    'duration_minutes': duration,
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat()
                },
                'results': {
                    'total_images_found': len(all_images),
                    'images_downloaded': self.stats['images_downloaded'],
                    'animations_downloaded': self.stats['animations_downloaded'],
                    'total_size_mb': self.stats['total_size_mb']
                }
            }
            
            with open(self.output_dir / "metadata/test_summary.json", 'w') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            print("\n" + "="*50)
            print("🧪 IMAGE EXTRACTION TEST COMPLETED!")
            print("="*50)
            print(f"⏱️  Duration: {duration:.1f} minutes")
            print(f"🎮 Generations Tested: {len(generations)}")
            print(f"🖼️  Total Images Found: {len(all_images)}")
            print(f"📥 Images Downloaded: {self.stats['images_downloaded']}")
            print(f"🎬 Animations Downloaded: {self.stats['animations_downloaded']}")
            print(f"💾 Total Size: {self.stats['total_size_mb']:.2f}MB")
            print(f"📁 Output: {self.output_dir.absolute()}")
            
            # Test success rate
            success_rate = (self.stats['images_downloaded'] / len(all_images) * 100) if all_images else 0
            print(f"📊 Download Success Rate: {success_rate:.1f}%")
            
            if success_rate > 50:
                print("✅ Image extraction fix is working!")
                print("🚀 Ready to run full scrape on all generations")
            else:
                print("⚠️  Image extraction needs further adjustment")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
        finally:
            if hasattr(self, 'driver'):
                self.driver.quit()

def main():
    print("🧪 PHYGITALS IMAGE EXTRACTION FIX TEST")
    print("="*45)
    print("Testing improved image extraction on Generation 1-3")
    print()
    
    confirm = input("Run image extraction test? [y/N]: ")
    if confirm.lower() != 'y':
        print("Test cancelled.")
        return
    
    scraper = PhygitalsImageFixScraper()
    scraper.test_specific_generations([1, 2, 3])

if __name__ == "__main__":
    main() 