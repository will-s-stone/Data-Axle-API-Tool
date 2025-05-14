import logging
from .base_api import make_request, get_base_urls

logger = logging.getLogger(__name__)


# URL constants
def get_people_insights_url():
    """Get the URL for the people insights endpoint."""
    return f"{get_base_urls()['people']}/insights"


def get_places_insights_url():
    """Get the URL for the places insights endpoint."""
    return f"{get_base_urls()['places']}/insights"


def get_income_distribution(polygon_json):
    """
    Get income distribution for households within a polygon.

    Args:
        polygon_json (list): List of lat/lon points defining a polygon

    Returns:
        dict: Income distribution data, or None if error
    """
    payload = {
        "filter": {
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
        },
        "insights": {
            "field": "family.estimated_income_range",
            "calculations": ["frequencies"]
        }
    }

    response = make_request("GET", get_people_insights_url(), data=payload)
    return response


def get_home_value_distribution(polygon_json):
    """
    Get home value distribution for households within a polygon.

    Args:
        polygon_json (list): List of lat/lon points defining a polygon

    Returns:
        dict: Home value distribution data, or None if error
    """
    payload = {
        "filter": {
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
        },
        "insights": {
            "field": "real_estate.estimated_home_value",
            "calculations": ["frequencies"],
            "insights": {
                "field": "street",
                "calculations": ["unique_count"]
            }
        }
    }

    response = make_request("GET", get_people_insights_url(), data=payload)
    return response


def get_home_ownership_rate(polygon_json):
    """
    Get home ownership rate for households within a polygon.

    Args:
        polygon_json (list): List of lat/lon points defining a polygon

    Returns:
        dict: Home ownership data, or None if error
    """
    payload = {
        "filter": {
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
        },
        "insights": {
            "field": "family.estimated_home_owner",
            "calculations": ["frequencies"],
            "insights": {
                "field": "street",
                "calculations": ["unique_count"]
            }
        }
    }

    response = make_request("GET", get_people_insights_url(), data=payload)
    return response


def get_wealth_distribution(polygon_json):
    """
    Get wealth distribution for households within a polygon.

    Args:
        polygon_json (list): List of lat/lon points defining a polygon

    Returns:
        dict: Wealth distribution data, or None if error
    """
    payload = {
        "filter": {
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
        },
        "insights": {
            "field": "family.estimated_wealth",
            "calculations": ["frequencies"],
            "insights": {
                "field": "street",
                "calculations": ["unique_count"]
            }
        }
    }

    response = make_request("GET", get_people_insights_url(), data=payload)
    return response


def get_education_levels(polygon_json):
    """
    Get education level distribution for people within a polygon.

    Args:
        polygon_json (list): List of lat/lon points defining a polygon

    Returns:
        dict: Education level distribution data, or None if error
    """
    payload = {
        "filter": {
            "relation": "geo_polygon",
            "value": polygon_json
        },
        "insights": {
            "field": "family.estimated_education_level",
            "calculations": ["frequencies"]
        }
    }

    response = make_request("GET", get_people_insights_url(), data=payload)
    return response


def get_language_distribution(polygon_json):
    """
    Get language distribution for people within a polygon.

    Args:
        polygon_json (list): List of lat/lon points defining a polygon

    Returns:
        dict: Language distribution data, or None if error
    """
    payload = {
        "filter": {
            "relation": "geo_polygon",
            "value": polygon_json
        },
        "insights": {
            "field": "estimated_language",
            "calculations": ["frequencies"]
        }
    }

    response = make_request("GET", get_people_insights_url(), data=payload)
    return response


def get_business_categories(polygon_json):
    """
    Get business category distribution within a polygon.

    Args:
        polygon_json (list): List of lat/lon points defining a polygon

    Returns:
        dict: Business category distribution data, or None if error
    """
    payload = {
        "filter": {
            "relation": "geo_polygon",
            "value": polygon_json
        },
        "insights": {
            "field": "primary_sic_code_id",
            "calculations": ["frequencies"]
        }
    }

    response = make_request("GET", get_places_insights_url(), data=payload)
    return response


def get_complete_area_insights(polygon_json):
    """
    Get a comprehensive set of insights for an area in one function.

    Args:
        polygon_json (list): List of lat/lon points defining a polygon

    Returns:
        dict: Dictionary containing all insight metrics
    """
    insights = {
        "household_count": None,
        "income_distribution": None,
        "home_value_distribution": None,
        "home_ownership_rate": None,
        "wealth_distribution": None,
        "education_levels": None,
        "language_distribution": None,
        "business_count": None,
        "business_categories": None
    }

    # Get consumer insights
    try:
        # Count households
        household_payload = {
            "filter": {
                "relation": "geo_polygon",
                "value": polygon_json
            },
            "insights": {
                "field": "street",
                "calculations": ["unique_count"]
            }
        }
        household_response = make_request("GET", get_people_insights_url(), data=household_payload)
        if household_response:
            insights["household_count"] = household_response.get("insights", {}).get("unique_count", 0)

        # Get other insights
        insights["income_distribution"] = get_income_distribution(polygon_json)
        insights["home_value_distribution"] = get_home_value_distribution(polygon_json)
        insights["home_ownership_rate"] = get_home_ownership_rate(polygon_json)
        insights["wealth_distribution"] = get_wealth_distribution(polygon_json)
        insights["education_levels"] = get_education_levels(polygon_json)
        insights["language_distribution"] = get_language_distribution(polygon_json)

    except Exception as e:
        logger.error(f"Error getting consumer insights: {str(e)}")

    # Get business insights
    try:
        # Count businesses
        business_payload = {
            "filter": {
                "relation": "geo_polygon",
                "value": polygon_json
            },
            "insights": {
                "field": "legal_name",
                "calculations": ["fill_count"]
            }
        }
        business_response = make_request("GET", get_places_insights_url(), data=business_payload)
        if business_response:
            insights["business_count"] = business_response.get("count", 0)

        # Get business categories
        insights["business_categories"] = get_business_categories(polygon_json)

    except Exception as e:
        logger.error(f"Error getting business insights: {str(e)}")

    return insights


# Calculation helper functions
def calculate_median_from_frequencies(frequencies):
    """
    Calculate the median value from a frequency distribution.

    Args:
        frequencies (list): List of frequency objects with lower, upper, and count

    Returns:
        float: Median value or 0 if error
    """
    if not frequencies:
        return 0

    total_count = sum(freq.get('count', 0) for freq in frequencies)
    if total_count == 0:
        return 0

    # Convert to list of value ranges with counts
    valid_frequencies = []
    for freq in frequencies:
        if freq.get('count', 0) > 0:
            # For ranges with upper and lower bounds
            if 'upper' in freq:
                midpoint = (freq.get('lower', 0) + freq.get('upper', 0)) / 2
            else:
                # For the special case with only a lower bound
                midpoint = freq.get('lower', 0)

            valid_frequencies.append({
                'midpoint': midpoint,
                'count': freq.get('count', 0)
            })

    valid_frequencies.sort(key=lambda x: x['midpoint'])

    # Find the median position
    cumulative_count = 0
    median_position = total_count / 2

    for freq in valid_frequencies:
        prev_cumulative = cumulative_count
        cumulative_count += freq.get('count', 0)

        if cumulative_count >= median_position:
            # If the median position is exactly at the boundary, take the average
            if cumulative_count == median_position and freq != valid_frequencies[-1]:
                next_midpoint = valid_frequencies[valid_frequencies.index(freq) + 1]['midpoint']
                return (freq['midpoint'] + next_midpoint) / 2
            return freq['midpoint']

    return 0


def calculate_home_ownership_rate(frequencies):
    """
    Calculate the home ownership rate from frequency data.

    Args:
        frequencies (list): List of frequency objects

    Returns:
        float: Home ownership rate (0-1) or 0 if error
    """
    if not frequencies:
        return 0

    owner_count = 0
    non_owner_count = 0

    for freq in frequencies:
        if 'insights' not in freq or 'unique_count' not in freq['insights']:
            continue

        unique_count = freq['insights']['unique_count']

        # Check if this is an owner or non-owner entry
        if 'value' in freq:
            if freq['value'] is True:
                owner_count += unique_count
            elif freq['value'] is False:
                non_owner_count += unique_count

    total_count = owner_count + non_owner_count
    if total_count == 0:
        return 0

    return owner_count / total_count


def calculate_affluence_score(polygon_json):
    """
    Calculate an affluence score based on multiple demographic factors.

    Args:
        polygon_json (list): List of lat/lon points defining a polygon

    Returns:
        float: Affluence score (0-100) or 0 if error
    """
    # Get necessary insights
    income_distribution = get_income_distribution(polygon_json)
    home_value_distribution = get_home_value_distribution(polygon_json)
    wealth_distribution = get_wealth_distribution(polygon_json)
    home_ownership_response = get_home_ownership_rate(polygon_json)

    # Calculate median income
    median_income = calculate_median_from_frequencies(
        income_distribution.get('insights', {}).get('frequencies', [])
    ) if income_distribution else 0

    # Calculate median home value
    median_home_value = calculate_median_from_frequencies(
        home_value_distribution.get('insights', {}).get('frequencies', [])
    ) if home_value_distribution else 0

    # Calculate median wealth
    median_wealth = calculate_median_from_frequencies(
        wealth_distribution.get('insights', {}).get('frequencies', [])
    ) if wealth_distribution else 0

    # Calculate home ownership rate
    home_ownership_rate = calculate_home_ownership_rate(
        home_ownership_response.get('insights', {}).get('frequencies', [])
    ) if home_ownership_response else 0

    # Calculate affluence score
    try:
        # Normalize each metric to a 0-100 scale
        income_score = min(median_income / 125000 * 100, 100)
        home_value_score = min(median_home_value / 250000 * 100, 100)
        wealth_score = min(median_wealth / 200000 * 100, 100)
        ownership_score = home_ownership_rate * 100

        # Apply weights: 30% income, 30% home value, 25% wealth, 15% home ownership
        weighted_income = income_score * 0.30
        weighted_home_value = home_value_score * 0.30
        weighted_wealth = wealth_score * 0.25
        weighted_ownership = ownership_score * 0.15

        total_score = weighted_income + weighted_home_value + weighted_wealth + weighted_ownership
        return round(total_score, 2)

    except Exception as e:
        logger.error(f"Error calculating affluence score: {str(e)}")
        return 0
