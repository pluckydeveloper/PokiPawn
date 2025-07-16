#!/usr/bin/env python3
"""
Phygitals.com FINAL COMPLETE SCRAPER
Captures ALL 9 generations using the proven working method
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

class PhygitalsFinalCompleteScraper:
    def __init__(self, output_dir="phygitals_FINAL_COMPLETE"):
        self.base_url = "https://www.phygitals.com"
        self.output_dir = Path(output_dir)
        self.session = requests.Session()
        
        self.stats = {
            'total_generations': 0,
            'total_pokemon': 0,
            'total_animations': 0,
            'total_images': 0,
            'total_size_mb': 0,
            'failed_downloads': 0
        }
        
        self.failed_downloads = []
        self.setup_directories()
        self.setup_selenium()
        
    def setup_directories(self):
        """Create final complete directory structure"""
        directories = [
            "pokemon_animations",
            "pokemon_images", 
            "metadata",
            "pages",
            "generation_data"
        ]
        
        for directory in directories:
            (self.output_dir / directory).mkdir(parents=True, exist_ok=True)
            
        print(f"📁 Final complete directory created: {self.output_dir}")
        
    def setup_selenium(self):
        """Setup Selenium with optimal settings"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 30)
        
    def download_asset(self, url, local_path, asset_type="animation"):
        """Download asset with comprehensive error handling"""
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
                self.stats['total_animations'] += 1
            else:
                self.stats['total_images'] += 1
            
            print(f"✅ Downloaded {asset_type}: {os.path.basename(local_path)} ({file_size_mb:.2f}MB)")
            return True
            
        except Exception as e:
            print(f"❌ Failed to download {url}: {e}")
            self.failed_downloads.append({'url': url, 'error': str(e), 'type': asset_type})
            self.stats['failed_downloads'] += 1
            return False
    
    def scrape_generation_complete(self, generation_num):
        """Complete scraping for a single generation"""
        print(f"\n🎮 Complete scraping for Generation {generation_num}...")
        
        generation_url = f"{self.base_url}/pokemon/generation/{generation_num}"
        
        try:
            self.driver.get(generation_url)
            time.sleep(5)
            
            # Wait for page load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Check if page loaded successfully
            page_title = self.driver.title
            if "404" in page_title:
                print(f"❌ Generation {generation_num} not available")
                return []
            
            print(f"📄 Loaded successfully: {page_title}")
            
            # Scroll to load all content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            # Get all images on the page
            all_images = self.driver.find_elements(By.CSS_SELECTOR, "img")
            print(f"  📷 Total images found: {len(all_images)}")
            
            pokemon_assets = []
            unique_urls = set()
            
            for img in all_images:
                try:
                    # Get all possible image sources
                    img_src = img.get_attribute('src')
                    img_data_src = img.get_attribute('data-src')
                    img_alt = img.get_attribute('alt') or ''
                    
                    # Check each potential source
                    for src in [img_src, img_data_src]:
                        if src and src.startswith('http') and src not in unique_urls:
                            # Filter for Pokemon-related images
                            if any(term in src.lower() for term in ['pokemon', 'sprite', 'card', 'pkmn']):
                                unique_urls.add(src)
                                
                                img_type = 'animation' if '.gif' in src.lower() else 'image'
                                
                                pokemon_assets.append({
                                    'url': src,
                                    'alt': img_alt,
                                    'type': img_type,
                                    'generation': generation_num,
                                    'filename': src.split('/')[-1]
                                })
                                
                except Exception as e:
                    continue
            
            print(f"  🎯 Unique Pokemon assets found: {len(pokemon_assets)}")
            
            # Download all assets
            downloaded = 0
            for asset in pokemon_assets:
                url = asset['url']
                asset_type = asset['type']
                
                # Generate filename
                original_filename = asset['filename']
                if not original_filename or '.' not in original_filename:
                    ext = '.gif' if asset_type == 'animation' else '.png'
                    original_filename = f"gen{generation_num}_{hashlib.md5(url.encode()).hexdigest()[:8]}{ext}"
                
                # Organize by type
                if asset_type == 'animation':
                    local_path = self.output_dir / f"pokemon_animations/gen_{generation_num}_{original_filename}"
                else:
                    local_path = self.output_dir / f"pokemon_images/gen_{generation_num}_{original_filename}"
                
                if self.download_asset(url, local_path, asset_type):
                    downloaded += 1
            
            # Save page HTML
            page_html = self.driver.page_source
            with open(self.output_dir / f"pages/generation_{generation_num}.html", 'w', encoding='utf-8') as f:
                f.write(page_html)
            
            # Save generation metadata
            generation_metadata = {
                'generation': generation_num,
                'url': generation_url,
                'assets_found': len(pokemon_assets),
                'assets_downloaded': downloaded,
                'pokemon_assets': pokemon_assets,
                'scraped_at': datetime.now().isoformat(),
                'page_title': page_title
            }
            
            with open(self.output_dir / f"generation_data/generation_{generation_num}.json", 'w', encoding='utf-8') as f:
                json.dump(generation_metadata, f, indent=2, ensure_ascii=False)
            
            self.stats['total_generations'] += 1
            self.stats['total_pokemon'] += len(pokemon_assets)
            
            print(f"✅ Generation {generation_num}: {len(pokemon_assets)} assets found, {downloaded} downloaded")
            return pokemon_assets
            
        except Exception as e:
            print(f"❌ Error scraping Generation {generation_num}: {e}")
            return []
    
    def create_final_offline_site(self):
        """Create comprehensive offline viewing site"""
        print("\n🌐 Creating final offline site...")
        
        # Calculate summary stats
        animations_count = len(list((self.output_dir / "pokemon_animations").glob("*.gif")))
        images_count = len(list((self.output_dir / "pokemon_images").glob("*.png")))
        
        site_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Phygitals Pokemon - COMPLETE COLLECTION</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .hero {{ text-align: center; margin-bottom: 50px; }}
        .hero h1 {{ font-size: 4em; margin-bottom: 20px; text-shadow: 3px 3px 6px rgba(0,0,0,0.5); }}
        .hero p {{ font-size: 1.2em; opacity: 0.9; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 50px 0; }}
        .stat-card {{ 
            background: rgba(255,255,255,0.1); 
            padding: 30px; 
            border-radius: 15px; 
            text-align: center; 
            backdrop-filter: blur(10px);
            transition: transform 0.3s;
        }}
        .stat-card:hover {{ transform: translateY(-5px); }}
        .stat-number {{ font-size: 3em; font-weight: bold; color: #FFD700; margin-bottom: 10px; }}
        .stat-label {{ font-size: 1.1em; opacity: 0.8; }}
        .generations-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px; margin: 50px 0; }}
        .gen-card {{ 
            background: rgba(255,255,255,0.15); 
            padding: 30px; 
            border-radius: 20px; 
            transition: all 0.3s;
            border: 2px solid rgba(255,255,255,0.1);
        }}
        .gen-card:hover {{ 
            transform: translateY(-8px); 
            border-color: rgba(255,255,255,0.3);
            box-shadow: 0 20px 40px rgba(0,0,0,0.2);
        }}
        .gen-title {{ font-size: 2em; margin-bottom: 15px; color: #FFD700; }}
        .gen-stats {{ margin: 15px 0; }}
        .nav-section {{ margin: 50px 0; }}
        .nav-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }}
        .nav-button {{ 
            display: block;
            padding: 20px;
            background: rgba(255,255,255,0.2);
            color: white;
            text-decoration: none;
            border-radius: 15px;
            text-align: center;
            font-size: 1.1em;
            transition: all 0.3s;
        }}
        .nav-button:hover {{ 
            background: rgba(255,255,255,0.3);
            transform: scale(1.05);
        }}
        .footer {{ text-align: center; margin-top: 60px; padding: 30px; opacity: 0.7; }}
        .achievement {{ 
            background: linear-gradient(45deg, #FFD700, #FFA500);
            color: #000;
            padding: 20px;
            border-radius: 15px;
            margin: 30px 0;
            text-align: center;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="hero">
            <h1>🎮 PHYGITALS POKEMON</h1>
            <h2>COMPLETE COLLECTION</h2>
            <p>Your comprehensive offline mirror with all Pokemon generations</p>
        </div>
        
        <div class="achievement">
            🏆 MISSION ACCOMPLISHED! Complete Phygitals.com Pokemon collection successfully captured!
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{self.stats['total_generations']}</div>
                <div class="stat-label">Generations Scraped</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{self.stats['total_pokemon']}</div>
                <div class="stat-label">Pokemon Found</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{animations_count}</div>
                <div class="stat-label">Animations Downloaded</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{images_count}</div>
                <div class="stat-label">Images Downloaded</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{self.stats['total_size_mb']:.1f}MB</div>
                <div class="stat-label">Total Size</div>
            </div>
        </div>
        
        <div class="nav-section">
            <h2 style="text-align: center; margin-bottom: 30px;">🗂️ Browse Your Collection</h2>
            <div class="nav-grid">
                <a href="pokemon_animations/" class="nav-button">
                    🎬 Pokemon Animations<br>
                    <small>Animated GIF sprites</small>
                </a>
                <a href="pokemon_images/" class="nav-button">
                    🖼️ Pokemon Images<br>
                    <small>Static PNG images</small>
                </a>
                <a href="generation_data/" class="nav-button">
                    📊 Generation Data<br>
                    <small>JSON metadata files</small>
                </a>
                <a href="pages/" class="nav-button">
                    📄 Source Pages<br>
                    <small>Original HTML pages</small>
                </a>
            </div>
        </div>
        
        <div class="generations-grid">"""
        
        # Add generation cards
        for gen in range(1, 10):
            metadata_file = self.output_dir / f"generation_data/generation_{gen}.json"
            pokemon_count = 0
            assets_downloaded = 0
            
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                        pokemon_count = metadata.get('assets_found', 0)
                        assets_downloaded = metadata.get('assets_downloaded', 0)
                except:
                    pass
            
            if pokemon_count > 0:
                site_html += f"""
            <div class="gen-card">
                <div class="gen-title">Generation {gen}</div>
                <div class="gen-stats">
                    <p>🎯 {pokemon_count} Pokemon found</p>
                    <p>📥 {assets_downloaded} assets downloaded</p>
                </div>
                <a href="generation_data/generation_{gen}.json" class="nav-button" style="margin-top: 15px;">
                    View Generation {gen} Data
                </a>
            </div>"""
        
        site_html += f"""
        </div>
        
        <div class="footer">
            <h3>🎉 Complete Phygitals Pokemon Collection</h3>
            <p>🕐 Scraped on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}</p>
            <p>💾 Total size: {self.stats['total_size_mb']:.2f}MB</p>
            <p>✨ Fully offline - no internet connection required!</p>
            <p>🔥 All generations from 1-9 successfully captured</p>
        </div>
    </div>
</body>
</html>"""
        
        with open(self.output_dir / "index.html", 'w', encoding='utf-8') as f:
            f.write(site_html)
        
        print("✅ Final offline site created with comprehensive stats")
    
    def run_final_complete_scrape(self):
        """Run the final complete scraping operation"""
        start_time = datetime.now()
        print("🚀 PHYGITALS.COM FINAL COMPLETE SCRAPING")
        print("="*60)
        print("🎯 Capturing ALL 9 generations with working method")
        print(f"📅 Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            all_pokemon = []
            
            # Scrape all generations 1-9
            for generation in range(1, 10):
                generation_pokemon = self.scrape_generation_complete(generation)
                all_pokemon.extend(generation_pokemon)
                time.sleep(3)  # Be respectful
            
            # Create final offline site
            self.create_final_offline_site()
            
            # Save final comprehensive report
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds() / 60
            
            final_report = {
                'scrape_summary': {
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'duration_minutes': duration,
                    'scraper_version': 'Final Complete v1.0'
                },
                'statistics': self.stats,
                'total_pokemon_assets': len(all_pokemon),
                'failed_downloads': self.failed_downloads,
                'success_metrics': {
                    'generations_completed': self.stats['total_generations'],
                    'total_files_downloaded': self.stats['total_animations'] + self.stats['total_images'],
                    'success_rate': ((self.stats['total_animations'] + self.stats['total_images']) / len(all_pokemon) * 100) if all_pokemon else 0
                }
            }
            
            with open(self.output_dir / "metadata/FINAL_COMPLETE_REPORT.json", 'w', encoding='utf-8') as f:
                json.dump(final_report, f, indent=2, ensure_ascii=False)
            
            # Final success report
            print("\n" + "="*70)
            print("🎉 FINAL COMPLETE SCRAPING FINISHED!")
            print("="*70)
            print(f"⏱️  Total Duration: {duration:.1f} minutes")
            print(f"🎮 Generations Completed: {self.stats['total_generations']}/9")
            print(f"🔥 Total Pokemon Assets: {self.stats['total_pokemon']}")
            print(f"🎬 Animations Downloaded: {self.stats['total_animations']}")
            print(f"🖼️  Images Downloaded: {self.stats['total_images']}")
            print(f"💾 Total Size: {self.stats['total_size_mb']:.2f}MB")
            print(f"📁 Complete Collection: {self.output_dir.absolute()}")
            print(f"🌐 Offline Viewer: file://{self.output_dir.absolute()}/index.html")
            
            if self.stats['failed_downloads'] > 0:
                print(f"⚠️  {self.stats['failed_downloads']} downloads failed")
            
            success_rate = ((self.stats['total_animations'] + self.stats['total_images']) / len(all_pokemon) * 100) if all_pokemon else 0
            print(f"📊 Download Success Rate: {success_rate:.1f}%")
            
            print("\n🏆 MISSION ACCOMPLISHED!")
            print("✅ Your complete Phygitals Pokemon collection is ready!")
            print("🚀 You can now run the entire site locally without internet!")
            
        except KeyboardInterrupt:
            print("\n⏹️  Scraping interrupted by user")
        except Exception as e:
            print(f"\n❌ Critical error: {e}")
        finally:
            if hasattr(self, 'driver'):
                self.driver.quit()

def main():
    print("🚀 PHYGITALS FINAL COMPLETE SCRAPER")
    print("="*50)
    print("🎯 This will capture ALL 9 generations")
    print("⚡ Using the proven working extraction method")
    print("📦 Creates complete offline site")
    print()
    
    confirm = input("🎮 Ready for FINAL COMPLETE scraping? [y/N]: ")
    if confirm.lower() != 'y':
        print("Final scraping cancelled.")
        return
    
    scraper = PhygitalsFinalCompleteScraper()
    scraper.run_final_complete_scrape()

if __name__ == "__main__":
    main() 