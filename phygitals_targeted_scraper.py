#!/usr/bin/env python3
"""
Phygitals.com Targeted Scraper - Using Correct URL Structure
Based on site inspection findings: Pokemon content is at /pokemon/generation/{num}
"""

import os
import requests
import json
import time
import re
from urllib.parse import urljoin, urlparse
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime
import hashlib

class PhygitalsTargetedScraper:
    def __init__(self, output_dir="phygitals_targeted_complete"):
        self.base_url = "https://www.phygitals.com"
        self.output_dir = Path(output_dir)
        self.session = requests.Session()
        self.pokemon_data = {}
        self.failed_downloads = []
        
        # Statistics
        self.stats = {
            'generations_scraped': 0,
            'pokemon_found': 0,
            'images_downloaded': 0,
            'animations_downloaded': 0,
            'total_size_mb': 0,
            'pages_captured': 0
        }
        
        self.setup_directories()
        self.setup_selenium()
        
    def setup_directories(self):
        """Create organized directory structure"""
        directories = [
            "pokemon_data",
            "pokemon_images", 
            "pokemon_animations",
            "site_assets",
            "pages",
            "metadata",
            "logs"
        ]
        
        for directory in directories:
            (self.output_dir / directory).mkdir(parents=True, exist_ok=True)
            
        print(f"📁 Created directory structure in: {self.output_dir}")
        
    def setup_selenium(self):
        """Setup Selenium with proper configuration"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 30)
        
    def download_asset(self, url, local_path, asset_type="asset"):
        """Download asset with proper error handling"""
        try:
            if local_path.exists():
                return True
                
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': self.base_url,
                'Accept': '*/*'
            }
            
            response = self.session.get(url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()
            
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            downloaded = 0
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
            
            file_size_mb = downloaded / (1024 * 1024)
            self.stats['total_size_mb'] += file_size_mb
            
            if asset_type == "animation":
                self.stats['animations_downloaded'] += 1
            else:
                self.stats['images_downloaded'] += 1
            
            print(f"✅ Downloaded {asset_type}: {os.path.basename(local_path)} ({file_size_mb:.2f}MB)")
            return True
            
        except Exception as e:
            print(f"❌ Failed to download {url}: {e}")
            self.failed_downloads.append({'url': url, 'error': str(e), 'type': asset_type})
            return False
    
    def scrape_generation(self, generation_num):
        """Scrape a specific generation using correct URL structure"""
        print(f"\n🎮 Scraping Generation {generation_num}...")
        
        # Use the correct URL structure discovered in inspection
        generation_url = f"{self.base_url}/pokemon/generation/{generation_num}"
        
        try:
            self.driver.get(generation_url)
            time.sleep(5)
            
            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Check if page loaded successfully
            page_title = self.driver.title
            if "404" in page_title:
                print(f"❌ Generation {generation_num} page not found")
                return []
            
            print(f"📄 Loaded: {page_title}")
            
            # Scroll to ensure all content loads
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            # Try multiple selectors to find Pokemon content
            pokemon_selectors = [
                ".pokemon-card",
                ".card", 
                ".item",
                "[data-pokemon]",
                ".pokemon",
                ".grid-item",
                ".gallery-item",
                ".marketplace-item",
                "img[src*='pokemon']",
                "img[alt*='pokemon']"
            ]
            
            all_pokemon_elements = []
            for selector in pokemon_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        print(f"  📋 Found {len(elements)} elements with selector: {selector}")
                        all_pokemon_elements.extend(elements)
                except:
                    continue
            
            # Remove duplicates
            unique_elements = list(set(all_pokemon_elements))
            print(f"  🎯 Total unique Pokemon elements: {len(unique_elements)}")
            
            generation_pokemon = []
            for i, element in enumerate(unique_elements):
                try:
                    pokemon_data = self.extract_pokemon_data(element, generation_num, generation_url)
                    if pokemon_data:
                        generation_pokemon.append(pokemon_data)
                        
                        # Download media for this Pokemon
                        self.download_pokemon_media(pokemon_data, generation_num)
                        
                except Exception as e:
                    print(f"  ⚠️  Error processing element {i}: {e}")
                    continue
            
            # Save page HTML
            page_html = self.driver.page_source
            page_file = self.output_dir / f"pages/generation_{generation_num}.html"
            with open(page_file, 'w', encoding='utf-8') as f:
                f.write(page_html)
            
            # Save generation metadata
            generation_metadata = {
                'generation': generation_num,
                'url': generation_url,
                'pokemon_count': len(generation_pokemon),
                'pokemon': generation_pokemon,
                'scraped_at': datetime.now().isoformat()
            }
            
            metadata_file = self.output_dir / f"pokemon_data/generation_{generation_num}.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(generation_metadata, f, indent=2, ensure_ascii=False)
            
            self.stats['generations_scraped'] += 1
            self.stats['pokemon_found'] += len(generation_pokemon)
            self.stats['pages_captured'] += 1
            
            print(f"✅ Generation {generation_num}: {len(generation_pokemon)} Pokemon captured")
            return generation_pokemon
            
        except Exception as e:
            print(f"❌ Error scraping Generation {generation_num}: {e}")
            return []
    
    def extract_pokemon_data(self, element, generation, source_url):
        """Extract Pokemon data from element"""
        try:
            pokemon_data = {
                'generation': generation,
                'source_url': source_url,
                'extracted_at': datetime.now().isoformat(),
                'images': [],
                'text_content': '',
                'attributes': {}
            }
            
            # Get text content
            text_content = element.text.strip()
            pokemon_data['text_content'] = text_content
            
            # Try to extract Pokemon number from text
            number_match = re.search(r'#?(\d{1,4})', text_content)
            if number_match:
                pokemon_data['number'] = int(number_match.group(1))
            
            # Extract all images
            try:
                img_elements = element.find_elements(By.CSS_SELECTOR, "img")
                for img in img_elements:
                    img_src = img.get_attribute('src')
                    img_alt = img.get_attribute('alt')
                    img_data_src = img.get_attribute('data-src')
                    
                    for src in [img_src, img_data_src]:
                        if src and src.startswith('http'):
                            pokemon_data['images'].append({
                                'url': src,
                                'alt': img_alt or '',
                                'type': self.classify_image_type(src)
                            })
            except:
                pass
            
            # Get element attributes
            try:
                for attr in ['id', 'class', 'data-pokemon', 'data-id']:
                    value = element.get_attribute(attr)
                    if value:
                        pokemon_data['attributes'][attr] = value
            except:
                pass
            
            # Only return if we found useful data
            if pokemon_data['images'] or pokemon_data['text_content'] or pokemon_data['attributes']:
                return pokemon_data
            
            return None
            
        except Exception as e:
            print(f"  ⚠️  Error extracting Pokemon data: {e}")
            return None
    
    def classify_image_type(self, url):
        """Classify image type from URL"""
        url_lower = url.lower()
        if '.gif' in url_lower:
            return 'animation'
        elif any(term in url_lower for term in ['sprite', 'pokemon']):
            return 'sprite'
        elif 'card' in url_lower:
            return 'card'
        else:
            return 'image'
    
    def download_pokemon_media(self, pokemon_data, generation):
        """Download all media for a Pokemon"""
        if not pokemon_data.get('images'):
            return
            
        for img_data in pokemon_data['images']:
            url = img_data['url']
            img_type = img_data['type']
            
            # Generate filename
            url_path = urlparse(url).path
            original_filename = os.path.basename(url_path)
            
            if not original_filename or '.' not in original_filename:
                ext = '.gif' if img_type == 'animation' else '.png'
                original_filename = f"gen{generation}_{hashlib.md5(url.encode()).hexdigest()[:8]}{ext}"
            
            # Organize by type
            if img_type == 'animation':
                local_path = self.output_dir / f"pokemon_animations/gen_{generation}_{original_filename}"
            else:
                local_path = self.output_dir / f"pokemon_images/gen_{generation}_{original_filename}"
            
            self.download_asset(url, local_path, img_type)
    
    def scrape_marketplace(self):
        """Scrape the marketplace for additional Pokemon content"""
        print("\n🏪 Scraping marketplace for Pokemon content...")
        
        marketplace_url = f"{self.base_url}/marketplace"
        
        try:
            self.driver.get(marketplace_url)
            time.sleep(5)
            
            # Scroll through marketplace
            self.driver.execute_script("""
                var totalHeight = 0;
                var distance = 100;
                var timer = setInterval(() => {
                    var scrollHeight = document.body.scrollHeight;
                    window.scrollBy(0, distance);
                    totalHeight += distance;
                    if(totalHeight >= scrollHeight){
                        clearInterval(timer);
                    }
                }, 100);
            """)
            time.sleep(10)
            
            # Find Pokemon items in marketplace
            marketplace_selectors = [
                ".card",
                ".item", 
                ".marketplace-item",
                "img[alt*='pokemon']",
                "[data-pokemon]"
            ]
            
            marketplace_pokemon = []
            for selector in marketplace_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        print(f"  📋 Found {len(elements)} marketplace items with: {selector}")
                        
                        for element in elements:
                            pokemon_data = self.extract_pokemon_data(element, 'marketplace', marketplace_url)
                            if pokemon_data:
                                marketplace_pokemon.append(pokemon_data)
                                self.download_pokemon_media(pokemon_data, 'marketplace')
                except:
                    continue
            
            # Save marketplace data
            marketplace_metadata = {
                'source': 'marketplace',
                'url': marketplace_url,
                'pokemon_count': len(marketplace_pokemon),
                'pokemon': marketplace_pokemon,
                'scraped_at': datetime.now().isoformat()
            }
            
            with open(self.output_dir / "pokemon_data/marketplace.json", 'w', encoding='utf-8') as f:
                json.dump(marketplace_metadata, f, indent=2, ensure_ascii=False)
            
            # Save marketplace HTML
            with open(self.output_dir / "pages/marketplace.html", 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            
            print(f"✅ Marketplace: {len(marketplace_pokemon)} Pokemon items captured")
            return marketplace_pokemon
            
        except Exception as e:
            print(f"❌ Error scraping marketplace: {e}")
            return []
    
    def create_offline_viewer(self):
        """Create offline viewer for captured content"""
        print("\n🌐 Creating offline viewer...")
        
        viewer_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Phygitals Pokemon - Complete Collection</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ text-align: center; margin-bottom: 40px; }}
        .header h1 {{ font-size: 3em; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 40px 0; }}
        .stat-card {{ background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; text-align: center; backdrop-filter: blur(10px); }}
        .stat-number {{ font-size: 2em; font-weight: bold; color: #FFD700; }}
        .generations {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }}
        .gen-card {{ background: rgba(255,255,255,0.15); padding: 25px; border-radius: 15px; transition: transform 0.3s; }}
        .gen-card:hover {{ transform: translateY(-5px); }}
        .nav-button {{ display: inline-block; padding: 12px 24px; background: rgba(255,255,255,0.2); color: white; text-decoration: none; border-radius: 25px; margin: 10px; }}
        .nav-button:hover {{ background: rgba(255,255,255,0.3); }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎮 Phygitals Pokemon Complete Collection</h1>
            <p>Your complete offline mirror with {self.stats['pokemon_found']} Pokemon</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{self.stats['generations_scraped']}</div>
                <div>Generations Scraped</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{self.stats['pokemon_found']}</div>
                <div>Pokemon Found</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{self.stats['images_downloaded']}</div>
                <div>Images Downloaded</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{self.stats['total_size_mb']:.1f}MB</div>
                <div>Total Size</div>
            </div>
        </div>
        
        <div style="text-align: center; margin: 40px 0;">
            <a href="pokemon_data/" class="nav-button">📁 Pokemon Data</a>
            <a href="pokemon_images/" class="nav-button">🖼️ Images</a>
            <a href="pokemon_animations/" class="nav-button">🎬 Animations</a>
            <a href="pages/" class="nav-button">📄 Pages</a>
        </div>
        
        <div class="generations">
"""
        
        # Add generation cards
        for gen in range(1, 10):
            metadata_file = self.output_dir / f"pokemon_data/generation_{gen}.json"
            pokemon_count = 0
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                        pokemon_count = metadata.get('pokemon_count', 0)
                except:
                    pass
            
            if pokemon_count > 0:
                viewer_html += f"""
            <div class="gen-card">
                <h3>Generation {gen}</h3>
                <p>{pokemon_count} Pokemon</p>
                <a href="pokemon_data/generation_{gen}.json" class="nav-button">View Data</a>
            </div>
"""
        
        viewer_html += """
        </div>
        
        <div style="text-align: center; margin: 40px 0; opacity: 0.8;">
            <p>🕐 Complete offline collection - no internet required!</p>
        </div>
    </div>
</body>
</html>"""
        
        with open(self.output_dir / "index.html", 'w', encoding='utf-8') as f:
            f.write(viewer_html)
        
        print("✅ Offline viewer created")
    
    def run_targeted_scrape(self):
        """Run the targeted scraping operation"""
        start_time = datetime.now()
        print("🎯 PHYGITALS.COM TARGETED SCRAPING")
        print("="*50)
        print("Using correct URL structure discovered in site inspection")
        print(f"📅 Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            all_pokemon = []
            
            # Scrape generations 1-9
            for generation in range(1, 10):
                generation_pokemon = self.scrape_generation(generation)
                all_pokemon.extend(generation_pokemon)
                time.sleep(2)  # Be respectful
            
            # Scrape marketplace for additional content
            marketplace_pokemon = self.scrape_marketplace()
            all_pokemon.extend(marketplace_pokemon)
            
            # Create offline viewer
            self.create_offline_viewer()
            
            # Save final report
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds() / 60
            
            final_report = {
                'scrape_summary': {
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'duration_minutes': duration,
                    'scraper_version': 'Targeted v1.0'
                },
                'statistics': self.stats,
                'total_pokemon': len(all_pokemon),
                'failed_downloads': self.failed_downloads
            }
            
            with open(self.output_dir / "metadata/final_report.json", 'w', encoding='utf-8') as f:
                json.dump(final_report, f, indent=2, ensure_ascii=False)
            
            # Success report
            print("\n" + "="*60)
            print("🎉 TARGETED SCRAPING COMPLETED!")
            print("="*60)
            print(f"⏱️  Duration: {duration:.1f} minutes")
            print(f"🎮 Generations Scraped: {self.stats['generations_scraped']}")
            print(f"🔥 Total Pokemon Found: {self.stats['pokemon_found']}")
            print(f"🖼️  Images Downloaded: {self.stats['images_downloaded']}")
            print(f"🎬 Animations Downloaded: {self.stats['animations_downloaded']}")
            print(f"💾 Total Size: {self.stats['total_size_mb']:.2f}MB")
            print(f"📁 Output: {self.output_dir.absolute()}")
            print(f"🌐 Viewer: file://{self.output_dir.absolute()}/index.html")
            
            if self.failed_downloads:
                print(f"⚠️  {len(self.failed_downloads)} downloads failed")
            
            print("\n✅ Your targeted Phygitals collection is ready!")
            
        except KeyboardInterrupt:
            print("\n⏹️  Scraping interrupted by user")
        except Exception as e:
            print(f"\n❌ Critical error: {e}")
        finally:
            if hasattr(self, 'driver'):
                self.driver.quit()

def main():
    print("🎯 PHYGITALS TARGETED SCRAPER")
    print("="*40)
    print("Using correct URL structure: /pokemon/generation/{num}")
    print()
    
    confirm = input("Start targeted scraping with correct URLs? [y/N]: ")
    if confirm.lower() != 'y':
        print("Scraping cancelled.")
        return
    
    scraper = PhygitalsTargetedScraper()
    scraper.run_targeted_scrape()

if __name__ == "__main__":
    main() 