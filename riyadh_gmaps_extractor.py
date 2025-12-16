#!/usr/bin/env python3
"""
Full Google Maps Business Extractor for Riyadh
Extracts: name, rating, address, phone, category, website, coordinates
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import pandas as pd
import json
import sys

def setup_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--lang=en')
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def extract_coords_from_url(url):
    """Extract lat/lng from Google Maps URL"""
    try:
        match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
        if match:
            return float(match.group(1)), float(match.group(2))
    except:
        pass
    return None, None

def search_and_extract(driver, query, max_results=50):
    """Search and extract businesses"""
    print(f"\n🔍 Searching: {query}")
    
    try:
        driver.get(f"https://www.google.com/maps/search/{query.replace(' ', '+')}?hl=en")
        time.sleep(5)
        
        # Scroll to load more
        for i in range(15):
            try:
                feed = driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", feed)
                time.sleep(1)
            except:
                break
        
        # Get place links
        links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/maps/place/"]')
        urls = list(set([l.get_attribute('href') for l in links if l.get_attribute('href')]))
        print(f"   Found {len(urls)} places")
        
        results = []
        for i, url in enumerate(urls[:max_results]):
            try:
                driver.get(url)
                time.sleep(2)
                
                info = {'search_query': query, 'url': url}
                
                # Extract coordinates from URL
                lat, lng = extract_coords_from_url(driver.current_url)
                info['latitude'] = lat
                info['longitude'] = lng
                
                # Name
                try:
                    info['name'] = driver.find_element(By.CSS_SELECTOR, 'h1').text
                except: info['name'] = ''
                
                # Rating
                try:
                    info['rating'] = driver.find_element(By.CSS_SELECTOR, 'div.F7nice span[aria-hidden="true"]').text
                except: info['rating'] = ''
                
                # Reviews count
                try:
                    reviews_text = driver.find_element(By.CSS_SELECTOR, 'span[aria-label*="review"]').get_attribute('aria-label')
                    info['reviews'] = re.search(r'[\d,]+', reviews_text).group().replace(',', '')
                except: info['reviews'] = ''
                
                # Address
                try:
                    info['address'] = driver.find_element(By.CSS_SELECTOR, 'button[data-item-id="address"] div.fontBodyMedium').text
                except: info['address'] = ''
                
                # Phone
                try:
                    info['phone'] = driver.find_element(By.CSS_SELECTOR, 'button[data-item-id*="phone"] div.fontBodyMedium').text
                except: info['phone'] = ''
                
                # Website
                try:
                    info['website'] = driver.find_element(By.CSS_SELECTOR, 'a[data-item-id="authority"]').get_attribute('href')
                except: info['website'] = ''
                
                # Category
                try:
                    info['category'] = driver.find_element(By.CSS_SELECTOR, 'button.DkEaL').text
                except: info['category'] = ''
                
                if info['name']:
                    results.append(info)
                    print(f"   [{i+1}/{min(len(urls), max_results)}] {info['name'][:35]}")
                
            except Exception as e:
                continue
            
            time.sleep(0.5)
        
        return results
        
    except Exception as e:
        print(f"   Error: {e}")
        return []

def main():
    print("=" * 60)
    print("🗺️  GOOGLE MAPS RIYADH BUSINESS EXTRACTOR")
    print("=" * 60)
    
    # Categories to extract
    searches = [
        "restaurants in Riyadh",
        "hotels in Riyadh",
        "hospitals in Riyadh", 
        "shopping malls in Riyadh",
        "banks in Riyadh",
        "supermarkets in Riyadh",
        "mosques in Riyadh",
        "schools in Riyadh",
        "coffee shops in Riyadh",
        "gyms in Riyadh",
        "pharmacies in Riyadh",
        "car rental in Riyadh",
        "gas stations in Riyadh",
        "clinics in Riyadh",
        "parks in Riyadh"
    ]
    
    driver = setup_driver()
    all_businesses = []
    
    try:
        for search in searches:
            results = search_and_extract(driver, search, max_results=30)
            all_businesses.extend(results)
            print(f"   ✓ Total so far: {len(all_businesses)}")
            time.sleep(3)
    finally:
        driver.quit()
    
    # Remove duplicates by URL
    seen = set()
    unique = []
    for b in all_businesses:
        if b['url'] not in seen:
            seen.add(b['url'])
            unique.append(b)
    
    print(f"\n📊 Extracted {len(unique)} unique businesses")
    
    # Save
    if unique:
        df = pd.DataFrame(unique)
        df.to_csv('/workspace/riyadh_google_businesses.csv', index=False)
        print(f"✅ Saved to /workspace/riyadh_google_businesses.csv")
        
        with open('/workspace/riyadh_google_businesses.json', 'w', encoding='utf-8') as f:
            json.dump(unique, f, ensure_ascii=False, indent=2)
        print(f"✅ Saved to /workspace/riyadh_google_businesses.json")
        
        # Show summary
        print("\n📈 Summary by category:")
        print(df['category'].value_counts().head(15).to_string())
    
    return unique

if __name__ == '__main__':
    main()
