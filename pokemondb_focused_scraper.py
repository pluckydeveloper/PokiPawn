#!/usr/bin/env python3
"""
PokemonDB Focused Scraper
========================
Specialized scraper for pokemondb.net with comprehensive data extraction
including Pokemon stats, sprites, types, moves, and detailed information.
"""

import os
import re
import json
import time
import requests
import pandas as pd
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
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

class PokemonDBFocusedScraper:
    """Focused scraper for comprehensive PokemonDB extraction"""
    
    def __init__(self, output_dir="pokemondb_comprehensive"):
        self.output_dir = Path(output_dir)
        self.base_url = "https://pokemondb.net"
        self.session = requests.Session()
        self.downloaded_files = set()
        
        # Stats tracking
        self.stats = {
            'pokemon_extracted': 0,
            'sprites_downloaded': 0,
            'detail_pages_scraped': 0,
            'type_icons_downloaded': 0,
            'move_data_extracted': 0,
            'total_files_downloaded': 0,
            'errors': 0
        }
        
        # Setup session
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        })
        
        self.create_directory_structure()
        
    def create_directory_structure(self):
        """Create organized directory structure"""
        subdirs = [
            'data', 'sprites', 'artwork', 'type_icons', 'move_icons',
            'screenshots', 'pages', 'individual_pokemon', 'generation_data',
            'moves', 'abilities', 'items', 'reference'
        ]
        
        for subdir in subdirs:
            (self.output_dir / subdir).mkdir(parents=True, exist_ok=True)
            
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
    
    def scrape_complete_pokedex_list(self) -> Dict:
        """Scrape the complete Pokemon list from /pokedex/all"""
        print("🎯 Starting PokemonDB Complete Pokedex List scraping...")
        
        driver = None
        pokemon_data = []
        
        try:
            # Use both driver and requests for comprehensive extraction
            driver = self.setup_selenium_driver(headless=False)
            driver.get("https://pokemondb.net/pokedex/all")
            
            # Wait for page to load
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            time.sleep(3)
            
            # Take screenshot
            screenshot_path = self.output_dir / 'screenshots' / 'complete_pokedex.png'
            driver.save_screenshot(str(screenshot_path))
            
            # Also get page with requests for BeautifulSoup parsing
            response = self.session.get("https://pokemondb.net/pokedex/all")
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Save HTML
            html_path = self.output_dir / 'pages' / 'complete_pokedex.html'
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            # Extract Pokemon data using multiple methods
            
            # Method 1: BeautifulSoup parsing
            pokemon_data_bs = self.extract_pokemon_with_beautifulsoup(soup)
            
            # Method 2: Selenium parsing
            pokemon_data_selenium = self.extract_pokemon_with_selenium(driver)
            
            # Combine and deduplicate data
            pokemon_data = self.merge_pokemon_data(pokemon_data_bs, pokemon_data_selenium)
            
            print(f"✅ Extracted {len(pokemon_data)} Pokemon from complete list")
            
            # Save Pokemon data
            data_file = self.output_dir / 'data' / 'complete_pokemon_list.json'
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'source': 'pokemondb.net/pokedex/all',
                    'scraped_at': datetime.now().isoformat(),
                    'total_pokemon': len(pokemon_data),
                    'pokemon': pokemon_data
                }, f, indent=2, ensure_ascii=False)
            
            # Save as CSV
            if pokemon_data:
                df = pd.DataFrame(pokemon_data)
                csv_file = self.output_dir / 'data' / 'complete_pokemon_list.csv'
                df.to_csv(csv_file, index=False)
            
            self.stats['pokemon_extracted'] = len(pokemon_data)
            
        except Exception as e:
            print(f"❌ Complete Pokedex scraping failed: {e}")
            self.stats['errors'] += 1
            
        finally:
            if driver:
                driver.quit()
        
        return pokemon_data
    
    def extract_pokemon_with_beautifulsoup(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract Pokemon data using BeautifulSoup"""
        print("🔍 Extracting Pokemon data with BeautifulSoup...")
        
        pokemon_list = []
        
        # Look for the main Pokemon table
        tables = soup.find_all('table')
        main_table = None
        
        for table in tables:
            # Check if this looks like the Pokemon table
            if table.find('th', string=re.compile('Name|Pokémon', re.IGNORECASE)):
                main_table = table
                break
        
        if not main_table:
            print("⚠️ Pokemon table not found with BeautifulSoup")
            return []
        
        rows = main_table.find_all('tr')[1:]  # Skip header
        print(f"📊 Found {len(rows)} Pokemon rows")
        
        for i, row in enumerate(rows):
            try:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 3:
                    continue
                
                pokemon_data = {'extraction_method': 'beautifulsoup'}
                
                # Extract number and sprite from first cell
                first_cell = cells[0]
                
                # Extract Pokemon number
                number_text = first_cell.get_text(strip=True)
                number_match = re.search(r'(\d+)', number_text)
                if number_match:
                    pokemon_data['number'] = int(number_match.group(1))
                    pokemon_data['formatted_number'] = f"{int(number_match.group(1)):04d}"
                
                # Extract sprite
                img = first_cell.find('img')
                if img:
                    sprite_src = img.get('src')
                    if sprite_src:
                        pokemon_data['sprite_url'] = urljoin(self.base_url, sprite_src)
                        pokemon_data['sprite_alt'] = img.get('alt', '')
                
                # Extract name and detail URL from second cell
                name_cell = cells[1]
                name_link = name_cell.find('a')
                if name_link:
                    pokemon_data['name'] = name_link.get_text(strip=True)
                    detail_href = name_link.get('href')
                    if detail_href:
                        pokemon_data['detail_url'] = urljoin(self.base_url, detail_href)
                else:
                    pokemon_data['name'] = name_cell.get_text(strip=True)
                
                # Extract types from third cell
                type_cell = cells[2]
                type_links = type_cell.find_all('a')
                if type_links:
                    pokemon_data['types'] = [link.get_text(strip=True) for link in type_links]
                else:
                    # Fallback to text parsing
                    type_text = type_cell.get_text(strip=True)
                    pokemon_data['types'] = [t.strip() for t in type_text.split() if t.strip()]
                
                # Extract stats (Total, HP, Attack, Defense, Sp. Atk, Sp. Def, Speed)
                stat_names = ['total', 'hp', 'attack', 'defense', 'sp_attack', 'sp_defense', 'speed']
                for j, stat_name in enumerate(stat_names):
                    cell_index = j + 3
                    if cell_index < len(cells):
                        stat_text = cells[cell_index].get_text(strip=True)
                        if stat_text.isdigit():
                            pokemon_data[stat_name] = int(stat_text)
                        else:
                            pokemon_data[stat_name] = stat_text
                
                pokemon_list.append(pokemon_data)
                
            except Exception as e:
                print(f"⚠️ Error parsing Pokemon row {i}: {e}")
                continue
        
        print(f"✅ BeautifulSoup extracted {len(pokemon_list)} Pokemon")
        return pokemon_list
    
    def extract_pokemon_with_selenium(self, driver) -> List[Dict]:
        """Extract Pokemon data using Selenium"""
        print("🔍 Extracting Pokemon data with Selenium...")
        
        pokemon_list = []
        
        try:
            # Find all table rows
            table_rows = driver.find_elements(By.CSS_SELECTOR, "table tr")
            
            # Skip header row
            data_rows = [row for row in table_rows if row.find_elements(By.TAG_NAME, "td")]
            
            print(f"📊 Found {len(data_rows)} Pokemon rows with Selenium")
            
            for i, row in enumerate(data_rows):
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) < 3:
                        continue
                    
                    pokemon_data = {'extraction_method': 'selenium'}
                    
                    # Extract number and sprite
                    first_cell = cells[0]
                    number_text = first_cell.text.strip()
                    number_match = re.search(r'(\d+)', number_text)
                    if number_match:
                        pokemon_data['number'] = int(number_match.group(1))
                        pokemon_data['formatted_number'] = f"{int(number_match.group(1)):04d}"
                    
                    # Extract sprite
                    try:
                        img = first_cell.find_element(By.TAG_NAME, "img")
                        pokemon_data['sprite_url'] = img.get_attribute('src')
                        pokemon_data['sprite_alt'] = img.get_attribute('alt')
                    except:
                        pass
                    
                    # Extract name and detail URL
                    name_cell = cells[1]
                    try:
                        name_link = name_cell.find_element(By.TAG_NAME, "a")
                        pokemon_data['name'] = name_link.text.strip()
                        pokemon_data['detail_url'] = name_link.get_attribute('href')
                    except:
                        pokemon_data['name'] = name_cell.text.strip()
                    
                    # Extract types
                    type_cell = cells[2]
                    try:
                        type_links = type_cell.find_elements(By.TAG_NAME, "a")
                        pokemon_data['types'] = [link.text.strip() for link in type_links]
                    except:
                        pokemon_data['types'] = [type_cell.text.strip()]
                    
                    # Extract stats
                    stat_names = ['total', 'hp', 'attack', 'defense', 'sp_attack', 'sp_defense', 'speed']
                    for j, stat_name in enumerate(stat_names):
                        cell_index = j + 3
                        if cell_index < len(cells):
                            stat_text = cells[cell_index].text.strip()
                            if stat_text.isdigit():
                                pokemon_data[stat_name] = int(stat_text)
                            else:
                                pokemon_data[stat_name] = stat_text
                    
                    pokemon_list.append(pokemon_data)
                    
                except Exception as e:
                    print(f"⚠️ Error parsing Pokemon row {i} with Selenium: {e}")
                    continue
            
            print(f"✅ Selenium extracted {len(pokemon_list)} Pokemon")
            
        except Exception as e:
            print(f"❌ Selenium extraction failed: {e}")
        
        return pokemon_list
    
    def merge_pokemon_data(self, data1: List[Dict], data2: List[Dict]) -> List[Dict]:
        """Merge Pokemon data from different extraction methods"""
        print("🔄 Merging Pokemon data from different extraction methods...")
        
        # Use data1 as base, supplement with data2
        merged_data = data1.copy()
        
        # Create a lookup for data2 by Pokemon number
        data2_lookup = {}
        for pokemon in data2:
            number = pokemon.get('number')
            if number:
                data2_lookup[number] = pokemon
        
        # Supplement data1 with missing info from data2
        for pokemon in merged_data:
            number = pokemon.get('number')
            if number and number in data2_lookup:
                data2_pokemon = data2_lookup[number]
                
                # Fill in missing fields
                for key, value in data2_pokemon.items():
                    if key not in pokemon or not pokemon[key]:
                        pokemon[key] = value
        
        # Add any Pokemon that were only found in data2
        data1_numbers = {p.get('number') for p in data1}
        for pokemon in data2:
            number = pokemon.get('number')
            if number and number not in data1_numbers:
                merged_data.append(pokemon)
        
        print(f"✅ Merged data: {len(merged_data)} unique Pokemon")
        return merged_data
    
    def download_all_sprites(self, pokemon_data: List[Dict]):
        """Download all Pokemon sprites"""
        print("📸 Downloading Pokemon sprites...")
        
        downloaded_count = 0
        
        def download_sprite(pokemon):
            try:
                sprite_url = pokemon.get('sprite_url')
                if not sprite_url:
                    return False
                
                # Generate filename
                number = pokemon.get('formatted_number', pokemon.get('number', 'unknown'))
                name = pokemon.get('name', 'unknown').lower().replace(' ', '_')
                filename = f"{number}_{name}.png"
                
                local_path = self.output_dir / 'sprites' / filename
                
                return self.download_file(sprite_url, local_path)
                
            except Exception as e:
                print(f"❌ Error downloading sprite for {pokemon.get('name', 'unknown')}: {e}")
                return False
        
        # Download sprites in parallel
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(download_sprite, pokemon) for pokemon in pokemon_data]
            
            for future in as_completed(futures):
                if future.result():
                    downloaded_count += 1
        
        print(f"✅ Downloaded {downloaded_count} Pokemon sprites")
        self.stats['sprites_downloaded'] = downloaded_count
    
    def scrape_individual_pokemon_pages(self, pokemon_data: List[Dict], limit: int = 50):
        """Scrape individual Pokemon detail pages"""
        print(f"📄 Scraping individual Pokemon pages (limit: {limit})...")
        
        detailed_data = []
        scraped_count = 0
        
        for pokemon in pokemon_data[:limit]:
            try:
                detail_url = pokemon.get('detail_url')
                if not detail_url:
                    continue
                
                print(f"🔍 Scraping {pokemon.get('name', 'Unknown')}...")
                
                response = self.session.get(detail_url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract detailed information
                detailed_pokemon = pokemon.copy()
                detailed_pokemon.update(self.extract_pokemon_details(soup, detail_url))
                
                detailed_data.append(detailed_pokemon)
                
                # Save individual page
                safe_name = re.sub(r'[^\w\-_\.]', '_', pokemon.get('name', 'unknown'))
                page_path = self.output_dir / 'individual_pokemon' / f"{safe_name}.html"
                with open(page_path, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                
                scraped_count += 1
                time.sleep(1)  # Be respectful to the server
                
            except Exception as e:
                print(f"❌ Error scraping {pokemon.get('name', 'unknown')}: {e}")
                continue
        
        # Save detailed data
        if detailed_data:
            detail_file = self.output_dir / 'data' / 'detailed_pokemon_data.json'
            with open(detail_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'scraped_at': datetime.now().isoformat(),
                    'total_detailed': len(detailed_data),
                    'pokemon': detailed_data
                }, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Scraped {scraped_count} individual Pokemon pages")
        self.stats['detail_pages_scraped'] = scraped_count
    
    def extract_pokemon_details(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract detailed Pokemon information from individual page"""
        details = {'detail_url': url}
        
        try:
            # Extract description
            desc_elem = soup.find('p', class_='mt-2')
            if desc_elem:
                details['description'] = desc_elem.get_text(strip=True)
            
            # Extract abilities
            ability_section = soup.find('h2', string=re.compile('Abilities'))
            if ability_section:
                abilities_table = ability_section.find_next('table')
                if abilities_table:
                    abilities = []
                    for row in abilities_table.find_all('tr')[1:]:  # Skip header
                        cells = row.find_all('td')
                        if len(cells) >= 2:
                            ability_name = cells[0].get_text(strip=True)
                            ability_desc = cells[1].get_text(strip=True)
                            abilities.append({
                                'name': ability_name,
                                'description': ability_desc
                            })
                    details['abilities'] = abilities
            
            # Extract base stats
            stats_section = soup.find('h2', string=re.compile('Stats'))
            if stats_section:
                stats_table = stats_section.find_next('table')
                if stats_table:
                    base_stats = {}
                    for row in stats_table.find_all('tr'):
                        cells = row.find_all(['th', 'td'])
                        if len(cells) >= 2:
                            stat_name = cells[0].get_text(strip=True).lower().replace(' ', '_')
                            stat_value = cells[1].get_text(strip=True)
                            if stat_value.isdigit():
                                base_stats[stat_name] = int(stat_value)
                    details['base_stats'] = base_stats
            
            # Extract moves (first few for sample)
            moves_section = soup.find('h2', string=re.compile('Moves'))
            if moves_section:
                moves_table = moves_section.find_next('table')
                if moves_table:
                    moves = []
                    for row in moves_table.find_all('tr')[1:6]:  # First 5 moves
                        cells = row.find_all('td')
                        if len(cells) >= 3:
                            move_name = cells[0].get_text(strip=True)
                            move_type = cells[1].get_text(strip=True)
                            move_power = cells[2].get_text(strip=True)
                            moves.append({
                                'name': move_name,
                                'type': move_type,
                                'power': move_power
                            })
                    details['sample_moves'] = moves
            
        except Exception as e:
            print(f"⚠️ Error extracting details: {e}")
        
        return details
    
    def download_file(self, url: str, local_path: Path) -> bool:
        """Download a file with error handling"""
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
            print(f"❌ Failed to download {url}: {e}")
            return False
    
    def run_comprehensive_scraping(self):
        """Run comprehensive PokemonDB scraping"""
        print("\n" + "="*70)
        print("🎮 POKEMONDB COMPREHENSIVE SCRAPING")
        print("="*70)
        
        start_time = datetime.now()
        
        # Step 1: Scrape complete Pokemon list
        pokemon_data = self.scrape_complete_pokedex_list()
        
        if pokemon_data:
            # Step 2: Download all sprites
            self.download_all_sprites(pokemon_data)
            
            # Step 3: Scrape individual Pokemon pages (sample)
            self.scrape_individual_pokemon_pages(pokemon_data, limit=20)
        
        # Generate final report
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\n" + "="*70)
        print("🏁 POKEMONDB SCRAPING COMPLETED")
        print("="*70)
        print(f"⏱️  Duration: {duration}")
        print(f"🎯 Pokemon Extracted: {self.stats['pokemon_extracted']}")
        print(f"📸 Sprites Downloaded: {self.stats['sprites_downloaded']}")
        print(f"📄 Detail Pages Scraped: {self.stats['detail_pages_scraped']}")
        print(f"📁 Total Files Downloaded: {self.stats['total_files_downloaded']}")
        print(f"❌ Errors: {self.stats['errors']}")
        print("="*70)
        
        # Save final report
        final_report = {
            'operation_summary': {
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration.total_seconds(),
                'stats': self.stats
            },
            'pokemon_count': len(pokemon_data),
            'output_directory': str(self.output_dir.absolute())
        }
        
        report_file = self.output_dir / 'reference' / 'POKEMONDB_FINAL_REPORT.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)
        
        print(f"📋 Final report saved: {report_file}")
        
        return pokemon_data


def main():
    """Main execution function"""
    scraper = PokemonDBFocusedScraper()
    scraper.run_comprehensive_scraping()


if __name__ == "__main__":
    main() 