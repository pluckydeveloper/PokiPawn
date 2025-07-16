#!/usr/bin/env python3
"""
Remaining Pokemon Sites Specialized Scraper
==========================================
Focused scrapers for the remaining high-priority Pokemon sites:
- Art of Pokemon (artwork gallery)
- PKMN.GG Pokedex (competitive data)
- PKMN.GG Series (game data)
- Serebii (game-specific data)
- Bulbapedia (comprehensive wiki)
- Portal Pokemon (interactive content)
"""

import os
import re
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

class RemainingPokemonSitesScraper:
    """Comprehensive scraper for remaining high-priority Pokemon sites"""
    
    def __init__(self, output_dir="remaining_pokemon_sites"):
        self.output_dir = Path(output_dir)
        self.session = requests.Session()
        self.downloaded_files = set()
        
        # Session setup
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        })
        
        # Site configurations
        self.remaining_sites = {
            'artofpkm': {
                'url': 'https://www.artofpkm.com/',
                'name': 'Art of Pokemon Gallery',
                'scraper_method': 'scrape_artofpkm',
                'requires_js': True,
                'expected_data': ['artwork_collection', 'artist_info', 'high_res_images']
            },
            'pkmn_pokedex': {
                'url': 'https://www.pkmn.gg/pokedex',
                'name': 'PKMN.GG Competitive Pokedex',
                'scraper_method': 'scrape_pkmn_pokedex',
                'requires_js': True,
                'expected_data': ['competitive_data', 'tier_listings', 'usage_stats']
            },
            'pkmn_series': {
                'url': 'https://www.pkmn.gg/series',
                'name': 'PKMN.GG Series Data',
                'scraper_method': 'scrape_pkmn_series',
                'requires_js': True,
                'expected_data': ['series_info', 'game_data', 'generation_details']
            },
            'serebii': {
                'url': 'https://www.serebii.net/pokemon/nationalpokedex.shtml',
                'name': 'Serebii National Pokedex',
                'scraper_method': 'scrape_serebii',
                'requires_js': False,
                'expected_data': ['game_specific_data', 'location_data', 'sprites']
            },
            'bulbapedia': {
                'url': 'https://bulbapedia.bulbagarden.net/wiki/List_of_Pokémon_by_National_Pokédex_number',
                'name': 'Bulbapedia Pokemon Wiki',
                'scraper_method': 'scrape_bulbapedia',
                'requires_js': False,
                'expected_data': ['comprehensive_info', 'wiki_data', 'references']
            },
            'portal_pokemon': {
                'url': 'https://ph.portal-pokemon.com/play/pokedex',
                'name': 'Portal Pokemon Interactive',
                'scraper_method': 'scrape_portal_pokemon',
                'requires_js': True,
                'expected_data': ['interactive_elements', 'dynamic_content']
            }
        }
        
        # Stats tracking
        self.stats = {
            'sites_processed': 0,
            'total_files_downloaded': 0,
            'total_images_downloaded': 0,
            'total_data_extracted': 0,
            'total_errors': 0
        }
        
        self.create_directory_structure()
        
    def create_directory_structure(self):
        """Create organized directory structure for each site"""
        for site_key in self.remaining_sites.keys():
            site_dir = self.output_dir / site_key
            subdirs = [
                'data', 'images', 'artwork', 'sprites', 'screenshots',
                'pages', 'css', 'javascript', 'reference', 'metadata'
            ]
            
            for subdir in subdirs:
                (site_dir / subdir).mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Directory structure created: {self.output_dir}")
    
    def setup_selenium_driver(self, headless=True):
        """Setup Selenium WebDriver"""
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def log_progress(self, site_key: str, message: str, level: str = "INFO"):
        """Log progress with timestamps"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        colors = {
            'INFO': '\033[94m',
            'SUCCESS': '\033[92m',
            'WARNING': '\033[93m',
            'ERROR': '\033[91m'
        }
        
        color = colors.get(level, '')
        reset = '\033[0m'
        
        print(f"{color}[{timestamp}] {site_key.upper()}: {message}{reset}")
    
    def scrape_artofpkm(self, site_config: Dict) -> Dict:
        """Scrape Art of Pokemon artwork gallery"""
        self.log_progress('artofpkm', "Starting Art of Pokemon gallery scraping...")
        
        site_dir = self.output_dir / 'artofpkm'
        results = {
            'site': 'artofpkm',
            'url': site_config['url'],
            'scraped_at': datetime.now().isoformat(),
            'artwork_found': [],
            'artists_found': [],
            'categories_found': [],
            'total_images_downloaded': 0
        }
        
        driver = None
        try:
            driver = self.setup_selenium_driver(headless=False)
            driver.get(site_config['url'])
            
            # Wait for page load
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            time.sleep(5)
            
            # Take screenshot
            screenshot_path = site_dir / 'screenshots' / 'artofpkm_main.png'
            driver.save_screenshot(str(screenshot_path))
            
            # Scroll to load all content
            self.scroll_page_gradually(driver)
            
            # Find artwork galleries
            galleries = self.find_artwork_galleries(driver)
            results['categories_found'] = galleries
            
            # Extract artwork images
            artwork_data = self.extract_artwork_images(driver, site_dir)
            results['artwork_found'] = artwork_data
            results['total_images_downloaded'] = len(artwork_data)
            
            # Extract artist information
            artists = self.extract_artist_information(driver)
            results['artists_found'] = artists
            
            self.log_progress('artofpkm', f"Completed - {len(artwork_data)} artworks found", "SUCCESS")
            
        except Exception as e:
            self.log_progress('artofpkm', f"Error: {e}", "ERROR")
            self.stats['total_errors'] += 1
        finally:
            if driver:
                driver.quit()
        
        # Save results
        result_file = site_dir / 'data' / 'artofpkm_data.json'
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        return results
    
    def find_artwork_galleries(self, driver) -> List[Dict]:
        """Find artwork galleries on Art of Pokemon"""
        galleries = []
        
        try:
            # Look for gallery sections
            gallery_selectors = [
                '.gallery',
                '.artwork-gallery',
                '.portfolio',
                '.art-section',
                '[class*="gallery"]',
                '.category'
            ]
            
            for selector in gallery_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for i, element in enumerate(elements):
                        gallery_data = {
                            'index': i,
                            'title': element.text.strip()[:100] if element.text else f"Gallery {i}",
                            'element_class': element.get_attribute('class'),
                            'element_id': element.get_attribute('id')
                        }
                        galleries.append(gallery_data)
                except:
                    continue
        
        except Exception as e:
            self.log_progress('artofpkm', f"Error finding galleries: {e}", "WARNING")
        
        return galleries
    
    def extract_artwork_images(self, driver, site_dir: Path) -> List[Dict]:
        """Extract all artwork images"""
        artwork_data = []
        
        try:
            # Find all images
            images = driver.find_elements(By.TAG_NAME, "img")
            
            for i, img in enumerate(images):
                try:
                    src = img.get_attribute('src')
                    if src and ('art' in src.lower() or 'pokemon' in src.lower() or i < 50):
                        artwork_info = {
                            'index': i,
                            'url': src,
                            'alt': img.get_attribute('alt'),
                            'title': img.get_attribute('title'),
                            'filename': os.path.basename(urlparse(src).path)
                        }
                        
                        # Download image
                        filename = artwork_info['filename'] or f"artwork_{i}.jpg"
                        local_path = site_dir / 'artwork' / filename
                        
                        if self.download_file(src, local_path):
                            artwork_info['local_path'] = str(local_path)
                            artwork_data.append(artwork_info)
                            self.stats['total_images_downloaded'] += 1
                
                except Exception as e:
                    continue
            
            self.log_progress('artofpkm', f"Downloaded {len(artwork_data)} artwork images")
            
        except Exception as e:
            self.log_progress('artofpkm', f"Error extracting artwork: {e}", "ERROR")
        
        return artwork_data
    
    def extract_artist_information(self, driver) -> List[Dict]:
        """Extract artist information"""
        artists = []
        
        try:
            # Look for artist credits or information
            artist_selectors = [
                '.artist',
                '.credit',
                '.author',
                '[class*="artist"]',
                '.by-line'
            ]
            
            for selector in artist_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        artist_text = element.text.strip()
                        if artist_text and len(artist_text) < 200:
                            artists.append({
                                'name': artist_text,
                                'element_class': element.get_attribute('class')
                            })
                except:
                    continue
        
        except Exception as e:
            self.log_progress('artofpkm', f"Error extracting artists: {e}", "WARNING")
        
        return list({artist['name']: artist for artist in artists}.values())  # Remove duplicates
    
    def scrape_pkmn_pokedex(self, site_config: Dict) -> Dict:
        """Scrape PKMN.GG Pokedex for competitive data"""
        self.log_progress('pkmn_pokedex', "Starting PKMN.GG Pokedex scraping...")
        
        site_dir = self.output_dir / 'pkmn_pokedex'
        results = {
            'site': 'pkmn_pokedex',
            'url': site_config['url'],
            'scraped_at': datetime.now().isoformat(),
            'pokemon_data': [],
            'tier_data': [],
            'usage_stats': []
        }
        
        driver = None
        try:
            driver = self.setup_selenium_driver(headless=False)
            driver.get(site_config['url'])
            
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            time.sleep(5)
            
            # Take screenshot
            screenshot_path = site_dir / 'screenshots' / 'pkmn_pokedex.png'
            driver.save_screenshot(str(screenshot_path))
            
            # Extract Pokemon competitive data
            pokemon_data = self.extract_competitive_pokemon_data(driver)
            results['pokemon_data'] = pokemon_data
            
            # Extract tier information
            tier_data = self.extract_tier_data(driver)
            results['tier_data'] = tier_data
            
            self.log_progress('pkmn_pokedex', f"Completed - {len(pokemon_data)} Pokemon found", "SUCCESS")
            
        except Exception as e:
            self.log_progress('pkmn_pokedex', f"Error: {e}", "ERROR")
            self.stats['total_errors'] += 1
        finally:
            if driver:
                driver.quit()
        
        # Save results
        result_file = site_dir / 'data' / 'pkmn_pokedex_data.json'
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        return results
    
    def extract_competitive_pokemon_data(self, driver) -> List[Dict]:
        """Extract competitive Pokemon data from PKMN.GG"""
        pokemon_data = []
        
        try:
            # Look for Pokemon cards or listings
            pokemon_selectors = [
                '.pokemon-card',
                '.pokemon-item',
                '.pokemon',
                '[class*="pokemon"]',
                '.card'
            ]
            
            for selector in pokemon_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        pokemon_info = {
                            'name': '',
                            'tier': '',
                            'usage_percent': '',
                            'competitive_data': {}
                        }
                        
                        # Extract Pokemon name
                        try:
                            name_elem = element.find_element(By.CSS_SELECTOR, 'h1, h2, h3, .name, .pokemon-name')
                            pokemon_info['name'] = name_elem.text.strip()
                        except:
                            pokemon_info['name'] = element.text.strip()[:50]
                        
                        # Extract tier information
                        try:
                            tier_elem = element.find_element(By.CSS_SELECTOR, '.tier, .rank, [class*="tier"]')
                            pokemon_info['tier'] = tier_elem.text.strip()
                        except:
                            pass
                        
                        # Extract usage statistics
                        try:
                            usage_elem = element.find_element(By.CSS_SELECTOR, '.usage, .percent, [class*="usage"]')
                            pokemon_info['usage_percent'] = usage_elem.text.strip()
                        except:
                            pass
                        
                        if pokemon_info['name']:
                            pokemon_data.append(pokemon_info)
                            
                    if pokemon_data:  # If we found Pokemon with this selector, break
                        break
                        
                except:
                    continue
        
        except Exception as e:
            self.log_progress('pkmn_pokedex', f"Error extracting Pokemon data: {e}", "ERROR")
        
        return pokemon_data[:100]  # Limit to first 100
    
    def extract_tier_data(self, driver) -> List[Dict]:
        """Extract tier/ranking data"""
        tier_data = []
        
        try:
            tier_elements = driver.find_elements(By.CSS_SELECTOR, '.tier, .rank, .rating, [class*="tier"]')
            
            for element in tier_elements:
                tier_text = element.text.strip()
                if tier_text and len(tier_text) < 50:
                    tier_data.append({
                        'tier_name': tier_text,
                        'element_class': element.get_attribute('class')
                    })
        
        except Exception as e:
            self.log_progress('pkmn_pokedex', f"Error extracting tiers: {e}", "WARNING")
        
        return list({tier['tier_name']: tier for tier in tier_data}.values())  # Remove duplicates
    
    def scrape_serebii(self, site_config: Dict) -> Dict:
        """Scrape Serebii National Pokedex"""
        self.log_progress('serebii', "Starting Serebii National Pokedex scraping...")
        
        site_dir = self.output_dir / 'serebii'
        results = {
            'site': 'serebii',
            'url': site_config['url'],
            'scraped_at': datetime.now().isoformat(),
            'pokemon_data': [],
            'sprites_downloaded': 0,
            'game_specific_data': []
        }
        
        try:
            # Use requests for static content
            response = self.session.get(site_config['url'])
            response.raise_for_status()
            
            # Save page
            page_path = site_dir / 'pages' / 'serebii_pokedex.html'
            with open(page_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract Pokemon data from tables
            pokemon_data = self.extract_serebii_pokemon_data(soup, site_dir)
            results['pokemon_data'] = pokemon_data
            
            # Download sprites
            sprites_count = self.download_serebii_sprites(soup, site_dir)
            results['sprites_downloaded'] = sprites_count
            
            self.log_progress('serebii', f"Completed - {len(pokemon_data)} Pokemon found", "SUCCESS")
            
        except Exception as e:
            self.log_progress('serebii', f"Error: {e}", "ERROR")
            self.stats['total_errors'] += 1
        
        # Save results
        result_file = site_dir / 'data' / 'serebii_data.json'
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        return results
    
    def extract_serebii_pokemon_data(self, soup: BeautifulSoup, site_dir: Path) -> List[Dict]:
        """Extract Pokemon data from Serebii"""
        pokemon_data = []
        
        try:
            # Look for Pokemon tables or lists
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 3:
                        try:
                            pokemon_info = {}
                            
                            # Extract Pokemon number and name
                            for cell in cells:
                                text = cell.get_text(strip=True)
                                if re.match(r'^\d{3}', text):  # Pokemon number
                                    pokemon_info['number'] = text[:3]
                                elif text and not text.isdigit() and len(text) > 2:
                                    if 'name' not in pokemon_info:
                                        pokemon_info['name'] = text
                            
                            # Look for images in cells
                            for cell in cells:
                                img = cell.find('img')
                                if img and img.get('src'):
                                    pokemon_info['sprite_url'] = urljoin('https://www.serebii.net/', img.get('src'))
                            
                            if pokemon_info.get('name'):
                                pokemon_data.append(pokemon_info)
                                
                        except:
                            continue
        
        except Exception as e:
            self.log_progress('serebii', f"Error extracting Pokemon data: {e}", "ERROR")
        
        return pokemon_data[:500]  # Limit for performance
    
    def download_serebii_sprites(self, soup: BeautifulSoup, site_dir: Path) -> int:
        """Download sprites from Serebii"""
        downloaded_count = 0
        
        try:
            images = soup.find_all('img')
            
            for img in images:
                src = img.get('src')
                if src and ('pokemon' in src.lower() or 'pokedex' in src.lower()):
                    img_url = urljoin('https://www.serebii.net/', src)
                    filename = os.path.basename(urlparse(src).path)
                    
                    if filename:
                        local_path = site_dir / 'sprites' / filename
                        if self.download_file(img_url, local_path):
                            downloaded_count += 1
        
        except Exception as e:
            self.log_progress('serebii', f"Error downloading sprites: {e}", "ERROR")
        
        return downloaded_count
    
    def scroll_page_gradually(self, driver):
        """Gradually scroll page to load content"""
        try:
            total_height = driver.execute_script("return document.body.scrollHeight")
            
            for i in range(0, total_height, 1000):
                driver.execute_script(f"window.scrollTo(0, {i});")
                time.sleep(1)
            
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
        except:
            pass
    
    def download_file(self, url: str, local_path: Path) -> bool:
        """Download file with error handling"""
        try:
            if url in self.downloaded_files:
                return True
            
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            self.downloaded_files.add(url)
            self.stats['total_files_downloaded'] += 1
            return True
            
        except Exception as e:
            return False
    
    def run_remaining_sites_scraping(self):
        """Run scraping for all remaining sites"""
        print("\n" + "="*70)
        print("🌐 REMAINING POKEMON SITES COMPREHENSIVE SCRAPING")
        print("="*70)
        
        start_time = datetime.now()
        all_results = []
        
        # Process sites in priority order
        priority_sites = ['artofpkm', 'pkmn_pokedex', 'serebii', 'pkmn_series', 'bulbapedia', 'portal_pokemon']
        
        for site_key in priority_sites:
            if site_key in self.remaining_sites:
                site_config = self.remaining_sites[site_key]
                
                print(f"\n🎯 Processing: {site_config['name']}")
                
                # Get scraper method
                scraper_method = getattr(self, site_config['scraper_method'], None)
                if scraper_method:
                    result = scraper_method(site_config)
                    all_results.append(result)
                    self.stats['sites_processed'] += 1
                else:
                    self.log_progress(site_key, "Scraper method not implemented", "WARNING")
                
                # Small delay between sites
                time.sleep(2)
        
        # Generate final report
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\n" + "="*70)
        print("🏁 REMAINING SITES SCRAPING COMPLETED")
        print("="*70)
        print(f"⏱️  Duration: {duration}")
        print(f"🌐 Sites Processed: {self.stats['sites_processed']}")
        print(f"📁 Files Downloaded: {self.stats['total_files_downloaded']}")
        print(f"🖼️  Images Downloaded: {self.stats['total_images_downloaded']}")
        print(f"❌ Errors: {self.stats['total_errors']}")
        print("="*70)
        
        # Save consolidated results
        final_results = {
            'operation_summary': {
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration.total_seconds(),
                'stats': self.stats
            },
            'site_results': all_results
        }
        
        final_file = self.output_dir / 'REMAINING_SITES_FINAL_REPORT.json'
        with open(final_file, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, indent=2, ensure_ascii=False)
        
        print(f"📋 Final report saved: {final_file}")
        
        return all_results


def main():
    """Main execution function"""
    scraper = RemainingPokemonSitesScraper()
    scraper.run_remaining_sites_scraping()


if __name__ == "__main__":
    main() 