/**
 * UFO Sightings Interactive Map
 * Handles map initialization, data loading, filtering, and interactions
 */

class UFOMap {
    constructor() {
        this.map = null;
        this.markersLayer = null;
        this.heatmapLayer = null;
        this.clusterGroup = null;
        this.currentData = [];
        this.filteredData = [];
        this.viewMode = 'markers';
        this.apiKey = null;
        
        this.init();
    }

    async init() {
        try {
            // Check if we need an API key for this deployment
            await this.checkAuthRequirement();
            
            // Initialize map
            this.initMap();
            
            // Load initial data
            await this.loadData();
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Apply default date range (last year)
            this.setDefaultDateRange();
            
        } catch (error) {
            console.error('Failed to initialize map:', error);
            this.showError('Failed to load map. Please refresh the page.');
        }
    }

    async checkAuthRequirement() {
        // For the map, we'll use public endpoints that don't require auth
        // This makes the map accessible to everyone
        console.log('Map using public endpoints - no authentication required');
    }

    promptForApiKey() {
        const apiKey = prompt('This map requires an API key. Please enter your SkyWatch API key:');
        if (apiKey) {
            this.apiKey = apiKey;
            localStorage.setItem('ufo_api_key', apiKey);
        } else {
            this.showError('API key required to view sightings data.');
        }
    }

    initMap() {
        // Initialize Leaflet map
        this.map = L.map('map', {
            center: [39.8283, -98.5795], // Center of USA
            zoom: 4,
            zoomControl: true,
            preferCanvas: true
        });

        // Add OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 18
        }).addTo(this.map);

        // Initialize marker cluster group
        this.clusterGroup = L.markerClusterGroup({
            chunkedLoading: true,
            chunkInterval: 200,
            maxClusterRadius: 50,
            spiderfyOnMaxZoom: true,
            showCoverageOnHover: false,
            zoomToBoundsOnClick: true
        });

        // Add cluster group to map
        this.map.addLayer(this.clusterGroup);
    }

    async loadData(filters = {}) {
        this.showLoading(true);
        
        try {
            // Build query parameters
            const params = new URLSearchParams();
            params.append('per_page', '10000'); // Large number to get all data
            
            // Add filters
            if (filters.date_from) params.append('date_from', filters.date_from);
            if (filters.date_to) params.append('date_to', filters.date_to);
            if (filters.shape) params.append('shape', filters.shape);
            if (filters.state) params.append('state', filters.state);
            if (filters.city) params.append('city', filters.city);

            // Use public map API endpoint
            const response = await fetch(`/v1/map/data?format=simple&${params}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            this.currentData = data.sightings || [];
            this.filteredData = [...this.currentData];
            
            // Update map display
            this.updateMapDisplay();
            this.updateStats();
            
        } catch (error) {
            console.error('Failed to load data:', error);
            this.showError(`Failed to load sightings: ${error.message}`);
        } finally {
            this.showLoading(false);
        }
    }

    updateMapDisplay() {
        if (this.viewMode === 'markers') {
            this.showMarkers();
            this.hideHeatmap();
        } else {
            this.showHeatmap();
            this.hideMarkers();
        }
    }

    showMarkers() {
        // Clear existing markers
        this.clusterGroup.clearLayers();

        // Filter out sightings without coordinates
        const validSightings = this.filteredData.filter(s => s.latitude && s.longitude);

        // Add markers for each sighting
        validSightings.forEach(sighting => {
            const marker = this.createMarker(sighting);
            this.clusterGroup.addLayer(marker);
        });

        // Fit map to show all markers if we have data
        if (validSightings.length > 0) {
            try {
                this.map.fitBounds(this.clusterGroup.getBounds(), { padding: [20, 20] });
            } catch (e) {
                // Ignore errors with bounds calculation
            }
        }
    }

    createMarker(sighting) {
        const lat = parseFloat(sighting.latitude);
        const lng = parseFloat(sighting.longitude);
        
        // Create custom icon based on shape
        const iconClass = this.getShapeIconClass(sighting.shape);
        const iconHtml = `<div class="ufo-marker ${iconClass}">${this.getShapeSymbol(sighting.shape)}</div>`;
        
        const customIcon = L.divIcon({
            html: iconHtml,
            className: 'custom-marker',
            iconSize: [24, 24],
            iconAnchor: [12, 12]
        });

        const marker = L.marker([lat, lng], { icon: customIcon });
        
        // Create popup content
        const popupContent = this.createPopupContent(sighting);
        marker.bindPopup(popupContent, { maxWidth: 300 });
        
        return marker;
    }

    getShapeIconClass(shape) {
        const shapeMap = {
            'disk': 'marker-disk',
            'triangle': 'marker-triangle',
            'sphere': 'marker-sphere',
            'light': 'marker-light',
            'oval': 'marker-disk',
            'fireball': 'marker-light',
            'cigar': 'marker-other'
        };
        return shapeMap[shape?.toLowerCase()] || 'marker-other';
    }

    getShapeSymbol(shape) {
        const symbolMap = {
            'disk': '●',
            'triangle': '▲',
            'sphere': '●',
            'light': '✦',
            'oval': '●',
            'fireball': '✦',
            'cigar': '━'
        };
        return symbolMap[shape?.toLowerCase()] || '?';
    }

    createPopupContent(sighting) {
        const date = new Date(sighting.date_time).toLocaleDateString();
        const time = new Date(sighting.date_time).toLocaleTimeString();
        
        return `
            <div style="min-width: 250px;">
                <h3 style="margin: 0 0 8px 0; color: #cc5500; font-size: 16px;">
                    ${sighting.city}, ${sighting.state}
                </h3>
                <div style="margin-bottom: 8px;">
                    <strong>Date:</strong> ${date} at ${time}<br>
                    <strong>Shape:</strong> ${sighting.shape}<br>
                    <strong>Duration:</strong> ${sighting.duration}
                </div>
                <div style="margin-bottom: 8px;">
                    <strong>Description:</strong><br>
                    <em>${sighting.summary}</em>
                </div>
                <div style="font-size: 12px; color: #666;">
                    Reported: ${new Date(sighting.posted).toLocaleDateString()}
                </div>
            </div>
        `;
    }

    showHeatmap() {
        this.hideMarkers();
        
        // Prepare heatmap data
        const validSightings = this.filteredData.filter(s => s.latitude && s.longitude);
        const heatmapData = validSightings.map(s => [
            parseFloat(s.latitude),
            parseFloat(s.longitude),
            1 // intensity
        ]);

        // Remove existing heatmap
        if (this.heatmapLayer) {
            this.map.removeLayer(this.heatmapLayer);
        }

        // Create new heatmap
        if (heatmapData.length > 0) {
            this.heatmapLayer = L.heatLayer(heatmapData, {
                radius: 20,
                blur: 15,
                maxZoom: 17,
                gradient: {
                    0.0: 'blue',
                    0.5: 'lime',
                    0.7: 'yellow',
                    1.0: 'red'
                }
            }).addTo(this.map);
        }
    }

    hideMarkers() {
        this.clusterGroup.clearLayers();
    }

    hideHeatmap() {
        if (this.heatmapLayer) {
            this.map.removeLayer(this.heatmapLayer);
            this.heatmapLayer = null;
        }
    }

    updateStats() {
        const totalCount = this.currentData.length;
        const visibleCount = this.filteredData.length;
        
        // Calculate most common shape
        const shapeCounts = {};
        this.filteredData.forEach(s => {
            const shape = s.shape || 'unknown';
            shapeCounts[shape] = (shapeCounts[shape] || 0) + 1;
        });
        
        const mostCommonShape = Object.keys(shapeCounts).reduce((a, b) => 
            shapeCounts[a] > shapeCounts[b] ? a : b, '-'
        );

        // Calculate date range
        let dateRange = '-';
        if (this.filteredData.length > 0) {
            const dates = this.filteredData.map(s => new Date(s.date_time)).sort();
            const earliest = dates[0].getFullYear();
            const latest = dates[dates.length - 1].getFullYear();
            dateRange = earliest === latest ? earliest.toString() : `${earliest}-${latest}`;
        }

        // Update DOM
        document.getElementById('total-count').textContent = totalCount.toLocaleString();
        document.getElementById('visible-count').textContent = visibleCount.toLocaleString();
        document.getElementById('common-shape').textContent = mostCommonShape;
        document.getElementById('date-range').textContent = dateRange;
    }

    setupEventListeners() {
        // Mobile responsive
        this.setupMobileHandlers();
        
        // Filter change listeners are handled by global functions
        // due to HTML onclick attributes
    }

    setupMobileHandlers() {
        const checkMobile = () => {
            const isMobile = window.innerWidth <= 768;
            const mobileToggle = document.querySelector('.mobile-toggle');
            const sidebar = document.getElementById('sidebar');
            
            if (isMobile) {
                mobileToggle.style.display = 'block';
                sidebar.classList.remove('open');
            } else {
                mobileToggle.style.display = 'none';
                sidebar.classList.remove('open');
            }
            
            // Invalidate map size when layout changes
            setTimeout(() => this.map.invalidateSize(), 100);
        };

        window.addEventListener('resize', checkMobile);
        checkMobile();
    }

    setDefaultDateRange() {
        const today = new Date();
        const oneYearAgo = new Date();
        oneYearAgo.setFullYear(today.getFullYear() - 1);
        
        document.getElementById('date-from').value = oneYearAgo.toISOString().split('T')[0];
        document.getElementById('date-to').value = today.toISOString().split('T')[0];
        document.getElementById('date-preset').value = '365';
    }

    showLoading(show) {
        const spinner = document.getElementById('loading-spinner');
        spinner.style.display = show ? 'block' : 'none';
    }

    showError(message) {
        // Create a simple error overlay
        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #fee;
            color: #c53030;
            padding: 12px 16px;
            border-radius: 6px;
            border: 1px solid #fed7d7;
            z-index: 10000;
            max-width: 300px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        `;
        errorDiv.textContent = message;
        
        document.body.appendChild(errorDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 5000);
    }
}

// Global functions for HTML event handlers
let ufoMap;

// Initialize map when page loads
document.addEventListener('DOMContentLoaded', () => {
    ufoMap = new UFOMap();
});

function setViewMode(mode) {
    if (!ufoMap) return;
    
    ufoMap.viewMode = mode;
    ufoMap.updateMapDisplay();
    
    // Update button states
    document.querySelectorAll('.toggle-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(mode + '-btn').classList.add('active');
}

function applyDatePreset() {
    const preset = document.getElementById('date-preset').value;
    const today = new Date();
    const fromInput = document.getElementById('date-from');
    const toInput = document.getElementById('date-to');
    
    toInput.value = today.toISOString().split('T')[0];
    
    if (preset === 'all') {
        fromInput.value = '';
        toInput.value = '';
    } else if (preset) {
        const daysAgo = new Date();
        daysAgo.setDate(today.getDate() - parseInt(preset));
        fromInput.value = daysAgo.toISOString().split('T')[0];
    }
}

async function applyFilters() {
    if (!ufoMap) return;
    
    const filters = {
        date_from: document.getElementById('date-from').value,
        date_to: document.getElementById('date-to').value,
        shape: document.getElementById('shape-filter').value,
        state: document.getElementById('state-filter').value,
        city: document.getElementById('city-search').value
    };
    
    // Remove empty filters
    Object.keys(filters).forEach(key => {
        if (!filters[key]) delete filters[key];
    });
    
    await ufoMap.loadData(filters);
}

function clearFilters() {
    document.getElementById('date-from').value = '';
    document.getElementById('date-to').value = '';
    document.getElementById('shape-filter').value = '';
    document.getElementById('state-filter').value = '';
    document.getElementById('city-search').value = '';
    document.getElementById('date-preset').value = '';
    
    if (ufoMap) {
        ufoMap.setDefaultDateRange();
        applyFilters();
    }
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('open');
}