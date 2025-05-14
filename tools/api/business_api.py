import logging
import time
from .base_api import make_request, get_base_urls

logger = logging.getLogger(__name__)


# URL constants
def get_insights_url():
    """Get the URL for the business insights endpoint."""
    return f"{get_base_urls()['places']}/insights"


def get_scan_url():
    """Get the URL for the business scan endpoint."""
    return f"{get_base_urls()['places']}/scan"


def get_business_count(polygon_json):
    """
    Get the count of businesses within a polygon.

    Args:
        polygon_json (list): List of lat/lon points defining a polygon

    Returns:
        int: Number of businesses in the polygon, or 0 if error
    """
    payload = {
        "filter": {
            "relation": "geo_polygon",
            "value": polygon_json
        },
        "insights": {
            "field": "legal_name",
            "calculations": ["fill_count"]
        }
    }

    response = make_request("GET", get_insights_url(), data=payload)

    if response is None:
        return 0  # Return 0 if the API request failed

    try:
        total_count = response['count']
        logger.info(f"Found {total_count} businesses in polygon")
        return total_count
    except (KeyError, TypeError):
        logger.error("Invalid response format")
        return 0


def get_businesses(polygon_json, max_results=None, packages="enhanced_v2"): # ************************************** make sure the package matches what we have.......
    """
    Get business records within a polygon.

    Args:
        polygon_json (list): List of lat/lon points defining a polygon
        max_results (int, optional): Maximum number of results to return (None for all)
        packages (str): API data package to use (default: "enhanced_v2")

    Returns:
        list: List of business records, or empty list if error
    """
    payload = {
        "filter": {
            "relation": "geo_polygon",
            "value": polygon_json
        }
    }

    response = make_request("POST", get_scan_url(), data=payload)

    if not response:
        logger.error("Failed to get initial business data")
        return []

    # Check if any businesses were found
    total_count = response.get('count', 0)
    logger.info(f"Total businesses found: {total_count}")

    # If no businesses found, return empty list
    if total_count == 0:
        return []

    # If max_results is specified, limit the count
    if max_results and max_results < total_count:
        target_count = max_results
        logger.info(f"Limiting results to {max_results} businesses")
    else:
        target_count = total_count

    # Get the scroll ID for pagination
    scroll_id = response['scroll_id']
    logger.debug(f"Using scroll ID: {scroll_id}")

    # Collect all results
    all_results = []
    results_retrieved = 0

    while results_retrieved < target_count:
        scroll_url = f"{get_scan_url()}/{scroll_id}"

        # Set up query parameters
        scroll_params = {
            "packages": packages
        }

        scroll_response = make_request("GET", scroll_url, params=scroll_params)

        if not scroll_response or len(scroll_response) == 0:
            break  # Break if no more results or error

        all_results.extend(scroll_response)
        results_retrieved += len(scroll_response)
        logger.info(f"Retrieved {results_retrieved} of {target_count} businesses")

        # Sleep briefly to avoid hitting rate limits
        time.sleep(0.1)

        # Break if we've reached the target count
        if results_retrieved >= target_count:
            break

    logger.info(f"Successfully retrieved {len(all_results)} businesses")
    return all_results


def get_businesses_by_category(polygon_json, category_codes, max_results=None):
    """
    Get business records within a polygon filtered by category codes.

    Args:
        polygon_json (list): List of lat/lon points defining a polygon
        category_codes (list): List of SIC or NAICS codes to filter by
        max_results (int, optional): Maximum number of results to return

    Returns:
        list: List of business records, or empty list if error
    """
    # Determine if codes are SIC or NAICS based on format
    if category_codes and len(category_codes[0]) >= 8:
        code_type = "naics_code_ids"
    else:
        code_type = "sic_code_ids"

    # Create filter with both polygon and category constraints
    payload = {
        "filter": {
            "connective": "and",
            "propositions": [
                {
                    "relation": "geo_polygon",
                    "value": polygon_json
                },
                {
                    "relation": "in",
                    "attribute": code_type,
                    "value": category_codes
                }
            ]
        }
    }

    response = make_request("POST", get_scan_url(), data=payload)

    if not response:
        return []

    # Process results similar to get_businesses method
    total_count = response.get('count', 0)
    if total_count == 0:
        return []

    if max_results and max_results < total_count:
        target_count = max_results
    else:
        target_count = total_count

    scroll_id = response['scroll_id']
    all_results = []
    results_retrieved = 0

    while results_retrieved < target_count:
        scroll_url = f"{get_scan_url()}/{scroll_id}"
        scroll_params = {"packages": "enhanced_v2"} # ************************************** make sure the package matches what we have.......

        scroll_response = make_request("GET", scroll_url, params=scroll_params)

        if not scroll_response or len(scroll_response) == 0:
            break

        all_results.extend(scroll_response)
        results_retrieved += len(scroll_response)

        time.sleep(0.1)

        if results_retrieved >= target_count:
            break

    return all_results


