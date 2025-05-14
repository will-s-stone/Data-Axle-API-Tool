"""
Date Utility Functions

Helpers for date and time operations, formatting, and parsing.
"""

import datetime
import logging

logger = logging.getLogger(__name__)


def format_timestamp(timestamp=None, format_string="%Y-%m-%d %H:%M:%S"):
    """
    Format a timestamp according to the specified format.

    Args:
        timestamp (datetime/int/float, optional): Timestamp to format, uses current time if None
        format_string (str): Format string for the output

    Returns:
        str: Formatted timestamp string
    """
    try:
        if timestamp is None:
            dt = datetime.datetime.now()
        elif isinstance(timestamp, (int, float)):
            dt = datetime.datetime.fromtimestamp(timestamp)
        elif isinstance(timestamp, datetime.datetime):
            dt = timestamp
        else:
            raise ValueError(f"Unsupported timestamp type: {type(timestamp)}")

        return dt.strftime(format_string)
    except Exception as e:
        logger.error(f"Error formatting timestamp: {str(e)}")
        return None


def get_current_datetime_string(format_string="%Y%m%d-%H%M%S"):
    """
    Get the current date/time as a formatted string.

    Args:
        format_string (str): Format string for the output

    Returns:
        str: Current date/time formatted as a string
    """
    return format_timestamp(datetime.datetime.now(), format_string)


def parse_date_string(date_string, format_string="%Y-%m-%d"):
    """
    Parse a date string into a datetime object.

    Args:
        date_string (str): String representation of a date
        format_string (str): Format string to use for parsing

    Returns:
        datetime: Parsed datetime object or None if parsing failed
    """
    try:
        return datetime.datetime.strptime(date_string, format_string)
    except Exception as e:
        logger.error(f"Error parsing date string '{date_string}': {str(e)}")
        return None


def get_date_range(start_date, end_date=None, days=None):
    """
    Get a list of dates in the range [start_date, end_date] or [start_date, start_date + days].

    Args:
        start_date (datetime/str): Start date (if string, assumed format is '%Y-%m-%d')
        end_date (datetime/str, optional): End date (if None, uses start_date + days)
        days (int, optional): Number of days to include (if end_date is None)

    Returns:
        list: List of datetime objects in the range
    """
    try:
        # Parse start_date if it's a string
        if isinstance(start_date, str):
            start_date = parse_date_string(start_date)

        # Determine end_date
        if end_date is None and days is not None:
            end_date = start_date + datetime.timedelta(days=days)
        elif isinstance(end_date, str):
            end_date = parse_date_string(end_date)

        if end_date is None:
            return [start_date]

        # Generate date range
        result = []
        current_date = start_date
        while current_date <= end_date:
            result.append(current_date)
            current_date += datetime.timedelta(days=1)

        return result
    except Exception as e:
        logger.error(f"Error generating date range: {str(e)}")
        return []


def is_date_between(date, start_date, end_date):
    """
    Check if a date is between start_date and end_date (inclusive).

    Args:
        date (datetime/str): Date to check
        start_date (datetime/str): Start date
        end_date (datetime/str): End date

    Returns:
        bool: True if date is between start_date and end_date, False otherwise
    """
    try:
        # Parse dates if they are strings
        if isinstance(date, str):
            date = parse_date_string(date)
        if isinstance(start_date, str):
            start_date = parse_date_string(start_date)
        if isinstance(end_date, str):
            end_date = parse_date_string(end_date)

        return start_date <= date <= end_date
    except Exception as e:
        logger.error(f"Error checking if date is between: {str(e)}")
        return False


def add_days(date, days):
    """
    Add a number of days to a date.

    Args:
        date (datetime/str): Date to add days to
        days (int): Number of days to add (can be negative)

    Returns:
        datetime: Date with days added
    """
    try:
        if isinstance(date, str):
            date = parse_date_string(date)

        return date + datetime.timedelta(days=days)
    except Exception as e:
        logger.error(f"Error adding days to date: {str(e)}")
        return None


def get_month_start_end(year, month):
    """
    Get the start and end dates for a specific month.

    Args:
        year (int): Year
        month (int): Month (1-12)

    Returns:
        tuple: (start_date, end_date) as datetime objects
    """
    try:
        start_date = datetime.datetime(year, month, 1)

        # Determine the last day of the month
        if month == 12:
            end_date = datetime.datetime(year + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            end_date = datetime.datetime(year, month + 1, 1) - datetime.timedelta(days=1)

        return start_date, end_date
    except Exception as e:
        logger.error(f"Error getting month start/end dates: {str(e)}")
        return None, None