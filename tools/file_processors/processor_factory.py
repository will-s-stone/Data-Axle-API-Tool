"""
Processor Factory Module

Factory pattern for selecting the appropriate file processor based on file type.
"""

import logging

logger = logging.getLogger(__name__)


def get_processor(file_type):
    """
    Factory method to get the appropriate file processor

    Args:
        file_type (str): File extension ('kmz' or 'kml')

    Returns:
        module: The appropriate processor module
    """
    if file_type.lower() == 'kmz':
        from . import kmz_processor
        logger.debug("Selected KMZ processor")
        return kmz_processor
    elif file_type.lower() == 'kml':
        from . import kml_processor
        logger.debug("Selected KML processor")
        return kml_processor
    else:
        logger.error(f"Unsupported file type: {file_type}")
        raise ValueError(f"Unsupported file type: {file_type}")