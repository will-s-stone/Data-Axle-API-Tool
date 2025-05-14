"""
Polygon Helper Module

Utilities for working with polygon geometries, including splitting large polygons,
simplifying geometry, and extracting selected polygons.
"""

import json
import copy
import os
import logging
from shapely.geometry import shape, mapping, LineString, Polygon, Point
from shapely.ops import split
import simplekml

# Set up logging
logger = logging.getLogger(__name__)


def count_polygon_points(polygon):
    """
    Count the number of points in a Shapely polygon.

    Args:
        polygon: Shapely polygon object

    Returns:
        int: Number of points in the polygon
    """
    return len(list(polygon.exterior.coords))


def split_polygon(polygon, properties, max_points=500):
    """
    Split a polygon into smaller parts if it exceeds max_points.

    Args:
        polygon: Shapely polygon object
        properties: Properties dictionary to preserve
        max_points: Maximum points allowed per polygon

    Returns:
        list: List of dictionaries with geometry and properties
    """
    if count_polygon_points(polygon) <= max_points:
        return [{
            "type": "Feature",
            "geometry": mapping(polygon),
            "properties": properties
        }]

    # Get polygon bounds
    minx, miny, maxx, maxy = polygon.bounds

    # Determine whether to split horizontally or vertically
    width = maxx - minx
    height = maxy - miny

    if width > height:
        # Split horizontally
        mid_x = minx + width / 2
        divider = LineString([(mid_x, miny - 1), (mid_x, maxy + 1)])
    else:
        # Split vertically
        mid_y = miny + height / 2
        divider = LineString([(minx - 1, mid_y), (maxx + 1, mid_y)])

    # Split the polygon
    try:
        split_polys = split(polygon, divider)

        # Recursively split if still too large
        result = []
        for poly in split_polys.geoms:
            # Ensure we're working with a polygon (not a line or point)
            if poly.geom_type == 'Polygon' and poly.is_valid:
                result.extend(split_polygon(poly, properties, max_points))

        return result
    except Exception as e:
        logger.error(f"Error splitting polygon: {e}")

        # If splitting fails, try to simplify instead as a fallback
        simplified = polygon.simplify(0.0001, preserve_topology=True)
        if count_polygon_points(simplified) <= max_points:
            return [{
                "type": "Feature",
                "geometry": mapping(simplified),
                "properties": properties
            }]
        else:
            # If we still can't get under the limit, force it by reducing points
            coords = list(polygon.exterior.coords)
            step = len(coords) // max_points + 1
            reduced_coords = coords[::step]
            # Ensure it's a closed polygon
            if reduced_coords[0] != reduced_coords[-1]:
                reduced_coords.append(reduced_coords[0])

            reduced_poly = Polygon(reduced_coords)
            return [{
                "type": "Feature",
                "geometry": mapping(reduced_poly),
                "properties": properties
            }]


def process_geojson(input_file, output_file, max_points=500):
    """
    Process a GeoJSON file, splitting polygons that exceed max_points
    while preserving their properties.

    Args:
        input_file: Path to input GeoJSON file
        output_file: Path to output GeoJSON file
        max_points: Maximum points allowed per polygon
    """
    # Read the input GeoJSON
    try:
        with open(input_file, 'r') as f:
            geojson_data = json.load(f)
    except Exception as e:
        logger.error(f"Error reading input GeoJSON {input_file}: {str(e)}")
        raise

    # Create the GeoJSON feature collection
    output_geojson = {
        "type": "FeatureCollection",
        "features": []
    }

    # Process each feature
    for feature in geojson_data['features']:
        geometry = feature['geometry']
        properties = feature['properties']

        # Skip non-polygon geometries
        if geometry['type'] not in ['Polygon', 'MultiPolygon']:
            output_geojson['features'].append(feature)
            continue

        # Convert to shapely geometry
        shapely_geom = shape(geometry)

        # Handle MultiPolygon
        if geometry['type'] == 'MultiPolygon':
            for poly in shapely_geom.geoms:
                # Process each polygon in the MultiPolygon
                split_features = split_polygon(poly, properties, max_points)
                output_geojson['features'].extend(split_features)
        else:
            # Process single Polygon
            split_features = split_polygon(shapely_geom, properties, max_points)
            output_geojson['features'].extend(split_features)

    # Write the output GeoJSON
    try:
        with open(output_file, 'w') as f:
            json.dump(output_geojson, f, indent=2)  # Can set indent=None for smaller output
    except Exception as e:
        logger.error(f"Error writing output GeoJSON {output_file}: {str(e)}")
        raise

    # Count and report results
    input_count = len(geojson_data['features'])
    output_count = len(output_geojson['features'])

    logger.info(f"Processed {input_count} features into {output_count} features")
    logger.info(f"Output saved to {output_file}")

    return output_count


def extract_named_polygons_to_kml(geojson_file, name_property, property_value, output_dir="kml_output"):
    """
    Extract polygons with a specific name property and save each to a KML file.

    Args:
        geojson_file: Path to the GeoJSON file
        name_property: The property name to filter on (e.g., 'name', 'NAME', 'title')
        property_value: The value to match (exact match)
        output_dir: Directory to save the KML files
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Read the GeoJSON file
    try:
        with open(geojson_file, 'r') as f:
            geojson_data = json.load(f)
    except Exception as e:
        logger.error(f"Error reading GeoJSON for extraction {geojson_file}: {str(e)}")
        raise

    # Filter features that match the name property
    matching_features = []
    for feature in geojson_data['features']:
        properties = feature.get('properties', {})
        if properties.get(name_property) == property_value:
            matching_features.append(feature)

    logger.info(f"Found {len(matching_features)} polygons with {name_property}='{property_value}'")

    # Create a KML file for each matching feature
    for i, feature in enumerate(matching_features):
        kml = simplekml.Kml()

        # Create a safe filename
        safe_name = property_value.replace(" ", "_").replace("/", "_").replace("\\", "_")
        filename = f"{safe_name}_{i + 1}.kml"
        filepath = os.path.join(output_dir, filename)

        # Get the geometry
        geometry = feature['geometry']
        properties = feature['properties']

        # Extract coordinates based on geometry type
        if geometry['type'] == 'Polygon':
            coords = geometry['coordinates'][0]  # Outer ring

            # Create polygon in KML
            pol = kml.newpolygon(name=f"{property_value} {i + 1}")
            pol.outerboundaryis = coords

            # Add properties as description
            description = "Properties:\n"
            for key, value in properties.items():
                description += f"{key}: {value}\n"
            pol.description = description

        elif geometry['type'] == 'MultiPolygon':
            # For MultiPolygon, create multiple polygons in the same KML
            for j, polygon in enumerate(geometry['coordinates']):
                coords = polygon[0]  # Outer ring of each polygon

                # Create polygon in KML
                pol = kml.newpolygon(name=f"{property_value} {i + 1}.{j + 1}")
                pol.outerboundaryis = coords

                # Add properties as description
                description = "Properties:\n"
                for key, value in properties.items():
                    description += f"{key}: {value}\n"
                pol.description = description

        # Save the KML file
        kml.save(filepath)
        logger.info(f"Saved KML file: {filepath}")

    logger.info(f"Extracted {len(matching_features)} polygons to KML files in {output_dir}")
    return len(matching_features)


def merge_polygons(polygons):
    """
    Merge multiple polygons into a single polygon.

    Args:
        polygons (list): List of Shapely polygon objects

    Returns:
        Polygon: Merged polygon
    """
    if not polygons:
        return None

    if len(polygons) == 1:
        return polygons[0]

    # Union all polygons
    result = polygons[0]
    for poly in polygons[1:]:
        result = result.union(poly)

    return result


def create_buffer_around_polygon(polygon, buffer_distance):
    """
    Create a buffer around a polygon.

    Args:
        polygon (Polygon): Shapely polygon object
        buffer_distance (float): Distance to buffer in degrees

    Returns:
        Polygon: Buffered polygon
    """
    return polygon.buffer(buffer_distance)


def check_point_in_polygon(point, polygon):
    """
    Check if a point is inside a polygon.

    Args:
        point (tuple): Point coordinates (lon, lat)
        polygon (Polygon): Shapely polygon object

    Returns:
        bool: True if point is in polygon, False otherwise
    """
    point_obj = Point(point)
    return polygon.contains(point_obj)