"""
KMZ File Processor Module

Handles extracting data from KMZ files and converting to GeoJSON format.
"""

from zipfile import ZipFile
import xml.etree.ElementTree as ET
import os
import re
import json
import logging
from shapely.geometry import Polygon, Point, LineString, MultiPolygon, mapping

logger = logging.getLogger(__name__)


def find_elements(element, xpath, namespaces):
    """Helper function to find elements using XPath with namespaces"""
    return element.findall(xpath, namespaces)


def find_element(element, xpath, namespaces):
    """Helper function to find a single element using XPath with namespaces"""
    elements = element.findall(xpath, namespaces)
    return elements[0] if elements else None


def find_parent_folder(placemark, root, namespaces):
    """Find the parent folder of a placemark"""
    # Find all folders in the document
    folders = find_elements(root, './/kml:Folder', namespaces)

    for folder in folders:
        # Check if this placemark is a direct child of this folder
        placemarks = find_elements(folder, './kml:Placemark', namespaces)
        for p in placemarks:
            if p == placemark:
                name_elem = find_element(folder, './kml:name', namespaces)
                return name_elem.text if name_elem is not None else "Unnamed Folder"

    # If placemark isn't in any folder, check if it's in the document
    document = find_element(root, './kml:Document', namespaces)
    if document is not None:
        placemarks = find_elements(document, './kml:Placemark', namespaces)
        for p in placemarks:
            if p == placemark:
                name_elem = find_element(document, './kml:name', namespaces)
                return name_elem.text if name_elem is not None else "Document"

    return "Root"


def parse_polygon_coords(coordinates_text):
    """Parse KML polygon coordinates into a Shapely Polygon"""

    try:
        # Split the coordinate string into individual points
        coords_text = coordinates_text.strip()
        if not coords_text:
            return None

        point_texts = coords_text.split()

        # Parse each point into a (lon, lat, [alt]) tuple
        points = []
        for pt in point_texts:
            if not pt.strip():
                continue

            parts = pt.split(',')
            if len(parts) >= 2:
                lon = float(parts[0])
                lat = float(parts[1])
                points.append((lon, lat))

        # Create a Shapely Polygon
        if len(points) >= 3:
            # Check if first and last points are the same (closed polygon)
            if points[0] != points[-1]:
                points.append(points[0])  # Close the polygon if needed

            return Polygon(points)

        return None

    except Exception as e:
        logger.error(f"Error parsing polygon coordinates: {e}")
        return None


def parse_point_coords(coordinates_text):
    """Parse KML point coordinates into a Shapely Point"""

    try:
        coords_text = coordinates_text.strip()
        if not coords_text:
            return None

        parts = coords_text.split(',')
        if len(parts) >= 2:
            lon = float(parts[0])
            lat = float(parts[1])
            return Point(lon, lat)

        return None

    except Exception as e:
        logger.error(f"Error parsing point coordinates: {e}")
        return None


def parse_linestring_coords(coordinates_text):
    """Parse KML linestring coordinates into a Shapely LineString"""

    try:
        coords_text = coordinates_text.strip()
        if not coords_text:
            return None

        point_texts = coords_text.split()

        points = []
        for pt in point_texts:
            if not pt.strip():
                continue

            parts = pt.split(',')
            if len(parts) >= 2:
                lon = float(parts[0])
                lat = float(parts[1])
                points.append((lon, lat))

        if len(points) >= 2:
            return LineString(points)

        return None

    except Exception as e:
        logger.error(f"Error parsing linestring coordinates: {e}")
        return None


def extract_placemarks_from_kmz(kmz_file_path):
    """
    Process a KMZ file and extract all placemarks with their geometries.
    Returns a list of dictionaries with placemark information.
    """
    logger.info(f"Opening KMZ file: {kmz_file_path}")

    # Check if file exists
    if not os.path.exists(kmz_file_path):
        logger.error(f"Error: File {kmz_file_path} does not exist")
        return []

    # Open KMZ and extract KML content
    kmz = ZipFile(kmz_file_path, "r")
    kml_files = [f for f in kmz.namelist() if f.endswith('.kml')]

    if not kml_files:
        logger.error("Error: No KML files found in the KMZ")
        return []

    kml_file = kml_files[0]
    logger.info(f"Using KML file: {kml_file}")

    kml_content = kmz.open(kml_file, "r").read()
    kml_content_str = kml_content.decode('utf-8')

    # Fix any namespace prefixes in attribute values
    kml_content_str = re.sub(r'type="xsd:(\w+)"', r'type="\1"', kml_content_str)

    # Parse the KML using ElementTree
    logger.info("Parsing KML...")

    # Define namespaces used in KML
    namespaces = {
        'kml': 'http://www.opengis.net/kml/2.2',
        'gx': 'http://www.google.com/kml/ext/2.2'
    }

    # Parse the XML
    root = ET.fromstring(kml_content_str)

    # Find all Placemarks (these typically contain geometries)
    placemarks = find_elements(root, './/kml:Placemark', namespaces)
    logger.info(f"Found {len(placemarks)} Placemarks")

    # Extract information from each placemark
    placemark_info = []

    for placemark in placemarks:
        # Get name and parent folder
        name_elem = find_element(placemark, './kml:name', namespaces)
        name = name_elem.text if name_elem is not None else "Unnamed"

        # Get description
        desc_elem = find_element(placemark, './kml:description', namespaces)
        description = desc_elem.text if desc_elem is not None else None

        parent_folder = find_parent_folder(placemark, root, namespaces)

        # Extract geometry elements
        polygon = find_element(placemark, './/kml:Polygon', namespaces)
        point = find_element(placemark, './/kml:Point', namespaces)
        linestring = find_element(placemark, './/kml:LineString', namespaces)
        multigeometry = find_element(placemark, './/kml:MultiGeometry', namespaces)

        # Determine geometry type and extract coordinates
        geometry_type = None
        coordinates_text = None
        shapely_geometry = None

        if polygon is not None:
            geometry_type = "Polygon"
            coords_elem = find_element(polygon, './/kml:coordinates', namespaces)
            if coords_elem is not None:
                coordinates_text = coords_elem.text
                shapely_geometry = parse_polygon_coords(coordinates_text)

        elif point is not None:
            geometry_type = "Point"
            coords_elem = find_element(point, './kml:coordinates', namespaces)
            if coords_elem is not None:
                coordinates_text = coords_elem.text
                shapely_geometry = parse_point_coords(coordinates_text)

        elif linestring is not None:
            geometry_type = "LineString"
            coords_elem = find_element(linestring, './kml:coordinates', namespaces)
            if coords_elem is not None:
                coordinates_text = coords_elem.text
                shapely_geometry = parse_linestring_coords(coordinates_text)

        elif multigeometry is not None:
            geometry_type = "MultiGeometry"
            polygons = find_elements(multigeometry, './/kml:Polygon', namespaces)
            if polygons:
                multi_polys = []
                for poly in polygons:
                    coords_elem = find_element(poly, './/kml:coordinates', namespaces)
                    if coords_elem is not None:
                        poly_geom = parse_polygon_coords(coords_elem.text)
                        if poly_geom:
                            multi_polys.append(poly_geom)

                if multi_polys:
                    shapely_geometry = MultiPolygon(multi_polys)

        # Get any extended data
        extended_data = {}
        ext_data_elem = find_element(placemark, './kml:ExtendedData', namespaces)
        if ext_data_elem is not None:
            data_elems = find_elements(ext_data_elem, './kml:Data', namespaces)
            for data_elem in data_elems:
                name_attr = data_elem.get('name')
                value_elem = find_element(data_elem, './kml:value', namespaces)
                if name_attr and value_elem is not None and value_elem.text:
                    extended_data[name_attr] = value_elem.text

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
    """Export extracted placemarks to a GeoJSON file"""

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


def process_file(kmz_file_path, geojson_output=None, print_summary=True):
    """
    Process a KMZ file and optionally export to GeoJSON.

    Args:
        kmz_file_path (str): Path to the KMZ file to process
        geojson_output (str, optional): Path to export GeoJSON file, or None to skip export
        print_summary (bool): Whether to print a summary of the results

    Returns:
        list: List of placemark information dictionaries
    """
    if print_summary:
        logger.info(f"Processing KMZ file: {kmz_file_path}")

    # Process the KMZ file
    placemark_info = extract_placemarks_from_kmz(kmz_file_path)

    if print_summary:
        # Print summary
        logger.info(f"Found {len(placemark_info)} placemarks in KMZ")

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
