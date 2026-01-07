const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
    const browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    const page = await browser.newPage();
    await page.setViewport({ width: 1920, height: 1080 });
    
    // Capture ALL API responses
    const apiResponses = [];
    page.on('response', async (response) => {
        const url = response.url();
        try {
            const text = await response.text();
            if (text.startsWith('{') || text.startsWith('[')) {
                const data = JSON.parse(text);
                apiResponses.push({ url, data });
                if (url.includes('landMetrics') || url.includes('mapMetrics') || url.includes('neighborhood')) {
                    console.log('*** METRICS API:', url);
                }
            }
        } catch (e) {}
    });
    
    // Navigate to a URL that directly shows Al-Muhammadiyah area at zoom level that triggers metrics
    console.log('Navigating to Al-Muhammadiyah area...');
    
    // The metrics page with zoom level 12 shows neighborhood data
    // Al-Muhammadiyah coordinates: 46.650092, 24.732633
    await page.goto('https://suhail.ai/Riyadh/metrics', { 
        waitUntil: 'networkidle2',
        timeout: 60000 
    });
    
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    // Execute JavaScript to fly to Al-Muhammadiyah and zoom in
    console.log('Flying to Al-Muhammadiyah coordinates...');
    await page.evaluate(() => {
        // Try to access mapbox map instance
        const mapElements = document.querySelectorAll('.mapboxgl-map');
        console.log('Map elements found:', mapElements.length);
    });
    
    // Use mouse to zoom in on the map
    // First find the map container and click on it to focus
    const mapContainer = await page.$('.mapboxgl-canvas, .mapboxgl-map, [class*="map"]');
    if (mapContainer) {
        console.log('Found map container, clicking and zooming...');
        const box = await mapContainer.boundingBox();
        const centerX = box.x + box.width / 2;
        const centerY = box.y + box.height / 2;
        
        // Click to focus
        await page.mouse.click(centerX, centerY);
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Zoom in multiple times using scroll
        for (let i = 0; i < 8; i++) {
            await page.mouse.wheel({ deltaY: -300 });
            await new Promise(resolve => setTimeout(resolve, 800));
        }
        
        await new Promise(resolve => setTimeout(resolve, 3000));
    }
    
    // Now search and navigate to Al-Muhammadiyah
    console.log('Searching for Al-Muhammadiyah...');
    await page.evaluate(() => {
        const buttons = Array.from(document.querySelectorAll('button'));
        const addressBtn = buttons.find(b => b.innerText.includes('العنوان'));
        if (addressBtn) addressBtn.click();
    });
    await new Promise(resolve => setTimeout(resolve, 500));
    
    const searchInput = await page.$('input[type="text"]');
    if (searchInput) {
        await searchInput.click({ clickCount: 3 });
        await searchInput.type('المحمدية الرياض', { delay: 50 });
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Click on first suggestion
        await page.evaluate(() => {
            const items = document.querySelectorAll('[class*="item"], [class*="suggestion"], [role="option"]');
            for (const item of items) {
                if (item.innerText.includes('المحمدية') && item.innerText.includes('الرياض')) {
                    item.click();
                    return true;
                }
            }
            return false;
        });
        
        await new Promise(resolve => setTimeout(resolve, 5000));
    }
    
    // Zoom in more to trigger neighborhood metrics
    if (mapContainer) {
        const box = await mapContainer.boundingBox();
        const centerX = box.x + box.width / 2;
        const centerY = box.y + box.height / 2;
        
        for (let i = 0; i < 5; i++) {
            await page.mouse.wheel({ deltaY: -300 });
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    }
    
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    // Take screenshot
    await page.screenshot({ path: '/workspace/suhail_muhammadiyah_zoomed.png', fullPage: true });
    console.log('Screenshot saved');
    
    // Get page metrics
    const pageContent = await page.evaluate(() => document.body.innerText);
    console.log('\n--- Page Content ---');
    console.log(pageContent.substring(0, 3000));
    
    // Print metrics API responses
    console.log('\n--- All Captured API Responses ---');
    for (const resp of apiResponses) {
        if (resp.url.includes('landMetrics') || resp.url.includes('mapMetrics') || 
            resp.url.includes('neighborhood') || resp.url.includes('metrics')) {
            console.log('\n=== METRICS URL:', resp.url);
            console.log(JSON.stringify(resp.data, null, 2).substring(0, 5000));
        }
    }
    
    // Save all responses
    fs.writeFileSync('/workspace/all_api_responses.json', JSON.stringify(apiResponses, null, 2));
    console.log('\nAll API responses saved');
    
    await browser.close();
})();
