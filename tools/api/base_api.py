import requests
import os
import time
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

request_counter = 0
request_limit = 150  # Data Axle limit: 150 requests per 10 seconds
window_start_time = time.time()
window_duration = 10  # seconds


def get_auth_token():
    """Get the authentication token from environment variables."""
    auth_token = os.getenv("X-AUTH-TOKEN")
    if not auth_token:
        logger.error("DATA_AXLE_API_TOKEN not found in environment variables")
        raise ValueError("Missing API token. Please set X-AUTH-TOKEN environment variable.")
    return auth_token


def get_base_headers():
    """Get the base headers for API requests."""
    return {
        "X-AUTH-TOKEN": get_auth_token(),
        "Content-Type": "application/json",
        "Accept": "application/json"
    }


def get_base_urls():
    """Get the base URLs for different API endpoints."""
    return {
        "places": "https://api.data-axle.com/v1/places",
        "people": "https://api.data-axle.com/v1/people"
    }


def check_rate_limit():
    """
    Check if we're approaching rate limits and delay if necessary.
    Implements a sliding window approach to manage API rate limits.
    """
    global request_counter, window_start_time

    current_time = time.time()
    time_elapsed = current_time - window_start_time

    # Reset counter if window has passed
    if time_elapsed >= window_duration:
        request_counter = 0
        window_start_time = current_time
        return

    # If approaching rate limit, sleep until window resets
    if request_counter >= request_limit:
        sleep_time = window_duration - time_elapsed
        if sleep_time > 0:
            logger.info(f"Rate limit approaching, sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
            request_counter = 0
            window_start_time = time.time()


def make_request(method, endpoint, data=None, params=None, additional_headers=None):
    """
    Make a request to the Data Axle API with rate limiting and error handling.

    Args:
        method (str): HTTP method ('GET', 'POST', etc.)
        endpoint (str): API endpoint to call
        data (dict, optional): JSON data for request body
        params (dict, optional): Query parameters
        additional_headers (dict, optional): Additional HTTP headers

    Returns:
        dict: JSON response from the API

    Raises:
        Exception: If the API request fails
    """
    global request_counter

    # Check and manage rate limits
    check_rate_limit()

    # Prepare headers
    headers = get_base_headers()
    if additional_headers:
        headers.update(additional_headers)

    # Make the request
    try:
        response = requests.request(
            method=method,
            url=endpoint,
            json=data,
            params=params,
            headers=headers
        )

        # Increment request counter
        request_counter += 1

        # Log request details (omit sensitive information)
        logger.debug(f"API Request: {method} {endpoint}")
        logger.debug(f"Status Code: {response.status_code}")

        # Handle different status codes
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            logger.warning("Rate limit exceeded. Retrying after delay.")
            time.sleep(2)  # Sleep and retry
            return make_request(method, endpoint, data, params, additional_headers)
        elif response.status_code == 500 and "polygon" in str(data):
            # Special handling for malformed polygon errors
            error_msg = f"Malformed polygon, please fix geometry. Status code {response.status_code}: {response.text}"
            logger.error(error_msg)
            return None
        else:
            error_msg = f"API request failed with status code {response.status_code}: {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        raise Exception(f"API request error: {str(e)}")


