#!/usr/bin/env node

/**
 * Puppeteer Test Script for UFO Map Debugging
 * Tests the map at http://localhost:8000/map to identify why it's showing no data
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// Configuration
const BASE_URL = 'http://localhost:8000';
const MAP_URL = `${BASE_URL}/map`;
const TIMEOUT = 30000; // 30 seconds
const SCREENSHOT_DIR = './screenshots';

// Create screenshots directory if it doesn't exist
if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

async function runMapTests() {
    console.log('🚀 Starting UFO Map Debug Tests...\n');
    
    const browser = await puppeteer.launch({
        headless: false, // Show browser for debugging
        devtools: true,  // Open DevTools
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--remote-debugging-port=9222'
        ]
    });

    const page = await browser.newPage();
    
    // Set viewport size
    await page.setViewport({ width: 1920, height: 1080 });

    // Arrays to collect errors and network issues
    const consoleErrors = [];
    const networkErrors = [];
    const apiResponses = [];

    // Listen for console errors
    page.on('console', (msg) => {
        const type = msg.type();
        const text = msg.text();
        
        if (type === 'error') {
            consoleErrors.push({ type, text, timestamp: new Date().toISOString() });
            console.log(`❌ Console Error: ${text}`);
        } else if (type === 'warn') {
            console.log(`⚠️  Console Warning: ${text}`);
        } else if (type === 'log') {
            console.log(`📝 Console Log: ${text}`);
        }
    });

    // Listen for network requests and responses
    page.on('response', (response) => {
        const url = response.url();
        const status = response.status();
        
        // Track API responses
        if (url.includes('/v1/') || url.includes('/api/')) {
            apiResponses.push({
                url,
                status,
                statusText: response.statusText(),
                timestamp: new Date().toISOString()
            });
            
            console.log(`🌐 API Response: ${status} ${url}`);
            
            if (status >= 400) {
                networkErrors.push({
                    url,
                    status,
                    statusText: response.statusText(),
                    timestamp: new Date().toISOString()
                });
                console.log(`❌ Network Error: ${status} ${response.statusText()} - ${url}`);
            }
        }
    });

    // Listen for failed requests
    page.on('requestfailed', (request) => {
        const url = request.url();
        const failure = request.failure();
        
        networkErrors.push({
            url,
            failure: failure.errorText,
            timestamp: new Date().toISOString()
        });
        
        console.log(`❌ Request Failed: ${failure.errorText} - ${url}`);
    });

    try {
        console.log(`📍 Navigating to: ${MAP_URL}`);
        
        // Navigate to the map page
        const response = await page.goto(MAP_URL, { 
            waitUntil: 'networkidle2',
            timeout: TIMEOUT 
        });

        if (!response.ok()) {
            throw new Error(`Failed to load map page: ${response.status()} ${response.statusText()}`);
        }

        console.log(`✅ Map page loaded successfully (${response.status()})`);

        // Take initial screenshot
        await page.screenshot({ 
            path: path.join(SCREENSHOT_DIR, 'map_initial.png'),
            fullPage: true 
        });
        console.log('📸 Initial screenshot saved');

        // Wait for map container to be visible
        await page.waitForSelector('#map', { timeout: 10000 });
        console.log('✅ Map container found');

        // Wait for Leaflet to load
        await page.waitForFunction(() => {
            return typeof window.L !== 'undefined';
        }, { timeout: 10000 });
        console.log('✅ Leaflet library loaded');

        // Wait for UFOMap class to be available
        await page.waitForFunction(() => {
            return typeof window.UFOMap !== 'undefined';
        }, { timeout: 10000 });
        console.log('✅ UFOMap class loaded');

        // Wait for map instance to be created
        await page.waitForFunction(() => {
            return window.ufoMap && window.ufoMap.map;
        }, { timeout: 15000 });
        console.log('✅ UFOMap instance created');

        // Wait a bit for data to load
        await page.waitForTimeout(5000);

        // Take screenshot after map loads
        await page.screenshot({ 
            path: path.join(SCREENSHOT_DIR, 'map_loaded.png'),
            fullPage: true 
        });
        console.log('📸 Map loaded screenshot saved');

        // Check if data has been loaded
        const mapData = await page.evaluate(() => {
            if (window.ufoMap) {
                return {
                    currentDataLength: window.ufoMap.currentData ? window.ufoMap.currentData.length : 0,
                    filteredDataLength: window.ufoMap.filteredData ? window.ufoMap.filteredData.length : 0,
                    viewMode: window.ufoMap.viewMode,
                    mapCenter: window.ufoMap.map ? window.ufoMap.map.getCenter() : null,
                    mapZoom: window.ufoMap.map ? window.ufoMap.map.getZoom() : null,
                    clusterGroupLayers: window.ufoMap.clusterGroup ? window.ufoMap.clusterGroup.getLayers().length : 0
                };
            }
            return null;
        });

        console.log('\n📊 Map Data Analysis:');
        console.log(`   • Current Data Length: ${mapData?.currentDataLength || 0}`);
        console.log(`   • Filtered Data Length: ${mapData?.filteredDataLength || 0}`);
        console.log(`   • View Mode: ${mapData?.viewMode || 'unknown'}`);
        console.log(`   • Map Center: ${mapData?.mapCenter ? `${mapData.mapCenter.lat.toFixed(3)}, ${mapData.mapCenter.lng.toFixed(3)}` : 'unknown'}`);
        console.log(`   • Map Zoom: ${mapData?.mapZoom || 'unknown'}`);
        console.log(`   • Cluster Group Layers: ${mapData?.clusterGroupLayers || 0}`);

        // Check stats panel values
        const statsData = await page.evaluate(() => {
            return {
                totalCount: document.getElementById('total-count')?.textContent || '0',
                visibleCount: document.getElementById('visible-count')?.textContent || '0',
                commonShape: document.getElementById('common-shape')?.textContent || '-',
                dateRange: document.getElementById('date-range')?.textContent || '-'
            };
        });

        console.log('\n📈 Stats Panel Data:');
        console.log(`   • Total Count: ${statsData.totalCount}`);
        console.log(`   • Visible Count: ${statsData.visibleCount}`);
        console.log(`   • Common Shape: ${statsData.commonShape}`);
        console.log(`   • Date Range: ${statsData.dateRange}`);

        // Test API endpoints directly
        console.log('\n🔍 Testing API Endpoints:');
        
        // Test map data endpoint
        try {
            const mapDataResponse = await page.goto(`${BASE_URL}/v1/map/data?format=simple&per_page=10`, {
                waitUntil: 'networkidle2',
                timeout: 10000
            });
            
            if (mapDataResponse.ok()) {
                const mapDataJson = await mapDataResponse.json();
                console.log(`✅ Map Data API: ${mapDataResponse.status()} - ${mapDataJson.total || 0} sightings returned`);
                
                if (mapDataJson.sightings && mapDataJson.sightings.length > 0) {
                    const firstSighting = mapDataJson.sightings[0];
                    console.log(`   • First sighting: ${firstSighting.city}, ${firstSighting.state} (${firstSighting.latitude}, ${firstSighting.longitude})`);
                } else {
                    console.log('   • No sightings in response');
                }
            } else {
                console.log(`❌ Map Data API: ${mapDataResponse.status()} ${mapDataResponse.statusText()}`);
            }
        } catch (error) {
            console.log(`❌ Map Data API Error: ${error.message}`);
        }

        // Test map stats endpoint
        try {
            const statsResponse = await page.goto(`${BASE_URL}/v1/map/stats`, {
                waitUntil: 'networkidle2',
                timeout: 10000
            });
            
            if (statsResponse.ok()) {
                const statsJson = await statsResponse.json();
                console.log(`✅ Map Stats API: ${statsResponse.status()} - ${statsJson.total_sightings || 0} total sightings`);
            } else {
                console.log(`❌ Map Stats API: ${statsResponse.status()} ${statsResponse.statusText()}`);
            }
        } catch (error) {
            console.log(`❌ Map Stats API Error: ${error.message}`);
        }

        // Navigate back to map page
        await page.goto(MAP_URL, { waitUntil: 'networkidle2' });

        // Try applying filters to see if that helps
        console.log('\n🔧 Testing Filter Functionality:');
        
        // Try setting a date range
        await page.evaluate(() => {
            const datePreset = document.getElementById('date-preset');
            if (datePreset) {
                datePreset.value = 'all';
                // Trigger change event
                datePreset.dispatchEvent(new Event('change'));
            }
        });

        // Apply date preset
        await page.evaluate(() => {
            if (typeof window.applyDatePreset === 'function') {
                window.applyDatePreset();
            }
        });

        // Apply filters
        await page.evaluate(() => {
            if (typeof window.applyFilters === 'function') {
                window.applyFilters();
            }
        });

        // Wait for filter application
        await page.waitForTimeout(3000);

        // Take screenshot after filters
        await page.screenshot({ 
            path: path.join(SCREENSHOT_DIR, 'map_after_filters.png'),
            fullPage: true 
        });
        console.log('📸 Screenshot after filters saved');

        // Check data again after filters
        const mapDataAfterFilters = await page.evaluate(() => {
            if (window.ufoMap) {
                return {
                    currentDataLength: window.ufoMap.currentData ? window.ufoMap.currentData.length : 0,
                    filteredDataLength: window.ufoMap.filteredData ? window.ufoMap.filteredData.length : 0,
                    clusterGroupLayers: window.ufoMap.clusterGroup ? window.ufoMap.clusterGroup.getLayers().length : 0
                };
            }
            return null;
        });

        console.log('\n📊 Map Data After Filters:');
        console.log(`   • Current Data Length: ${mapDataAfterFilters?.currentDataLength || 0}`);
        console.log(`   • Filtered Data Length: ${mapDataAfterFilters?.filteredDataLength || 0}`);
        console.log(`   • Cluster Group Layers: ${mapDataAfterFilters?.clusterGroupLayers || 0}`);

        // Test database connectivity
        console.log('\n🗄️  Testing Database Connectivity:');
        try {
            const healthResponse = await page.goto(`${BASE_URL}/health`, {
                waitUntil: 'networkidle2',
                timeout: 10000
            });
            
            if (healthResponse.ok()) {
                const healthJson = await healthResponse.json();
                console.log(`✅ Health Check: ${healthResponse.status()} - Database: ${healthJson.database_status || 'unknown'}`);
            } else {
                console.log(`❌ Health Check: ${healthResponse.status()} ${healthResponse.statusText()}`);
            }
        } catch (error) {
            console.log(`❌ Health Check Error: ${error.message}`);
        }

        // Final screenshot
        await page.screenshot({ 
            path: path.join(SCREENSHOT_DIR, 'map_final.png'),
            fullPage: true 
        });
        console.log('📸 Final screenshot saved');

    } catch (error) {
        console.error('❌ Test failed:', error.message);
        
        // Take error screenshot
        try {
            await page.screenshot({ 
                path: path.join(SCREENSHOT_DIR, 'map_error.png'),
                fullPage: true 
            });
            console.log('📸 Error screenshot saved');
        } catch (screenshotError) {
            console.error('Failed to take error screenshot:', screenshotError.message);
        }
    } finally {
        // Generate test report
        console.log('\n📋 Test Report Summary:');
        console.log('='.repeat(50));
        
        console.log(`\n🔍 Console Errors (${consoleErrors.length}):`);
        if (consoleErrors.length === 0) {
            console.log('   ✅ No console errors detected');
        } else {
            consoleErrors.forEach((error, index) => {
                console.log(`   ${index + 1}. ${error.text}`);
            });
        }

        console.log(`\n🌐 Network Errors (${networkErrors.length}):`);
        if (networkErrors.length === 0) {
            console.log('   ✅ No network errors detected');
        } else {
            networkErrors.forEach((error, index) => {
                console.log(`   ${index + 1}. ${error.status || 'FAILED'} - ${error.url}`);
            });
        }

        console.log(`\n📡 API Responses (${apiResponses.length}):`);
        if (apiResponses.length === 0) {
            console.log('   ⚠️  No API responses detected');
        } else {
            apiResponses.forEach((response, index) => {
                console.log(`   ${index + 1}. ${response.status} - ${response.url}`);
            });
        }

        console.log(`\n📸 Screenshots saved in: ${SCREENSHOT_DIR}`);
        console.log('\n🏁 Test completed');

        await browser.close();
    }
}

// Run the tests
runMapTests().catch(console.error);