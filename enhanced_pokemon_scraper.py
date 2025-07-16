#!/usr/bin/env python3
"""
Enhanced Comprehensive Pokemon Sites Scraper
============================================
Improved version with browser automation, dynamic structure analysis,
and robust error handling for all 10 Pokemon sites.
"""

import os
import re
import json
import time
import requests
import threading
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, urlparse, quote
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Set, Any

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

# BeautifulSoup for HTML parsing
from bs4 import BeautifulSoup
import pandas as pd

class EnhancedPokemonScraper:
    """Enhanced Pokemon scraper with dynamic structure analysis"""
    
    def __init__(self, output_dir="pokemon_enhanced_scrape"):
        self.start_time = datetime.now()
        self.output_dir = Path(output_dir)
        self.session = requests.Session()
        self.downloaded_files = set()
        self.stats = {
            'sites_processed': 0,
            'files_downloaded': 0,
            'data_extracted': 0,
            'animations_captured': 0,
            'errors': 0
        }
        
        # Target sites with enhanced configurations
        self.target_sites = [
            {
                'key': 'pokemondb_all',
                'url': 'https://pokemondb.net/pokedex/all',
                'name': 'PokemonDB Complete List',
                'requires_js': False,
                'data_type': 'pokemon_database',
                'priority': 1
            },
            {
                'key': 'cardmarket',
                'url': 'https://www.cardmarket.com/en/Pokemon',
                'name': 'Card Market Pokemon',
                'requires_js': True,
                'data_type': 'card_marketplace',
                'priority': 2
            },
            {
                'key': 'pokemondb_pokedex',
                'url': 'https://pokemondb.net/pokedex',
                'name': 'PokemonDB Individual Pages',
                'requires_js': False,
                'data_type': 'pokemon_database',
                'priority': 1
            },
            {
                'key': 'bulbapedia',
                'url': 'https://bulbapedia.bulbagarden.net/wiki/List_of_Pokémon_by_National_Pokédex_number',
                'name': 'Bulbapedia Pokemon List',
                'requires_js': False,
                'data_type': 'wiki_database',
                'priority': 2
            },
            {
                'key': 'serebii',
                'url': 'https://www.serebii.net/pokemon/nationalpokedex.shtml',
                'name': 'Serebii National Pokedex',
                'requires_js': False,
                'data_type': 'game_database',
                'priority': 2
            },
            {
                'key': 'portal_pokemon',
                'url': 'https://ph.portal-pokemon.com/play/pokedex',
                'name': 'Portal Pokemon Pokedex',
                'requires_js': True,
                'data_type': 'interactive_pokedex',
                'priority': 3
            },
            {
                'key': 'pkmn_pokedex',
                'url': 'https://www.pkmn.gg/pokedex',
                'name': 'PKMN.GG Pokedex',
                'requires_js': True,
                'data_type': 'modern_database',
                'priority': 1
            },
            {
                'key': 'pkmn_series',
                'url': 'https://www.pkmn.gg/series',
                'name': 'PKMN.GG Series',
                'requires_js': True,
                'data_type': 'series_database',
                'priority': 3
            },
            {
                'key': 'artofpkm',
                'url': 'https://www.artofpkm.com/',
                'name': 'Art of Pokemon',
                'requires_js': True,
                'data_type': 'artwork_gallery',
                'priority': 2
            },
            {
                'key': 'tcg_galleries',
                'url': 'https://tcg.pokemon.com/en-us/all-galleries/',
                'name': 'Pokemon TCG Galleries',
                'requires_js': True,
                'data_type': 'card_animations',
                'priority': 1
            }
        ]
        
        # Setup session
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        self.create_directory_structure()
        
    def create_directory_structure(self):
        """Create organized directory structure"""
        print("🏗️ Creating enhanced directory structure...")
        
        for site in self.target_sites:
            site_dir = self.output_dir / site['key']
            subdirs = ['data', 'images', 'animations', 'videos', 'css', 'javascript', 
                      'pages', 'screenshots', 'interactions', 'reference', 'extracted']
            
            for subdir in subdirs:
                (site_dir / subdir).mkdir(parents=True, exist_ok=True)
        
        # Master directories
        (self.output_dir / 'master_analysis').mkdir(parents=True, exist_ok=True)
        (self.output_dir / 'comprehensive_reference').mkdir(parents=True, exist_ok=True)
        
        print(f"✅ Directory structure created: {self.output_dir}")
    
    def setup_selenium_driver(self, headless=True):
        """Setup enhanced Selenium WebDriver"""
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument('--headless')
        
        # Enhanced options for better compatibility
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Download preferences
        prefs = {
            "profile.default_content_settings.popups": 0,
            "download.default_directory": str(self.output_dir.absolute()),
            "download.prompt_for_download": False,
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Execute script to avoid detection
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def log_progress(self, site_key: str, message: str, level: str = "INFO"):
        """Enhanced logging with timestamps and colors"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        colors = {
            'INFO': '\033[94m',     # Blue
            'SUCCESS': '\033[92m',  # Green
            'WARNING': '\033[93m',  # Yellow
            'ERROR': '\033[91m',    # Red
            'DEBUG': '\033[96m'     # Cyan
        }
        
        reset_color = '\033[0m'
        color = colors.get(level, '')
        
        print(f"{color}[{timestamp}] {site_key.upper()}: {message}{reset_color}")
    
    def analyze_page_structure(self, driver, site_key: str) -> Dict:
        """Analyze page structure to understand content layout"""
        self.log_progress(site_key, "Analyzing page structure...", "DEBUG")
        
        try:
            # Get page source
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Analyze structure
            structure = {
                'title': driver.title,
                'url': driver.current_url,
                'total_elements': len(soup.find_all()),
                'images': len(soup.find_all('img')),
                'links': len(soup.find_all('a')),
                'scripts': len(soup.find_all('script')),
                'styles': len(soup.find_all(['style', 'link'])),
                'tables': len(soup.find_all('table')),
                'forms': len(soup.find_all('form')),
                'divs': len(soup.find_all('div')),
                'classes_found': []
            }
            
            # Extract common class names
            for element in soup.find_all(class_=True):
                classes = element.get('class')
                if isinstance(classes, list):
                    structure['classes_found'].extend(classes)
            
            # Get unique classes
            structure['classes_found'] = list(set(structure['classes_found']))[:50]  # Limit to 50
            
            # Save analysis
            analysis_file = self.output_dir / site_key / 'reference' / 'page_structure.json'
            with open(analysis_file, 'w', encoding='utf-8') as f:
                json.dump(structure, f, indent=2, ensure_ascii=False)
            
            self.log_progress(site_key, f"Structure analysis complete - {structure['total_elements']} elements found")
            return structure
            
        except Exception as e:
            self.log_progress(site_key, f"Structure analysis failed: {e}", "ERROR")
            return {}
    
    def scrape_site_comprehensive(self, site_config: Dict) -> Dict:
        """Comprehensive scraping for a single site"""
        site_key = site_config['key']
        site_url = site_config['url']
        
        self.log_progress(site_key, f"Starting comprehensive scraping: {site_config['name']}")
        self.log_progress(site_key, f"URL: {site_url}")
        self.log_progress(site_key, f"Requires JS: {site_config['requires_js']}")
        
        driver = None
        results = {
            'site_key': site_key,
            'url': site_url,
            'scraped_at': datetime.now().isoformat(),
            'success': False,
            'data_extracted': {},
            'files_downloaded': 0,
            'animations_captured': 0,
            'errors': []
        }
        
        try:
            # Setup driver
            driver = self.setup_selenium_driver(headless=False)  # Run with GUI for better debugging
            
            # Navigate to site
            self.log_progress(site_key, "Loading page...")
            driver.get(site_url)
            
            # Wait for page load
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Let dynamic content load
            time.sleep(5)
            
            # Analyze page structure
            structure = self.analyze_page_structure(driver, site_key)
            results['page_structure'] = structure
            
            # Take initial screenshot
            screenshot_path = self.output_dir / site_key / 'screenshots' / 'initial_page.png'
            driver.save_screenshot(str(screenshot_path))
            self.log_progress(site_key, "Initial screenshot captured")
            
            # Site-specific scraping based on data type
            if site_config['data_type'] == 'pokemon_database':
                results['data_extracted'] = self.scrape_pokemon_database(driver, site_key)
            elif site_config['data_type'] == 'card_marketplace':
                results['data_extracted'] = self.scrape_card_marketplace(driver, site_key)
            elif site_config['data_type'] == 'card_animations':
                results['data_extracted'] = self.scrape_card_animations(driver, site_key)
            elif site_config['data_type'] == 'artwork_gallery':
                results['data_extracted'] = self.scrape_artwork_gallery(driver, site_key)
            elif site_config['data_type'] == 'wiki_database':
                results['data_extracted'] = self.scrape_wiki_database(driver, site_key)
            else:
                results['data_extracted'] = self.scrape_generic_content(driver, site_key)
            
            # Download images and media
            results['files_downloaded'] = self.download_all_media(driver, site_key)
            
            # Capture animations and interactions
            results['animations_captured'] = self.capture_animations_and_interactions(driver, site_key)
            
            # Save page source
            page_source_path = self.output_dir / site_key / 'pages' / 'source.html'
            with open(page_source_path, 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            
            results['success'] = True
            self.log_progress(site_key, "Scraping completed successfully!", "SUCCESS")
            
        except Exception as e:
            self.log_progress(site_key, f"Scraping failed: {e}", "ERROR")
            results['errors'].append(str(e))
            self.stats['errors'] += 1
            
        finally:
            if driver:
                driver.quit()
        
        # Save individual site results
        result_file = self.output_dir / site_key / 'reference' / 'scraping_results.json'
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        return results
    
    def scrape_pokemon_database(self, driver, site_key: str) -> Dict:
        """Scrape Pokemon database sites (PokemonDB, etc.)"""
        self.log_progress(site_key, "Extracting Pokemon database data...")
        
        data = {'pokemon': [], 'types': [], 'generations': []}
        
        try:
            # Look for Pokemon table with multiple possible selectors
            table_selectors = [
                'table#pokedex',
                'table.data-table',
                'table.pokemon-table',
                '.pokemon-list table',
                'table',  # Generic fallback
            ]
            
            table = None
            for selector in table_selectors:
                try:
                    table = driver.find_element(By.CSS_SELECTOR, selector)
                    self.log_progress(site_key, f"Found table with selector: {selector}")
                    break
                except:
                    continue
            
            if table:
                # Extract table data
                rows = table.find_elements(By.TAG_NAME, "tr")
                self.log_progress(site_key, f"Found {len(rows)} table rows")
                
                headers = []
                pokemon_count = 0
                
                for i, row in enumerate(rows):
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if not cells:  # Header row
                        header_cells = row.find_elements(By.TAG_NAME, "th")
                        headers = [cell.text.strip() for cell in header_cells]
                        continue
                    
                    if len(cells) >= 3:  # Ensure minimum required columns
                        pokemon_data = {}
                        
                        try:
                            # Extract Pokemon number
                            first_cell_text = cells[0].text.strip()
                            number_match = re.search(r'(\d+)', first_cell_text)
                            if number_match:
                                pokemon_data['number'] = number_match.group(1)
                            
                            # Look for sprite image
                            img = cells[0].find_element(By.TAG_NAME, "img")
                            if img:
                                pokemon_data['sprite_url'] = img.get_attribute('src')
                                pokemon_data['sprite_alt'] = img.get_attribute('alt')
                        except:
                            pass
                        
                        try:
                            # Extract name (usually in second column)
                            name_element = cells[1].find_element(By.TAG_NAME, "a")
                            pokemon_data['name'] = name_element.text.strip()
                            pokemon_data['detail_url'] = name_element.get_attribute('href')
                        except:
                            pokemon_data['name'] = cells[1].text.strip()
                        
                        try:
                            # Extract types (usually in third column)
                            type_elements = cells[2].find_elements(By.TAG_NAME, "a")
                            pokemon_data['types'] = [t.text.strip() for t in type_elements]
                        except:
                            pokemon_data['types'] = [cells[2].text.strip()]
                        
                        # Extract stats if available
                        for j, cell in enumerate(cells[3:], 3):
                            if j < len(headers):
                                stat_name = headers[j].lower().replace(' ', '_')
                                pokemon_data[stat_name] = cell.text.strip()
                        
                        data['pokemon'].append(pokemon_data)
                        pokemon_count += 1
                
                self.log_progress(site_key, f"Extracted {pokemon_count} Pokemon entries")
            
            # Look for type information
            type_elements = driver.find_elements(By.CSS_SELECTOR, ".type-icon, .type, [class*='type']")
            for type_elem in type_elements:
                type_text = type_elem.text.strip()
                if type_text and type_text not in data['types']:
                    data['types'].append(type_text)
            
        except Exception as e:
            self.log_progress(site_key, f"Pokemon database extraction error: {e}", "ERROR")
        
        return data
    
    def scrape_card_marketplace(self, driver, site_key: str) -> Dict:
        """Scrape card marketplace sites"""
        self.log_progress(site_key, "Extracting card marketplace data...")
        
        data = {'cards': [], 'sellers': [], 'prices': []}
        
        try:
            # Scroll to load more content
            self.scroll_page_gradually(driver)
            
            # Look for card listings
            card_selectors = [
                '.card-item',
                '.product-item',
                '.listing-item',
                '[class*="card"]',
                '[class*="product"]'
            ]
            
            cards_found = []
            for selector in card_selectors:
                try:
                    cards_found.extend(driver.find_elements(By.CSS_SELECTOR, selector))
                except:
                    continue
            
            self.log_progress(site_key, f"Found {len(cards_found)} potential card elements")
            
            for card in cards_found[:50]:  # Limit to first 50 cards
                try:
                    card_data = {}
                    
                    # Extract card name
                    name_selectors = ['.card-name', '.product-name', 'h3', 'h4', '[class*="name"]']
                    for name_sel in name_selectors:
                        try:
                            name_elem = card.find_element(By.CSS_SELECTOR, name_sel)
                            card_data['name'] = name_elem.text.strip()
                            break
                        except:
                            continue
                    
                    # Extract price
                    price_selectors = ['.price', '.cost', '.amount', '[class*="price"]']
                    for price_sel in price_selectors:
                        try:
                            price_elem = card.find_element(By.CSS_SELECTOR, price_sel)
                            card_data['price'] = price_elem.text.strip()
                            break
                        except:
                            continue
                    
                    # Extract image
                    try:
                        img = card.find_element(By.TAG_NAME, "img")
                        card_data['image_url'] = img.get_attribute('src')
                        card_data['image_alt'] = img.get_attribute('alt')
                    except:
                        pass
                    
                    if card_data:
                        data['cards'].append(card_data)
                        
                except Exception as e:
                    continue
            
            self.log_progress(site_key, f"Extracted {len(data['cards'])} card listings")
            
        except Exception as e:
            self.log_progress(site_key, f"Card marketplace extraction error: {e}", "ERROR")
        
        return data
    
    def scrape_card_animations(self, driver, site_key: str) -> Dict:
        """Scrape Pokemon TCG card animations"""
        self.log_progress(site_key, "Capturing card animations...")
        
        data = {'animations': [], 'interactions': []}
        
        try:
            # Look for card elements
            card_elements = driver.find_elements(By.CSS_SELECTOR, 
                ".card, .pokemon-card, .tcg-card, [class*='card']")
            
            self.log_progress(site_key, f"Found {len(card_elements)} potential card elements")
            
            for i, card in enumerate(card_elements[:10]):  # Limit for testing
                try:
                    # Scroll card into view
                    driver.execute_script("arguments[0].scrollIntoView(true);", card)
                    time.sleep(1)
                    
                    # Capture initial state
                    initial_screenshot = self.output_dir / site_key / 'animations' / f'card_{i}_initial.png'
                    card.screenshot(str(initial_screenshot))
                    
                    # Test hover animation
                    ActionChains(driver).move_to_element(card).perform()
                    time.sleep(2)
                    
                    hover_screenshot = self.output_dir / site_key / 'animations' / f'card_{i}_hover.png'
                    card.screenshot(str(hover_screenshot))
                    
                    # Test click animation
                    try:
                        card.click()
                        time.sleep(2)
                        
                        click_screenshot = self.output_dir / site_key / 'animations' / f'card_{i}_click.png'
                        card.screenshot(str(click_screenshot))
                        
                        data['animations'].append({
                            'card_index': i,
                            'initial_state': str(initial_screenshot),
                            'hover_state': str(hover_screenshot),
                            'click_state': str(click_screenshot),
                            'has_hover_effect': True,
                            'has_click_effect': True
                        })
                        
                    except:
                        data['animations'].append({
                            'card_index': i,
                            'initial_state': str(initial_screenshot),
                            'hover_state': str(hover_screenshot),
                            'has_hover_effect': True,
                            'has_click_effect': False
                        })
                    
                except Exception as e:
                    self.log_progress(site_key, f"Error capturing animation for card {i}: {e}", "WARNING")
                    continue
            
            self.log_progress(site_key, f"Captured {len(data['animations'])} card animations")
            
        except Exception as e:
            self.log_progress(site_key, f"Animation capture error: {e}", "ERROR")
        
        return data
    
    def scrape_artwork_gallery(self, driver, site_key: str) -> Dict:
        """Scrape artwork gallery sites"""
        self.log_progress(site_key, "Extracting artwork gallery data...")
        
        data = {'artworks': [], 'artists': [], 'categories': []}
        
        try:
            # Scroll to load more content
            self.scroll_page_gradually(driver)
            
            # Look for artwork elements
            artwork_elements = driver.find_elements(By.CSS_SELECTOR, 
                ".artwork, .gallery-item, .art-piece, img")
            
            self.log_progress(site_key, f"Found {len(artwork_elements)} potential artwork elements")
            
            for artwork in artwork_elements[:100]:  # Limit to first 100
                try:
                    artwork_data = {}
                    
                    if artwork.tag_name == 'img':
                        artwork_data['image_url'] = artwork.get_attribute('src')
                        artwork_data['alt_text'] = artwork.get_attribute('alt')
                        artwork_data['title'] = artwork.get_attribute('title')
                    else:
                        # Look for image within element
                        try:
                            img = artwork.find_element(By.TAG_NAME, "img")
                            artwork_data['image_url'] = img.get_attribute('src')
                            artwork_data['alt_text'] = img.get_attribute('alt')
                        except:
                            pass
                        
                        # Look for title/description
                        artwork_data['description'] = artwork.text.strip()
                    
                    if artwork_data.get('image_url'):
                        data['artworks'].append(artwork_data)
                        
                except:
                    continue
            
            self.log_progress(site_key, f"Extracted {len(data['artworks'])} artwork entries")
            
        except Exception as e:
            self.log_progress(site_key, f"Artwork gallery extraction error: {e}", "ERROR")
        
        return data
    
    def scrape_wiki_database(self, driver, site_key: str) -> Dict:
        """Scrape wiki-style database sites"""
        self.log_progress(site_key, "Extracting wiki database data...")
        
        return self.scrape_pokemon_database(driver, site_key)  # Use similar logic
    
    def scrape_generic_content(self, driver, site_key: str) -> Dict:
        """Generic content scraping for unknown site types"""
        self.log_progress(site_key, "Extracting generic content...")
        
        data = {'text_content': [], 'links': [], 'images': []}
        
        try:
            # Extract all text content
            text_elements = driver.find_elements(By.CSS_SELECTOR, "p, h1, h2, h3, h4, h5, h6, span, div")
            for elem in text_elements:
                text = elem.text.strip()
                if text and len(text) > 10:  # Only meaningful text
                    data['text_content'].append(text)
            
            # Extract all links
            links = driver.find_elements(By.TAG_NAME, "a")
            for link in links:
                href = link.get_attribute('href')
                text = link.text.strip()
                if href and text:
                    data['links'].append({'url': href, 'text': text})
            
            # Extract all images
            images = driver.find_elements(By.TAG_NAME, "img")
            for img in images:
                src = img.get_attribute('src')
                alt = img.get_attribute('alt')
                if src:
                    data['images'].append({'url': src, 'alt': alt})
            
            self.log_progress(site_key, f"Extracted generic content: {len(data['text_content'])} text elements, {len(data['links'])} links, {len(data['images'])} images")
            
        except Exception as e:
            self.log_progress(site_key, f"Generic content extraction error: {e}", "ERROR")
        
        return data
    
    def scroll_page_gradually(self, driver):
        """Gradually scroll page to trigger lazy loading"""
        try:
            # Get page height
            total_height = driver.execute_script("return document.body.scrollHeight")
            
            # Scroll in steps
            for i in range(0, total_height, 1000):
                driver.execute_script(f"window.scrollTo(0, {i});")
                time.sleep(1)
            
            # Scroll to bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
        except Exception as e:
            pass
    
    def download_all_media(self, driver, site_key: str) -> int:
        """Download all media files from the current page"""
        self.log_progress(site_key, "Downloading media files...")
        
        downloaded_count = 0
        
        try:
            # Get all images
            images = driver.find_elements(By.TAG_NAME, "img")
            
            for img in images:
                try:
                    src = img.get_attribute('src')
                    if src and src.startswith('http'):
                        filename = os.path.basename(urlparse(src).path)
                        if not filename or '.' not in filename:
                            filename = f"image_{abs(hash(src))}.png"
                        
                        local_path = self.output_dir / site_key / 'images' / filename
                        
                        if self.download_file(src, local_path):
                            downloaded_count += 1
                            
                except:
                    continue
            
            self.log_progress(site_key, f"Downloaded {downloaded_count} media files")
            
        except Exception as e:
            self.log_progress(site_key, f"Media download error: {e}", "ERROR")
        
        return downloaded_count
    
    def download_file(self, url: str, local_path: Path) -> bool:
        """Download a file with error handling"""
        try:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            return True
        except:
            return False
    
    def capture_animations_and_interactions(self, driver, site_key: str) -> int:
        """Capture animations and interactive elements"""
        self.log_progress(site_key, "Capturing animations and interactions...")
        
        captured_count = 0
        
        try:
            # Look for elements with hover effects
            hoverable_elements = driver.find_elements(By.CSS_SELECTOR, 
                "[onmouseover], [onhover], .hover, .interactive, .clickable")
            
            for i, element in enumerate(hoverable_elements[:5]):  # Limit to 5
                try:
                    # Test hover effect
                    ActionChains(driver).move_to_element(element).perform()
                    time.sleep(1)
                    
                    screenshot_path = self.output_dir / site_key / 'interactions' / f'hover_{i}.png'
                    element.screenshot(str(screenshot_path))
                    captured_count += 1
                    
                except:
                    continue
            
            self.log_progress(site_key, f"Captured {captured_count} interaction states")
            
        except Exception as e:
            self.log_progress(site_key, f"Animation capture error: {e}", "ERROR")
        
        return captured_count
    
    def run_comprehensive_scraping(self):
        """Run comprehensive scraping for all sites"""
        print("\n" + "="*80)
        print("🎮 ENHANCED COMPREHENSIVE POKEMON SITES SCRAPING")
        print("="*80)
        print(f"📅 Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Target Sites: {len(self.target_sites)}")
        print(f"💾 Output Directory: {self.output_dir.absolute()}")
        print("="*80)
        
        # Sort sites by priority
        sorted_sites = sorted(self.target_sites, key=lambda x: x['priority'])
        
        all_results = []
        
        for site_config in sorted_sites:
            print(f"\n🌐 Processing: {site_config['name']} (Priority {site_config['priority']})")
            
            result = self.scrape_site_comprehensive(site_config)
            all_results.append(result)
            
            self.stats['sites_processed'] += 1
            
            # Small delay between sites
            time.sleep(2)
        
        # Generate final report
        self.generate_comprehensive_report(all_results)
        
        return all_results
    
    def generate_comprehensive_report(self, all_results: List[Dict]):
        """Generate comprehensive final report"""
        end_time = datetime.now()
        total_duration = end_time - self.start_time
        
        # Calculate totals
        total_files = sum(r.get('files_downloaded', 0) for r in all_results)
        total_animations = sum(r.get('animations_captured', 0) for r in all_results)
        successful_sites = sum(1 for r in all_results if r.get('success', False))
        
        print("\n" + "="*80)
        print("🏁 ENHANCED COMPREHENSIVE SCRAPING COMPLETED")
        print("="*80)
        print(f"⏱️  Total Duration: {total_duration}")
        print(f"🌐 Sites Processed: {self.stats['sites_processed']}/{len(self.target_sites)}")
        print(f"✅ Successful Sites: {successful_sites}")
        print(f"📁 Files Downloaded: {total_files}")
        print(f"🎬 Animations Captured: {total_animations}")
        print(f"❌ Errors: {self.stats['errors']}")
        print("="*80)
        
        # Save comprehensive report
        final_report = {
            'operation_summary': {
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'total_duration_seconds': total_duration.total_seconds(),
                'sites_processed': self.stats['sites_processed'],
                'successful_sites': successful_sites,
                'total_files_downloaded': total_files,
                'total_animations_captured': total_animations,
                'total_errors': self.stats['errors']
            },
            'site_results': all_results,
            'target_sites_config': self.target_sites
        }
        
        report_file = self.output_dir / 'comprehensive_reference' / 'ENHANCED_FINAL_REPORT.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)
        
        # Create summary CSV
        summary_data = []
        for result in all_results:
            summary_data.append({
                'site_key': result.get('site_key', ''),
                'url': result.get('url', ''),
                'success': result.get('success', False),
                'files_downloaded': result.get('files_downloaded', 0),
                'animations_captured': result.get('animations_captured', 0),
                'data_entries': len(result.get('data_extracted', {}).get('pokemon', [])),
                'errors': len(result.get('errors', []))
            })
        
        if summary_data:
            df = pd.DataFrame(summary_data)
            csv_file = self.output_dir / 'comprehensive_reference' / 'scraping_summary.csv'
            df.to_csv(csv_file, index=False)
        
        print(f"📋 Final report saved: {report_file}")
        print(f"📊 Summary CSV saved: {csv_file}")


def main():
    """Main execution function"""
    scraper = EnhancedPokemonScraper()
    scraper.run_comprehensive_scraping()


if __name__ == "__main__":
    main() 