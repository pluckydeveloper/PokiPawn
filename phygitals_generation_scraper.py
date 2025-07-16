#!/usr/bin/env python3
"""
Phygitals Pokemon Generation Scraper
Enhanced scraper for all Pokemon generations from Phygitals.com
Focus on images, animations, and media content
"""

import os
import re
import requests
import urllib.parse
from pathlib import Path
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin, urlparse
import json
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class PhygitalsGenerationScraper:
    def __init__(self, output_dir="phygitals_pokemon_complete"):
        self.base_url = "https://www.phygitals.com"
        self.output_dir = Path(output_dir)
        self.session = requests.Session()
        self.downloaded_files = set()
        self.download_stats = {
            'images': 0,
            'videos': 0, 
            'audio': 0,
            'other': 0,
            'failed': 0
        }
        self.failed_downloads = []
        self.lock = threading.Lock()
        
        # Enhanced user agent and headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # Create output directory structure
        self.create_directories()
        
    def create_directories(self):
        """Create organized directory structure for each generation"""
        directories = []
        
        # Create directories for each generation
        for gen in range(1, 10):
            gen_dirs = [
                f"generation_{gen}/images/pokemon",
                f"generation_{gen}/images/artwork", 
                f"generation_{gen}/images/sprites",
                f"generation_{gen}/animations/videos",
                f"generation_{gen}/animations/gifs",
                f"generation_{gen}/audio",
                f"generation_{gen}/data",
                f"generation_{gen}/pages"
            ]
            directories.extend(gen_dirs)
        
        # Global directories
        directories.extend([
            "assets/css",
            "assets/js", 
            "assets/fonts",
            "assets/icons"
        ])
        
        for directory in directories:
            (self.output_dir / directory).mkdir(parents=True, exist_ok=True)
    
    def clean_filename(self, filename):
        """Clean filename for filesystem compatibility"""
        # Remove or replace problematic characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'[^\w\-_\.]', '_', filename)
        return filename
    
    def get_file_type(self, url, content_type=None):
        """Determine file type from URL and content type"""
        url_lower = url.lower()
        
        # Images
        if any(ext in url_lower for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.bmp']):
            return 'images'
        
        # Videos
        if any(ext in url_lower for ext in ['.mp4', '.webm', '.avi', '.mov', '.mkv']):
            return 'videos'
        
        # Audio
        if any(ext in url_lower for ext in ['.mp3', '.wav', '.ogg', '.m4a']):
            return 'audio'
        
        # Check content type if available
        if content_type:
            if content_type.startswith('image/'):
                return 'images'
            elif content_type.startswith('video/'):
                return 'videos'
            elif content_type.startswith('audio/'):
                return 'audio'
        
        return 'other'
    
    def download_file(self, url, local_path, generation=None, file_category='other'):
        """Download a file with progress tracking"""
        if url in self.downloaded_files:
            return True
            
        try:
            print(f"📥 Downloading: {url}")
            response = self.session.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Create directory if it doesn't exist
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Get content type for better categorization
            content_type = response.headers.get('content-type', '')
            actual_file_type = self.get_file_type(url, content_type)
            
            # Download with progress for large files
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
            
            # Update statistics
            with self.lock:
                self.downloaded_files.add(url)
                self.download_stats[actual_file_type] += 1
            
            print(f"✅ Saved: {local_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to download {url}: {e}")
            with self.lock:
                self.failed_downloads.append(url)
                self.download_stats['failed'] += 1
            return False
    
    def get_local_path(self, url, generation=None, file_category='other'):
        """Convert URL to local file path with generation organization"""
        parsed = urlparse(url)
        path = parsed.path
        
        if not path or path == '/':
            path = '/index.html'
        elif not Path(path).suffix and not path.endswith('/'):
            # Try to determine file extension from URL or add .html
            if any(img_ext in url.lower() for img_ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                pass  # Keep as is
            elif not path.endswith('/'):
                path += '.html'
        
        # Clean the path
        path = path.lstrip('/')
        path_parts = path.split('/')
        clean_parts = [self.clean_filename(part) for part in path_parts]
        clean_path = '/'.join(clean_parts)
        
        # Organize by generation if specified
        if generation:
            base_path = f"generation_{generation}"
            
            # Determine subcategory based on file type
            file_type = self.get_file_type(url)
            if file_type == 'images':
                if 'sprite' in url.lower():
                    base_path += "/images/sprites"
                elif any(art in url.lower() for art in ['artwork', 'art', 'official']):
                    base_path += "/images/artwork"
                else:
                    base_path += "/images/pokemon"
            elif file_type == 'videos':
                base_path += "/animations/videos"
            elif file_type == 'audio':
                base_path += "/audio"
            else:
                if clean_path.endswith('.html'):
                    base_path += "/pages"
                else:
                    base_path += "/data"
            
            local_path = self.output_dir / base_path / clean_path
        else:
            # Global assets
            if any(asset in url.lower() for asset in ['css', 'style']):
                local_path = self.output_dir / "assets" / "css" / clean_path
            elif any(asset in url.lower() for asset in ['js', 'javascript']):
                local_path = self.output_dir / "assets" / "js" / clean_path
            elif any(asset in url.lower() for asset in ['font', 'woff', 'ttf']):
                local_path = self.output_dir / "assets" / "fonts" / clean_path
            else:
                local_path = self.output_dir / clean_path
        
        return local_path
    
    def extract_media_from_html(self, soup, base_url):
        """Extract all media URLs from HTML"""
        media_urls = []
        
        # Images
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                media_urls.append(urljoin(base_url, src))
            
            # Also check srcset for responsive images
            srcset = img.get('srcset')
            if srcset:
                for src_item in srcset.split(','):
                    src_url = src_item.strip().split(' ')[0]
                    media_urls.append(urljoin(base_url, src_url))
        
        # Videos
        for video in soup.find_all('video'):
            src = video.get('src')
            if src:
                media_urls.append(urljoin(base_url, src))
            
            # Check source tags within video
            for source in video.find_all('source'):
                src = source.get('src')
                if src:
                    media_urls.append(urljoin(base_url, src))
        
        # Audio
        for audio in soup.find_all('audio'):
            src = audio.get('src')
            if src:
                media_urls.append(urljoin(base_url, src))
            
            # Check source tags within audio
            for source in audio.find_all('source'):
                src = source.get('src')
                if src:
                    media_urls.append(urljoin(base_url, src))
        
        # Background images in CSS and style attributes
        for element in soup.find_all(style=True):
            style = element.get('style')
            bg_matches = re.findall(r'background-image:\s*url\(["\']?([^)"\'\s]+)["\']?\)', style)
            for match in bg_matches:
                media_urls.append(urljoin(base_url, match))
        
        # Links to media files
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and any(ext in href.lower() for ext in ['.png', '.jpg', '.jpeg', '.gif', '.mp4', '.webm', '.mp3']):
                media_urls.append(urljoin(base_url, href))
        
        return list(set(media_urls))  # Remove duplicates
    
    def process_css_for_media(self, css_content, css_url):
        """Extract media URLs from CSS content"""
        media_urls = []
        
        # Find all url() references in CSS
        url_pattern = r'url\(["\']?([^)"\'\s]+)["\']?\)'
        matches = re.findall(url_pattern, css_content)
        
        for match in matches:
            if not match.startswith('data:'):  # Skip data URLs
                full_url = urljoin(css_url, match)
                media_urls.append(full_url)
        
        return media_urls
    
    def scrape_generation(self, generation_num, max_workers=5):
        """Scrape a specific Pokemon generation"""
        print(f"\n🎮 Scraping Pokemon Generation {generation_num}")
        print("=" * 60)
        
        generation_url = f"{self.base_url}/pokemon/generation/{generation_num}"
        
        try:
            response = self.session.get(generation_url, timeout=30)
            response.raise_for_status()
            
            # Save the main page
            main_page_path = self.output_dir / f"generation_{generation_num}" / "pages" / "index.html"
            main_page_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract all media URLs
            media_urls = self.extract_media_from_html(soup, generation_url)
            print(f"📊 Found {len(media_urls)} media files for Generation {generation_num}")
            
            # Download CSS files and extract media from them
            css_urls = []
            for link in soup.find_all('link', {'rel': 'stylesheet'}):
                href = link.get('href')
                if href:
                    css_url = urljoin(generation_url, href)
                    css_urls.append(css_url)
            
            # Process CSS files for additional media
            for css_url in css_urls:
                try:
                    css_response = self.session.get(css_url, timeout=30)
                    css_media = self.process_css_for_media(css_response.text, css_url)
                    media_urls.extend(css_media)
                    
                    # Save CSS file
                    css_local_path = self.get_local_path(css_url)
                    self.download_file(css_url, css_local_path)
                    
                except Exception as e:
                    print(f"❌ Error processing CSS {css_url}: {e}")
            
            # Download JavaScript files (may contain dynamic media loading)
            for script in soup.find_all('script', src=True):
                src = script.get('src')
                if src:
                    js_url = urljoin(generation_url, src)
                    js_local_path = self.get_local_path(js_url)
                    self.download_file(js_url, js_local_path)
            
            # Download all media files with threading
            print(f"📥 Starting download of {len(set(media_urls))} unique media files...")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_url = {}
                
                for url in set(media_urls):
                    local_path = self.get_local_path(url, generation_num)
                    future = executor.submit(self.download_file, url, local_path, generation_num)
                    future_to_url[future] = url
                
                # Process completed downloads
                for future in as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        future.result()
                    except Exception as e:
                        print(f"❌ Error downloading {url}: {e}")
            
            # Update HTML with local paths
            self.update_html_paths(soup, generation_url, generation_num)
            
            # Save updated HTML
            with open(main_page_path, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            
            print(f"✅ Generation {generation_num} scraping completed!")
            
        except Exception as e:
            print(f"❌ Error scraping Generation {generation_num}: {e}")
    
    def update_html_paths(self, soup, base_url, generation):
        """Update HTML to use local file paths"""
        # Update image sources
        for img in soup.find_all('img', src=True):
            src = img.get('src')
            if src and not src.startswith('data:'):
                full_url = urljoin(base_url, src)
                local_path = self.get_local_path(full_url, generation)
                relative_path = os.path.relpath(local_path, self.output_dir / f"generation_{generation}" / "pages")
                img['src'] = relative_path
        
        # Update video sources
        for video in soup.find_all('video', src=True):
            src = video.get('src')
            if src:
                full_url = urljoin(base_url, src)
                local_path = self.get_local_path(full_url, generation)
                relative_path = os.path.relpath(local_path, self.output_dir / f"generation_{generation}" / "pages")
                video['src'] = relative_path
        
        # Update CSS links
        for link in soup.find_all('link', {'rel': 'stylesheet'}):
            href = link.get('href')
            if href:
                full_url = urljoin(base_url, href)
                local_path = self.get_local_path(full_url)
                relative_path = os.path.relpath(local_path, self.output_dir / f"generation_{generation}" / "pages")
                link['href'] = relative_path
        
        # Update script sources
        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src:
                full_url = urljoin(base_url, src)
                local_path = self.get_local_path(full_url)
                relative_path = os.path.relpath(local_path, self.output_dir / f"generation_{generation}" / "pages")
                script['src'] = relative_path
    
    def scrape_all_generations(self, generations=None, max_workers=3):
        """Scrape all or specified Pokemon generations"""
        if generations is None:
            generations = list(range(1, 10))  # Generations 1-9
        
        print(f"🚀 Starting Phygitals Pokemon Generation Scraper")
        print(f"📊 Generations to scrape: {generations}")
        print(f"📁 Output directory: {self.output_dir}")
        print("=" * 80)
        
        start_time = time.time()
        
        for generation in generations:
            try:
                self.scrape_generation(generation, max_workers)
                time.sleep(1)  # Brief pause between generations
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
        print("📊 COMPLETE DOWNLOAD SUMMARY")
        print("=" * 80)
        
        total_files = sum(self.download_stats.values()) - self.download_stats['failed']
        
        print(f"✅ Total files downloaded: {total_files}")
        print(f"🖼️  Images: {self.download_stats['images']}")
        print(f"🎬 Videos: {self.download_stats['videos']}")
        print(f"🔊 Audio: {self.download_stats['audio']}")
        print(f"📄 Other files: {self.download_stats['other']}")
        print(f"❌ Failed downloads: {self.download_stats['failed']}")
        print(f"⏱️  Total time: {elapsed_time:.2f} seconds")
        print(f"📁 Files saved to: {self.output_dir}")
        
        if self.failed_downloads:
            print(f"\n⚠️  Failed URLs (first 10):")
            for url in self.failed_downloads[:10]:
                print(f"   {url}")
        
        print(f"\n🎉 Scraping complete!")
        
        # Save summary as JSON
        summary = {
            'stats': self.download_stats,
            'total_files': total_files,
            'elapsed_time': elapsed_time,
            'failed_urls': self.failed_downloads,
            'output_directory': str(self.output_dir)
        }
        
        summary_path = self.output_dir / "scraping_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

def main():
    parser = argparse.ArgumentParser(description="Scrape Pokemon generations from Phygitals.com")
    parser.add_argument("--output", "-o", default="phygitals_pokemon_complete",
                       help="Output directory (default: phygitals_pokemon_complete)")
    parser.add_argument("--generations", "-g", nargs="+", type=int, 
                       help="Specific generations to scrape (e.g., -g 1 2 3)")
    parser.add_argument("--workers", "-w", type=int, default=5,
                       help="Number of download workers per generation (default: 5)")
    
    # Generation shortcuts
    parser.add_argument("--classic", action="store_true",
                       help="Download classic generations (1-3)")
    parser.add_argument("--modern", action="store_true",
                       help="Download modern generations (6-9)")
    parser.add_argument("--all", action="store_true",
                       help="Download all generations (1-9)")
    
    args = parser.parse_args()
    
    # Determine which generations to scrape
    if args.all:
        generations = list(range(1, 10))
    elif args.classic:
        generations = [1, 2, 3]
    elif args.modern:
        generations = [6, 7, 8, 9]
    elif args.generations:
        generations = args.generations
    else:
        # Default to first 3 generations for demo
        generations = [1, 2, 3]
    
    # Create and run scraper
    scraper = PhygitalsGenerationScraper(args.output)
    scraper.scrape_all_generations(generations, args.workers)

if __name__ == "__main__":
    main() 