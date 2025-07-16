#!/usr/bin/env python3
"""
Phygitals.com Advanced Complete Mirror Scraper v2.0
Enhanced scraper that adapts to current site structure and captures ALL content
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
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime
import hashlib
from bs4 import BeautifulSoup
import mimetypes
import logging

class PhygitalsAdvancedMirror:
    def __init__(self, output_dir="phygitals_complete_site_mirror"):
        self.base_url = "https://www.phygitals.com"
        self.pokemon_base = f"{self.base_url}/pokemon/"
        self.output_dir = Path(output_dir)
        self.session = requests.Session()
        self.downloaded_files = {}
        self.pokemon_data = {}
        self.all_urls = set()
        self.failed_downloads = []
        
        # Enhanced statistics
        self.stats = {
            'pokemon_found': 0,
            'pokemon_downloaded': 0,
            'images_downloaded': 0,
            'animations_downloaded': 0,
            'assets_downloaded': 0,
            'pages_scraped': 0,
            'total_size_mb': 0,
            'generations_processed': 0,
            'unique_urls_found': 0
        }
        
        # Setup logging
        self.setup_logging()
        
        # Setup directories
        self.setup_directories()
        
        # Setup enhanced Selenium
        self.setup_selenium()
        
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_dir = self.output_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'scraping.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_directories(self):
        """Create comprehensive directory structure"""
        directories = [
            # Site structure
            "site_pages",
            "site_assets/css",
            "site_assets/js", 
            "site_assets/fonts",
            "site_assets/images",
            "site_assets/videos",
            
            # Pokemon by generation
            "pokemon_data/generation_1",
            "pokemon_data/generation_2", 
            "pokemon_data/generation_3",
            "pokemon_data/generation_4",
            "pokemon_data/generation_5",
            "pokemon_data/generation_6",
            "pokemon_data/generation_7",
            "pokemon_data/generation_8",
            "pokemon_data/generation_9",
            
            # Media assets
            "media/pokemon_sprites",
            "media/pokemon_animations",
            "media/pokemon_cards",
            "media/backgrounds",
            "media/ui_elements",
            
            # Metadata and logs
            "metadata",
            "logs",
            "reference"
        ]
        
        for directory in directories:
            (self.output_dir / directory).mkdir(parents=True, exist_ok=True)
            
        self.logger.info(f"Directory structure created in: {self.output_dir}")
        
    def setup_selenium(self):
        """Setup enhanced Selenium with comprehensive options"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Enable media and interactive content
        chrome_options.add_argument("--autoplay-policy=no-user-gesture-required")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        
        # Disable images initially for faster discovery
        prefs = {
            "profile.managed_default_content_settings.images": 1,
            "profile.default_content_setting_values.notifications": 2
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 30)
        self.actions = ActionChains(self.driver)
        
    def download_asset(self, url, local_path, asset_type="asset", max_retries=3):
        """Enhanced asset download with retry logic"""
        for attempt in range(max_retries):
            try:
                if local_path.exists():
                    return True
                    
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': self.base_url,
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br'
                }
                
                response = self.session.get(url, headers=headers, timeout=30, stream=True)
                response.raise_for_status()
                
                local_path.parent.mkdir(parents=True, exist_ok=True)
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                
                file_size_mb = downloaded / (1024 * 1024)
                self.stats['total_size_mb'] += file_size_mb
                
                if asset_type == "Pokemon sprite":
                    self.stats['images_downloaded'] += 1
                elif asset_type == "Pokemon animation":
                    self.stats['animations_downloaded'] += 1
                else:
                    self.stats['assets_downloaded'] += 1
                
                self.logger.info(f"✅ Downloaded {asset_type}: {url.split('/')[-1]} ({file_size_mb:.2f}MB)")
                return True
                
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == max_retries - 1:
                    self.failed_downloads.append({'url': url, 'error': str(e), 'type': asset_type})
                    return False
                time.sleep(2)
        
        return False
    
    def discover_pokemon_content(self):
        """Enhanced Pokemon content discovery with multiple strategies"""
        self.logger.info("🔍 Discovering Pokemon content with multiple strategies...")
        
        strategies = [
            self.discover_by_navigation,
            self.discover_by_search,
            self.discover_by_direct_urls,
            self.discover_by_api_endpoints
        ]
        
        all_pokemon_urls = set()
        
        for strategy in strategies:
            try:
                urls = strategy()
                all_pokemon_urls.update(urls)
                time.sleep(2)
            except Exception as e:
                self.logger.warning(f"Strategy failed: {e}")
        
        self.stats['unique_urls_found'] = len(all_pokemon_urls)
        self.logger.info(f"🎯 Found {len(all_pokemon_urls)} unique Pokemon URLs")
        
        return all_pokemon_urls
    
    def discover_by_navigation(self):
        """Discover Pokemon through site navigation"""
        self.logger.info("📋 Discovering via navigation...")
        urls = set()
        
        try:
            self.driver.get(self.pokemon_base)
            time.sleep(5)
            
            # Look for generation selectors
            generation_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                "[data-generation], .generation, [href*='generation'], .gen-")
            
            for elem in generation_elements:
                try:
                    href = elem.get_attribute('href')
                    data_gen = elem.get_attribute('data-generation')
                    
                    if href:
                        urls.add(href)
                    if data_gen:
                        gen_url = f"{self.pokemon_base}generation-{data_gen}/"
                        urls.add(gen_url)
                        
                except:
                    continue
            
            # Look for Pokemon cards/items
            pokemon_elements = self.driver.find_elements(By.CSS_SELECTOR,
                ".pokemon, [data-pokemon], .card, .item")
            
            for elem in pokemon_elements:
                try:
                    href = elem.get_attribute('href')
                    if href:
                        urls.add(href)
                except:
                    continue
                    
        except Exception as e:
            self.logger.error(f"Navigation discovery failed: {e}")
        
        return urls
    
    def discover_by_search(self):
        """Discover Pokemon by searching the page source"""
        self.logger.info("🔍 Discovering via page source analysis...")
        urls = set()
        
        try:
            self.driver.get(self.pokemon_base)
            time.sleep(3)
            
            # Get page source and extract URLs
            page_source = self.driver.page_source
            
            # Look for Pokemon-related URLs in the source
            url_patterns = [
                r'href=["\']([^"\']*pokemon[^"\']*)["\']',
                r'src=["\']([^"\']*\.gif[^"\']*)["\']',
                r'data-url=["\']([^"\']*)["\']',
                r'url\(["\']([^"\']*\.(?:gif|png|jpg)[^"\']*)["\']'
            ]
            
            for pattern in url_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                for match in matches:
                    full_url = urljoin(self.base_url, match)
                    urls.add(full_url)
                    
        except Exception as e:
            self.logger.error(f"Source analysis failed: {e}")
        
        return urls
    
    def discover_by_direct_urls(self):
        """Try direct generation URLs"""
        self.logger.info("🎯 Trying direct generation URLs...")
        urls = set()
        
        # Try various URL patterns
        patterns = [
            f"{self.pokemon_base}generation-{{}}",
            f"{self.pokemon_base}gen{{}}",
            f"{self.pokemon_base}{{}}",
            f"{self.base_url}/generation{{}}/pokemon"
        ]
        
        for gen in range(1, 10):
            for pattern in patterns:
                url = pattern.format(gen)
                urls.add(url)
        
        return urls
    
    def discover_by_api_endpoints(self):
        """Look for API endpoints that might contain Pokemon data"""
        self.logger.info("🔧 Looking for API endpoints...")
        urls = set()
        
        try:
            # Check common API patterns
            api_patterns = [
                f"{self.base_url}/api/pokemon",
                f"{self.base_url}/api/generations",
                f"{self.base_url}/_next/static/chunks",
            ]
            
            for api_url in api_patterns:
                urls.add(api_url)
                
        except Exception as e:
            self.logger.error(f"API discovery failed: {e}")
        
        return urls
    
    def scrape_pokemon_generation_enhanced(self, generation_num):
        """Enhanced generation scraping with multiple extraction methods"""
        self.logger.info(f"🎮 Enhanced scraping for Generation {generation_num}...")
        
        generation_dir = self.output_dir / f"pokemon_data/generation_{generation_num}"
        generation_dir.mkdir(parents=True, exist_ok=True)
        
        # Try multiple URL patterns for this generation
        urls_to_try = [
            f"{self.pokemon_base}generation-{generation_num}/",
            f"{self.pokemon_base}gen{generation_num}/",
            f"{self.pokemon_base}{generation_num}/",
            f"{self.base_url}/generation{generation_num}/"
        ]
        
        generation_pokemon = []
        
        for url in urls_to_try:
            try:
                self.logger.info(f"Trying URL: {url}")
                self.driver.get(url)
                time.sleep(5)
                
                # Wait for content to load
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                
                # Try to trigger any lazy loading
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                
                # Look for Pokemon with multiple selectors
                pokemon_selectors = [
                    ".pokemon-card",
                    ".pokemon",
                    ".card",
                    "[data-pokemon]",
                    ".item",
                    ".pokemon-item",
                    ".grid-item",
                    ".gallery-item"
                ]
                
                pokemon_elements = []
                for selector in pokemon_selectors:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    pokemon_elements.extend(elements)
                
                if pokemon_elements:
                    self.logger.info(f"Found {len(pokemon_elements)} Pokemon elements")
                    
                    for elem in pokemon_elements:
                        pokemon_data = self.extract_pokemon_data_enhanced(elem, generation_num, url)
                        if pokemon_data:
                            generation_pokemon.append(pokemon_data)
                    
                    break  # If we found Pokemon, don't try other URLs
                    
            except Exception as e:
                self.logger.warning(f"Failed to scrape {url}: {e}")
                continue
        
        # Save generation page HTML if we accessed it
        try:
            page_html = self.driver.page_source
            with open(generation_dir / "page_source.html", 'w', encoding='utf-8') as f:
                f.write(page_html)
        except:
            pass
        
        # Save generation metadata
        generation_metadata = {
            'generation': generation_num,
            'pokemon_count': len(generation_pokemon),
            'pokemon': generation_pokemon,
            'scraped_at': datetime.now().isoformat(),
            'urls_tried': urls_to_try
        }
        
        with open(generation_dir / "metadata.json", 'w', encoding='utf-8') as f:
            json.dump(generation_metadata, f, indent=2, ensure_ascii=False)
        
        self.stats['generations_processed'] += 1
        self.stats['pokemon_found'] += len(generation_pokemon)
        
        self.logger.info(f"✅ Generation {generation_num}: {len(generation_pokemon)} Pokemon found")
        return generation_pokemon
    
    def extract_pokemon_data_enhanced(self, element, generation, source_url):
        """Enhanced Pokemon data extraction with multiple strategies"""
        try:
            pokemon_data = {
                'generation': generation,
                'source_url': source_url,
                'extracted_at': datetime.now().isoformat(),
                'images': [],
                'animations': [],
                'metadata': {}
            }
            
            # Extract all images from this element
            img_elements = element.find_elements(By.CSS_SELECTOR, "img")
            for img in img_elements:
                img_src = img.get_attribute('src')
                img_alt = img.get_attribute('alt')
                img_data_src = img.get_attribute('data-src')
                
                for src in [img_src, img_data_src]:
                    if src and src.startswith('http'):
                        pokemon_data['images'].append({
                            'url': src,
                            'alt': img_alt,
                            'type': self.classify_image_type(src)
                        })
            
            # Look for any text that might be Pokemon name/number
            text_content = element.text.strip()
            if text_content:
                pokemon_data['text_content'] = text_content
                
                # Try to extract number from text
                number_match = re.search(r'#?(\d{1,4})', text_content)
                if number_match:
                    pokemon_data['number'] = int(number_match.group(1))
            
            # Look for data attributes
            for attr in element.get_attribute_names():
                if attr.startswith('data-'):
                    value = element.get_attribute(attr)
                    pokemon_data['metadata'][attr] = value
            
            # If we found at least one image or some data, it's valid
            if pokemon_data['images'] or pokemon_data['metadata'] or pokemon_data.get('text_content'):
                return pokemon_data
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error extracting Pokemon data: {e}")
            return None
    
    def classify_image_type(self, url):
        """Enhanced image classification"""
        url_lower = url.lower()
        if '.gif' in url_lower:
            return 'animation'
        elif any(term in url_lower for term in ['sprite', 'pokemon']):
            return 'sprite'
        elif 'card' in url_lower:
            return 'card'
        elif 'background' in url_lower:
            return 'background'
        elif any(ext in url_lower for ext in ['.png', '.jpg', '.jpeg']):
            return 'image'
        else:
            return 'unknown'
    
    def download_pokemon_media(self, pokemon_data):
        """Download all media for Pokemon with organized storage"""
        if not pokemon_data.get('images'):
            return
            
        generation = pokemon_data.get('generation', 'unknown')
        pokemon_num = pokemon_data.get('number', 'unknown')
        
        for img_data in pokemon_data['images']:
            url = img_data['url']
            img_type = img_data['type']
            
            # Generate filename
            url_path = urlparse(url).path
            original_filename = os.path.basename(url_path)
            
            if not original_filename or '.' not in original_filename:
                ext = '.gif' if img_type == 'animation' else '.png'
                original_filename = f"pokemon_{generation}_{pokemon_num}_{hashlib.md5(url.encode()).hexdigest()[:8]}{ext}"
            
            # Organize by type
            if img_type == 'animation':
                local_path = self.output_dir / f"media/pokemon_animations/gen_{generation}_{original_filename}"
            elif img_type == 'sprite':
                local_path = self.output_dir / f"media/pokemon_sprites/gen_{generation}_{original_filename}"
            elif img_type == 'card':
                local_path = self.output_dir / f"media/pokemon_cards/gen_{generation}_{original_filename}"
            else:
                local_path = self.output_dir / f"media/pokemon_sprites/gen_{generation}_{original_filename}"
            
            # Download the asset
            self.download_asset(url, local_path, f"Pokemon {img_type}")
    
    def scrape_comprehensive_assets(self):
        """Comprehensive asset scraping including hidden/lazy-loaded content"""
        self.logger.info("🎨 Comprehensive asset scraping...")
        
        try:
            self.driver.get(self.pokemon_base)
            time.sleep(5)
            
            # Scroll through the page to trigger lazy loading
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
            
            # Get all assets after lazy loading
            all_assets = self.driver.find_elements(By.CSS_SELECTOR, 
                "link[href], script[src], img[src], img[data-src], source[src]")
            
            for asset in all_assets:
                try:
                    asset_url = None
                    asset_type = "asset"
                    
                    if asset.tag_name == "link":
                        asset_url = asset.get_attribute('href')
                        asset_type = "CSS" if asset.get_attribute('rel') == 'stylesheet' else "resource"
                    elif asset.tag_name == "script":
                        asset_url = asset.get_attribute('src')
                        asset_type = "JavaScript"
                    elif asset.tag_name == "img":
                        asset_url = asset.get_attribute('src') or asset.get_attribute('data-src')
                        asset_type = "image"
                    elif asset.tag_name == "source":
                        asset_url = asset.get_attribute('src')
                        asset_type = "media"
                    
                    if asset_url and asset_url.startswith('http'):
                        # Determine local path based on asset type
                        filename = os.path.basename(urlparse(asset_url).path)
                        if not filename:
                            filename = hashlib.md5(asset_url.encode()).hexdigest()[:12]
                        
                        if asset_type == "CSS":
                            local_path = self.output_dir / f"site_assets/css/{filename}"
                        elif asset_type == "JavaScript":
                            local_path = self.output_dir / f"site_assets/js/{filename}"
                        else:
                            local_path = self.output_dir / f"site_assets/images/{filename}"
                        
                        self.download_asset(asset_url, local_path, asset_type)
                        
                except Exception as e:
                    continue
            
            self.logger.info("✅ Comprehensive asset scraping completed")
            
        except Exception as e:
            self.logger.error(f"Asset scraping failed: {e}")
    
    def create_enhanced_offline_site(self):
        """Create enhanced offline browsing experience"""
        self.logger.info("🌐 Creating enhanced offline site...")
        
        # Create main index
        index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Phygitals Pokemon - Complete Offline Mirror</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .header {{ text-align: center; margin-bottom: 40px; }}
        .header h1 {{ font-size: 3em; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 40px 0; }}
        .stat-card {{ background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; text-align: center; backdrop-filter: blur(10px); }}
        .stat-number {{ font-size: 2em; font-weight: bold; color: #FFD700; }}
        .generation-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }}
        .generation-card {{ background: rgba(255,255,255,0.15); padding: 25px; border-radius: 15px; transition: transform 0.3s; }}
        .generation-card:hover {{ transform: translateY(-5px); }}
        .generation-title {{ font-size: 1.5em; margin-bottom: 10px; }}
        .nav-button {{ display: inline-block; padding: 12px 24px; background: rgba(255,255,255,0.2); color: white; text-decoration: none; border-radius: 25px; margin: 10px; transition: all 0.3s; }}
        .nav-button:hover {{ background: rgba(255,255,255,0.3); transform: scale(1.05); }}
        .folder-tree {{ background: rgba(0,0,0,0.2); padding: 20px; border-radius: 10px; margin: 20px 0; }}
        .folder-tree code {{ color: #FFD700; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎮 Phygitals Pokemon Complete Mirror</h1>
            <p>Your comprehensive offline copy of the entire Phygitals Pokemon collection</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{self.stats['pokemon_found']}</div>
                <div>Pokemon Found</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{self.stats['images_downloaded']}</div>
                <div>Images Downloaded</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{self.stats['animations_downloaded']}</div>
                <div>Animations Downloaded</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{self.stats['total_size_mb']:.1f}MB</div>
                <div>Total Size</div>
            </div>
        </div>
        
        <div style="text-align: center; margin: 40px 0;">
            <a href="pokemon_data/" class="nav-button">📁 Pokemon Data</a>
            <a href="media/" class="nav-button">🎬 Media Files</a>
            <a href="site_assets/" class="nav-button">🎨 Site Assets</a>
            <a href="metadata/" class="nav-button">📊 Metadata</a>
            <a href="logs/" class="nav-button">📋 Logs</a>
        </div>
        
        <div class="generation-grid">
"""
        
        # Add generation cards
        for gen in range(1, 10):
            gen_dir = self.output_dir / f"pokemon_data/generation_{gen}"
            pokemon_count = 0
            if gen_dir.exists():
                metadata_file = gen_dir / "metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                            pokemon_count = metadata.get('pokemon_count', 0)
                    except:
                        pass
            
            index_html += f"""
            <div class="generation-card">
                <div class="generation-title">Generation {gen}</div>
                <p>{pokemon_count} Pokemon discovered</p>
                <a href="pokemon_data/generation_{gen}/" class="nav-button">Explore</a>
            </div>
"""
        
        index_html += f"""
        </div>
        
        <div class="folder-tree">
            <h3>📁 Directory Structure</h3>
            <pre><code>
phygitals_complete_site_mirror/
├── pokemon_data/          # Pokemon organized by generation
├── media/                 # All Pokemon images and animations
├── site_assets/          # Website CSS, JS, and assets
├── metadata/             # Scraping metadata and statistics
└── logs/                 # Detailed scraping logs
            </code></pre>
        </div>
        
        <div style="text-align: center; margin: 40px 0; opacity: 0.8;">
            <p>🕐 Scraped on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}</p>
            <p>✨ Complete offline mirror - no internet required!</p>
        </div>
    </div>
</body>
</html>"""
        
        with open(self.output_dir / "index.html", 'w', encoding='utf-8') as f:
            f.write(index_html)
        
        self.logger.info("✅ Enhanced offline site created")
    
    def run_comprehensive_scrape(self):
        """Run the complete comprehensive scraping operation"""
        start_time = datetime.now()
        self.logger.info("🚀 Starting COMPREHENSIVE Phygitals.com scraping...")
        self.logger.info(f"📅 Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Phase 1: Discover all Pokemon content
            pokemon_urls = self.discover_pokemon_content()
            
            # Phase 2: Scrape each generation with enhanced methods
            all_pokemon = []
            for generation in range(1, 10):
                generation_pokemon = self.scrape_pokemon_generation_enhanced(generation)
                all_pokemon.extend(generation_pokemon)
                
                # Download media for this generation
                for pokemon in generation_pokemon:
                    self.download_pokemon_media(pokemon)
                
                time.sleep(3)  # Be respectful
            
            # Phase 3: Comprehensive asset scraping
            self.scrape_comprehensive_assets()
            
            # Phase 4: Create enhanced offline experience
            self.create_enhanced_offline_site()
            
            # Phase 5: Save comprehensive metadata
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds() / 60
            
            final_metadata = {
                'scrape_summary': {
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'duration_minutes': duration,
                    'scraper_version': 'Advanced v2.0'
                },
                'statistics': self.stats,
                'pokemon_data': all_pokemon,
                'failed_downloads': self.failed_downloads
            }
            
            with open(self.output_dir / "metadata/comprehensive_scrape_report.json", 'w', encoding='utf-8') as f:
                json.dump(final_metadata, f, indent=2, ensure_ascii=False)
            
            # Final success report
            print("\n" + "="*70)
            print("🎉 COMPREHENSIVE SCRAPING COMPLETED!")
            print("="*70)
            print(f"⏱️  Total Duration: {duration:.1f} minutes")
            print(f"🎮 Generations Processed: {self.stats['generations_processed']}")
            print(f"🔥 Pokemon Found: {self.stats['pokemon_found']}")
            print(f"🖼️  Images Downloaded: {self.stats['images_downloaded']}")
            print(f"🎬 Animations Downloaded: {self.stats['animations_downloaded']}")
            print(f"📦 Total Assets: {self.stats['assets_downloaded']}")
            print(f"💾 Total Size: {self.stats['total_size_mb']:.2f}MB")
            print(f"📁 Output Directory: {self.output_dir.absolute()}")
            print(f"🌐 Offline Site: file://{self.output_dir.absolute()}/index.html")
            
            if self.failed_downloads:
                print(f"⚠️  {len(self.failed_downloads)} downloads failed (see metadata)")
            
            print("\n✅ Your complete Phygitals mirror is ready for offline use!")
            
        except KeyboardInterrupt:
            self.logger.info("⏹️  Scraping interrupted by user")
        except Exception as e:
            self.logger.error(f"❌ Critical error during scraping: {e}")
        finally:
            if hasattr(self, 'driver'):
                self.driver.quit()

def main():
    print("🎮 PHYGITALS.COM ADVANCED COMPLETE MIRROR")
    print("="*50)
    print("Advanced scraper with enhanced Pokemon detection")
    print("Creates a fully functional offline copy")
    print()
    
    confirm = input("Start comprehensive scraping? [y/N]: ")
    if confirm.lower() != 'y':
        print("Scraping cancelled.")
        return
    
    scraper = PhygitalsAdvancedMirror()
    scraper.run_comprehensive_scrape()

if __name__ == "__main__":
    main() 