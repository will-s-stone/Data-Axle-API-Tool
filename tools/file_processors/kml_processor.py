"""
KML File Processor Module

Handles extracting data from KML files and converting to GeoJSON format.
"""

import os
import json
import logging
from fastkml import KML
from fastkml.utils import find_all
from fastkml import Placemark

logger = logging.getLogger(__name__)


def extract_placemarks_from_kml(kml_file_path):
    """
    Extract placemarks from a KML file.

    Args:
        kml_file_path (str): Path to the KML file

    Returns:
        list: List of fastkml Placemark objects
    """
    logger.info(f"Opening KML file: {kml_file_path}")

    # Check if file exists
    if not os.path.exists(kml_file_path):
        logger.error(f"Error: File {kml_file_path} does not exist")
        return []

    try:
        # Parse the KML file
        with open(kml_file_path, 'rb') as kml_file:
            kml_content = kml_file.read()

        k = KML.parse(kml_content, validate=False)
        placemarks = find_all(k, of_type=Placemark)

        logger.info(f"Found {len(placemarks)} Placemarks in KML")
        return placemarks

    except Exception as e:
        logger.error(f"Error parsing KML file: {e}")
        return []


def get_folder_for_placemark(placemark, kml_doc):
    """
    Get the parent folder for a placemark.

    Args:
        placemark: A fastkml Placemark object
        kml_doc: The KML document

    Returns:
        str: Name of the parent folder or "Root" if none
    """
    # This is a simplified version - fastkml doesn't easily expose the parent-child relationship
    # Might need to traverse the KML structure
    return getattr(placemark, 'parent_name', "Root")


def convert_placemarks_to_info(placemarks):
    """
    Convert fastkml placemarks to a list of dictionaries with placemark information.

    Args:
        placemarks (list): List of fastkml Placemark objects

    Returns:
        list: List of dictionaries with placemark information
    """
    placemark_info = []

    for placemark in placemarks:
        # Get basic information
        name = placemark.name or "Unnamed"
        description = placemark.description or None

        # The parent folder might be accessible
        parent_folder = getattr(placemark, 'parent_name', "Root")

        # Check geometry type
        geometry = placemark.geometry
        geometry_type = geometry.geom_type if geometry else None
        shapely_geometry = None
        coordinates_text = None

        if geometry:
            # Fastkml already gives us Shapely geometries
            shapely_geometry = geometry

            # Extract coordinates as text for compatibility
            if geometry_type == 'Polygon':
                coordinates_text = " ".join([f"{x},{y},{z or 0}" for x, y, z in geometry.exterior.coords])
            elif geometry_type == 'Point':
                coordinates_text = f"{geometry.x},{geometry.y},0"
            elif geometry_type == 'LineString':
                coordinates_text = " ".join([f"{x},{y},{z or 0}" for x, y, z in geometry.coords])

        # Get extended data
        extended_data = {}
        # In fastkml, extended data might be accessible differently
        if hasattr(placemark, 'extended_data') and placemark.extended_data:
            for data in placemark.extended_data:
                extended_data[data.name] = data.value

        # Add to our results
        placemark_info.append({
            'name': name,
            'description': description,
            'parent_folder': parent_folder,
            'geometry_type': geometry_type,
            'coordinates_text': coordinates_text,
            'geometry': shapely_geometry,
            'extended_data': extended_data
        })

    return placemark_info


def export_to_geojson(placemark_info, output_file):
    """Export placemark information to a GeoJSON file"""

    try:
        features = []

        for placemark in placemark_info:
            if placemark['geometry'] is not None:
                # Create a GeoJSON feature
                feature = {
                    "type": "Feature",
                    "geometry": mapping(placemark['geometry']),
                    "properties": {
                        "name": placemark['name'],
                        "description": placemark['description'],
                        "folder": placemark['parent_folder']
                    }
                }

                # Add any extended data as properties
                if placemark['extended_data']:
                    for key, value in placemark['extended_data'].items():
                        feature["properties"][key] = value

                features.append(feature)

        # Create the GeoJSON feature collection
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }

        # Write to file
        with open(output_file, 'w') as f:
            json.dump(geojson, f, indent=2)  # Can set indent=None for smaller files

        logger.info(f"Exported {len(features)} features to {output_file}")
        return True

    except Exception as e:
        logger.error(f"Error exporting to GeoJSON: {e}")
        return False


def parse_folder_structure(kml_file_path):
    """
    Parse the folder structure of a KML file.

    Args:
        kml_file_path (str): Path to the KML file

    Returns:
        dict: Dictionary mapping folder names to lists of placemarks
    """
    # This would be a more complex implementation in a real system
    # For now, we'll just return a simple structure
    placemarks = extract_placemarks_from_kml(kml_file_path)

    folder_structure = {}
    for placemark in placemarks:
        folder = getattr(placemark, 'parent_name', "Root")
        if folder not in folder_structure:
            folder_structure[folder] = []
        folder_structure[folder].append(placemark)

    return folder_structure


def process_file(kml_file_path, geojson_output=None, print_summary=True):
    """
    Process a KML file and optionally export to GeoJSON.

    Args:
        kml_file_path (str): Path to the KML file to process
        geojson_output (str, optional): Path to export GeoJSON file, or None to skip export
        print_summary (bool): Whether to print a summary of the results

    Returns:
        list: List of placemark information dictionaries
    """
    if print_summary:
        logger.info(f"Processing KML file: {kml_file_path}")

    # Extract placemarks from KML
    placemarks = extract_placemarks_from_kml(kml_file_path)

    # Convert to our standard info format
    placemark_info = convert_placemarks_to_info(placemarks)

    if print_summary:
        # Print summary
        logger.info(f"Found {len(placemark_info)} placemarks in KML")

        # Analyze results
        geometry_types = {}
        folder_counts = {}

        for item in placemark_info:
            # Count by geometry type
            geom_type = item['geometry_type']
            geometry_types[geom_type] = geometry_types.get(geom_type, 0) + 1

            # Count by folder
            folder = item['parent_folder']
            folder_counts[folder] = folder_counts.get(folder, 0) + 1

        # Print summaries
        if geometry_types:
            logger.info("Geometry types:")
            for geom_type, count in geometry_types.items():
                logger.info(f"- {geom_type}: {count}")

        if folder_counts:
            logger.info("Folder structure:")
            for folder_name, count in folder_counts.items():
                logger.info(f"- {folder_name}: {count} features")

    # Export to GeoJSON if requested
    if geojson_output:
        export_to_geojson(placemark_info, geojson_output)

    return placemark_info
