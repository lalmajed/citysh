#!/usr/bin/env python3
"""
Selenium-based scraper for Balady Urban Maps (umaps.balady.gov.sa)
Extracts Al-Mumayyidiyah district data: entries/exits, road widths, etc.
"""

import json
import time
import csv
import os
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

# District to search for
TARGET_DISTRICT = "المميزية"  # Al-Mumayyidiyah in Arabic
DISTRICT_EN = "Al-Mumayyidiyah"

def setup_driver():
    """Setup Chrome driver with headless options"""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--lang=ar")
    
    # Enable logging network requests
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    return driver

def capture_network_logs(driver):
    """Capture and analyze network requests"""
    logs = driver.get_log("performance")
    network_data = []
    
    for log in logs:
        try:
            message = json.loads(log["message"])["message"]
            if message["method"] == "Network.responseReceived":
                url = message["params"]["response"]["url"]
                if "arcgis" in url.lower() or "mapserver" in url.lower() or "query" in url.lower():
                    network_data.append({
                        "url": url,
                        "status": message["params"]["response"]["status"],
                        "type": message["params"]["type"]
                    })
        except:
            pass
    
    return network_data

def extract_arcgis_urls(driver):
    """Extract ArcGIS service URLs from the page"""
    urls = set()
    
    # Get all script content
    scripts = driver.find_elements(By.TAG_NAME, "script")
    for script in scripts:
        try:
            src = script.get_attribute("src") or ""
            content = script.get_attribute("innerHTML") or ""
            
            # Look for service URLs
            for text in [src, content]:
                if "momrah" in text or "arcgis" in text.lower() or "mapserver" in text.lower():
                    # Extract URLs
                    import re
                    found_urls = re.findall(r'https?://[^\s"\'\)]+(?:MapServer|FeatureServer)[^\s"\'\)]*', text)
                    urls.update(found_urls)
        except:
            pass
    
    return list(urls)

def search_district(driver, district_name):
    """Search for a district in the map"""
    print(f"\nSearching for district: {district_name}")
    
    try:
        # Wait for page to load
        time.sleep(5)
        
        # Look for search input
        search_selectors = [
            "input[placeholder*='بحث']",
            "input[placeholder*='Search']",
            "input.search-input",
            "input[type='search']",
            ".esri-search__input",
            "input[aria-label*='search']",
        ]
        
        search_input = None
        for selector in search_selectors:
            try:
                search_input = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                if search_input:
                    print(f"Found search input with selector: {selector}")
                    break
            except:
                continue
        
        if search_input:
            search_input.clear()
            search_input.send_keys(district_name)
            time.sleep(2)
            search_input.send_keys(Keys.RETURN)
            time.sleep(3)
            return True
        else:
            print("Could not find search input")
            
            # Try clicking on search icon first
            try:
                search_icon = driver.find_element(By.CSS_SELECTOR, ".esri-search, .search-icon, [class*='search']")
                search_icon.click()
                time.sleep(1)
            except:
                pass
                
    except Exception as e:
        print(f"Search error: {e}")
    
    return False

def extract_layer_info(driver):
    """Extract information about available layers"""
    print("\nExtracting layer information...")
    
    layers = []
    
    try:
        # Look for layer panel/list
        layer_elements = driver.find_elements(By.CSS_SELECTOR, "[class*='layer'], [class*='Layer']")
        for elem in layer_elements:
            try:
                text = elem.text.strip()
                if text and len(text) < 200:
                    layers.append(text)
            except:
                pass
    except Exception as e:
        print(f"Layer extraction error: {e}")
    
    return layers

def get_page_data(driver):
    """Extract all relevant data from the page"""
    data = {
        "timestamp": datetime.now().isoformat(),
        "district": TARGET_DISTRICT,
        "urls": [],
        "layers": [],
        "network_requests": [],
        "page_content": ""
    }
    
    # Get ArcGIS URLs
    data["urls"] = extract_arcgis_urls(driver)
    
    # Get layer info
    data["layers"] = extract_layer_info(driver)
    
    # Get network logs
    data["network_requests"] = capture_network_logs(driver)
    
    # Get page source excerpt
    data["page_content"] = driver.page_source[:5000]
    
    return data

def intercept_api_calls(driver):
    """Intercept and log API calls made by the map"""
    print("\nIntercepting API calls...")
    
    # Execute JavaScript to capture XHR/Fetch calls
    js_code = """
    window._capturedRequests = window._capturedRequests || [];
    
    // Override fetch
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        window._capturedRequests.push({type: 'fetch', url: args[0], time: new Date().toISOString()});
        return originalFetch.apply(this, args);
    };
    
    // Override XMLHttpRequest
    const originalXHR = window.XMLHttpRequest;
    window.XMLHttpRequest = function() {
        const xhr = new originalXHR();
        const originalOpen = xhr.open;
        xhr.open = function(method, url, ...rest) {
            window._capturedRequests.push({type: 'xhr', method: method, url: url, time: new Date().toISOString()});
            return originalOpen.apply(this, [method, url, ...rest]);
        };
        return xhr;
    };
    
    return 'Interceptors installed';
    """
    
    try:
        result = driver.execute_script(js_code)
        print(f"  {result}")
    except Exception as e:
        print(f"  Interceptor error: {e}")

def get_captured_requests(driver):
    """Get captured API requests"""
    try:
        requests = driver.execute_script("return window._capturedRequests || [];")
        return requests
    except:
        return []

def explore_map_controls(driver):
    """Explore and interact with map controls"""
    print("\nExploring map controls...")
    
    findings = []
    
    # Look for common ESRI/ArcGIS UI elements
    selectors_to_try = [
        (".esri-layer-list", "Layer List"),
        (".esri-legend", "Legend"),
        (".esri-print", "Print"),
        (".esri-basemap-gallery", "Basemap Gallery"),
        (".esri-widget", "ESRI Widget"),
        ("[class*='district']", "District Element"),
        ("[class*='layer']", "Layer Element"),
        ("[class*='road']", "Road Element"),
        ("[class*='street']", "Street Element"),
    ]
    
    for selector, name in selectors_to_try:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                findings.append(f"Found {len(elements)} '{name}' elements")
                for elem in elements[:3]:
                    text = elem.text[:100] if elem.text else "(no text)"
                    findings.append(f"  - {text}")
        except:
            pass
    
    return findings

def main():
    print("=" * 70)
    print("Balady Urban Maps Scraper")
    print(f"Target District: {DISTRICT_EN} ({TARGET_DISTRICT})")
    print("=" * 70)
    
    driver = None
    
    try:
        print("\n[1] Setting up Chrome driver...")
        driver = setup_driver()
        
        print("\n[2] Loading Balady Urban Maps...")
        driver.get("https://umaps.balady.gov.sa/")
        
        # Wait for initial load
        time.sleep(10)
        
        print(f"\n[3] Page title: {driver.title}")
        print(f"    Current URL: {driver.current_url}")
        
        # Install interceptors
        intercept_api_calls(driver)
        
        print("\n[4] Waiting for map to initialize...")
        time.sleep(5)
        
        # Get captured requests
        requests = get_captured_requests(driver)
        print(f"\n[5] Captured {len(requests)} API requests:")
        
        arcgis_requests = [r for r in requests if 'arcgis' in str(r.get('url', '')).lower() or 'mapserver' in str(r.get('url', '')).lower()]
        for req in arcgis_requests[:20]:
            print(f"    - {req.get('url', '')[:100]}")
        
        # Try to search for the district
        print("\n[6] Searching for district...")
        search_district(driver, TARGET_DISTRICT)
        
        time.sleep(5)
        
        # Get more requests after search
        new_requests = get_captured_requests(driver)
        print(f"\n[7] Total requests after search: {len(new_requests)}")
        
        # Explore map controls
        print("\n[8] Exploring map controls...")
        controls = explore_map_controls(driver)
        for ctrl in controls:
            print(f"    {ctrl}")
        
        # Extract data
        print("\n[9] Extracting page data...")
        data = get_page_data(driver)
        
        # Save results
        output_file = "/workspace/balady_scrape_results.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "district": DISTRICT_EN,
                "district_ar": TARGET_DISTRICT,
                "timestamp": data["timestamp"],
                "arcgis_urls": data["urls"],
                "layers_found": data["layers"],
                "api_requests": [r for r in new_requests if 'mapserver' in str(r.get('url', '')).lower()],
                "controls_found": controls
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n[10] Results saved to: {output_file}")
        
        # Save screenshot
        screenshot_file = "/workspace/balady_screenshot.png"
        driver.save_screenshot(screenshot_file)
        print(f"     Screenshot saved to: {screenshot_file}")
        
        # Print summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"ArcGIS URLs found: {len(data['urls'])}")
        for url in data['urls'][:5]:
            print(f"  - {url[:80]}...")
        
        print(f"\nAPI requests captured: {len(new_requests)}")
        mapserver_reqs = [r for r in new_requests if 'mapserver' in str(r.get('url', '')).lower()]
        print(f"MapServer requests: {len(mapserver_reqs)}")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if driver:
            driver.quit()
            print("\n[Done] Browser closed")

if __name__ == "__main__":
    main()
