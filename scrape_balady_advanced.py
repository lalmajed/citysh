#!/usr/bin/env python3
"""
Advanced Balady Urban Maps Scraper
Uses Chrome DevTools Protocol to capture all network requests
"""

import json
import time
import re
import csv
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from webdriver_manager.chrome import ChromeDriverManager

# District info
TARGET_DISTRICT = "المميزية"  # Al-Mumayyidiyah in Arabic
DISTRICT_EN = "Al-Mumayyidiyah"

class BaladyScraper:
    def __init__(self):
        self.driver = None
        self.captured_responses = []
        self.arcgis_data = {}
        
    def setup_driver(self):
        """Setup Chrome with network logging"""
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--lang=ar")
        
        # Enable performance logging
        options.set_capability("goog:loggingPrefs", {"performance": "ALL", "browser": "ALL"})
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        
        # Enable CDP for network interception
        self.driver.execute_cdp_cmd("Network.enable", {})
        
        return self.driver
    
    def process_network_logs(self):
        """Process performance logs to extract API responses"""
        logs = self.driver.get_log("performance")
        
        for log in logs:
            try:
                message = json.loads(log["message"])["message"]
                method = message.get("method", "")
                
                if method == "Network.responseReceived":
                    response = message["params"]["response"]
                    url = response.get("url", "")
                    
                    # Filter for ArcGIS/MapServer requests
                    if any(x in url.lower() for x in ["mapserver", "featureserver", "arcgis", "query", "identify"]):
                        self.captured_responses.append({
                            "url": url,
                            "status": response.get("status"),
                            "type": message["params"].get("type"),
                            "requestId": message["params"].get("requestId")
                        })
                        
            except Exception as e:
                pass
        
        return self.captured_responses
    
    def wait_for_map_load(self, timeout=30):
        """Wait for map to fully load"""
        print("Waiting for map to load...")
        
        # Wait for ESRI map container
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".esri-view-root, .esri-view, [class*='esri']"))
            )
            print("  Map container found")
        except:
            print("  Map container not found, continuing...")
        
        # Wait additional time for layers to load
        time.sleep(10)
        
        # Process any network logs
        self.process_network_logs()
        print(f"  Captured {len(self.captured_responses)} ArcGIS responses")
    
    def search_and_zoom(self, district_name):
        """Search for district and zoom to it"""
        print(f"\nSearching for: {district_name}")
        
        try:
            # Find search input
            search = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='بحث'], .esri-search__input"))
            )
            
            search.clear()
            time.sleep(0.5)
            search.send_keys(district_name)
            time.sleep(2)
            
            # Click search or press enter
            search.send_keys(Keys.RETURN)
            time.sleep(3)
            
            # Try to click on first result
            try:
                suggestion = self.driver.find_element(By.CSS_SELECTOR, ".esri-search__suggestions-list li, [class*='suggestion']")
                suggestion.click()
                time.sleep(3)
            except:
                pass
            
            print("  Search completed")
            
            # Process new network logs
            self.process_network_logs()
            
        except Exception as e:
            print(f"  Search error: {e}")
    
    def click_on_map_location(self):
        """Click on the center of the map to trigger identify"""
        print("\nClicking on map to get feature info...")
        
        try:
            # Find map element
            map_elem = self.driver.find_element(By.CSS_SELECTOR, ".esri-view-root, #viewDiv, [class*='map']")
            
            # Get map dimensions
            size = map_elem.size
            location = map_elem.location
            
            # Click center of map
            from selenium.webdriver.common.action_chains import ActionChains
            actions = ActionChains(self.driver)
            actions.move_to_element_with_offset(map_elem, size['width']//2, size['height']//2)
            actions.click()
            actions.perform()
            
            time.sleep(5)
            
            # Process network logs
            self.process_network_logs()
            print(f"  Now have {len(self.captured_responses)} responses")
            
        except Exception as e:
            print(f"  Map click error: {e}")
    
    def extract_popup_data(self):
        """Extract data from any popups/info windows"""
        print("\nExtracting popup data...")
        
        popup_data = []
        
        try:
            # Look for ESRI popup
            popups = self.driver.find_elements(By.CSS_SELECTOR, ".esri-popup, .esri-feature, [class*='popup'], [class*='info-window']")
            
            for popup in popups:
                text = popup.text
                if text:
                    popup_data.append(text)
                    print(f"  Found popup: {text[:100]}...")
                    
        except Exception as e:
            print(f"  Popup extraction error: {e}")
        
        return popup_data
    
    def extract_service_urls_from_page(self):
        """Extract all ArcGIS service URLs from page source"""
        print("\nExtracting service URLs from page...")
        
        urls = set()
        source = self.driver.page_source
        
        # Find all URLs containing MapServer or FeatureServer
        patterns = [
            r'https?://[^\s"\'<>]+(?:MapServer|FeatureServer)[^\s"\'<>]*',
            r'https?://[^\s"\'<>]+momrah[^\s"\'<>]*',
            r'https?://[^\s"\'<>]+balady[^\s"\'<>]+(?:proxy|arcgis)[^\s"\'<>]*'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, source)
            urls.update(matches)
        
        print(f"  Found {len(urls)} unique service URLs")
        return list(urls)
    
    def open_layers_panel(self):
        """Try to open layers panel to see available data"""
        print("\nOpening layers panel...")
        
        try:
            # Look for layer button/icon
            layer_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                "[class*='layer'], [aria-label*='layer'], [title*='layer'], "
                "[class*='طبقة'], [aria-label*='طبقات']"
            )
            
            for btn in layer_buttons[:3]:
                try:
                    btn.click()
                    time.sleep(2)
                    break
                except:
                    continue
                    
        except Exception as e:
            print(f"  Layers panel error: {e}")
    
    def get_all_visible_text(self):
        """Get all visible text on page for analysis"""
        try:
            body = self.driver.find_element(By.TAG_NAME, "body")
            return body.text
        except:
            return ""
    
    def run(self):
        """Main scraping workflow"""
        print("=" * 70)
        print("Balady Urban Maps Advanced Scraper")
        print(f"Target: {DISTRICT_EN} ({TARGET_DISTRICT})")
        print("=" * 70)
        
        results = {
            "district": DISTRICT_EN,
            "district_ar": TARGET_DISTRICT,
            "timestamp": datetime.now().isoformat(),
            "service_urls": [],
            "api_responses": [],
            "popup_data": [],
            "page_text": "",
            "entries_exits": [],
            "roads": []
        }
        
        try:
            print("\n[1] Setting up browser...")
            self.setup_driver()
            
            print("\n[2] Loading Balady Urban Maps...")
            self.driver.get("https://umaps.balady.gov.sa/")
            
            print("\n[3] Waiting for initial load...")
            self.wait_for_map_load()
            
            print("\n[4] Extracting initial service URLs...")
            results["service_urls"] = self.extract_service_urls_from_page()
            
            print("\n[5] Searching for district...")
            self.search_and_zoom(TARGET_DISTRICT)
            
            time.sleep(5)
            
            print("\n[6] Clicking on map...")
            self.click_on_map_location()
            
            print("\n[7] Opening layers panel...")
            self.open_layers_panel()
            time.sleep(3)
            
            print("\n[8] Processing all captured responses...")
            self.process_network_logs()
            results["api_responses"] = self.captured_responses
            
            print("\n[9] Extracting popup data...")
            results["popup_data"] = self.extract_popup_data()
            
            print("\n[10] Getting page text...")
            results["page_text"] = self.get_all_visible_text()[:5000]
            
            # Save screenshot
            self.driver.save_screenshot("/workspace/balady_advanced_screenshot.png")
            
            # Analyze captured responses for road data
            print("\n" + "=" * 70)
            print("ANALYSIS")
            print("=" * 70)
            
            print(f"\nTotal ArcGIS responses captured: {len(self.captured_responses)}")
            
            # Group by service type
            services = {}
            for resp in self.captured_responses:
                url = resp.get("url", "")
                # Extract service name
                match = re.search(r'/services/([^/]+/[^/]+)/', url)
                if match:
                    service_name = match.group(1)
                    if service_name not in services:
                        services[service_name] = []
                    services[service_name].append(url)
            
            print("\nServices accessed:")
            for service, urls in services.items():
                print(f"  {service}: {len(urls)} requests")
                for url in urls[:2]:
                    print(f"    - {url[:80]}...")
            
            # Look for specific data in responses
            road_keywords = ["street", "road", "شارع", "طريق", "width", "عرض", "entry", "exit", "مدخل", "مخرج"]
            
            print("\nLooking for road-related data...")
            for url in results["service_urls"]:
                url_lower = url.lower()
                for keyword in road_keywords:
                    if keyword in url_lower:
                        print(f"  Found: {url[:100]}...")
                        break
            
            # Save results
            output_file = "/workspace/balady_advanced_results.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            print(f"\nResults saved to: {output_file}")
            
            # Print service URLs for manual investigation
            print("\n" + "=" * 70)
            print("SERVICE URLs FOR MANUAL INVESTIGATION")
            print("=" * 70)
            for url in results["service_urls"][:10]:
                print(f"\n{url}")
            
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            if self.driver:
                self.driver.quit()
                print("\n[Done] Browser closed")
        
        return results

def main():
    scraper = BaladyScraper()
    scraper.run()

if __name__ == "__main__":
    main()
