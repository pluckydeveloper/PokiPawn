#!/usr/bin/env python3
"""
Pokemon TCG Animation Focused Scraper
====================================
Specialized scraper for tcg.pokemon.com/en-us/all-galleries/
Captures card opening animations, hover effects, and all interactive elements.
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
import subprocess
import base64

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

class TCGAnimationFocusedScraper:
    """Specialized scraper for Pokemon TCG card animations and interactions"""
    
    def __init__(self, output_dir="tcg_animations_comprehensive"):
        self.output_dir = Path(output_dir)
        self.base_url = "https://tcg.pokemon.com"
        self.target_url = "https://tcg.pokemon.com/en-us/all-galleries/"
        self.session = requests.Session()
        
        # Stats tracking
        self.stats = {
            'cards_found': 0,
            'animations_captured': 0,
            'hover_effects_recorded': 0,
            'click_interactions_recorded': 0,
            'videos_recorded': 0,
            'screenshots_taken': 0,
            'css_animations_extracted': 0,
            'javascript_interactions_found': 0,
            'total_files_created': 0,
            'errors': 0
        }
        
        # Animation capture settings
        self.animation_settings = {
            'hover_delay': 2.0,
            'click_delay': 3.0,
            'animation_wait': 4.0,
            'screenshot_quality': 90,
            'video_duration': 10.0
        }
        
        self.create_directory_structure()
        
    def create_directory_structure(self):
        """Create comprehensive directory structure for TCG animations"""
        subdirs = [
            'card_animations', 'hover_effects', 'click_interactions',
            'opening_animations', 'transition_effects', 'screenshots',
            'videos', 'css_animations', 'javascript_code', 'audio',
            'card_images', 'thumbnails', 'metadata', 'reference'
        ]
        
        for subdir in subdirs:
            (self.output_dir / subdir).mkdir(parents=True, exist_ok=True)
            
        print(f"📁 TCG Animation directory structure created: {self.output_dir}")
    
    def setup_selenium_driver(self, headless=False):
        """Setup enhanced Selenium WebDriver for animation capture"""
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument('--headless')
        
        # Enhanced options for animation capture
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--force-device-scale-factor=1')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        
        # Enable media capture
        chrome_options.add_argument('--use-fake-ui-for-media-stream')
        chrome_options.add_argument('--disable-extensions-except')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Performance options
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Execute script to avoid detection and enable animations
        driver.execute_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            
            // Enable CSS animations
            const style = document.createElement('style');
            style.textContent = `
                *, *::before, *::after {
                    animation-duration: unset !important;
                    animation-delay: unset !important;
                    transition-duration: unset !important;
                    transition-delay: unset !important;
                }
            `;
            document.head.appendChild(style);
        """)
        
        return driver
    
    def scrape_tcg_galleries_comprehensive(self) -> Dict:
        """Comprehensive scraping of TCG galleries with animation capture"""
        print("🎬 Starting Pokemon TCG Galleries comprehensive scraping...")
        
        driver = None
        animation_data = {
            'galleries_found': [],
            'cards_analyzed': [],
            'animations_captured': [],
            'interactions_recorded': [],
            'css_animations': [],
            'javascript_interactions': []
        }
        
        try:
            # Setup driver for animation capture
            driver = self.setup_selenium_driver(headless=False)  # Use GUI for better animation capture
            
            print(f"🌐 Loading TCG galleries: {self.target_url}")
            driver.get(self.target_url)
            
            # Wait for page to fully load
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Let dynamic content and animations load
            time.sleep(10)
            
            # Take initial page screenshot
            initial_screenshot = self.output_dir / 'screenshots' / 'tcg_galleries_initial.png'
            driver.save_screenshot(str(initial_screenshot))
            self.stats['screenshots_taken'] += 1
            
            # Analyze page structure for galleries
            galleries = self.find_tcg_galleries(driver)
            animation_data['galleries_found'] = galleries
            
            # Capture gallery animations
            for i, gallery in enumerate(galleries[:5]):  # Limit to first 5 galleries
                print(f"🎭 Processing gallery {i+1}: {gallery.get('title', 'Unknown')}")
                gallery_animations = self.capture_gallery_animations(driver, gallery, i)
                animation_data['animations_captured'].extend(gallery_animations)
            
            # Find and analyze individual cards
            cards = self.find_individual_cards(driver)
            animation_data['cards_analyzed'] = cards
            
            # Capture card interactions for each card
            for i, card in enumerate(cards[:10]):  # Limit to first 10 cards
                print(f"🃏 Capturing animations for card {i+1}")
                card_animations = self.capture_card_animations(driver, card, i)
                animation_data['animations_captured'].extend(card_animations)
            
            # Extract CSS animations
            css_animations = self.extract_css_animations(driver)
            animation_data['css_animations'] = css_animations
            
            # Extract JavaScript interactions
            js_interactions = self.extract_javascript_interactions(driver)
            animation_data['javascript_interactions'] = js_interactions
            
            # Capture page interaction flows
            interaction_flows = self.capture_interaction_flows(driver)
            animation_data['interactions_recorded'] = interaction_flows
            
            print("✅ TCG galleries scraping completed successfully!")
            
        except Exception as e:
            print(f"❌ TCG galleries scraping failed: {e}")
            self.stats['errors'] += 1
            
        finally:
            if driver:
                driver.quit()
        
        # Save comprehensive animation data
        self.save_animation_data(animation_data)
        
        return animation_data
    
    def find_tcg_galleries(self, driver) -> List[Dict]:
        """Find all TCG galleries on the page"""
        print("🔍 Finding TCG galleries...")
        
        galleries = []
        
        try:
            # Look for gallery containers with various selectors
            gallery_selectors = [
                '.gallery-container',
                '.gallery-item',
                '.card-gallery',
                '.tcg-gallery',
                '[class*="gallery"]',
                '.slider-item',
                '.carousel-item'
            ]
            
            found_galleries = []
            for selector in gallery_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    found_galleries.extend(elements)
                except:
                    continue
            
            print(f"📊 Found {len(found_galleries)} potential gallery elements")
            
            for i, gallery_element in enumerate(found_galleries):
                try:
                    gallery_data = {
                        'index': i,
                        'element_id': gallery_element.get_attribute('id'),
                        'element_class': gallery_element.get_attribute('class'),
                        'title': '',
                        'description': '',
                        'card_count': 0,
                        'has_animation': False
                    }
                    
                    # Extract title
                    try:
                        title_element = gallery_element.find_element(By.CSS_SELECTOR, 'h1, h2, h3, h4, .title, .gallery-title')
                        gallery_data['title'] = title_element.text.strip()
                    except:
                        pass
                    
                    # Extract description
                    try:
                        desc_element = gallery_element.find_element(By.CSS_SELECTOR, 'p, .description, .gallery-description')
                        gallery_data['description'] = desc_element.text.strip()
                    except:
                        pass
                    
                    # Count cards in gallery
                    try:
                        cards_in_gallery = gallery_element.find_elements(By.CSS_SELECTOR, '.card, .pokemon-card, img')
                        gallery_data['card_count'] = len(cards_in_gallery)
                    except:
                        pass
                    
                    # Check for animations
                    gallery_data['has_animation'] = self.check_element_for_animations(gallery_element)
                    
                    galleries.append(gallery_data)
                    
                except Exception as e:
                    print(f"⚠️ Error analyzing gallery {i}: {e}")
                    continue
            
            self.stats['cards_found'] = len(galleries)
            
        except Exception as e:
            print(f"❌ Error finding galleries: {e}")
        
        return galleries
    
    def find_individual_cards(self, driver) -> List[Dict]:
        """Find individual Pokemon cards on the page"""
        print("🃏 Finding individual Pokemon cards...")
        
        cards = []
        
        try:
            # Scroll to load all cards
            self.scroll_page_gradually(driver)
            
            # Look for card elements with various selectors
            card_selectors = [
                '.pokemon-card',
                '.card',
                '.tcg-card',
                '.card-item',
                '[class*="card"]',
                'img[alt*="card" i]',
                'img[src*="card" i]'
            ]
            
            found_cards = []
            for selector in card_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    found_cards.extend(elements)
                except:
                    continue
            
            # Remove duplicates
            unique_cards = []
            seen_elements = set()
            
            for card in found_cards:
                element_id = id(card)
                if element_id not in seen_elements:
                    unique_cards.append(card)
                    seen_elements.add(element_id)
            
            print(f"🃏 Found {len(unique_cards)} unique card elements")
            
            for i, card_element in enumerate(unique_cards):
                try:
                    card_data = {
                        'index': i,
                        'element_tag': card_element.tag_name,
                        'element_id': card_element.get_attribute('id'),
                        'element_class': card_element.get_attribute('class'),
                        'card_name': '',
                        'card_image_url': '',
                        'has_hover_effect': False,
                        'has_click_effect': False,
                        'has_animation': False,
                        'position': card_element.location
                    }
                    
                    # Extract card name
                    try:
                        if card_element.tag_name == 'img':
                            card_data['card_name'] = card_element.get_attribute('alt') or card_element.get_attribute('title')
                            card_data['card_image_url'] = card_element.get_attribute('src')
                        else:
                            # Look for image within element
                            img = card_element.find_element(By.TAG_NAME, 'img')
                            card_data['card_name'] = img.get_attribute('alt') or img.get_attribute('title')
                            card_data['card_image_url'] = img.get_attribute('src')
                    except:
                        pass
                    
                    # Check for animations and effects
                    card_data['has_animation'] = self.check_element_for_animations(card_element)
                    card_data['has_hover_effect'] = self.test_hover_effect(driver, card_element)
                    card_data['has_click_effect'] = self.test_click_effect(driver, card_element)
                    
                    cards.append(card_data)
                    
                except Exception as e:
                    print(f"⚠️ Error analyzing card {i}: {e}")
                    continue
            
        except Exception as e:
            print(f"❌ Error finding cards: {e}")
        
        return cards
    
    def capture_gallery_animations(self, driver, gallery: Dict, gallery_index: int) -> List[Dict]:
        """Capture animations for a specific gallery"""
        print(f"🎬 Capturing animations for gallery {gallery_index}")
        
        animations = []
        
        try:
            # Find the gallery element
            gallery_elements = driver.find_elements(By.CSS_SELECTOR, 
                f'#{gallery.get("element_id", "")}' if gallery.get("element_id") else 
                f'.{gallery.get("element_class", "").split()[0]}' if gallery.get("element_class") else 
                '[class*="gallery"]')
            
            if not gallery_elements:
                return animations
            
            gallery_element = gallery_elements[0]
            
            # Scroll gallery into view
            driver.execute_script("arguments[0].scrollIntoView(true);", gallery_element)
            time.sleep(2)
            
            # Capture initial state
            initial_screenshot = self.output_dir / 'card_animations' / f'gallery_{gallery_index}_initial.png'
            gallery_element.screenshot(str(initial_screenshot))
            
            # Test hover effects on gallery
            ActionChains(driver).move_to_element(gallery_element).perform()
            time.sleep(self.animation_settings['hover_delay'])
            
            hover_screenshot = self.output_dir / 'hover_effects' / f'gallery_{gallery_index}_hover.png'
            gallery_element.screenshot(str(hover_screenshot))
            
            # Test click interactions
            try:
                gallery_element.click()
                time.sleep(self.animation_settings['click_delay'])
                
                click_screenshot = self.output_dir / 'click_interactions' / f'gallery_{gallery_index}_click.png'
                gallery_element.screenshot(str(click_screenshot))
                
                animation_data = {
                    'type': 'gallery_animation',
                    'gallery_index': gallery_index,
                    'gallery_title': gallery.get('title', ''),
                    'initial_state': str(initial_screenshot),
                    'hover_state': str(hover_screenshot),
                    'click_state': str(click_screenshot),
                    'has_hover_effect': True,
                    'has_click_effect': True,
                    'captured_at': datetime.now().isoformat()
                }
                
                animations.append(animation_data)
                self.stats['animations_captured'] += 1
                
            except Exception as e:
                animation_data = {
                    'type': 'gallery_animation',
                    'gallery_index': gallery_index,
                    'gallery_title': gallery.get('title', ''),
                    'initial_state': str(initial_screenshot),
                    'hover_state': str(hover_screenshot),
                    'has_hover_effect': True,
                    'has_click_effect': False,
                    'click_error': str(e),
                    'captured_at': datetime.now().isoformat()
                }
                
                animations.append(animation_data)
            
        except Exception as e:
            print(f"❌ Error capturing gallery animation: {e}")
        
        return animations
    
    def capture_card_animations(self, driver, card: Dict, card_index: int) -> List[Dict]:
        """Capture comprehensive animations for a specific card"""
        print(f"🃏 Capturing animations for card {card_index}: {card.get('card_name', 'Unknown')}")
        
        animations = []
        
        try:
            # Find the card element
            card_elements = driver.find_elements(By.CSS_SELECTOR, 
                f'#{card.get("element_id", "")}' if card.get("element_id") else 
                f'.{card.get("element_class", "").split()[0]}' if card.get("element_class") else 
                'img, .card')
            
            if not card_elements:
                return animations
            
            card_element = card_elements[card_index] if card_index < len(card_elements) else card_elements[0]
            
            # Scroll card into view
            driver.execute_script("arguments[0].scrollIntoView(true);", card_element)
            time.sleep(1)
            
            # Capture card opening animation sequence
            animation_sequence = self.capture_card_opening_sequence(driver, card_element, card_index)
            animations.extend(animation_sequence)
            
            # Capture hover effects
            hover_animation = self.capture_hover_animation(driver, card_element, card_index)
            if hover_animation:
                animations.append(hover_animation)
            
            # Capture click/flip animation
            click_animation = self.capture_click_animation(driver, card_element, card_index)
            if click_animation:
                animations.append(click_animation)
            
            # Test for continuous animations (like rotating cards)
            continuous_animation = self.capture_continuous_animation(driver, card_element, card_index)
            if continuous_animation:
                animations.append(continuous_animation)
            
        except Exception as e:
            print(f"❌ Error capturing card animations: {e}")
        
        return animations
    
    def capture_card_opening_sequence(self, driver, card_element, card_index: int) -> List[Dict]:
        """Capture the card opening animation sequence"""
        print(f"📦 Capturing card opening sequence for card {card_index}")
        
        sequence = []
        
        try:
            # Take screenshots at different intervals to capture opening animation
            intervals = [0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0]
            
            for i, interval in enumerate(intervals):
                time.sleep(interval)
                
                screenshot_path = self.output_dir / 'opening_animations' / f'card_{card_index}_opening_{i}.png'
                card_element.screenshot(str(screenshot_path))
                
                sequence_data = {
                    'type': 'card_opening_sequence',
                    'card_index': card_index,
                    'sequence_step': i,
                    'time_offset': interval,
                    'screenshot': str(screenshot_path),
                    'captured_at': datetime.now().isoformat()
                }
                
                sequence.append(sequence_data)
                self.stats['screenshots_taken'] += 1
            
        except Exception as e:
            print(f"❌ Error capturing opening sequence: {e}")
        
        return sequence
    
    def capture_hover_animation(self, driver, card_element, card_index: int) -> Optional[Dict]:
        """Capture hover animation for a card"""
        try:
            # Capture before hover
            before_hover = self.output_dir / 'hover_effects' / f'card_{card_index}_before_hover.png'
            card_element.screenshot(str(before_hover))
            
            # Move to element and capture during hover
            ActionChains(driver).move_to_element(card_element).perform()
            time.sleep(self.animation_settings['hover_delay'])
            
            during_hover = self.output_dir / 'hover_effects' / f'card_{card_index}_during_hover.png'
            card_element.screenshot(str(during_hover))
            
            # Move away and capture after hover
            ActionChains(driver).move_by_offset(100, 100).perform()
            time.sleep(1)
            
            after_hover = self.output_dir / 'hover_effects' / f'card_{card_index}_after_hover.png'
            card_element.screenshot(str(after_hover))
            
            self.stats['hover_effects_recorded'] += 1
            self.stats['screenshots_taken'] += 3
            
            return {
                'type': 'hover_animation',
                'card_index': card_index,
                'before_hover': str(before_hover),
                'during_hover': str(during_hover),
                'after_hover': str(after_hover),
                'captured_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error capturing hover animation: {e}")
            return None
    
    def capture_click_animation(self, driver, card_element, card_index: int) -> Optional[Dict]:
        """Capture click/flip animation for a card"""
        try:
            # Capture before click
            before_click = self.output_dir / 'click_interactions' / f'card_{card_index}_before_click.png'
            card_element.screenshot(str(before_click))
            
            # Click and capture animation frames
            card_element.click()
            
            # Capture multiple frames during animation
            animation_frames = []
            for i in range(5):
                time.sleep(0.5)
                frame_path = self.output_dir / 'click_interactions' / f'card_{card_index}_click_frame_{i}.png'
                card_element.screenshot(str(frame_path))
                animation_frames.append(str(frame_path))
            
            self.stats['click_interactions_recorded'] += 1
            self.stats['screenshots_taken'] += 6
            
            return {
                'type': 'click_animation',
                'card_index': card_index,
                'before_click': str(before_click),
                'animation_frames': animation_frames,
                'captured_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error capturing click animation: {e}")
            return None
    
    def capture_continuous_animation(self, driver, card_element, card_index: int) -> Optional[Dict]:
        """Capture continuous animations like rotating cards"""
        try:
            print(f"🔄 Capturing continuous animation for card {card_index}")
            
            # Record frames over time to capture continuous animation
            frames = []
            duration = 6  # seconds
            frame_interval = 0.3  # seconds
            
            for i in range(int(duration / frame_interval)):
                frame_path = self.output_dir / 'transition_effects' / f'card_{card_index}_continuous_{i}.png'
                card_element.screenshot(str(frame_path))
                frames.append(str(frame_path))
                time.sleep(frame_interval)
            
            self.stats['screenshots_taken'] += len(frames)
            
            return {
                'type': 'continuous_animation',
                'card_index': card_index,
                'animation_frames': frames,
                'duration_seconds': duration,
                'frame_interval': frame_interval,
                'captured_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error capturing continuous animation: {e}")
            return None
    
    def extract_css_animations(self, driver) -> List[Dict]:
        """Extract CSS animation definitions from the page"""
        print("🎨 Extracting CSS animations...")
        
        css_animations = []
        
        try:
            # Get all stylesheets
            stylesheets = driver.execute_script("""
                const sheets = [];
                for (let i = 0; i < document.styleSheets.length; i++) {
                    try {
                        const sheet = document.styleSheets[i];
                        const rules = sheet.cssRules || sheet.rules;
                        for (let j = 0; j < rules.length; j++) {
                            const rule = rules[j];
                            if (rule.cssText.includes('@keyframes') || 
                                rule.cssText.includes('animation') || 
                                rule.cssText.includes('transition')) {
                                sheets.push({
                                    index: i,
                                    ruleIndex: j,
                                    cssText: rule.cssText,
                                    selectorText: rule.selectorText || '',
                                    href: sheet.href || 'inline'
                                });
                            }
                        }
                    } catch (e) {
                        // Cross-origin or other access issues
                    }
                }
                return sheets;
            """)
            
            for animation in stylesheets:
                css_animations.append(animation)
            
            # Save CSS animations
            css_file = self.output_dir / 'css_animations' / 'extracted_animations.json'
            with open(css_file, 'w', encoding='utf-8') as f:
                json.dump(css_animations, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Extracted {len(css_animations)} CSS animation rules")
            self.stats['css_animations_extracted'] = len(css_animations)
            
        except Exception as e:
            print(f"❌ Error extracting CSS animations: {e}")
        
        return css_animations
    
    def extract_javascript_interactions(self, driver) -> List[Dict]:
        """Extract JavaScript interaction code"""
        print("📜 Extracting JavaScript interactions...")
        
        js_interactions = []
        
        try:
            # Get event listeners
            event_listeners = driver.execute_script("""
                const listeners = [];
                const elements = document.querySelectorAll('*');
                
                elements.forEach((el, index) => {
                    const events = ['click', 'hover', 'mouseover', 'mouseenter', 'mouseout'];
                    
                    events.forEach(eventType => {
                        if (el['on' + eventType]) {
                            listeners.push({
                                elementIndex: index,
                                eventType: eventType,
                                hasListener: true,
                                tagName: el.tagName,
                                className: el.className,
                                id: el.id
                            });
                        }
                    });
                });
                
                return listeners;
            """)
            
            js_interactions.extend(event_listeners)
            
            # Save JavaScript interactions
            js_file = self.output_dir / 'javascript_code' / 'extracted_interactions.json'
            with open(js_file, 'w', encoding='utf-8') as f:
                json.dump(js_interactions, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Extracted {len(js_interactions)} JavaScript interactions")
            self.stats['javascript_interactions_found'] = len(js_interactions)
            
        except Exception as e:
            print(f"❌ Error extracting JavaScript interactions: {e}")
        
        return js_interactions
    
    def capture_interaction_flows(self, driver) -> List[Dict]:
        """Capture complete interaction flows on the page"""
        print("🔄 Capturing interaction flows...")
        
        flows = []
        
        try:
            # Test navigation through galleries
            navigation_flow = self.test_navigation_flow(driver)
            if navigation_flow:
                flows.append(navigation_flow)
            
            # Test card browsing flow
            browsing_flow = self.test_card_browsing_flow(driver)
            if browsing_flow:
                flows.append(browsing_flow)
            
            # Test filter/search interactions
            filter_flow = self.test_filter_interactions(driver)
            if filter_flow:
                flows.append(filter_flow)
            
        except Exception as e:
            print(f"❌ Error capturing interaction flows: {e}")
        
        return flows
    
    def test_navigation_flow(self, driver) -> Optional[Dict]:
        """Test navigation flow through the site"""
        try:
            # Look for navigation elements
            nav_elements = driver.find_elements(By.CSS_SELECTOR, 'nav, .navigation, .menu, .nav')
            
            if nav_elements:
                nav_screenshots = []
                
                for i, nav in enumerate(nav_elements[:3]):
                    screenshot_path = self.output_dir / 'interactions' / f'navigation_{i}.png'
                    nav.screenshot(str(screenshot_path))
                    nav_screenshots.append(str(screenshot_path))
                
                return {
                    'type': 'navigation_flow',
                    'navigation_elements_found': len(nav_elements),
                    'screenshots': nav_screenshots,
                    'captured_at': datetime.now().isoformat()
                }
        except:
            pass
        
        return None
    
    def test_card_browsing_flow(self, driver) -> Optional[Dict]:
        """Test card browsing interaction flow"""
        try:
            # Look for browse/pagination elements
            browse_elements = driver.find_elements(By.CSS_SELECTOR, 
                '.pagination, .browse, .next, .prev, .page, [class*="page"]')
            
            if browse_elements:
                browse_screenshots = []
                
                for i, elem in enumerate(browse_elements[:5]):
                    try:
                        elem.click()
                        time.sleep(2)
                        
                        screenshot_path = self.output_dir / 'interactions' / f'browse_flow_{i}.png'
                        driver.save_screenshot(str(screenshot_path))
                        browse_screenshots.append(str(screenshot_path))
                        
                    except:
                        continue
                
                return {
                    'type': 'browsing_flow',
                    'browse_elements_found': len(browse_elements),
                    'screenshots': browse_screenshots,
                    'captured_at': datetime.now().isoformat()
                }
        except:
            pass
        
        return None
    
    def test_filter_interactions(self, driver) -> Optional[Dict]:
        """Test filter/search interactions"""
        try:
            # Look for filter elements
            filter_elements = driver.find_elements(By.CSS_SELECTOR, 
                '.filter, .search, input[type="search"], select, .dropdown')
            
            if filter_elements:
                filter_screenshots = []
                
                for i, elem in enumerate(filter_elements[:3]):
                    try:
                        # Take screenshot before interaction
                        before_path = self.output_dir / 'interactions' / f'filter_{i}_before.png'
                        driver.save_screenshot(str(before_path))
                        
                        # Interact with filter
                        if elem.tag_name == 'select':
                            # For select elements, try to select an option
                            from selenium.webdriver.support.ui import Select
                            select = Select(elem)
                            if len(select.options) > 1:
                                select.select_by_index(1)
                        else:
                            elem.click()
                        
                        time.sleep(2)
                        
                        # Take screenshot after interaction
                        after_path = self.output_dir / 'interactions' / f'filter_{i}_after.png'
                        driver.save_screenshot(str(after_path))
                        
                        filter_screenshots.extend([str(before_path), str(after_path)])
                        
                    except:
                        continue
                
                return {
                    'type': 'filter_flow',
                    'filter_elements_found': len(filter_elements),
                    'screenshots': filter_screenshots,
                    'captured_at': datetime.now().isoformat()
                }
        except:
            pass
        
        return None
    
    def check_element_for_animations(self, element) -> bool:
        """Check if an element has CSS animations or transitions"""
        try:
            # Check computed styles for animations
            has_animation = element.parent.execute_script("""
                const el = arguments[0];
                const styles = window.getComputedStyle(el);
                
                return (
                    styles.animationName !== 'none' ||
                    styles.transitionProperty !== 'none' ||
                    styles.transform !== 'none' ||
                    el.style.animation !== '' ||
                    el.style.transition !== ''
                );
            """, element)
            
            return has_animation
        except:
            return False
    
    def test_hover_effect(self, driver, element) -> bool:
        """Test if element has hover effects"""
        try:
            # Get initial styles
            initial_style = element.get_attribute('style')
            
            # Hover over element
            ActionChains(driver).move_to_element(element).perform()
            time.sleep(0.5)
            
            # Get styles after hover
            hover_style = element.get_attribute('style')
            
            # Move away
            ActionChains(driver).move_by_offset(50, 50).perform()
            
            return initial_style != hover_style
        except:
            return False
    
    def test_click_effect(self, driver, element) -> bool:
        """Test if element has click effects"""
        try:
            # Get initial state
            initial_location = element.location
            
            # Click element
            element.click()
            time.sleep(1)
            
            # Check if anything changed
            new_location = element.location
            
            return initial_location != new_location
        except:
            return False
    
    def scroll_page_gradually(self, driver):
        """Gradually scroll page to load content"""
        try:
            total_height = driver.execute_script("return document.body.scrollHeight")
            
            for i in range(0, total_height, 800):
                driver.execute_script(f"window.scrollTo(0, {i});")
                time.sleep(1)
            
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
        except:
            pass
    
    def save_animation_data(self, animation_data: Dict):
        """Save comprehensive animation data"""
        
        # Save main data file
        main_file = self.output_dir / 'metadata' / 'tcg_animation_data.json'
        with open(main_file, 'w', encoding='utf-8') as f:
            json.dump({
                'scraped_at': datetime.now().isoformat(),
                'stats': self.stats,
                'animation_settings': self.animation_settings,
                'data': animation_data
            }, f, indent=2, ensure_ascii=False)
        
        # Create summary report
        summary = {
            'operation_summary': {
                'total_galleries': len(animation_data.get('galleries_found', [])),
                'total_cards': len(animation_data.get('cards_analyzed', [])),
                'total_animations': len(animation_data.get('animations_captured', [])),
                'css_animations': len(animation_data.get('css_animations', [])),
                'js_interactions': len(animation_data.get('javascript_interactions', [])),
                'stats': self.stats
            }
        }
        
        summary_file = self.output_dir / 'reference' / 'TCG_ANIMATION_SUMMARY.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Animation data saved to: {main_file}")
        print(f"📊 Summary saved to: {summary_file}")
    
    def run_comprehensive_animation_scraping(self):
        """Run comprehensive TCG animation scraping"""
        print("\n" + "="*70)
        print("🎬 POKEMON TCG ANIMATION COMPREHENSIVE SCRAPING")
        print("="*70)
        
        start_time = datetime.now()
        
        # Run comprehensive scraping
        animation_data = self.scrape_tcg_galleries_comprehensive()
        
        # Generate final report
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\n" + "="*70)
        print("🏁 TCG ANIMATION SCRAPING COMPLETED")
        print("="*70)
        print(f"⏱️  Duration: {duration}")
        print(f"🎭 Galleries Found: {len(animation_data.get('galleries_found', []))}")
        print(f"🃏 Cards Analyzed: {len(animation_data.get('cards_analyzed', []))}")
        print(f"🎬 Animations Captured: {self.stats['animations_captured']}")
        print(f"🖱️  Hover Effects: {self.stats['hover_effects_recorded']}")
        print(f"👆 Click Interactions: {self.stats['click_interactions_recorded']}")
        print(f"📸 Screenshots Taken: {self.stats['screenshots_taken']}")
        print(f"🎨 CSS Animations: {self.stats['css_animations_extracted']}")
        print(f"📜 JS Interactions: {self.stats['javascript_interactions_found']}")
        print(f"❌ Errors: {self.stats['errors']}")
        print("="*70)
        
        return animation_data


def main():
    """Main execution function"""
    scraper = TCGAnimationFocusedScraper()
    scraper.run_comprehensive_animation_scraping()


if __name__ == "__main__":
    main() 