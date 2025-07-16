#!/usr/bin/env python3
"""
Specialized Site Scrapers for Pokemon Comprehensive Extraction
==============================================================
Detailed implementations for each of the 10 target sites with specific
extraction logic for Pokemon data, animations, UI elements, and interactions.
"""

import os
import re
import json
import time
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, urlparse, quote
from typing import Dict, List, Optional, Set, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import lxml

class PokemonDBAllScraper:
    """Specialized scraper for pokemondb.net/pokedex/all"""
    
    def __init__(self, output_dir: Path, session: requests.Session):
        self.output_dir = output_dir
        self.session = session
        self.base_url = "https://pokemondb.net"
        self.target_url = "https://pokemondb.net/pokedex/all"
        
    def scrape_complete_pokedex(self) -> Dict:
        """Scrape the complete Pokemon database with all stats and sprites"""
        print("🎯 Starting PokemonDB Complete Pokedex scraping...")
        
        try:
            # Get the main page
            response = self.session.get(self.target_url, timeout=30)
            response.raise_for_status()
            
            # Save main page
            main_page_path = self.output_dir / 'pages' / 'complete_pokedex.html'
            with open(main_page_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract Pokemon table data
            pokemon_data = self.extract_pokemon_table_data(soup)
            
            # Extract all Pokemon sprites
            self.extract_pokemon_sprites(soup)
            
            # Download type icons and images
            self.extract_type_icons(soup)
            
            # Save Pokemon data
            data_file = self.output_dir / 'data' / 'complete_pokemon_data.json'
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(pokemon_data, f, indent=2, ensure_ascii=False)
            
            # Save as CSV for easy analysis
            if pokemon_data.get('pokemon'):
                df = pd.DataFrame(pokemon_data['pokemon'])
                csv_file = self.output_dir / 'data' / 'pokemon_stats.csv'
                df.to_csv(csv_file, index=False)
            
            print(f"✅ PokemonDB scraping completed! Found {len(pokemon_data.get('pokemon', []))} Pokemon")
            return pokemon_data
            
        except Exception as e:
            print(f"❌ PokemonDB scraping failed: {e}")
            return {}
    
    def extract_pokemon_table_data(self, soup: BeautifulSoup) -> Dict:
        """Extract Pokemon data from the main table"""
        pokemon_list = []
        
        # Find the main Pokemon table
        table = soup.find('table', {'id': 'pokedex'})
        if not table:
            print("⚠️ Pokemon table not found")
            return {'pokemon': []}
        
        rows = table.find_all('tr')[1:]  # Skip header
        
        for row in rows:
            try:
                cells = row.find_all('td')
                if len(cells) < 8:
                    continue
                
                # Extract Pokemon data
                pokemon_data = {}
                
                # Number and sprite
                first_cell = cells[0]
                img = first_cell.find('img')
                if img:
                    pokemon_data['sprite_url'] = img.get('src')
                    pokemon_data['sprite_alt'] = img.get('alt', '')
                
                number_text = first_cell.get_text(strip=True)
                pokemon_data['number'] = re.search(r'(\d+)', number_text).group(1) if re.search(r'(\d+)', number_text) else ''
                
                # Name
                name_cell = cells[1]
                name_link = name_cell.find('a')
                if name_link:
                    pokemon_data['name'] = name_link.get_text(strip=True)
                    pokemon_data['detail_url'] = urljoin(self.base_url, name_link.get('href', ''))
                
                # Types
                type_cell = cells[2]
                type_links = type_cell.find_all('a')
                pokemon_data['types'] = [link.get_text(strip=True) for link in type_links]
                
                # Stats
                stat_names = ['total', 'hp', 'attack', 'defense', 'sp_attack', 'sp_defense', 'speed']
                for i, stat_name in enumerate(stat_names):
                    if i + 3 < len(cells):
                        pokemon_data[stat_name] = cells[i + 3].get_text(strip=True)
                
                pokemon_list.append(pokemon_data)
                
            except Exception as e:
                print(f"⚠️ Error parsing Pokemon row: {e}")
                continue
        
        return {
            'source': 'pokemondb.net/pokedex/all',
            'scraped_at': datetime.now().isoformat(),
            'total_pokemon': len(pokemon_list),
            'pokemon': pokemon_list
        }
    
    def extract_pokemon_sprites(self, soup: BeautifulSoup):
        """Download all Pokemon sprites from the page"""
        print("📸 Downloading Pokemon sprites...")
        
        sprites_found = 0
        images = soup.find_all('img')
        
        for img in images:
            src = img.get('src')
            if src and 'sprites' in src and 'icon' in src:
                sprite_url = urljoin(self.base_url, src)
                
                # Extract Pokemon name from alt text or filename
                alt_text = img.get('alt', '')
                filename = os.path.basename(urlparse(sprite_url).path)
                
                if alt_text:
                    safe_name = re.sub(r'[^\w\-_\.]', '_', alt_text.lower())
                    filename = f"{safe_name}.png"
                
                local_path = self.output_dir / 'images' / 'sprites' / filename
                
                if self.download_file(sprite_url, local_path):
                    sprites_found += 1
        
        print(f"✅ Downloaded {sprites_found} Pokemon sprites")
    
    def extract_type_icons(self, soup: BeautifulSoup):
        """Download Pokemon type icons"""
        print("🏷️ Downloading type icons...")
        
        type_icons = soup.find_all('a', class_='type-icon')
        icons_found = 0
        
        for type_link in type_icons:
            # Type icons are usually background images in CSS
            style = type_link.get('style', '')
            if 'background-image' in style:
                # Extract URL from CSS
                url_match = re.search(r'url\(["\']?([^"\']+)["\']?\)', style)
                if url_match:
                    icon_url = urljoin(self.base_url, url_match.group(1))
                    type_name = type_link.get_text(strip=True).lower()
                    
                    local_path = self.output_dir / 'images' / 'types' / f"{type_name}_icon.png"
                    
                    if self.download_file(icon_url, local_path):
                        icons_found += 1
        
        print(f"✅ Downloaded {icons_found} type icons")
    
    def download_file(self, url: str, local_path: Path) -> bool:
        """Download a file with error handling"""
        try:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            return True
        except Exception as e:
            print(f"❌ Failed to download {url}: {e}")
            return False


class CardMarketScraper:
    """Specialized scraper for cardmarket.com/en/Pokemon"""
    
    def __init__(self, output_dir: Path, driver_setup_func):
        self.output_dir = output_dir
        self.setup_driver = driver_setup_func
        self.base_url = "https://www.cardmarket.com"
        self.target_url = "https://www.cardmarket.com/en/Pokemon"
    
    def scrape_card_market(self) -> Dict:
        """Scrape Pokemon card marketplace data"""
        print("🎴 Starting Card Market scraping...")
        
        driver = None
        try:
            driver = self.setup_driver()
            driver.get(self.target_url)
            
            # Wait for page load
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            time.sleep(5)  # Let dynamic content load
            
            # Extract card data
            card_data = self.extract_card_listings(driver)
            
            # Extract card images
            self.extract_card_images(driver)
            
            # Save data
            data_file = self.output_dir / 'data' / 'card_market_data.json'
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(card_data, f, indent=2, ensure_ascii=False)
            
            return card_data
            
        except Exception as e:
            print(f"❌ Card Market scraping failed: {e}")
            return {}
        finally:
            if driver:
                driver.quit()
    
    def extract_card_listings(self, driver) -> Dict:
        """Extract card listings and pricing data"""
        cards = []
        
        # Look for card elements (site-specific selectors)
        card_elements = driver.find_elements(By.CSS_SELECTOR, ".product-item, .card-item, .listing-item")
        
        for card_element in card_elements:
            try:
                card_data = {}
                
                # Extract card name
                name_element = card_element.find_element(By.CSS_SELECTOR, ".card-name, .product-name, h3, h4")
                card_data['name'] = name_element.text.strip()
                
                # Extract price
                price_element = card_element.find_element(By.CSS_SELECTOR, ".price, .cost, .amount")
                card_data['price'] = price_element.text.strip()
                
                # Extract image URL
                img_element = card_element.find_element(By.TAG_NAME, "img")
                card_data['image_url'] = img_element.get_attribute('src')
                
                cards.append(card_data)
                
            except Exception as e:
                continue
        
        return {
            'source': 'cardmarket.com/en/Pokemon',
            'scraped_at': datetime.now().isoformat(),
            'total_cards': len(cards),
            'cards': cards
        }
    
    def extract_card_images(self, driver):
        """Download Pokemon card images"""
        print("🖼️ Downloading card images...")
        
        images = driver.find_elements(By.TAG_NAME, "img")
        downloaded = 0
        
        for img in images:
            try:
                src = img.get_attribute('src')
                if src and ('card' in src.lower() or 'pokemon' in src.lower()):
                    filename = os.path.basename(urlparse(src).path)
                    if not filename:
                        filename = f"card_{abs(hash(src))}.jpg"
                    
                    local_path = self.output_dir / 'images' / 'cards' / filename
                    
                    if self.download_image(src, local_path):
                        downloaded += 1
            except:
                continue
        
        print(f"✅ Downloaded {downloaded} card images")
    
    def download_image(self, url: str, local_path: Path) -> bool:
        """Download image with requests"""
        try:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            return True
        except:
            return False


class TCGAnimationScraper:
    """Specialized scraper for tcg.pokemon.com card animations"""
    
    def __init__(self, output_dir: Path, driver_setup_func):
        self.output_dir = output_dir
        self.setup_driver = driver_setup_func
        self.base_url = "https://tcg.pokemon.com"
        self.target_url = "https://tcg.pokemon.com/en-us/all-galleries/"
    
    def scrape_tcg_animations(self) -> Dict:
        """Scrape Pokemon TCG card animations and interactions"""
        print("🎬 Starting TCG Animation scraping...")
        
        driver = None
        try:
            driver = self.setup_driver()
            driver.get(self.target_url)
            
            # Wait for page load
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            time.sleep(10)  # Let animations and dynamic content load
            
            # Capture card animations
            animation_data = self.capture_card_animations(driver)
            
            # Record interactive elements
            interaction_data = self.record_card_interactions(driver)
            
            # Save data
            data_file = self.output_dir / 'data' / 'tcg_animations.json'
            animation_data['interactions'] = interaction_data
            
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(animation_data, f, indent=2, ensure_ascii=False)
            
            return animation_data
            
        except Exception as e:
            print(f"❌ TCG Animation scraping failed: {e}")
            return {}
        finally:
            if driver:
                driver.quit()
    
    def capture_card_animations(self, driver) -> Dict:
        """Capture Pokemon card animations"""
        print("🎥 Capturing card animations...")
        
        animations_captured = []
        
        # Find card elements
        card_elements = driver.find_elements(By.CSS_SELECTOR, ".card, .pokemon-card, .tcg-card")
        
        for i, card in enumerate(card_elements[:10]):  # Limit to first 10 cards
            try:
                # Scroll card into view
                driver.execute_script("arguments[0].scrollIntoView(true);", card)
                time.sleep(2)
                
                # Hover over card to trigger animation
                ActionChains(driver).move_to_element(card).perform()
                time.sleep(3)
                
                # Take screenshot of animated state
                screenshot_path = self.output_dir / 'animations' / f'card_hover_{i}.png'
                screenshot_path.parent.mkdir(parents=True, exist_ok=True)
                card.screenshot(str(screenshot_path))
                
                # Click card to trigger flip animation
                try:
                    card.click()
                    time.sleep(2)
                    
                    # Screenshot flipped state
                    flip_screenshot_path = self.output_dir / 'animations' / f'card_flip_{i}.png'
                    card.screenshot(str(flip_screenshot_path))
                    
                    animations_captured.append({
                        'card_index': i,
                        'hover_screenshot': str(screenshot_path),
                        'flip_screenshot': str(flip_screenshot_path),
                        'animations_found': True
                    })
                    
                except:
                    animations_captured.append({
                        'card_index': i,
                        'hover_screenshot': str(screenshot_path),
                        'animations_found': False
                    })
                
            except Exception as e:
                print(f"⚠️ Error capturing animation for card {i}: {e}")
                continue
        
        print(f"✅ Captured {len(animations_captured)} card animations")
        
        return {
            'source': 'tcg.pokemon.com/en-us/all-galleries/',
            'scraped_at': datetime.now().isoformat(),
            'animations_captured': len(animations_captured),
            'animation_details': animations_captured
        }
    
    def record_card_interactions(self, driver) -> List[Dict]:
        """Record interactive elements and their behaviors"""
        print("🖱️ Recording card interactions...")
        
        interactions = []
        
        # Look for interactive elements
        interactive_elements = driver.find_elements(By.CSS_SELECTOR, 
            ".interactive, .clickable, .hoverable, [onclick], [onhover]")
        
        for element in interactive_elements:
            try:
                interaction_data = {
                    'element_tag': element.tag_name,
                    'element_class': element.get_attribute('class'),
                    'element_id': element.get_attribute('id'),
                    'has_onclick': bool(element.get_attribute('onclick')),
                    'has_hover_effect': False
                }
                
                # Test hover effect
                original_style = element.get_attribute('style')
                ActionChains(driver).move_to_element(element).perform()
                time.sleep(1)
                new_style = element.get_attribute('style')
                
                if original_style != new_style:
                    interaction_data['has_hover_effect'] = True
                    interaction_data['hover_style_change'] = {
                        'original': original_style,
                        'hover': new_style
                    }
                
                interactions.append(interaction_data)
                
            except:
                continue
        
        print(f"✅ Recorded {len(interactions)} interactive elements")
        return interactions


class ComprehensiveSiteOrchestrator:
    """Orchestrates scraping across all specialized scrapers"""
    
    def __init__(self, output_base_dir: Path):
        self.output_base_dir = output_base_dir
        self.session = requests.Session()
        
        # Setup session headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        })
    
    def setup_selenium_driver(self, headless=False):
        """Setup Selenium WebDriver"""
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
        
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    
    def run_all_scrapers(self):
        """Run all specialized scrapers in sequence"""
        print("🚀 Starting comprehensive Pokemon sites scraping...")
        
        scrapers = [
            ('pokemondb_all', PokemonDBAllScraper(
                self.output_base_dir / 'pokemondb_all', self.session)),
            ('cardmarket', CardMarketScraper(
                self.output_base_dir / 'cardmarket', self.setup_selenium_driver)),
            ('tcg_galleries', TCGAnimationScraper(
                self.output_base_dir / 'tcg_galleries', self.setup_selenium_driver)),
        ]
        
        results = {}
        
        for scraper_name, scraper in scrapers:
            print(f"\n📍 Starting {scraper_name} scraper...")
            
            if hasattr(scraper, 'scrape_complete_pokedex'):
                results[scraper_name] = scraper.scrape_complete_pokedex()
            elif hasattr(scraper, 'scrape_card_market'):
                results[scraper_name] = scraper.scrape_card_market()
            elif hasattr(scraper, 'scrape_tcg_animations'):
                results[scraper_name] = scraper.scrape_tcg_animations()
        
        # Save consolidated results
        consolidated_file = self.output_base_dir / 'consolidated_results.json'
        with open(consolidated_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print("✅ All specialized scrapers completed!")
        return results


def main():
    """Main execution function"""
    output_dir = Path("pokemon_comprehensive_scrape")
    orchestrator = ComprehensiveSiteOrchestrator(output_dir)
    orchestrator.run_all_scrapers()


if __name__ == "__main__":
    main() 