"""
Geo Utility Functions

Helpers for common geographic calculations and operations.
"""

import math
import logging

logger = logging.getLogger(__name__)


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on Earth.

    Args:
        lat1 (float): Latitude of first point in degrees
        lon1 (float): Longitude of first point in degrees
        lat2 (float): Latitude of second point in degrees
        lon2 (float): Longitude of second point in degrees

    Returns:
        float: Distance in kilometers
    """
    try:
        # Convert latitude and longitude from degrees to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # Haversine formula
        dlon = lon2_rad - lon1_rad
        dlat = lat2_rad - lat1_rad
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        # Earth radius in kilometers
        earth_radius = 6371.0

        # Calculate the distance
        distance = earth_radius * c

        return distance
    except Exception as e:
        logger.error(f"Error calculating haversine distance: {str(e)}")
        return None


def degrees_to_meters(delta_lat, delta_lon, reference_lat):
    """
    Convert a change in latitude and longitude (in degrees) to meters.

    Args:
        delta_lat (float): Change in latitude in degrees
        delta_lon (float): Change in longitude in degrees
        reference_lat (float): Reference latitude in degrees

    Returns:
        tuple: (meters_north, meters_east)
    """
    try:
        # Earth's radius in meters
        earth_radius = 6371000

        # Convert degrees to radians
        ref_lat_rad = math.radians(reference_lat)

        # Calculate meters per degree of latitude and longitude
        meters_per_degree_lat = earth_radius * math.pi / 180
        meters_per_degree_lon = earth_radius * math.cos(ref_lat_rad) * math.pi / 180

        # Calculate meters north and east
        meters_north = delta_lat * meters_per_degree_lat
        meters_east = delta_lon * meters_per_degree_lon

        return (meters_north, meters_east)
    except Exception as e:
        logger.error(f"Error converting degrees to meters: {str(e)}")
        return (None, None)


def meters_to_acres(square_meters):
    """
    Convert square meters to acres.

    Args:
        square_meters (float): Area in square meters

    Returns:
        float: Area in acres
    """
    try:
        # 1 acre = 4046.86 square meters
        return square_meters / 4046.86
    except Exception as e:
        logger.error(f"Error converting square meters to acres: {str(e)}")
        return None


def get_centroid(points):
    """
    Calculate the centroid of a set of points.

    Args:
        points (list): List of points in format [{'lat': lat, 'lon': lon}, ...]

    Returns:
        dict: Centroid point {'lat': lat, 'lon': lon}
    """
    try:
        if not points:
            return None

        # Sum up coordinates
        lat_sum = 0
        lon_sum = 0

        for point in points:
            lat_sum += point['lat']
            lon_sum += point['lon']

        # Calculate average
        count = len(points)
        centroid = {
            'lat': lat_sum / count,
            'lon': lon_sum / count
        }

        return centroid
    except Exception as e:
        logger.error(f"Error calculating centroid: {str(e)}")
        return None


def format_coordinates_for_display(lat, lon, format_type="decimal"):
    """
    Format coordinates for display in various formats.

    Args:
        lat (float): Latitude in decimal degrees
        lon (float): Longitude in decimal degrees
        format_type (str): Format type ('decimal', 'dms' for degrees-minutes-seconds)

    Returns:
        str: Formatted coordinates string
    """
    try:
        if format_type == "decimal":
            return f"{lat:.6f}, {lon:.6f}"
        elif format_type == "dms":
            # Convert decimal degrees to degrees, minutes, seconds
            def decimal_to_dms(coord):
                # Get the degrees
                degrees = int(coord)
                # Get the minutes
                minutes_decimal = abs(coord - degrees) * 60
                minutes = int(minutes_decimal)
                # Get the seconds
                seconds = (minutes_decimal - minutes) * 60
                return (degrees, minutes, seconds)

            lat_dms = decimal_to_dms(lat)
            lon_dms = decimal_to_dms(lon)

            # Format DMS
            lat_dir = "N" if lat >= 0 else "S"
            lon_dir = "E" if lon >= 0 else "W"

            return f"{abs(lat_dms[0])}°{lat_dms[1]}'{lat_dms[2]:.2f}\"{lat_dir}, {abs(lon_dms[0])}°{lon_dms[1]}'{lon_dms[2]:.2f}\"{lon_dir}"
        else:
            return f"{lat}, {lon}"
    except Exception as e:
        logger.error(f"Error formatting coordinates for display: {str(e)}")
        return f"{lat}, {lon}"


def is_point_in_polygon(point, polygon_points):
    """
    Check if a point is inside a polygon using the ray casting algorithm.

    Args:
        point (dict): Point in format {'lat': lat, 'lon': lon}
        polygon_points (list): List of points defining the polygon in format [{'lat': lat, 'lon': lon}, ...]

    Returns:
        bool: True if point is inside polygon
    """
    try:
        # Implementation of ray casting algorithm
        x, y = point['lon'], point['lat']
        n = len(polygon_points)
        inside = False

        p1x, p1y = polygon_points[0]['lon'], polygon_points[0]['lat']
        for i in range(n + 1):
            p2x, p2y = polygon_points[i % n]['lon'], polygon_points[i % n]['lat']
            if y > min(p1y, p2y) and y <= max(p1y, p2y) and x <= max(p1x, p2x):
                if p1y != p2y:
                    xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                if p1x == p2x or x <= xinters:
                    inside = not inside
            p1x, p1y = p2x, p2y

        return inside
    except Exception as e:
        logger.error(f"Error checking if point is in polygon: {str(e)}")
        return False


def bounding_box_from_points(points):
    """
    Calculate the bounding box for a set of points.

    Args:
        points (list): List of points in format [{'lat': lat, 'lon': lon}, ...]

    Returns:
        dict: Bounding box as {'min_lat': min_lat, 'min_lon': min_lon, 'max_lat': max_lat, 'max_lon': max_lon}
    """
    try:
        if not points:
            return None

        # Initialize with first point
        min_lat = max_lat = points[0]['lat']
        min_lon = max_lon = points[0]['lon']

        # Find min and max values
        for point in points:
            min_lat = min(min_lat, point['lat'])
            max_lat = max(max_lat, point['lat'])
            min_lon = min(min_lon, point['lon'])
            max_lon = max(max_lon, point['lon'])

        return {
            'min_lat': min_lat,
            'min_lon': min_lon,
            'max_lat': max_lat,
            'max_lon': max_lon
        }
    except Exception as e:
        logger.error(f"Error calculating bounding box: {str(e)}")
        return None