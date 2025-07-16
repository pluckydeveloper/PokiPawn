#!/usr/bin/env python3
"""
Advanced Pokemon TCG Galleries Scraper
=====================================
Enhanced scraper with multiple evasion techniques for tcg.pokemon.com/en-us/all-galleries/
Implements multiple bypass strategies to penetrate site protection.
"""

import os
import time
import json
import random
import asyncio
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pyautogui
import cv2
import numpy as np

class AdvancedTCGScraper:
    """Advanced scraper with multiple bypass techniques for Pokemon TCG galleries"""
    
    def __init__(self, output_dir="tcg_advanced_capture"):
        self.output_dir = Path(output_dir)
        self.target_url = "https://tcg.pokemon.com/en-us/all-galleries/"
        self.base_url = "https://tcg.pokemon.com"
        
        # Multiple user agents to rotate
        self.user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
        ]
        
        # Proxy rotation (add your proxies here)
        self.proxies = [
            None,  # Direct connection
            # Add proxy configurations here if available
        ]
        
        self.session = None
        self.driver = None
        self.captured_data = {}
        
        self.create_output_structure()
    
    def create_output_structure(self):
        """Create comprehensive output directory structure"""
        subdirs = [
            'screenshots', 'card_images', 'animations', 'videos',
            'raw_html', 'json_data', 'metadata', 'network_logs',
            'bypass_attempts', 'success_logs'
        ]
        
        for subdir in subdirs:
            (self.output_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    def setup_undetected_chrome(self):
        """Setup undetected Chrome driver with advanced evasion"""
        options = uc.ChromeOptions()
        
        # Anti-detection options
        options.add_argument('--no-first-run')
        options.add_argument('--no-service-autorun')
        options.add_argument('--no-default-browser-check')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--disable-ipc-flooding-protection')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Randomize window size
        width = random.randint(1200, 1920)
        height = random.randint(800, 1080)
        options.add_argument(f'--window-size={width},{height}')
        
        # Random user agent
        user_agent = random.choice(self.user_agents)
        options.add_argument(f'--user-agent={user_agent}')
        
        # Additional stealth options
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-setuid-sandbox')
        options.add_argument('--disable-accelerated-2d-canvas')
        options.add_argument('--disable-accelerated-video-decode')
        
        try:
            self.driver = uc.Chrome(options=options, version_main=None)
            
            # Execute stealth scripts
            self.apply_stealth_scripts()
            
            print(f"✅ Undetected Chrome driver initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup undetected Chrome: {e}")
            return False
    
    def apply_stealth_scripts(self):
        """Apply JavaScript stealth scripts to avoid detection"""
        stealth_scripts = [
            # Hide webdriver property
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})",
            
            # Override permissions
            """
            Object.defineProperty(navigator, 'permissions', {
                get: () => ({
                    query: async (parameters) => ({ state: 'granted' })
                })
            });
            """,
            
            # Override plugins
            """
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            """,
            
            # Override languages
            "Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});",
            
            # Override chrome property
            """
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            """
        ]
        
        for script in stealth_scripts:
            try:
                self.driver.execute_script(script)
            except:
                pass
    
    def human_like_behavior(self):
        """Simulate human-like browsing behavior"""
        # Random mouse movements
        try:
            actions = ActionChains(self.driver)
            
            # Random scrolling
            scroll_amount = random.randint(100, 500)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(0.5, 2.0))
            
            # Random mouse movement
            element = self.driver.find_element(By.TAG_NAME, "body")
            actions.move_to_element_with_offset(element, 
                                              random.randint(0, 200), 
                                              random.randint(0, 200)).perform()
            
            # Random delay
            time.sleep(random.uniform(1.0, 3.0))
            
        except Exception as e:
            print(f"Human behavior simulation error: {e}")
    
    def capture_network_traffic(self):
        """Capture network requests to find API endpoints"""
        try:
            logs = self.driver.get_log('performance')
            api_calls = []
            
            for log in logs:
                message = json.loads(log['message'])
                if message['message']['method'] == 'Network.responseReceived':
                    url = message['message']['params']['response']['url']
                    if 'api' in url.lower() or 'gallery' in url.lower() or 'card' in url.lower():
                        api_calls.append({
                            'url': url,
                            'timestamp': log['timestamp'],
                            'status': message['message']['params']['response']['status']
                        })
            
            # Save API calls
            with open(self.output_dir / 'network_logs' / 'api_calls.json', 'w') as f:
                json.dump(api_calls, f, indent=2)
            
            return api_calls
            
        except Exception as e:
            print(f"Network capture error: {e}")
            return []
    
    def bypass_cloudflare(self):
        """Attempt to bypass Cloudflare protection"""
        try:
            # Wait for potential Cloudflare check
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Check for Cloudflare challenge
            cf_indicators = [
                "Checking your browser",
                "cloudflare",
                "cf-browser-verification",
                "DDoS protection"
            ]
            
            page_source = self.driver.page_source.lower()
            for indicator in cf_indicators:
                if indicator.lower() in page_source:
                    print(f"🛡️ Cloudflare challenge detected: {indicator}")
                    
                    # Wait longer for challenge to complete
                    time.sleep(random.uniform(5, 10))
                    
                    # Try to wait for challenge completion
                    WebDriverWait(self.driver, 30).until(
                        lambda driver: indicator.lower() not in driver.page_source.lower()
                    )
                    
                    print("✅ Cloudflare challenge potentially bypassed")
                    return True
            
            return True
            
        except TimeoutException:
            print("⚠️ Cloudflare challenge timeout")
            return False
        except Exception as e:
            print(f"❌ Cloudflare bypass error: {e}")
            return False
    
    def extract_card_data(self):
        """Extract Pokemon card data from the galleries"""
        cards_found = []
        
        try:
            # Wait for page to load completely
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Try multiple selectors for card containers
            card_selectors = [
                '.gallery-item',
                '.card-item', 
                '.pokemon-card',
                '.tcg-card',
                '[class*="card"]',
                '[class*="gallery"]',
                'img[src*="card"]',
                'img[src*="pokemon"]'
            ]
            
            for selector in card_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    print(f"Found {len(elements)} elements with selector: {selector}")
                    
                    for i, element in enumerate(elements[:10]):  # Limit to first 10
                        try:
                            # Extract card information
                            card_data = {
                                'selector': selector,
                                'index': i,
                                'element_tag': element.tag_name,
                                'element_text': element.text[:100] if element.text else '',
                                'src': element.get_attribute('src') if element.tag_name == 'img' else '',
                                'alt': element.get_attribute('alt') if element.tag_name == 'img' else '',
                                'class': element.get_attribute('class'),
                                'id': element.get_attribute('id')
                            }
                            
                            cards_found.append(card_data)
                            
                            # Try to screenshot the element
                            try:
                                element.screenshot(str(self.output_dir / 'card_images' / f'card_{selector.replace(".", "")}_{i}.png'))
                            except:
                                pass
                                
                        except Exception as e:
                            print(f"Error extracting card {i}: {e}")
                            
                except NoSuchElementException:
                    continue
                except Exception as e:
                    print(f"Error with selector {selector}: {e}")
            
            return cards_found
            
        except Exception as e:
            print(f"Card extraction error: {e}")
            return []
    
    def save_page_source(self):
        """Save complete page source for analysis"""
        try:
            html_content = self.driver.page_source
            
            # Save raw HTML
            with open(self.output_dir / 'raw_html' / 'tcg_galleries_full.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Save page info
            page_info = {
                'url': self.driver.current_url,
                'title': self.driver.title,
                'timestamp': datetime.now().isoformat(),
                'html_length': len(html_content),
                'contains_cards': 'card' in html_content.lower(),
                'contains_gallery': 'gallery' in html_content.lower(),
                'contains_pokemon': 'pokemon' in html_content.lower()
            }
            
            with open(self.output_dir / 'metadata' / 'page_analysis.json', 'w') as f:
                json.dump(page_info, f, indent=2)
            
            return page_info
            
        except Exception as e:
            print(f"Page source save error: {e}")
            return {}
    
    async def run_advanced_scrape(self):
        """Execute the advanced scraping operation"""
        results = {
            'success': False,
            'cards_found': 0,
            'files_captured': 0,
            'errors': [],
            'bypass_attempts': []
        }
        
        try:
            print("🚀 Starting advanced TCG scraping operation...")
            
            # Setup undetected Chrome
            if not self.setup_undetected_chrome():
                results['errors'].append("Failed to setup undetected Chrome")
                return results
            
            # Navigate to target URL
            print(f"🌐 Navigating to: {self.target_url}")
            self.driver.get(self.target_url)
            
            # Initial screenshot
            self.driver.save_screenshot(str(self.output_dir / 'screenshots' / 'initial_load.png'))
            
            # Attempt Cloudflare bypass
            bypass_success = self.bypass_cloudflare()
            results['bypass_attempts'].append({
                'method': 'cloudflare_bypass',
                'success': bypass_success,
                'timestamp': datetime.now().isoformat()
            })
            
            # Simulate human behavior
            self.human_like_behavior()
            
            # Capture network traffic
            api_calls = self.capture_network_traffic()
            results['api_calls_found'] = len(api_calls)
            
            # Take post-bypass screenshot
            self.driver.save_screenshot(str(self.output_dir / 'screenshots' / 'post_bypass.png'))
            
            # Save page source
            page_info = self.save_page_source()
            
            # Extract card data
            cards_found = self.extract_card_data()
            results['cards_found'] = len(cards_found)
            
            # Save results
            with open(self.output_dir / 'json_data' / 'extraction_results.json', 'w') as f:
                json.dump({
                    'cards_found': cards_found,
                    'page_info': page_info,
                    'api_calls': api_calls,
                    'results': results
                }, f, indent=2)
            
            results['success'] = len(cards_found) > 0 or len(api_calls) > 0
            results['files_captured'] = len(list(self.output_dir.rglob('*.*')))
            
            print(f"✅ Scraping completed. Found {len(cards_found)} cards, {len(api_calls)} API calls")
            
        except Exception as e:
            error_msg = f"Advanced scraping error: {e}"
            print(f"❌ {error_msg}")
            results['errors'].append(error_msg)
        
        finally:
            if self.driver:
                self.driver.quit()
        
        return results

def main():
    """Main execution function"""
    scraper = AdvancedTCGScraper()
    
    # Run the advanced scraping operation
    results = asyncio.run(scraper.run_advanced_scrape())
    
    # Display results
    print("\n" + "="*60)
    print("🎯 ADVANCED TCG SCRAPING RESULTS")
    print("="*60)
    print(f"Success: {results.get('success', False)}")
    print(f"Cards Found: {results.get('cards_found', 0)}")
    print(f"Files Captured: {results.get('files_captured', 0)}")
    print(f"API Calls Discovered: {results.get('api_calls_found', 0)}")
    print(f"Errors: {len(results.get('errors', []))}")
    
    if results.get('errors'):
        print("\nErrors encountered:")
        for error in results['errors']:
            print(f"  • {error}")
    
    return results.get('success', False)

if __name__ == "__main__":
    main() 