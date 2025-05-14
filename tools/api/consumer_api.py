import logging
import time
from .base_api import make_request, get_base_urls

logger = logging.getLogger(__name__)


def get_insights_url():
    """Get the URL for the consumer insights endpoint."""
    return f"{get_base_urls()['people']}/insights"


def get_scan_url():
    """Get the URL for the consumer scan endpoint."""
    return f"{get_base_urls()['people']}/scan"


def get_household_count(polygon_json):
    """
    Get the count of households within a polygon.

    Args:
        polygon_json (list): List of lat/lon points defining a polygon

    Returns:
        int: Number of households in the polygon, or 0 if error
    """
    payload = {
        "filter": {
            "relation": "geo_polygon",
            "value": polygon_json
        },
        "insights": {
            "field": "street",
            "calculations": ["unique_count"]
        }
    }

    response = make_request("GET", get_insights_url(), data=payload)

    if not response:
        return 0

    try:
        unique_count = response['insights']['unique_count']
        logger.info(f"Found {unique_count} households in polygon")
        return unique_count
    except (KeyError, TypeError):
        logger.error("Invalid response format for household count")
        return 0


def get_consumers(polygon_json, head_of_household=True, max_results=None, packages="enhanced"):
    """
    Get consumer records within a polygon.

    Args:
        polygon_json (list): List of lat/lon points defining a polygon
        head_of_household (bool): Whether to filter for head of household only
        max_results (int, optional): Maximum number of results to return
        packages (str): API data package to use

    Returns:
        list: List of consumer records, or empty list if error
    """
    # Construct the filter based on parameters
    if head_of_household:
        filter_payload = {
            "connective": "and",
            "propositions": [
                {
                    "relation": "geo_polygon",
                    "value": polygon_json
                },
                {
                    "relation": "equals",
                    "attribute": "estimated_head_of_family",
                    "value": True
                }
            ]
        }
    else:
        filter_payload = {
            "relation": "geo_polygon",
            "value": polygon_json
        }

    payload = {
        "filter": filter_payload
    }

    response = make_request("POST", get_scan_url(), data=payload)

    if not response:
        return []

    # Process results similar to get_businesses in business_api.py
    total_count = response.get('count', 0)
    logger.info(f"Total consumers found: {total_count}")

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
        scroll_params = {"packages": packages}

        scroll_response = make_request("GET", scroll_url, params=scroll_params)

        if not scroll_response or len(scroll_response) == 0:
            break

        all_results.extend(scroll_response)
        results_retrieved += len(scroll_response)

        if results_retrieved >= target_count:
            break

    logger.info(f"Successfully retrieved {len(all_results)} consumer records")
    return all_results


def get_consumers_by_attributes(polygon_json, attributes, max_results=None):
    """
    Get consumer records within a polygon filtered by specific attributes.

    Args:
        polygon_json (list): List of lat/lon points defining a polygon
        attributes (dict): Dictionary of attributes and values to filter by
                           e.g. {"family.estimated_income_range": {"min": 100000}}
        max_results (int, optional): Maximum number of results to return

    Returns:
        list: List of consumer records, or empty list if error
    """
    propositions = [
        {
            "relation": "geo_polygon",
            "value": polygon_json
        }
    ]

    # Add attribute filters
    for attribute, value in attributes.items():
        if isinstance(value, dict) and "min" in value:
            propositions.append({
                "relation": "greater_than_equals",
                "attribute": attribute,
                "value": value["min"]
            })
        elif isinstance(value, dict) and "max" in value:
            propositions.append({
                "relation": "less_than_equals",
                "attribute": attribute,
                "value": value["max"]
            })
        else:
            propositions.append({
                "relation": "equals",
                "attribute": attribute,
                "value": value
            })

    payload = {
        "filter": {
            "connective": "and",
            "propositions": propositions
        }
    }

    # Process request and results similar to get_consumers method
    response = make_request("POST", get_scan_url(), data=payload)

    if not response:
        return []

    # Rest of implementation similar to get_consumers...
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

        scroll_response = make_request("GET", scroll_url, params={"packages": "enhanced"})

        if not scroll_response or len(scroll_response) == 0:
            break

        all_results.extend(scroll_response)
        results_retrieved += len(scroll_response)

        if results_retrieved >= target_count:
            break

    return all_results