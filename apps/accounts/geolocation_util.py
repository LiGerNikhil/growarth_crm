"""
Geolocation utility functions for office premises access control
"""

import math
from typing import Tuple, Optional

# Office premises coordinates (latitude, longitude)
# OFFICE_COORDINATES = {
#     'latitude': 28.585975,
#     'longitude': 77.312637,
# }
OFFICE_COORDINATES = {
    'latitude': 28.5859642,
    'longitude': 77.3126031,
}
# Allowed radius in meters
ALLOWED_RADIUS_METERS = 100

# Roles that can bypass geolocation restrictions
BYPASS_ROLES = ['superadmin', 'admin', 'hr', 'manager', 'team_leader']


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on earth using haversine formula.
    
    Args:
        lat1, lon1: Latitude and longitude of point 1
        lat2, lon2: Latitude and longitude of point 2
    
    Returns:
        Distance in meters
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in meters
    r = 6371000
    
    return c * r


def is_within_office_premises(user_lat: float, user_lon: float) -> Tuple[bool, float]:
    """
    Check if user coordinates are within the allowed radius of office premises.
    
    Args:
        user_lat: User's latitude
        user_lon: User's longitude
    
    Returns:
        Tuple of (is_within_premises, distance_in_meters)
    """
    distance = haversine_distance(
        user_lat, user_lon,
        OFFICE_COORDINATES['latitude'], OFFICE_COORDINATES['longitude']
    )
    
    return distance <= ALLOWED_RADIUS_METERS, distance


def can_bypass_geolocation(user_role: str) -> bool:
    """
    Check if user role can bypass geolocation restrictions.
    
    Args:
        user_role: User's role
    
    Returns:
        True if user can bypass restrictions, False otherwise
    """
    return user_role in BYPASS_ROLES


def get_geolocation_error_message(distance: float) -> str:
    """
    Generate user-friendly error message for geolocation violations.
    
    Args:
        distance: Distance from office in meters
    
    Returns:
        Error message string
    """
    return f"You are not within office premises. You are {distance:.1f} meters away from the office location."


def format_distance_for_display(distance: float) -> str:
    """
    Format distance for display purposes.
    
    Args:
        distance: Distance in meters
    
    Returns:
        Formatted distance string
    """
    if distance < 1000:
        return f"{distance:.1f} meters"
    else:
        return f"{distance/1000:.2f} kilometers"


def validate_coordinates(lat: float, lon: float) -> bool:
    """
    Validate if coordinates are within reasonable bounds.
    
    Args:
        lat: Latitude
        lon: Longitude
    
    Returns:
        True if coordinates are valid, False otherwise
    """
    return -90 <= lat <= 90 and -180 <= lon <= 180


def get_office_coordinates() -> Tuple[float, float]:
    """
    Get office coordinates.
    
    Returns:
        Tuple of (latitude, longitude)
    """
    return OFFICE_COORDINATES['latitude'], OFFICE_COORDINATES['longitude']


def get_allowed_radius() -> int:
    """
    Get allowed radius in meters.
    
    Returns:
        Allowed radius in meters
    """
    return ALLOWED_RADIUS_METERS
