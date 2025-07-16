#!/usr/bin/env python3
"""
Phygitals.com Site Inspector
Analyzes the current site structure to understand how to properly extract Pokemon content
"""

import os
import time
import json
from urllib.parse import urljoin, urlparse
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import requests

class PhygitalsSiteInspector:
    def __init__(self):
        self.base_url = "https://www.phygitals.com"
        self.pokemon_base = f"{self.base_url}/pokemon/"
        self.setup_selenium()
        
    def setup_selenium(self):
        """Setup Selenium for site inspection"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
        
    def inspect_main_pokemon_page(self):
        """Inspect the main Pokemon page structure"""
        print("🔍 Inspecting main Pokemon page...")
        
        try:
            self.driver.get(self.pokemon_base)
            time.sleep(5)
            
            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Get page title and basic info
            page_title = self.driver.title
            current_url = self.driver.current_url
            
            print(f"📄 Page Title: {page_title}")
            print(f"🔗 Current URL: {current_url}")
            
            # Analyze page structure
            self.analyze_page_elements()
            
            # Look for navigation
            self.analyze_navigation()
            
            # Look for Pokemon-related content
            self.analyze_pokemon_content()
            
            # Save page source for analysis
            page_source = self.driver.page_source
            with open("phygitals_page_analysis.html", 'w', encoding='utf-8') as f:
                f.write(page_source)
            print("💾 Page source saved to phygitals_page_analysis.html")
            
            # Parse with BeautifulSoup for deeper analysis
            self.analyze_with_beautiful_soup(page_source)
            
        except Exception as e:
            print(f"❌ Error inspecting main page: {e}")
    
    def analyze_page_elements(self):
        """Analyze the basic page structure"""
        print("\n🏗️  Page Structure Analysis:")
        
        # Check for common container elements
        containers = [
            "main", "section", "article", "div.container", 
            "div.content", "div.page", "div.app", "#app", "#root"
        ]
        
        for container in containers:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, container)
                if elements:
                    print(f"  ✅ Found {len(elements)} {container} elements")
            except:
                continue
        
        # Check for React/Next.js app structure
        react_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-reactroot], #__next")
        if react_elements:
            print(f"  ⚛️  React/Next.js app detected: {len(react_elements)} elements")
    
    def analyze_navigation(self):
        """Analyze navigation structure"""
        print("\n🧭 Navigation Analysis:")
        
        # Look for navigation elements
        nav_selectors = [
            "nav", ".navigation", ".nav", ".menu", 
            "header nav", ".header-nav", ".main-nav"
        ]
        
        all_nav_links = []
        
        for selector in nav_selectors:
            try:
                nav_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for nav in nav_elements:
                    links = nav.find_elements(By.CSS_SELECTOR, "a")
                    for link in links:
                        href = link.get_attribute('href')
                        text = link.text.strip()
                        if href:
                            all_nav_links.append({'href': href, 'text': text})
            except:
                continue
        
        # Remove duplicates and filter
        unique_links = []
        seen_hrefs = set()
        for link in all_nav_links:
            if link['href'] not in seen_hrefs:
                unique_links.append(link)
                seen_hrefs.add(link['href'])
        
        print(f"  📋 Found {len(unique_links)} unique navigation links:")
        for link in unique_links[:10]:  # Show first 10
            print(f"    • {link['text']} → {link['href']}")
        
        if len(unique_links) > 10:
            print(f"    ... and {len(unique_links) - 10} more")
            
        return unique_links
    
    def analyze_pokemon_content(self):
        """Analyze Pokemon-specific content"""
        print("\n🎮 Pokemon Content Analysis:")
        
        # Look for Pokemon-related elements with various selectors
        pokemon_selectors = [
            # Common Pokemon selectors
            ".pokemon", "[data-pokemon]", ".pokemon-card", ".pokemon-item",
            # Gallery/grid selectors
            ".gallery", ".grid", ".collection", ".cards",
            # Generation selectors
            ".generation", "[data-generation]", ".gen",
            # Image/media selectors
            "img[src*='pokemon']", "img[alt*='pokemon']",
            # Interactive elements
            ".clickable", ".interactive", "[onclick]"
        ]
        
        found_elements = {}
        
        for selector in pokemon_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    found_elements[selector] = len(elements)
                    print(f"  ✅ {selector}: {len(elements)} elements")
                    
                    # Sample the first element for analysis
                    if elements:
                        first_elem = elements[0]
                        elem_html = first_elem.get_attribute('outerHTML')[:200]
                        print(f"    📝 Sample: {elem_html}...")
            except:
                continue
        
        if not found_elements:
            print("  ❌ No Pokemon-specific elements found with standard selectors")
            
            # Try broader search
            print("  🔍 Trying broader search...")
            self.broader_content_search()
    
    def broader_content_search(self):
        """Perform broader content search when standard selectors fail"""
        print("\n🔍 Broader Content Search:")
        
        try:
            # Look for any images
            all_images = self.driver.find_elements(By.CSS_SELECTOR, "img")
            print(f"  📷 Total images found: {len(all_images)}")
            
            pokemon_related_images = []
            for img in all_images[:20]:  # Check first 20 images
                src = img.get_attribute('src')
                alt = img.get_attribute('alt')
                if src:
                    pokemon_related_images.append({
                        'src': src,
                        'alt': alt,
                        'is_pokemon': any(term in src.lower() for term in ['pokemon', 'sprite', 'animation'])
                    })
            
            if pokemon_related_images:
                print("  🎯 Sample images found:")
                for img in pokemon_related_images[:5]:
                    print(f"    • {img['alt']} → {img['src'][:50]}...")
            
            # Look for JavaScript that might load content dynamically
            scripts = self.driver.find_elements(By.CSS_SELECTOR, "script")
            print(f"  📜 Total script elements: {len(scripts)}")
            
            # Check for data attributes
            data_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-*]")
            print(f"  📊 Elements with data attributes: {len(data_elements)}")
            
        except Exception as e:
            print(f"  ❌ Error in broader search: {e}")
    
    def analyze_with_beautiful_soup(self, page_source):
        """Use BeautifulSoup for deeper HTML analysis"""
        print("\n🍲 BeautifulSoup Analysis:")
        
        try:
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Look for common patterns
            patterns = {
                'data_attributes': soup.find_all(attrs={'data-pokemon': True}),
                'pokemon_classes': [elem for elem in soup.find_all() if elem.get('class') and any('pokemon' in str(cls).lower() for cls in elem.get('class', []))],
                'generation_elements': [elem for elem in soup.find_all() if elem.get('class') and any('generation' in str(cls).lower() for cls in elem.get('class', []))],
                'cards': [elem for elem in soup.find_all() if elem.get('class') and any('card' in str(cls).lower() for cls in elem.get('class', []))],
                'grids': [elem for elem in soup.find_all() if elem.get('class') and any(term in str(cls).lower() for cls in elem.get('class', []) for term in ['grid', 'gallery', 'collection'])]
            }
            
            for pattern_name, elements in patterns.items():
                if elements:
                    print(f"  ✅ {pattern_name}: {len(elements)} elements")
                    # Show sample
                    if elements:
                        sample = str(elements[0])[:200]
                        print(f"    📝 Sample: {sample}...")
            
            # Look for JSON data in script tags
            scripts = soup.find_all('script')
            json_data_found = []
            
            for script in scripts:
                if script.text:
                    script_content = script.text
                    if 'pokemon' in script_content.lower() and ('{' in script_content or '[' in script_content):
                        json_data_found.append(script_content[:100])
            
            if json_data_found:
                print(f"  📊 Found {len(json_data_found)} scripts with potential Pokemon JSON data")
                for i, data in enumerate(json_data_found[:3]):
                    print(f"    📄 Script {i+1}: {data}...")
                    
        except Exception as e:
            print(f"  ❌ BeautifulSoup analysis error: {e}")
    
    def test_specific_urls(self):
        """Test specific URLs that might contain Pokemon content"""
        print("\n🎯 Testing Specific URLs:")
        
        test_urls = [
            f"{self.base_url}/pokemon",
            f"{self.base_url}/pokemon/",
            f"{self.base_url}/generations",
            f"{self.base_url}/gallery",
            f"{self.base_url}/collection",
            f"{self.base_url}/cards",
            f"{self.base_url}/marketplace",
        ]
        
        for url in test_urls:
            try:
                print(f"  🔍 Testing: {url}")
                self.driver.get(url)
                time.sleep(3)
                
                # Check if page loaded successfully
                page_title = self.driver.title
                current_url = self.driver.current_url
                
                # Look for content indicators
                body_text = self.driver.find_element(By.TAG_NAME, "body").text
                has_pokemon_content = 'pokemon' in body_text.lower()
                
                print(f"    📄 Title: {page_title}")
                print(f"    🔗 Redirected to: {current_url}")
                print(f"    🎮 Has Pokemon content: {has_pokemon_content}")
                
                if has_pokemon_content:
                    # Quick analysis of this page
                    pokemon_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                        ".pokemon, [data-pokemon], .card, img")
                    print(f"    🎯 Pokemon-related elements: {len(pokemon_elements)}")
                
                print()
                
            except Exception as e:
                print(f"    ❌ Error testing {url}: {e}")
                print()
    
    def generate_inspection_report(self):
        """Generate a comprehensive inspection report"""
        report = {
            'inspection_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'base_url': self.base_url,
            'findings': {
                'site_accessible': True,
                'pokemon_content_found': False,
                'recommendations': []
            }
        }
        
        # Save report
        with open('phygitals_inspection_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print("📋 Inspection report saved to phygitals_inspection_report.json")
    
    def run_full_inspection(self):
        """Run complete site inspection"""
        print("🔍 PHYGITALS.COM SITE INSPECTION")
        print("="*50)
        
        try:
            # Step 1: Inspect main page
            self.inspect_main_pokemon_page()
            
            # Step 2: Test specific URLs
            self.test_specific_urls()
            
            # Step 3: Generate report
            self.generate_inspection_report()
            
            print("\n✅ Site inspection completed!")
            print("📋 Check phygitals_page_analysis.html for full page source")
            print("📊 Check phygitals_inspection_report.json for findings")
            
        except Exception as e:
            print(f"❌ Inspection failed: {e}")
        finally:
            if hasattr(self, 'driver'):
                self.driver.quit()

def main():
    inspector = PhygitalsSiteInspector()
    inspector.run_full_inspection()

if __name__ == "__main__":
    main() 