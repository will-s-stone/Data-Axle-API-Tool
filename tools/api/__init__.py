from .base_api import make_request
from .business_api import get_business_count, get_businesses, get_businesses_by_category
from .consumer_api import get_household_count, get_consumers, get_consumers_by_attributes
from .insights_api import (
    get_income_distribution,
    get_home_value_distribution,
    get_home_ownership_rate,
    get_wealth_distribution,
    get_education_levels,
    get_language_distribution,
    get_business_categories,
    get_complete_area_insights,
    calculate_affluence_score
)

__all__ = [
    # Base API
    'make_request',

    # Business API
    'get_business_count',
    'get_businesses',
    'get_businesses_by_category',

    # Consumer API
    'get_household_count',
    'get_consumers',
    'get_consumers_by_attributes',

    # Insights API
    'get_income_distribution',
    'get_home_value_distribution',
    'get_home_ownership_rate',
    'get_wealth_distribution',
    'get_education_levels',
    'get_language_distribution',
    'get_business_categories',
    'get_complete_area_insights',
    'calculate_affluence_score'
]
