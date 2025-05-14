"""
GeoJSON Helper Module

Utilities for working with GeoJSON files, specifically for the Data Axle API.
Handles formatting polygons in the right format for API requests.
"""

import json
import logging
from shapely.geometry import Polygon
import pyproj
from shapely.ops import transform
from functools import partial

# Set up logging
logger = logging.getLogger(__name__)


def format_polygon_points(coordinates):
    """
    Format polygon coordinates from GeoJSON format to the required format for Data Axle API.

    Args:
        coordinates (list): GeoJSON coordinates in format [lon, lat]

    Returns:
        list: List of dictionaries in format {"lat": lat, "lon": lon}
    """
    formatted_points = []

    # GeoJSON polygons can have multiple rings (exterior and holes)
    # We'll assume we want the first ring (exterior) for simplicity
    if coordinates and len(coordinates) > 0:
        # Get the first ring
        ring = coordinates[0]

        # Process each point in the ring
        previous_point = None
        for point in ring:
            # GeoJSON stores coordinates as [lon, lat]
            # Convert to {"lat": lat, "lon": lon}
            formatted_point = {
                "lat": point[1],
                "lon": point[0]
            }

            # Avoid duplicate consecutive points (can cause API issues)
            if previous_point is None or previous_point != point:
                formatted_points.append(formatted_point)
            previous_point = point

    return formatted_points


def parse_geojson(file_path):
    """
    Parse a GeoJSON file and format polygon points for API requests.

    Args:
        file_path (str): Path to the GeoJSON file

    Returns:
        list: List of dictionaries with polygon metadata and formatted points
    """
    # Read the GeoJSON file
    try:
        with open(file_path, 'r') as f:
            geojson_data = json.load(f)
    except Exception as e:
        logger.error(f"Error reading GeoJSON file {file_path}: {str(e)}")
        raise

    results = []

    # Process each feature in the GeoJSON
    for feature in geojson_data.get('features', []):
        # Get properties
        properties = feature.get('properties', {})
        name = properties.get('name', 'Unnamed')
        folder = properties.get('folder', 'No folder')

        # Print requested attributes (for debugging)
        logger.debug(f"Name: {name}")
        logger.debug(f"Folder: {folder}")

        # Get geometry
        geometry = feature.get('geometry', {})
        geom_type = geometry.get('type', '')
        coordinates = geometry.get('coordinates', [])

        # Process the geometry if it's a Polygon
        if geom_type == 'Polygon':
            formatted_points = format_polygon_points(coordinates)

            # Create a new entry for each polygon with its metadata
            polygon_entry = {
                "name": name,
                "folder": folder,
                "points": formatted_points
            }

            # Add this entry to our results list
            results.append(polygon_entry)

            logger.debug(f"Formatted {len(formatted_points)} points for {name}")
        else:
            logger.debug(f"Skipping non-polygon geometry type: {geom_type}")

    logger.info(f"Processed {len(results)} polygons from GeoJSON")
    return results


def get_area_in_square_miles(json_polygon):
    """
    Calculate the area of a polygon in square miles.

    Args:
        json_polygon (list): List of points in {"lat": lat, "lon": lon} format

    Returns:
        float: Area in square miles
    """
    try:
        coords = [(point['lon'], point['lat']) for point in json_polygon]
        polygon = Polygon(coords)

        # Define the projection transformation
        # Using UTM zone 18N (appropriate for Eastern Pennsylvania) as in your original code
        project = pyproj.Transformer.from_crs(
            "EPSG:4326",  # WGS84 (standard lat/lon)
            "EPSG:32618",  # UTM zone 18N
            always_xy=True
        )

        # Apply the projection
        transformed_polygon = transform(
            project.transform,
            polygon
        )

        # Calculate area
        area_square_meters = transformed_polygon.area
        area_square_miles = area_square_meters / 2589988  # Convert to square miles

        return area_square_miles
    except Exception as e:
        logger.error(f"Error calculating area: {str(e)}")
        return 0


def get_area_in_acres(json_polygon):
    """
    Calculate the area of a polygon in acres.

    Args:
        json_polygon (list): List of points in {"lat": lat, "lon": lon} format

    Returns:
        float: Area in acres
    """
    try:
        coords = [(point['lon'], point['lat']) for point in json_polygon]
        polygon = Polygon(coords)

        # Define the projection transformation
        project = pyproj.Transformer.from_crs(
            "EPSG:4326",  # WGS84 (standard lat/lon)
            "EPSG:32618",  # UTM zone 18N
            always_xy=True
        )

        # Apply the projection
        transformed_polygon = transform(
            project.transform,
            polygon
        )

        # Calculate area
        area_square_meters = transformed_polygon.area
        area_square_feet = area_square_meters * 10.7639  # Convert to square feet
        area_acres = area_square_feet / 43560  # Convert to acres

        return area_acres
    except Exception as e:
        logger.error(f"Error calculating area in acres: {str(e)}")
        return 0


def get_folders_in_geojson(file_path):
    """
    Extract all unique folder names from a GeoJSON file.

    Args:
        file_path (str): Path to the GeoJSON file

    Returns:
        list: List of unique folder names
    """
    try:
        with open(file_path, 'r') as f:
            geojson_data = json.load(f)
    except Exception as e:
        logger.error(f"Error reading GeoJSON file for folders {file_path}: {str(e)}")
        raise

    folders = []

    for feature in geojson_data.get('features', []):
        properties = feature.get('properties', {})
        folder = properties.get('folder', 'No folder')
        if folder not in folders:
            folders.append(folder)

    logger.info(f"Found {len(folders)} unique folders in GeoJSON")
    return folders


def validate_polygon(points):
    """
    Validate if a polygon is properly formed for API requests.

    Args:
        points (list): List of points in {"lat": lat, "lon": lon} format

    Returns:
        tuple: (is_valid, error_message)
    """
    if not points:
        return False, "Empty polygon"

    if len(points) < 3:
        return False, f"Polygon has only {len(points)} points, minimum 3 required"

    # Check if the first and last points match (closed polygon)
    if points[0] != points[-1]:
        # This is just a warning, API might accept open polygons
        logger.warning("Polygon is not closed (first and last points differ)")

    # Check for valid coordinates
    for i, point in enumerate(points):
        if 'lat' not in point or 'lon' not in point:
            return False, f"Point {i} missing lat/lon properties"

        lat, lon = point['lat'], point['lon']

        # Basic geo-coordinate validation
        if not (-90 <= lat <= 90):
            return False, f"Invalid latitude at point {i}: {lat}"

        if not (-180 <= lon <= 180):
            return False, f"Invalid longitude at point {i}: {lon}"

    # Check for self-intersection using Shapely
    try:
        coords = [(point['lon'], point['lat']) for point in points]
        polygon = Polygon(coords)
        if not polygon.is_valid:
            return False, "Polygon is self-intersecting or has other topological errors"
    except Exception as e:
        logger.warning(f"Could not validate polygon topology: {str(e)}")

    return True, ""


def simplify_polygon(points, tolerance=0.0001):
    """
    Simplify a polygon to reduce the number of points while preserving shape.
    Useful for complex polygons that may exceed API limits.

    Args:
        points (list): List of points in {"lat": lat, "lon": lon} format
        tolerance (float): Tolerance for simplification (higher = more simplification)

    Returns:
        list: Simplified list of points in {"lat": lat, "lon": lon} format
    """
    try:
        # Convert to shapely format
        coords = [(point['lon'], point['lat']) for point in points]
        polygon = Polygon(coords)

        # Simplify the polygon
        simplified = polygon.simplify(tolerance, preserve_topology=True)

        # Convert back to API format
        result = []
        for x, y in simplified.exterior.coords:
            result.append({"lat": y, "lon": x})

        logger.info(f"Simplified polygon from {len(points)} to {len(result)} points")
        return result
    except Exception as e:
        logger.error(f"Error simplifying polygon: {str(e)}")
        return points  # Return original points if simplification fails
