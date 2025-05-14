"""
API Utility Functions

Helpers for making API requests, handling responses, caching, etc.
"""

import time
import logging
import json
import hashlib
import os
import requests
from functools import wraps

logger = logging.getLogger(__name__)


def retry_api_call(max_retries=3, retry_delay=1, backoff_factor=2, retryable_errors=None):
    """
    Decorator to retry API calls on failure.

    Args:
        max_retries (int): Maximum number of retry attempts
        retry_delay (float): Initial delay between retries in seconds
        backoff_factor (float): Factor to increase delay with each retry
        retryable_errors (tuple): Tuple of error types that should trigger a retry

    Returns:
        function: Decorated function
    """
    if retryable_errors is None:
        # Default retryable errors
        retryable_errors = (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.RequestException
        )

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_retry = 0
            current_delay = retry_delay

            while True:
                try:
                    return func(*args, **kwargs)
                except retryable_errors as e:
                    current_retry += 1

                    if current_retry > max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded for API call")
                        raise

                    logger.warning(f"API call failed (attempt {current_retry}/{max_retries}): {str(e)}")
                    logger.warning(f"Retrying in {current_delay} seconds...")

                    time.sleep(current_delay)
                    current_delay *= backoff_factor

        return wrapper

    return decorator


def cache_api_result(cache_dir, expiry_seconds=3600):
    """
    Decorator to cache API results to disk.

    Args:
        cache_dir (str): Directory to store cache files
        expiry_seconds (int): Cache expiry time in seconds

    Returns:
        function: Decorated function
    """
    os.makedirs(cache_dir, exist_ok=True)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create a cache key from the function name and arguments
            cache_key = f"{func.__name__}_{str(args)}_{str(sorted(kwargs.items()))}"
            cache_key_hash = hashlib.md5(cache_key.encode()).hexdigest()
            cache_file = os.path.join(cache_dir, f"{cache_key_hash}.json")

            # Check if cache file exists and is valid
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r') as f:
                        cache_data = json.load(f)

                    # Check if cache is still valid
                    if time.time() - cache_data['timestamp'] < expiry_seconds:
                        logger.debug(f"Using cached result for {func.__name__}")
                        return cache_data['result']
                except Exception as e:
                    logger.warning(f"Error reading cache: {str(e)}")

            # Call the original function
            result = func(*args, **kwargs)

            # Cache the result
            try:
                with open(cache_file, 'w') as f:
                    json.dump({
                        'timestamp': time.time(),
                        'result': result
                    }, f)
                logger.debug(f"Cached result for {func.__name__}")
            except Exception as e:
                logger.warning(f"Error writing cache: {str(e)}")

            return result

        return wrapper

    return decorator


def format_api_request(url, params=None, headers=None, data=None, method="GET"):
    """
    Format an API request for logging.

    Args:
        url (str): Request URL
        params (dict): URL parameters
        headers (dict): HTTP headers
        data (dict): Request body data
        method (str): HTTP method

    Returns:
        str: Formatted request string
    """
    try:
        # Start with the method and URL
        formatted = f"{method} {url}"

        # Add query parameters
        if params:
            formatted += "\nParams:"
            for key, value in params.items():
                formatted += f"\n  {key}: {value}"

        # Add headers (excluding sensitive data)
        if headers:
            formatted += "\nHeaders:"
            for key, value in headers.items():
                # Mask sensitive header values
                if key.lower() in ['authorization', 'x-auth-token', 'api-key']:
                    value = "[REDACTED]"
                formatted += f"\n  {key}: {value}"

        # Add request body
        if data:
            # Convert to string if it's not already
            if isinstance(data, dict):
                body_str = json.dumps(data)
            else:
                body_str = str(data)

            # Truncate long bodies
            if len(body_str) > 1000:
                body_str = body_str[:1000] + "... [truncated]"

            formatted += f"\nBody: {body_str}"

        return formatted
    except Exception as e:
        logger.error(f"Error formatting API request: {str(e)}")
        return f"{method} {url}"


def parse_api_response(response, expected_fields=None):
    """
    Parse and validate an API response.

    Args:
        response (requests.Response): API response
        expected_fields (list): List of fields expected in the response

    Returns:
        tuple: (data, errors) - data is the parsed response, errors is a list of validation errors
    """
    try:
        # Try to parse response as JSON
        data = response.json()
        errors = []

        # Check for error responses
        if response.status_code >= 400:
            errors.append(f"API returned error status: {response.status_code}")
            if isinstance(data, dict) and 'error' in data:
                errors.append(f"API error: {data['error']}")

        # Validate expected fields
        if expected_fields and isinstance(data, dict):
            for field in expected_fields:
                if field not in data:
                    errors.append(f"Expected field '{field}' missing from response")

        return data, errors
    except json.JSONDecodeError:
        # Return the text response if not JSON
        return response.text, ["Response is not valid JSON"]
    except Exception as e:
        logger.error(f"Error parsing API response: {str(e)}")
        return None, [f"Error parsing response: {str(e)}"]


def build_api_error_response(error, status_code=500):
    """
    Build a standardized API error response.

    Args:
        error (Exception or str): The error that occurred
        status_code (int): HTTP status code

    Returns:
        dict: Standardized error response
    """
    if isinstance(error, Exception):
        error_message = str(error)
        error_type = type(error).__name__
    else:
        error_message = str(error)
        error_type = "Error"

    return {
        'success': False,
        'error': {
            'message': error_message,
            'type': error_type,
            'status_code': status_code
        }
    }


def api_rate_limiter(rate_limit, time_period=60):
    """
    Decorator to limit the rate of API calls.

    Args:
        rate_limit (int): Maximum number of calls allowed in the time period
        time_period (int): Time period in seconds

    Returns:
        function: Decorated function
    """
    calls = []

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()

            # Remove calls outside the time period
            calls[:] = [call_time for call_time in calls if current_time - call_time < time_period]

            # Check if we're over the rate limit
            if len(calls) >= rate_limit:
                # Calculate wait time
                oldest_call = min(calls)
                wait_time = time_period - (current_time - oldest_call)

                if wait_time > 0:
                    logger.warning(f"Rate limit reached. Waiting {wait_time:.2f} seconds before next call")
                    time.sleep(wait_time)
                    # Update current time after sleeping
                    current_time = time.time()

            # Add this call to the list
            calls.append(current_time)

            # Call the original function
            return func(*args, **kwargs)

        return wrapper

    return decorator
