#!/usr/bin/env python3
"""
Phygitals.com Complete Site Mirror Scraper
Creates a fully functional offline copy of the entire Phygitals Pokemon site
"""

import os
import requests
import json
import time
import re
from urllib.parse import urljoin, urlparse, parse_qs
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime
import hashlib
from bs4 import BeautifulSoup
import mimetypes

class PhygitalsCompleteMirror:
    def __init__(self, output_dir="phygitals_complete_mirror"):
        self.base_url = "https://www.phygitals.com"
        self.pokemon_base = f"{self.base_url}/pokemon/"
        self.output_dir = Path(output_dir)
        self.session = requests.Session()
        self.downloaded_files = {}
        self.site_map = {}
        self.scraped_urls = set()
        self.failed_downloads = []
        
        # Statistics
        self.stats = {
            'pokemon_downloaded': 0,
            'assets_downloaded': 0,
            'pages_scraped': 0,
            'total_size_mb': 0,
            'generations_found': 0
        }
        
        # Setup directories
        self.setup_directories()
        
        # Setup Selenium
        self.setup_selenium()
        
    def setup_directories(self):
        """Create comprehensive directory structure for complete site mirror"""
        directories = [
            # Core site structure
            "assets/css",
            "assets/js", 
            "assets/fonts",
            "assets/images",
            "assets/icons",
            "assets/sounds",
            "assets/videos",
            
            # Pokemon data by generation
            "pokemon/generation_1",
            "pokemon/generation_2", 
            "pokemon/generation_3",
            "pokemon/generation_4",
            "pokemon/generation_5",
            "pokemon/generation_6",
            "pokemon/generation_7",
            "pokemon/generation_8",
            "pokemon/generation_9",
            
            # Pokemon assets
            "pokemon_assets/sprites",
            "pokemon_assets/animations",
            "pokemon_assets/cards",
            "pokemon_assets/backgrounds",
            "pokemon_assets/sounds",
            
            # Site pages
            "pages",
            "pages/pokemon",
            "pages/generations",
            "pages/features",
            
            # Navigation and components
            "components/navigation",
            "components/ui",
            "components/interactive",
            
            # Metadata and references
            "metadata",
            "reference",
            "logs"
        ]
        
        for directory in directories:
            (self.output_dir / directory).mkdir(parents=True, exist_ok=True)
            
        print(f"📁 Created directory structure in: {self.output_dir}")
        
    def setup_selenium(self):
        """Setup Selenium with optimal settings for comprehensive scraping"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Enable additional features for comprehensive capture
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-web-security")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
        
    def safe_filename(self, filename):
        """Create safe filename for filesystem"""
        # Remove invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Limit length
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:190] + ext
        return filename
        
    def download_asset(self, url, local_path, asset_type="asset"):
        """Download any asset (image, CSS, JS, etc.) with proper handling"""
        try:
            # Skip if already downloaded
            if local_path.exists():
                return True
                
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': self.base_url,
                'Accept': '*/*'
            }
            
            response = self.session.get(url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()
            
            # Create parent directory
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download with progress tracking
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
            
            # Update statistics
            file_size_mb = downloaded / (1024 * 1024)
            self.stats['total_size_mb'] += file_size_mb
            self.stats['assets_downloaded'] += 1
            
            print(f"✅ Downloaded {asset_type}: {url.split('/')[-1]} ({file_size_mb:.2f}MB)")
            return True
            
        except Exception as e:
            print(f"❌ Failed to download {asset_type} {url}: {e}")
            self.failed_downloads.append({'url': url, 'error': str(e), 'type': asset_type})
            return False
    
    def discover_site_structure(self):
        """Discover and map the complete site structure"""
        print("🗺️  Discovering site structure...")
        
        try:
            self.driver.get(self.pokemon_base)
            time.sleep(5)
            
            # Discover all navigation links
            nav_links = self.driver.find_elements(By.CSS_SELECTOR, "nav a, .navigation a, .menu a")
            
            # Discover generation links
            generation_links = self.driver.find_elements(By.CSS_SELECTOR, "[href*='generation'], [data-generation]")
            
            # Discover feature links
            feature_links = self.driver.find_elements(By.CSS_SELECTOR, "[href*='pokemon'], [href*='card'], [href*='animation']")
            
            # Map all discovered URLs
            all_links = nav_links + generation_links + feature_links
            
            for link in all_links:
                try:
                    href = link.get_attribute('href')
                    text = link.text.strip()
                    if href and href.startswith(self.base_url):
                        self.site_map[href] = {
                            'text': text,
                            'type': self.classify_link(href),
                            'discovered': True
                        }
                except:
                    continue
                    
            print(f"🗺️  Discovered {len(self.site_map)} unique URLs")
            
        except Exception as e:
            print(f"⚠️  Error discovering site structure: {e}")
    
    def classify_link(self, url):
        """Classify link type for organized scraping"""
        url_lower = url.lower()
        if 'generation' in url_lower:
            return 'generation'
        elif 'pokemon' in url_lower:
            return 'pokemon'
        elif 'card' in url_lower:
            return 'card'
        elif 'animation' in url_lower:
            return 'animation'
        else:
            return 'general'
    
    def scrape_complete_generation(self, generation_num):
        """Scrape a complete generation with all Pokemon and assets"""
        print(f"\n🎮 Scraping Generation {generation_num} completely...")
        
        generation_dir = self.output_dir / f"pokemon/generation_{generation_num}"
        generation_dir.mkdir(parents=True, exist_ok=True)
        
        generation_url = f"{self.pokemon_base}generation-{generation_num}/"
        
        try:
            self.driver.get(generation_url)
            time.sleep(3)
            
            # Wait for page to load completely
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Capture page HTML
            page_html = self.driver.page_source
            with open(generation_dir / "index.html", 'w', encoding='utf-8') as f:
                f.write(page_html)
            
            # Find all Pokemon in this generation
            pokemon_elements = self.driver.find_elements(By.CSS_SELECTOR, ".pokemon-card, .pokemon-item, [data-pokemon], .pokemon")
            
            generation_pokemon = []
            
            for pokemon_element in pokemon_elements:
                try:
                    # Extract Pokemon data
                    pokemon_data = self.extract_pokemon_data(pokemon_element, generation_num)
                    if pokemon_data:
                        generation_pokemon.append(pokemon_data)
                        
                        # Download Pokemon assets
                        self.download_pokemon_assets(pokemon_data, generation_num)
                        
                except Exception as e:
                    print(f"⚠️  Error processing Pokemon in Gen {generation_num}: {e}")
                    continue
            
            # Save generation metadata
            generation_metadata = {
                'generation': generation_num,
                'pokemon_count': len(generation_pokemon),
                'pokemon': generation_pokemon,
                'scraped_at': datetime.now().isoformat(),
                'source_url': generation_url
            }
            
            with open(generation_dir / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(generation_metadata, f, indent=2, ensure_ascii=False)
            
            self.stats['generations_found'] += 1
            print(f"✅ Generation {generation_num}: {len(generation_pokemon)} Pokemon captured")
            
            return generation_pokemon
            
        except Exception as e:
            print(f"❌ Failed to scrape Generation {generation_num}: {e}")
            return []
    
    def extract_pokemon_data(self, element, generation):
        """Extract comprehensive Pokemon data from element"""
        try:
            pokemon_data = {
                'generation': generation,
                'extracted_at': datetime.now().isoformat()
            }
            
            # Try to extract Pokemon number
            number_element = element.find_element(By.CSS_SELECTOR, ".number, .pokemon-number, [data-number]")
            if number_element:
                pokemon_data['number'] = number_element.text.strip()
            
            # Try to extract Pokemon name
            name_element = element.find_element(By.CSS_SELECTOR, ".name, .pokemon-name, h3, h4")
            if name_element:
                pokemon_data['name'] = name_element.text.strip()
            
            # Try to extract sprite/image URLs
            img_elements = element.find_elements(By.CSS_SELECTOR, "img")
            pokemon_data['images'] = []
            
            for img in img_elements:
                img_src = img.get_attribute('src')
                img_alt = img.get_attribute('alt')
                if img_src:
                    pokemon_data['images'].append({
                        'url': img_src,
                        'alt': img_alt,
                        'type': self.classify_image_type(img_src)
                    })
            
            # Try to extract any animation URLs
            animation_elements = element.find_elements(By.CSS_SELECTOR, "[data-animation], [src*='.gif']")
            pokemon_data['animations'] = []
            
            for anim in animation_elements:
                anim_src = anim.get_attribute('src') or anim.get_attribute('data-animation')
                if anim_src:
                    pokemon_data['animations'].append(anim_src)
            
            return pokemon_data
            
        except Exception as e:
            print(f"⚠️  Error extracting Pokemon data: {e}")
            return None
    
    def classify_image_type(self, url):
        """Classify image type based on URL"""
        url_lower = url.lower()
        if '.gif' in url_lower:
            return 'animation'
        elif 'sprite' in url_lower:
            return 'sprite'
        elif 'card' in url_lower:
            return 'card'
        elif 'background' in url_lower:
            return 'background'
        else:
            return 'image'
    
    def download_pokemon_assets(self, pokemon_data, generation):
        """Download all assets for a specific Pokemon"""
        pokemon_dir = self.output_dir / f"pokemon/generation_{generation}/pokemon_assets"
        pokemon_dir.mkdir(parents=True, exist_ok=True)
        
        # Download images
        for img_data in pokemon_data.get('images', []):
            if img_data['url']:
                img_url = urljoin(self.base_url, img_data['url'])
                filename = self.safe_filename(os.path.basename(urlparse(img_url).path))
                if not filename:
                    filename = f"image_{hashlib.md5(img_url.encode()).hexdigest()[:8]}.png"
                
                local_path = pokemon_dir / img_data['type'] / filename
                self.download_asset(img_url, local_path, f"Pokemon {img_data['type']}")
        
        # Download animations
        for anim_url in pokemon_data.get('animations', []):
            if anim_url:
                anim_url = urljoin(self.base_url, anim_url)
                filename = self.safe_filename(os.path.basename(urlparse(anim_url).path))
                if not filename:
                    filename = f"animation_{hashlib.md5(anim_url.encode()).hexdigest()[:8]}.gif"
                
                local_path = pokemon_dir / "animations" / filename
                self.download_asset(anim_url, local_path, "Pokemon animation")
    
    def scrape_site_assets(self):
        """Scrape all site-wide assets (CSS, JS, fonts, etc.)"""
        print("\n🎨 Scraping site-wide assets...")
        
        try:
            self.driver.get(self.pokemon_base)
            time.sleep(3)
            
            # Get all CSS files
            css_links = self.driver.find_elements(By.CSS_SELECTOR, "link[rel='stylesheet']")
            for css_link in css_links:
                href = css_link.get_attribute('href')
                if href:
                    css_url = urljoin(self.base_url, href)
                    filename = self.safe_filename(os.path.basename(urlparse(css_url).path))
                    local_path = self.output_dir / "assets/css" / filename
                    self.download_asset(css_url, local_path, "CSS")
            
            # Get all JavaScript files
            js_scripts = self.driver.find_elements(By.CSS_SELECTOR, "script[src]")
            for js_script in js_scripts:
                src = js_script.get_attribute('src')
                if src:
                    js_url = urljoin(self.base_url, src)
                    filename = self.safe_filename(os.path.basename(urlparse(js_url).path))
                    local_path = self.output_dir / "assets/js" / filename
                    self.download_asset(js_url, local_path, "JavaScript")
            
            # Get all images
            images = self.driver.find_elements(By.CSS_SELECTOR, "img")
            for img in images:
                src = img.get_attribute('src')
                if src and not src.startswith('data:'):
                    img_url = urljoin(self.base_url, src)
                    filename = self.safe_filename(os.path.basename(urlparse(img_url).path))
                    local_path = self.output_dir / "assets/images" / filename
                    self.download_asset(img_url, local_path, "Site image")
            
            print("✅ Site assets scraped")
            
        except Exception as e:
            print(f"❌ Error scraping site assets: {e}")
    
    def create_offline_index(self):
        """Create a local index page for offline browsing"""
        print("\n📄 Creating offline index page...")
        
        index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Phygitals Pokemon - Offline Mirror</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        .generation-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .generation-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 20px;
            backdrop-filter: blur(10px);
        }
        .stats {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
        }
        .navigation {
            margin: 20px 0;
        }
        .nav-button {
            display: inline-block;
            padding: 10px 20px;
            background: rgba(255, 255, 255, 0.2);
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin: 5px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎮 Phygitals Pokemon - Complete Offline Mirror</h1>
        <p>Your complete local copy of Phygitals.com Pokemon collection</p>
    </div>
    
    <div class="navigation">
        <a href="assets/" class="nav-button">📁 Site Assets</a>
        <a href="pokemon/" class="nav-button">🎯 Pokemon Data</a>
        <a href="metadata/" class="nav-button">📊 Metadata</a>
        <a href="logs/" class="nav-button">📋 Logs</a>
    </div>
    
    <div class="generation-grid">
"""
        
        # Add generation cards
        for gen in range(1, 10):
            gen_dir = self.output_dir / f"pokemon/generation_{gen}"
            if gen_dir.exists():
                metadata_file = gen_dir / "metadata.json"
                pokemon_count = 0
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                            pokemon_count = metadata.get('pokemon_count', 0)
                    except:
                        pass
                
                index_html += f"""
        <div class="generation-card">
            <h3>Generation {gen}</h3>
            <p>{pokemon_count} Pokemon</p>
            <a href="pokemon/generation_{gen}/" class="nav-button">Explore Gen {gen}</a>
        </div>
"""
        
        # Add statistics
        index_html += f"""
    </div>
    
    <div class="stats">
        <h3>📊 Collection Statistics</h3>
        <ul>
            <li>Generations Found: {self.stats['generations_found']}</li>
            <li>Pokemon Downloaded: {self.stats['pokemon_downloaded']}</li>
            <li>Assets Downloaded: {self.stats['assets_downloaded']}</li>
            <li>Total Size: {self.stats['total_size_mb']:.2f}MB</li>
            <li>Scraped At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
        </ul>
    </div>
    
    <div class="stats">
        <h3>🚀 How to Use</h3>
        <p>This is your complete offline mirror of Phygitals.com. Navigate through the generations to explore Pokemon, or browse the assets folder for all downloaded files.</p>
        <p><strong>No internet connection required!</strong> Everything is stored locally.</p>
    </div>
</body>
</html>
"""
        
        with open(self.output_dir / "index.html", 'w', encoding='utf-8') as f:
            f.write(index_html)
        
        print("✅ Offline index page created")
    
    def save_comprehensive_metadata(self):
        """Save complete metadata about the scraping operation"""
        metadata = {
            'scrape_info': {
                'timestamp': datetime.now().isoformat(),
                'source_url': self.pokemon_base,
                'scraper_version': '2.0.0',
                'total_duration_minutes': 0  # Will be updated
            },
            'statistics': self.stats,
            'site_structure': self.site_map,
            'failed_downloads': self.failed_downloads,
            'directory_structure': self.get_directory_structure()
        }
        
        metadata_file = self.output_dir / "metadata/complete_scrape_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Comprehensive metadata saved to: {metadata_file}")
    
    def get_directory_structure(self):
        """Get the complete directory structure that was created"""
        structure = {}
        for root, dirs, files in os.walk(self.output_dir):
            rel_path = os.path.relpath(root, self.output_dir)
            structure[rel_path] = {
                'directories': dirs,
                'files': len(files),
                'file_list': files[:10]  # First 10 files as sample
            }
        return structure
    
    def run_complete_scrape(self):
        """Run the complete comprehensive scrape"""
        start_time = datetime.now()
        print("🚀 Starting COMPLETE Phygitals.com mirror scrape...")
        print(f"📅 Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Step 1: Discover site structure
            self.discover_site_structure()
            
            # Step 2: Scrape all generations (1-9)
            all_pokemon = []
            for generation in range(1, 10):
                generation_pokemon = self.scrape_complete_generation(generation)
                all_pokemon.extend(generation_pokemon)
                time.sleep(2)  # Be respectful
            
            # Step 3: Scrape all site assets
            self.scrape_site_assets()
            
            # Step 4: Create offline browsing interface
            self.create_offline_index()
            
            # Step 5: Save comprehensive metadata
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds() / 60
            self.stats['total_duration_minutes'] = duration
            
            self.save_comprehensive_metadata()
            
            # Final report
            print("\n" + "="*60)
            print("🎉 COMPLETE SCRAPE FINISHED!")
            print("="*60)
            print(f"⏱️  Total Duration: {duration:.1f} minutes")
            print(f"🎮 Generations: {self.stats['generations_found']}")
            print(f"🔥 Pokemon: {self.stats['pokemon_downloaded']}")
            print(f"📦 Assets: {self.stats['assets_downloaded']}")
            print(f"💾 Total Size: {self.stats['total_size_mb']:.2f}MB")
            print(f"📁 Output Directory: {self.output_dir}")
            print(f"🌐 Access offline at: file://{self.output_dir.absolute()}/index.html")
            
            if self.failed_downloads:
                print(f"⚠️  {len(self.failed_downloads)} downloads failed (see metadata for details)")
            
            print("\n✅ Your complete Phygitals Pokemon mirror is ready!")
            print("🔗 Open index.html in your browser to explore offline")
            
        except KeyboardInterrupt:
            print("\n⏹️  Scrape interrupted by user")
        except Exception as e:
            print(f"\n❌ Error during scrape: {e}")
        finally:
            if hasattr(self, 'driver'):
                self.driver.quit()

def main():
    print("🎮 Phygitals.com COMPLETE MIRROR SCRAPER")
    print("="*50)
    print("This will create a complete offline copy of Phygitals.com")
    print("including ALL generations, assets, and functionality.")
    print()
    
    # Confirm with user
    confirm = input("Ready to start complete scrape? This may take 30-60 minutes [y/N]: ")
    if confirm.lower() != 'y':
        print("Scrape cancelled.")
        return
    
    scraper = PhygitalsCompleteMirror()
    scraper.run_complete_scrape()

if __name__ == "__main__":
    main() 