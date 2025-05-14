"""
Format Utility Functions

Helpers for formatting data, numbers, text, etc.
"""

import logging
import re
import json

logger = logging.getLogger(__name__)


def format_currency(amount, currency_symbol="$", decimal_places=2):
    """
    Format a number as currency.

    Args:
        amount (float/int): Amount to format
        currency_symbol (str): Currency symbol to use
        decimal_places (int): Number of decimal places to include

    Returns:
        str: Formatted currency string
    """
    try:
        return f"{currency_symbol}{amount:,.{decimal_places}f}"
    except Exception as e:
        logger.error(f"Error formatting currency: {str(e)}")
        return f"{currency_symbol}{amount}"


def format_percentage(value, decimal_places=1, include_symbol=True):
    """
    Format a decimal value as a percentage.

    Args:
        value (float): Value to format (0.1 = 10%)
        decimal_places (int): Number of decimal places to include
        include_symbol (bool): Whether to include the % symbol

    Returns:
        str: Formatted percentage string
    """
    try:
        percentage = value * 100
        formatted = f"{percentage:.{decimal_places}f}"

        if include_symbol:
            return f"{formatted}%"
        return formatted
    except Exception as e:
        logger.error(f"Error formatting percentage: {str(e)}")
        return f"{value:.{decimal_places}f}" + ("%" if include_symbol else "")


def format_number_with_commas(number):
    """
    Format a number with commas as thousands separators.

    Args:
        number (int/float): Number to format

    Returns:
        str: Formatted number string
    """
    try:
        return f"{number:,}"
    except Exception as e:
        logger.error(f"Error formatting number with commas: {str(e)}")
        return str(number)


def format_coordinates(latitude, longitude, decimal_places=6):
    """
    Format coordinates as a string.

    Args:
        latitude (float): Latitude
        longitude (float): Longitude
        decimal_places (int): Number of decimal places to include

    Returns:
        str: Formatted coordinates string
    """
    try:
        return f"{latitude:.{decimal_places}f}, {longitude:.{decimal_places}f}"
    except Exception as e:
        logger.error(f"Error formatting coordinates: {str(e)}")
        return f"{latitude}, {longitude}"


def truncate_string(text, max_length=100, suffix="..."):
    """
    Truncate a string to a maximum length.

    Args:
        text (str): Text to truncate
        max_length (int): Maximum length before truncation
        suffix (str): String to append when truncated

    Returns:
        str: Truncated string
    """
    try:
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
    except Exception as e:
        logger.error(f"Error truncating string: {str(e)}")
        return text


def format_area(area_sq_meters, unit="acres", decimal_places=2):
    """
    Format an area measurement with the appropriate unit.

    Args:
        area_sq_meters (float): Area in square meters
        unit (str): Target unit ('acres', 'sq_m', 'sq_km', 'sq_ft', 'sq_mi')
        decimal_places (int): Number of decimal places to include

    Returns:
        str: Formatted area string with unit
    """
    try:
        # Convert to target unit
        if unit == "acres":
            # 1 acre = 4046.86 square meters
            value = area_sq_meters / 4046.86
            unit_str = "acres"
        elif unit == "sq_m":
            value = area_sq_meters
            unit_str = "m²"
        elif unit == "sq_km":
            value = area_sq_meters / 1000000
            unit_str = "km²"
        elif unit == "sq_ft":
            # 1 square meter = 10.7639 square feet
            value = area_sq_meters * 10.7639
            unit_str = "ft²"
        elif unit == "sq_mi":
            # 1 square mile = 2589988.11 square meters
            value = area_sq_meters / 2589988.11
            unit_str = "mi²"
        else:
            value = area_sq_meters
            unit_str = "m²"

        return f"{value:.{decimal_places}f} {unit_str}"
    except Exception as e:
        logger.error(f"Error formatting area: {str(e)}")
        return f"{area_sq_meters} sq m"


def format_phone_number(phone, format_type="us"):
    """
    Format a phone number according to a specific format.

    Args:
        phone (str): Phone number to format
        format_type (str): Format type ('us', 'international', etc.)

    Returns:
        str: Formatted phone number
    """
    try:
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)

        if format_type == "us":
            if len(digits) == 10:
                return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
            elif len(digits) == 11 and digits[0] == '1':
                return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        elif format_type == "international":
            if len(digits) == 10:  # Assume US number
                return f"+1 ({digits[:3]}) {digits[3:6]}-{digits[6:]}"
            elif len(digits) == 11 and digits[0] == '1':  # US number with country code
                return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"

        # If no specific formatting applied, return cleaned digits
        return digits
    except Exception as e:
        logger.error(f"Error formatting phone number: {str(e)}")
        return phone


def camel_to_snake(camel_case):
    """
    Convert a camelCase string to snake_case.

    Args:
        camel_case (str): CamelCase string

    Returns:
        str: snake_case string
    """
    try:
        # Insert underscore before capital letters and convert to lowercase
        snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', camel_case).lower()
        return snake_case
    except Exception as e:
        logger.error(f"Error converting camelCase to snake_case: {str(e)}")
        return camel_case


def snake_to_camel(snake_case):
    """
    Convert a snake_case string to camelCase.

    Args:
        snake_case (str): snake_case string

    Returns:
        str: camelCase string
    """
    try:
        # Split by underscore and capitalize each part except the first
        parts = snake_case.split('_')
        camel_case = parts[0] + ''.join(part.capitalize() for part in parts[1:])
        return camel_case
    except Exception as e:
        logger.error(f"Error converting snake_case to camelCase: {str(e)}")
        return snake_case


def clean_html(html_string):
    """
    Remove HTML tags from a string.

    Args:
        html_string (str): String with HTML tags

    Returns:
        str: String with HTML tags removed
    """
    try:
        # Basic HTML tag removal regex
        clean_text = re.sub(r'<[^>]*>', '', html_string)
        # Replace common HTML entities
        clean_text = clean_text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        clean_text = clean_text.replace('&nbsp;', ' ')
        return clean_text.strip()
    except Exception as e:
        logger.error(f"Error cleaning HTML: {str(e)}")
        return html_string


def format_file_size(size_bytes):
    """
    Format a file size in bytes to a human-readable string.

    Args:
        size_bytes (int): Size in bytes

    Returns:
        str: Formatted file size string
    """
    try:
        # Define unit prefixes
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}" if unit != 'B' else f"{size_bytes} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    except Exception as e:
        logger.error(f"Error formatting file size: {str(e)}")
        return f"{size_bytes} bytes"