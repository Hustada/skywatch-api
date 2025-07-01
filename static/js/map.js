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
            
            // Load available states for dropdown
            await this.loadStates();
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Set default date range inputs
            this.setDefaultDateRange();
            
            // Load initial data (with default filters applied)
            await this.loadData();
            
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

    async loadStates() {
        try {
            const response = await fetch('/v1/map/states');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            const stateSelect = document.getElementById('state-filter');
            
            // Clear existing state options (keep the first 4 options)
            while (stateSelect.children.length > 4) {
                stateSelect.removeChild(stateSelect.lastChild);
            }
            
            // Add states to dropdown
            data.states.forEach(state => {
                const option = document.createElement('option');
                option.value = state.code;
                option.textContent = `${state.name} (${state.sighting_count})`;
                stateSelect.appendChild(option);
            });
            
        } catch (error) {
            console.error('Failed to load states:', error);
            // Continue without state data - user can still use basic filtering
        }
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
                <button class="popup-research-btn" onclick="researchSighting(${sighting.id}, '${sighting.city}, ${sighting.state}')">
                    🔍 AI Research This Sighting
                </button>
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

        // Create new heatmap with improved visibility
        if (heatmapData.length > 0) {
            this.heatmapLayer = L.heatLayer(heatmapData, {
                radius: 35,           // Increased from 20 for larger hotspots
                blur: 25,             // Increased from 15 for smoother blending
                maxZoom: 18,          // Allow heatmap to show at higher zoom levels
                minOpacity: 0.4,      // Set minimum opacity so faint areas are still visible
                gradient: {
                    0.0: 'rgba(0, 0, 255, 0.6)',      // Semi-transparent blue
                    0.2: 'rgba(0, 255, 255, 0.7)',    // Cyan
                    0.4: 'rgba(0, 255, 0, 0.8)',      // Green  
                    0.6: 'rgba(255, 255, 0, 0.9)',    // Yellow
                    0.8: 'rgba(255, 165, 0, 0.9)',    // Orange
                    1.0: 'rgba(255, 0, 0, 1.0)'       // Bright red
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
        
        let mostCommonShape = '-';
        if (Object.keys(shapeCounts).length > 0) {
            mostCommonShape = Object.keys(shapeCounts).reduce((a, b) => 
                shapeCounts[a] > shapeCounts[b] ? a : b
            );
        }

        // Calculate date range
        let dateRange = '-';
        if (this.filteredData.length > 0) {
            const dates = this.filteredData.map(s => new Date(s.date_time)).sort((a, b) => a - b);
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
        // Start with no date filter - show all sightings by default
        // Users can apply date filters if they want to narrow down
        document.getElementById('date-from').value = '';
        document.getElementById('date-to').value = '';
        document.getElementById('date-preset').value = 'all';
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

// Research functionality
let currentSighting = null;
let currentQuickAnalysis = null;
let researchCache = new Map();

async function researchSighting(sightingId, location) {
    currentSighting = { id: sightingId, location: location };
    currentQuickAnalysis = null;
    
    // Check cache first
    const cacheKey = `quick_${sightingId}`;
    if (researchCache.has(cacheKey)) {
        const cachedResult = researchCache.get(cacheKey);
        showResearchModal(cachedResult, true);
        return;
    }
    
    // Show modal with loading state
    showResearchModal(null, false);
    
    try {
        // For now, let's use a test API key - we'll improve this later
        const response = await fetch(`/v1/research/quick/${sightingId}`, {
            headers: {
                'X-API-Key': 'sk_live_aff5306db031a32f565953b83f0b11418b0c4a965c09a5196e93f65cdc84a41f'
            }
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                throw new Error('Authentication required. Please contact administrator for access.');
            }
            throw new Error(`Research service unavailable (${response.status})`);
        }
        
        const result = await response.json();
        currentQuickAnalysis = result;
        
        // Cache the result
        researchCache.set(cacheKey, result);
        
        // Show the result
        showResearchModal(result, true);
        
    } catch (error) {
        console.error('Research error:', error);
        showResearchError(error.message);
    }
}

async function getFullResearch() {
    if (!currentSighting) return;
    
    const cacheKey = `full_${currentSighting.id}`;
    if (researchCache.has(cacheKey)) {
        const cachedResult = researchCache.get(cacheKey);
        showFullResearchResult(cachedResult);
        return;
    }
    
    // Show loading state for full research
    showFullResearchLoading();
    
    try {
        const response = await fetch(`/v1/research/sighting/${currentSighting.id}`, {
            headers: {
                'X-API-Key': 'sk_live_aff5306db031a32f565953b83f0b11418b0c4a965c09a5196e93f65cdc84a41f'
            }
        });
        
        if (!response.ok) {
            throw new Error(`Research service unavailable (${response.status})`);
        }
        
        const result = await response.json();
        
        // Cache the result
        researchCache.set(cacheKey, result);
        
        // Show the result
        showFullResearchResult(result);
        
    } catch (error) {
        console.error('Full research error:', error);
        showResearchError(error.message);
    }
}

function showResearchModal(result, showActions) {
    const modal = document.getElementById('research-modal');
    const modalBody = document.getElementById('research-modal-body');
    const actions = document.getElementById('research-actions');
    
    if (!result) {
        // Show loading state
        modalBody.innerHTML = `
            <div class="research-loading">
                <div class="research-loading-spinner"></div>
                <div class="research-loading-text">Analyzing UFO sighting with AI...</div>
            </div>
        `;
        actions.style.display = 'none';
    } else {
        // Show quick analysis result
        modalBody.innerHTML = `
            <div class="research-quick-analysis">
                <div class="research-quick-title">
                    🤖 Quick AI Analysis
                    <span style="font-size: 12px; font-weight: normal; color: #6b7280;">
                        ${currentSighting.location}
                    </span>
                </div>
                ${formatQuickAnalysis(result.quick_analysis)}
            </div>
        `;
        
        if (showActions) {
            actions.style.display = 'flex';
            document.getElementById('full-research-btn').disabled = false;
        }
    }
    
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function showFullResearchLoading() {
    const modalBody = document.getElementById('research-modal-body');
    modalBody.innerHTML = `
        <div class="research-loading">
            <div class="research-loading-spinner"></div>
            <div class="research-loading-text">Generating comprehensive research report...</div>
            <div style="font-size: 12px; color: #9ca3af; margin-top: 8px;">
                This may take 10-15 seconds
            </div>
        </div>
    `;
    
    // Disable the button
    document.getElementById('full-research-btn').disabled = true;
}

function showFullResearchResult(result) {
    const modalBody = document.getElementById('research-modal-body');
    
    modalBody.innerHTML = `
        <div class="research-quick-analysis">
            <div class="research-quick-title">
                🛸 Comprehensive Research Report
                <span style="font-size: 12px; font-weight: normal; color: #6b7280;">
                    ${currentSighting.location}
                </span>
            </div>
            <div class="research-content">
                ${formatResearchReport(result.research_report)}
            </div>
            ${result.citations && result.citations.length > 0 ? `
                <div style="margin-top: 20px; padding-top: 16px; border-top: 1px solid #e5e7eb;">
                    <h3>Sources & Citations</h3>
                    ${result.citations.map(citation => `
                        <div style="margin-bottom: 8px; font-size: 12px;">
                            <strong>${citation.title}</strong><br>
                            <a href="${citation.url}" target="_blank" style="color: #cc5500;">${citation.url}</a>
                        </div>
                    `).join('')}
                </div>
            ` : ''}
        </div>
    `;
}

function showResearchError(message) {
    const modalBody = document.getElementById('research-modal-body');
    const actions = document.getElementById('research-actions');
    
    modalBody.innerHTML = `
        <div class="research-error">
            <div class="research-error-icon">⚠️</div>
            <div class="research-error-title">Research Unavailable</div>
            <div class="research-error-message">${message}</div>
            <button class="research-btn research-btn-primary" onclick="closeResearchModal()">
                Close
            </button>
        </div>
    `;
    
    actions.style.display = 'none';
}

function formatQuickAnalysis(analysis) {
    // Simple formatting - convert line breaks and basic markdown-style formatting
    return analysis
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>')
        .replace(/^/, '<p>')
        .replace(/$/, '</p>')
        .replace(/(<p>)?(\d+\.\s.*?)(<\/p>|$)/g, '<p><strong>$2</strong></p>');
}

function formatResearchReport(report) {
    // Advanced formatting for research reports with reference system
    let references = [];
    let referenceCount = 0;
    let validatedUrls = new Map();
    
    // Step 1: Extract all URLs first and validate them
    const urlRegex = /(https?:\/\/[^\s)]+)/g;
    const foundUrls = [...report.matchAll(urlRegex)].map(match => {
        let cleanUrl = match[1].replace(/[.,;!?]+$/, '');
        return cleanUrl;
    });
    
    // Step 2: Validate URLs asynchronously (but return promise for better UX)
    validateUrls(foundUrls).then(validUrls => {
        validatedUrls = new Map(validUrls.map(url => [url, true]));
    });
    
    // Step 3: Replace URLs with reference links, only for valid ones
    let formattedReport = report.replace(urlRegex, (url) => {
        // Clean up URL (remove trailing punctuation)
        let cleanUrl = url.replace(/[.,;!?]+$/, '');
        let trailing = url.substring(cleanUrl.length);
        
        // Check if URL is likely to be valid (basic heuristics)
        if (isLikelyValidUrl(cleanUrl)) {
            referenceCount++;
            references.push({
                number: referenceCount,
                url: cleanUrl,
                title: extractDomainName(cleanUrl)
            });
            
            return `<a href="${cleanUrl}" target="_blank" class="reference-link">[${referenceCount}]</a>${trailing}`;
        } else {
            // Return URL as plain text if likely invalid
            return cleanUrl + trailing;
        }
    });
    
    // Step 2: Clean up excessive whitespace and formatting
    formattedReport = formattedReport
        // Handle section headers (bold text that appears to be headers)
        .replace(/\*\*([\w\s:]+):\*\*/g, '<h3>$1</h3>')
        .replace(/\*\*([\w\s]+)\*\*/g, '<h3>$1</h3>')
        
        // Handle emphasis
        .replace(/\*([^*]+)\*/g, '<em>$1</em>')
        
        // Clean up bullet points
        .replace(/^\*\s+/gm, '• ')
        
        // Handle numbered lists better
        .replace(/^(\d+\.)\s+(.+)$/gm, '<div class="numbered-item"><strong>$1</strong> $2</div>')
        
        // Clean up excessive newlines (3+ newlines become 2)
        .replace(/\n{3,}/g, '\n\n')
        
        // Convert double newlines to paragraph breaks
        .replace(/\n\n/g, '</p><p>')
        
        // Convert remaining single newlines to line breaks, but be smarter about it
        .replace(/\n(?![•\d])/g, '<br>')
        
        // Wrap in paragraphs
        .replace(/^/, '<p>')
        .replace(/$/, '</p>')
        
        // Fix paragraph wrapping around headers
        .replace(/^<p>(<h3>.*?<\/h3>)/gm, '$1<p>')
        .replace(/(<\/h3>)<\/p>/g, '$1')
        
        // Clean up empty paragraphs
        .replace(/<p>\s*<\/p>/g, '')
        .replace(/<p>(<br>\s*)+<\/p>/g, '')
        
        // Fix spacing around numbered items
        .replace(/<p>(<div class="numbered-item">)/g, '$1')
        .replace(/(<\/div>)<\/p>/g, '$1');
    
    // Step 3: Add references section if we have any
    if (references.length > 0) {
        let referencesHtml = '<div class="references-section"><h3>References</h3><ol class="references-list">';
        
        references.forEach(ref => {
            referencesHtml += `<li id="ref-${ref.number}">
                <a href="${ref.url}" target="_blank" class="reference-url">${ref.title}</a>
                <br><span class="reference-full-url">${ref.url}</span>
            </li>`;
        });
        
        referencesHtml += '</ol></div>';
        formattedReport += referencesHtml;
    }
    
    return formattedReport;
}

function extractDomainName(url) {
    try {
        const domain = new URL(url).hostname;
        return domain.replace(/^www\./, '');
    } catch {
        return url;
    }
}

function isLikelyValidUrl(url) {
    try {
        const urlObj = new URL(url);
        
        // Filter out common broken URL patterns
        const invalidPatterns = [
            /\/ref\/abouttx\/ghosts\.html/,  // Broken Texas.gov paths
            /\/webreports\/\[/,               // Broken NUFORC paths with brackets
            /\]\[/,                           // URLs with bracket artifacts
            /\/\[https:/,                     // Malformed nested URLs
            /\s/,                             // URLs with spaces
        ];
        
        // Check for invalid patterns
        for (const pattern of invalidPatterns) {
            if (pattern.test(url)) {
                return false;
            }
        }
        
        // Check for valid domains we trust
        const trustedDomains = [
            'ncei.noaa.gov',
            'timeanddate.com',
            'weather.gov',
            'faa.gov',
            'nasa.gov',
            'nws.noaa.gov',
            'nationalweatherservice.com'
        ];
        
        const domain = urlObj.hostname.replace(/^www\./, '');
        
        // If it's a trusted domain, likely valid
        if (trustedDomains.some(trusted => domain.includes(trusted))) {
            return true;
        }
        
        // Basic URL structure validation
        return urlObj.protocol.startsWith('http') && 
               urlObj.hostname.includes('.') &&
               !urlObj.pathname.includes('[') &&
               !urlObj.pathname.includes(']');
               
    } catch {
        return false;
    }
}

async function validateUrls(urls) {
    // For now, use heuristic validation
    // In a production system, you might want to make HEAD requests
    // to check if URLs are accessible, but that has CORS limitations
    
    const validUrls = [];
    
    for (const url of urls) {
        if (isLikelyValidUrl(url)) {
            validUrls.push(url);
        }
    }
    
    return validUrls;
}

function closeResearchModal() {
    const modal = document.getElementById('research-modal');
    modal.classList.remove('active');
    document.body.style.overflow = '';
}

// Close modal when clicking outside
document.addEventListener('click', function(event) {
    const modal = document.getElementById('research-modal');
    if (event.target === modal) {
        closeResearchModal();
    }
});

// Close modal with Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeResearchModal();
    }
});