"""
Utils Package

Collection of utility functions used across the application.
"""

# Import key functions for easier access
from .file_utils import (
    ensure_directory_exists,
    safe_file_write,
    safe_file_read,
    get_file_extension,
    list_files_by_extension
)

from .date_utils import (
    format_timestamp,
    get_current_datetime_string,
    parse_date_string,
    get_date_range
)

from .format_utils import (
    format_currency,
    format_percentage,
    format_number_with_commas,
    format_coordinates,
    truncate_string,
    format_area
)

from .error_utils import (
    log_exception,
    handle_api_error,
    format_error_message,
    create_error_response
)

from .geo_utils import (
    haversine_distance,
    degrees_to_meters,
    meters_to_acres,
    get_centroid,
    format_coordinates_for_display
)

from .api_utils import (
    retry_api_call,
    cache_api_result,
    format_api_request,
    parse_api_response
)

# Export all key functions for easier imports
__all__ = [
    # File Utils
    'ensure_directory_exists',
    'safe_file_write',
    'safe_file_read',
    'get_file_extension',
    'list_files_by_extension',

    # Date Utils
    'format_timestamp',
    'get_current_datetime_string',
    'parse_date_string',
    'get_date_range',

    # Format Utils
    'format_currency',
    'format_percentage',
    'format_number_with_commas',
    'format_coordinates',
    'truncate_string',
    'format_area',

    # Error Utils
    'log_exception',
    'handle_api_error',
    'format_error_message',
    'create_error_response',

    # Geo Utils
    'haversine_distance',
    'degrees_to_meters',
    'meters_to_acres',
    'get_centroid',
    'format_coordinates_for_display',

    # API Utils
    'retry_api_call',
    'cache_api_result',
    'format_api_request',
    'parse_api_response'
]