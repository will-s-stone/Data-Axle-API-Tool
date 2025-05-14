"""
Geo Helpers Package

Contains modules for working with geographic data,
particularly focused on polygons and GeoJSON formats.
"""

from .geojson_helper import (
    parse_geojson,
    format_polygon_points,
    get_area_in_square_miles,
    get_area_in_acres,
    get_folders_in_geojson,
    validate_polygon,
    simplify_polygon
)

from .polygon_helper import (
    process_geojson,
    split_polygon,
    extract_named_polygons_to_kml,
    merge_polygons,
    create_buffer_around_polygon,
    check_point_in_polygon
)

__all__ = [
    # From geojson_helper
    'parse_geojson',
    'format_polygon_points',
    'get_area_in_square_miles',
    'get_area_in_acres',
    'get_folders_in_geojson',
    'validate_polygon',
    'simplify_polygon',

    # From polygon_helper
    'process_geojson',
    'split_polygon',
    'extract_named_polygons_to_kml',
    'merge_polygons',
    'create_buffer_around_polygon',
    'check_point_in_polygon'
]