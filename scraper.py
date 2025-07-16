#!/usr/bin/env python3
"""
Website Scraper for Phygitals Pokemon Site
Downloads the complete website including all assets for local hosting
"""

import os
import re
import requests
import urllib.parse
from pathlib import Path
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin, urlparse
import mimetypes

class WebsiteScraper:
    def __init__(self, base_url, output_dir="scraped_site"):
        self.base_url = base_url.rstrip('/')
        self.domain = urlparse(base_url).netloc
        self.output_dir = Path(output_dir)
        self.downloaded_files = set()
        self.session = requests.Session()
        
        # Set user agent to avoid blocking
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True)
        
    def clean_filename(self, filename):
        """Clean filename for filesystem compatibility"""
        return re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    def download_file(self, url, local_path):
        """Download a file from URL to local path"""
        try:
            if url in self.downloaded_files:
                return True
                
            print(f"Downloading: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Create directory if it doesn't exist
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            self.downloaded_files.add(url)
            print(f"Saved: {local_path}")
            return True
            
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return False
    
    def get_local_path(self, url):
        """Convert URL to local file path"""
        parsed = urlparse(url)
        path = parsed.path
        
        if not path or path == '/':
            path = '/index.html'
        elif not Path(path).suffix:
            path = path.rstrip('/') + '/index.html'
        
        # Clean the path
        path = path.lstrip('/')
        local_path = self.output_dir / self.clean_filename(path)
        
        return local_path
    
    def process_css(self, css_content, css_url):
        """Process CSS content to download referenced assets"""
        # Find URLs in CSS (url(), @import, etc.)
        url_pattern = r'url\(["\']?([^)"\'\s]+)["\']?\)'
        import_pattern = r'@import\s+["\']([^"\']+)["\']'
        
        def replace_url(match):
            asset_url = match.group(1)
            if asset_url.startswith('data:'):
                return match.group(0)
            
            full_url = urljoin(css_url, asset_url)
            local_path = self.get_local_path(full_url)
            
            if self.download_file(full_url, local_path):
                # Convert to relative path
                rel_path = os.path.relpath(local_path, css_url.parent if hasattr(css_url, 'parent') else self.output_dir)
                return f'url("{rel_path}")'
            
            return match.group(0)
        
        css_content = re.sub(url_pattern, replace_url, css_content)
        css_content = re.sub(import_pattern, lambda m: f'@import "{self.process_import(m.group(1), css_url)}"', css_content)
        
        return css_content
    
    def process_import(self, import_url, base_url):
        """Process CSS @import statements"""
        full_url = urljoin(str(base_url), import_url)
        local_path = self.get_local_path(full_url)
        
        if self.download_file(full_url, local_path):
            return os.path.relpath(local_path, self.output_dir)
        
        return import_url
    
    def scrape_page(self, url, local_path=None):
        """Scrape a single page and all its assets"""
        try:
            print(f"Scraping page: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            if local_path is None:
                local_path = self.get_local_path(url)
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Download and update CSS files
            for link in soup.find_all('link', {'rel': 'stylesheet'}):
                href = link.get('href')
                if href:
                    css_url = urljoin(url, href)
                    css_local_path = self.get_local_path(css_url)
                    
                    if self.download_file(css_url, css_local_path):
                        # Process CSS content
                        try:
                            css_response = self.session.get(css_url)
                            processed_css = self.process_css(css_response.text, css_url)
                            
                            with open(css_local_path, 'w', encoding='utf-8') as f:
                                f.write(processed_css)
                        except Exception as e:
                            print(f"Error processing CSS {css_url}: {e}")
                        
                        # Update link href to local path
                        rel_path = os.path.relpath(css_local_path, local_path.parent)
                        link['href'] = rel_path
            
            # Download and update JavaScript files
            for script in soup.find_all('script', src=True):
                src = script.get('src')
                if src:
                    js_url = urljoin(url, src)
                    js_local_path = self.get_local_path(js_url)
                    
                    if self.download_file(js_url, js_local_path):
                        rel_path = os.path.relpath(js_local_path, local_path.parent)
                        script['src'] = rel_path
            
            # Download and update images
            for img in soup.find_all('img', src=True):
                src = img.get('src')
                if src and not src.startswith('data:'):
                    img_url = urljoin(url, src)
                    img_local_path = self.get_local_path(img_url)
                    
                    if self.download_file(img_url, img_local_path):
                        rel_path = os.path.relpath(img_local_path, local_path.parent)
                        img['src'] = rel_path
            
            # Handle srcset attributes
            for img in soup.find_all(['img', 'source'], srcset=True):
                srcset = img.get('srcset')
                if srcset:
                    new_srcset_parts = []
                    for part in srcset.split(','):
                        part = part.strip()
                        if ' ' in part:
                            src_part, size_part = part.rsplit(' ', 1)
                        else:
                            src_part, size_part = part, ''
                        
                        if not src_part.startswith('data:'):
                            img_url = urljoin(url, src_part)
                            img_local_path = self.get_local_path(img_url)
                            
                            if self.download_file(img_url, img_local_path):
                                rel_path = os.path.relpath(img_local_path, local_path.parent)
                                new_part = f"{rel_path} {size_part}".strip()
                                new_srcset_parts.append(new_part)
                            else:
                                new_srcset_parts.append(part)
                        else:
                            new_srcset_parts.append(part)
                    
                    img['srcset'] = ', '.join(new_srcset_parts)
            
            # Download and update other assets (fonts, videos, etc.)
            for tag in soup.find_all(['link', 'source', 'video', 'audio']):
                for attr in ['href', 'src']:
                    url_val = tag.get(attr)
                    if url_val and not url_val.startswith('data:') and not url_val.startswith('#'):
                        asset_url = urljoin(url, url_val)
                        asset_local_path = self.get_local_path(asset_url)
                        
                        if self.download_file(asset_url, asset_local_path):
                            rel_path = os.path.relpath(asset_local_path, local_path.parent)
                            tag[attr] = rel_path
            
            # Handle inline styles with background images
            for tag in soup.find_all(style=True):
                style = tag.get('style')
                if 'url(' in style:
                    # Process inline CSS
                    processed_style = self.process_css(style, url)
                    tag['style'] = processed_style
            
            # Save the modified HTML
            local_path.parent.mkdir(parents=True, exist_ok=True)
            with open(local_path, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            
            print(f"Saved page: {local_path}")
            return True
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return False
    
    def scrape_website(self):
        """Scrape the entire website starting from the base URL"""
        print(f"Starting to scrape: {self.base_url}")
        
        # Start with the main page
        main_page_path = self.output_dir / "index.html"
        success = self.scrape_page(self.base_url, main_page_path)
        
        if success:
            print(f"\nScraping completed!")
            print(f"Website saved to: {self.output_dir}")
            print(f"Open {main_page_path} in your browser to view the local version")
        else:
            print("Failed to scrape the website")
        
        return success

def main():
    url = "https://www.phygitals.com/pokemon/generation/1"
    output_dir = "scraped_pokemon_site"
    
    scraper = WebsiteScraper(url, output_dir)
    scraper.scrape_website()

if __name__ == "__main__":
    main() 