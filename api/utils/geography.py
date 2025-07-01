"""Geographic utility functions for coordinate-based operations."""

from typing import Optional, Tuple


def get_state_from_coordinates(latitude: float, longitude: float) -> Optional[str]:
    """
    Determine US state code from latitude/longitude coordinates.
    Returns None if coordinates are outside the US.
    
    Args:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        
    Returns:
        Two-letter US state code or None if not in US
    """
    # Check if coordinates are within US bounds (including Alaska and Hawaii)
    if not is_coordinates_in_us(latitude, longitude):
        return None
    
    # State boundary definitions (simplified bounding boxes)
    # Format: (min_lat, max_lat, min_lon, max_lon)
    state_bounds = {
        'AL': (30.2, 35.0, -88.5, -84.9),      # Alabama
        'AK': (54.0, 71.4, -179.0, -129.0),   # Alaska
        'AZ': (31.3, 37.0, -114.8, -109.0),   # Arizona
        'AR': (33.0, 36.5, -94.6, -89.6),     # Arkansas
        'CA': (32.5, 42.0, -124.4, -114.1),   # California
        'CO': (37.0, 41.0, -109.1, -102.0),   # Colorado
        'CT': (40.9, 42.1, -73.7, -71.8),     # Connecticut
        'DE': (38.4, 39.8, -75.8, -75.0),     # Delaware
        'FL': (24.5, 31.0, -87.6, -80.0),     # Florida
        'GA': (30.4, 35.0, -85.6, -80.8),     # Georgia
        'HI': (18.9, 22.2, -160.2, -154.8),   # Hawaii
        'ID': (42.0, 49.0, -117.2, -111.0),   # Idaho
        'IL': (37.0, 42.5, -91.5, -87.0),     # Illinois
        'IN': (37.8, 41.8, -88.1, -84.8),     # Indiana
        'IA': (40.4, 43.5, -96.6, -90.1),     # Iowa
        'KS': (37.0, 40.0, -102.1, -94.6),    # Kansas
        'KY': (36.5, 39.1, -89.6, -82.0),     # Kentucky
        'LA': (28.9, 33.0, -94.0, -88.8),     # Louisiana
        'ME': (43.1, 47.5, -71.1, -66.9),     # Maine
        'MD': (37.9, 39.7, -79.5, -75.0),     # Maryland
        'MA': (41.2, 42.9, -73.5, -69.9),     # Massachusetts
        'MI': (41.7, 48.3, -90.4, -82.4),     # Michigan
        'MN': (43.5, 49.4, -97.2, -89.5),     # Minnesota
        'MS': (30.2, 35.0, -91.7, -88.1),     # Mississippi
        'MO': (36.0, 40.6, -95.8, -89.1),     # Missouri
        'MT': (45.0, 49.0, -116.1, -104.0),   # Montana
        'NE': (40.0, 43.0, -104.1, -95.3),    # Nebraska
        'NV': (35.0, 42.0, -120.0, -114.0),   # Nevada
        'NH': (42.7, 45.3, -72.6, -70.6),     # New Hampshire
        'NJ': (38.9, 41.4, -75.6, -73.9),     # New Jersey
        'NM': (31.3, 37.0, -109.1, -103.0),   # New Mexico
        'NY': (40.5, 45.0, -79.8, -71.9),     # New York
        'NC': (33.8, 36.6, -84.3, -75.5),     # North Carolina
        'ND': (45.9, 49.0, -104.1, -96.6),    # North Dakota
        'OH': (38.4, 42.3, -84.8, -80.5),     # Ohio
        'OK': (33.6, 37.0, -103.0, -94.4),    # Oklahoma
        'OR': (42.0, 46.3, -124.6, -116.5),   # Oregon
        'PA': (39.7, 42.5, -80.5, -74.7),     # Pennsylvania
        'RI': (41.1, 42.0, -71.9, -71.1),     # Rhode Island
        'SC': (32.0, 35.2, -83.4, -78.5),     # South Carolina
        'SD': (42.5, 45.9, -104.1, -96.4),    # South Dakota
        'TN': (35.0, 36.7, -90.3, -81.6),     # Tennessee
        'TX': (25.8, 36.5, -106.6, -93.5),    # Texas
        'UT': (37.0, 42.0, -114.1, -109.0),   # Utah
        'VT': (42.7, 45.0, -73.4, -71.5),     # Vermont
        'VA': (36.5, 39.5, -83.7, -75.2),     # Virginia
        'WA': (45.5, 49.0, -124.8, -116.9),   # Washington
        'WV': (37.2, 40.6, -82.6, -77.7),     # West Virginia
        'WI': (42.5, 47.1, -92.9, -86.8),     # Wisconsin
        'WY': (41.0, 45.0, -111.1, -104.0),   # Wyoming
        'DC': (38.8, 38.9, -77.1, -76.9),     # District of Columbia
    }
    
    # Find the state that contains these coordinates
    for state_code, (min_lat, max_lat, min_lon, max_lon) in state_bounds.items():
        if (min_lat <= latitude <= max_lat and 
            min_lon <= longitude <= max_lon):
            return state_code
    
    # If no state found but coordinates are in US, return None
    # This handles territories or edge cases
    return None


def is_coordinates_in_us(latitude: float, longitude: float) -> bool:
    """
    Check if coordinates are within US boundaries (including Alaska and Hawaii).
    
    Args:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        
    Returns:
        True if coordinates are in US territory
    """
    # Continental US bounds
    if (24.5 <= latitude <= 49.4 and -125.0 <= longitude <= -66.9):
        return True
    
    # Alaska bounds
    if (54.0 <= latitude <= 71.4 and -179.0 <= longitude <= -129.0):
        return True
    
    # Hawaii bounds
    if (18.9 <= latitude <= 22.2 and -160.2 <= longitude <= -154.8):
        return True
    
    # US territories (simplified)
    # Puerto Rico
    if (17.9 <= latitude <= 18.5 and -67.3 <= longitude <= -65.2):
        return True
    
    # US Virgin Islands
    if (17.7 <= latitude <= 18.4 and -65.1 <= longitude <= -64.6):
        return True
    
    # American Samoa
    if (-14.4 <= latitude <= -14.1 and -171.1 <= longitude <= -169.4):
        return True
    
    # Guam
    if (13.2 <= latitude <= 13.7 and 144.6 <= longitude <= 145.0):
        return True
    
    return False


def correct_state_from_coordinates(latitude: float, longitude: float, 
                                 current_state: Optional[str]) -> Optional[str]:
    """
    Correct state assignment based on coordinates.
    
    Args:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        current_state: Current state assignment from data
        
    Returns:
        Corrected state code or None if international
    """
    # Get state from coordinates
    coord_state = get_state_from_coordinates(latitude, longitude)
    
    # If coordinates are outside US, mark as international (None)
    if not is_coordinates_in_us(latitude, longitude):
        return None
    
    # If coordinates indicate a specific US state, use that
    if coord_state:
        return coord_state
    
    # If coordinates are in US but no specific state found,
    # check if current_state is a valid 2-letter US state code
    if current_state and len(current_state) == 2 and current_state.isalpha():
        # Could be a territory or edge case - keep original if it's US format
        return current_state.upper()
    
    # Default to None (international) if can't determine
    return None