const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
    const browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1920,1080']
    });
    
    const page = await browser.newPage();
    await page.setViewport({ width: 1920, height: 1080 });
    
    const parcelData = [];
    
    page.on('response', async (response) => {
        const url = response.url();
        try {
            if (url.includes('api2.suhail.ai/parcel') || url.includes('transaction')) {
                const text = await response.text();
                if (text && text.startsWith('{')) {
                    const data = JSON.parse(text);
                    if (data.data) {
                        console.log('PARCEL API:', url.substring(0, 80));
                        parcelData.push(data.data);
                    }
                }
            }
        } catch (e) {}
    });
    
    // Go to the main page first
    console.log('Loading suhail.ai homepage...');
    await page.goto('https://suhail.ai/', { 
        waitUntil: 'networkidle2',
        timeout: 60000 
    });
    await new Promise(r => setTimeout(r, 3000));
    
    // Now navigate to Riyadh
    console.log('Navigating to Riyadh...');
    await page.goto('https://suhail.ai/Riyadh', { 
        waitUntil: 'networkidle2',
        timeout: 60000 
    });
    await new Promise(r => setTimeout(r, 5000));
    
    // Take screenshot to see what we have
    await page.screenshot({ path: '/workspace/suhail_riyadh.png', fullPage: true });
    
    // Check for search input
    const pageContent = await page.content();
    console.log('Has search:', pageContent.includes('search') || pageContent.includes('بحث'));
    
    // Try to search
    console.log('Looking for search...');
    const searchInput = await page.$('input[placeholder*="مخطط"], input[placeholder*="بحث"], input[type="text"]');
    
    if (searchInput) {
        console.log('Found search input!');
        await searchInput.click();
        await searchInput.type('المحمدية', { delay: 100 });
        await new Promise(r => setTimeout(r, 2000));
        
        // Look for suggestions
        const suggestions = await page.$$('[class*="suggestion"], [class*="autocomplete"], [role="option"], [class*="item"]');
        console.log('Suggestions found:', suggestions.length);
        
        // Click first relevant one
        for (const s of suggestions) {
            const text = await s.evaluate(el => el.innerText);
            if (text.includes('المحمدية') && text.includes('الرياض')) {
                console.log('Clicking:', text.substring(0, 50));
                await s.click();
                break;
            }
        }
        
        await new Promise(r => setTimeout(r, 5000));
    }
    
    // Zoom in using scroll
    console.log('Zooming...');
    const canvas = await page.$('canvas');
    if (canvas) {
        const box = await canvas.boundingBox();
        await page.mouse.move(box.x + box.width/2, box.y + box.height/2);
        
        for (let i = 0; i < 10; i++) {
            await page.mouse.wheel({ deltaY: -300 });
            await new Promise(r => setTimeout(r, 1000));
        }
    }
    
    await new Promise(r => setTimeout(r, 5000));
    
    // Click on parcels
    console.log('Clicking parcels...');
    if (canvas) {
        const box = await canvas.boundingBox();
        for (let x = 0.2; x <= 0.8; x += 0.15) {
            for (let y = 0.2; y <= 0.8; y += 0.15) {
                await page.mouse.click(box.x + box.width * x, box.y + box.height * y);
                await new Promise(r => setTimeout(r, 1000));
            }
        }
    }
    
    await page.screenshot({ path: '/workspace/suhail_parcels_final.png', fullPage: true });
    
    console.log('\n=== RESULTS ===');
    console.log('Parcels captured:', parcelData.length);
    
    fs.writeFileSync('/workspace/suhail_captured_parcels.json', JSON.stringify(parcelData, null, 2));
    
    if (parcelData.length > 0) {
        console.log('\nSample:');
        console.log(JSON.stringify(parcelData[0], null, 2).substring(0, 1000));
    }
    
    await browser.close();
})();
