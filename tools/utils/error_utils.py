"""
Error Utility Functions

Helpers for error handling, logging, and formatting error messages.
"""

import logging
import traceback
import json
import sys

logger = logging.getLogger(__name__)


def log_exception(ex, message=None, level=logging.ERROR):
    """
    Log an exception with detailed traceback.

    Args:
        ex (Exception): The exception to log
        message (str): Optional additional message
        level (int): Logging level to use

    Returns:
        str: The formatted error message that was logged
    """
    # Format the error message
    ex_type = type(ex).__name__
    ex_message = str(ex)
    if message:
        error_message = f"{message}: {ex_type} - {ex_message}"
    else:
        error_message = f"{ex_type} - {ex_message}"

    # Get the traceback
    tb_str = ''.join(traceback.format_exception(type(ex), ex, ex.__traceback__))

    # Log the error
    logger.log(level, error_message)
    logger.log(level, f"Traceback:\n{tb_str}")

    return error_message


def handle_api_error(ex, default_message="An error occurred while making the API request"):
    """
    Handle an API error and return appropriate response data.

    Args:
        ex (Exception): The exception that occurred
        default_message (str): Default message if no specific message can be extracted

    Returns:
        dict: Error response data
    """
    # Log the exception
    log_exception(ex, "API Error")

    # Try to extract status code from the exception (for requests exceptions)
    status_code = 500
    error_detail = str(ex)

    if hasattr(ex, 'response') and ex.response is not None:
        status_code = ex.response.status_code

        # Try to parse response JSON
        try:
            error_data = ex.response.json()
            error_detail = error_data.get('message', error_data.get('error', str(ex)))
        except:
            # If response is not JSON, use response text
            error_detail = ex.response.text or str(ex)

    # Return error response
    return {
        'success': False,
        'error': {
            'status_code': status_code,
            'message': default_message,
            'detail': error_detail
        }
    }


def format_error_message(error, include_class=True, include_traceback=False):
    """
    Format an error into a readable message.

    Args:
        error (Exception): The exception to format
        include_class (bool): Whether to include the exception class name
        include_traceback (bool): Whether to include the traceback

    Returns:
        str: Formatted error message
    """
    if include_class:
        message = f"{type(error).__name__}: {str(error)}"
    else:
        message = str(error)

    if include_traceback:
        tb_str = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        message = f"{message}\n\nTraceback:\n{tb_str}"

    return message


def create_error_response(message, status_code=500, details=None):
    """
    Create a standardized error response dict.

    Args:
        message (str): Error message
        status_code (int): HTTP status code
        details (dict): Additional error details

    Returns:
        dict: Standardized error response
    """
    response = {
        'success': False,
        'error': {
            'message': message,
            'status_code': status_code
        }
    }

    if details:
        response['error']['details'] = details

    return response


def safe_function(func, default_return=None, log_errors=True):
    """
    Decorator to safely execute a function and handle exceptions.

    Args:
        func (callable): Function to execute
        default_return: Value to return if an exception occurs
        log_errors (bool): Whether to log errors

    Returns:
        callable: Wrapped function
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if log_errors:
                log_exception(e, f"Error in function {func.__name__}")
            return default_return

    return wrapper


def get_exception_context(ex, num_frames=3):
    """
    Get context information about where an exception occurred.

    Args:
        ex (Exception): The exception
        num_frames (int): Number of stack frames to include

    Returns:
        dict: Context information
    """
    try:
        tb = ex.__traceback__
        frames = []

        for _ in range(num_frames):
            if tb is None:
                break

            frame = tb.tb_frame
            filename = frame.f_code.co_filename
            line_number = tb.tb_lineno
            function_name = frame.f_code.co_name

            # Get local variables (limited to simple types for safety)
            local_vars = {}
            for key, value in frame.f_locals.items():
                if isinstance(value, (str, int, float, bool, type(None))):
                    local_vars[key] = value
                else:
                    try:
                        # Try to represent as string, with fallback
                        local_vars[key] = str(value)[:100]
                    except:
                        local_vars[key] = f"<{type(value).__name__}>"

            frames.append({
                'filename': filename,
                'line': line_number,
                'function': function_name,
                'locals': local_vars
            })

            tb = tb.tb_next

        return {
            'exception_type': type(ex).__name__,
            'exception_message': str(ex),
            'frames': frames
        }
    except Exception as inner_ex:
        logger.error(f"Error getting exception context: {str(inner_ex)}")
        return {
            'exception_type': type(ex).__name__,
            'exception_message': str(ex),
            'frames': []
        }


def is_error_retryable(error):
    """
    Determine if an error is potentially retryable (e.g., network timeout).

    Args:
        error (Exception): The exception to check

    Returns:
        bool: True if error is potentially retryable
    """
    import requests.exceptions

    # Common network-related errors that might be temporary
    retryable_errors = (
        requests.exceptions.Timeout,
        requests.exceptions.ConnectionError,
        requests.exceptions.ConnectTimeout,
        requests.exceptions.ReadTimeout,
        ConnectionResetError,
        ConnectionError,
        TimeoutError
    )

    # Check if error is an instance of retryable errors
    if isinstance(error, retryable_errors):
        return True

    # Check for specific HTTP status codes in requests exceptions
    if isinstance(error, requests.exceptions.HTTPError):
        # 429, 500, 502, 503, 504 are potentially retryable
        retryable_status_codes = {429, 500, 502, 503, 504}

        if hasattr(error, 'response') and error.response is not None:
            return error.response.status_code in retryable_status_codes

    return False