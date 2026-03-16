"""
Common utilities used across multiple tools.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def ensure_tmp_dir() -> str:
    """
    Ensure .tmp directory exists.

    Returns:
        str: Path to .tmp directory
    """
    tmp_dir = '.tmp'
    os.makedirs(tmp_dir, exist_ok=True)
    return tmp_dir


def safe_file_write(filepath: str, content: str, mode: str = 'w') -> bool:
    """
    Safely write content to a file.

    Args:
        filepath: Target file path
        content: Content to write
        mode: File mode ('w' or 'a')

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, mode) as f:
            f.write(content)
        logger.info(f"Successfully wrote to {filepath}")
        return True
    except Exception as e:
        logger.error(f"Failed to write to {filepath}: {str(e)}")
        return False


def validate_env_var(var_name: str) -> Optional[str]:
    """
    Validate and retrieve environment variable.

    Args:
        var_name: Name of environment variable

    Returns:
        str: Value of environment variable, or None if not set
    """
    value = os.getenv(var_name)
    if not value:
        logger.error(f"Environment variable {var_name} is not set")
    return value


def safe_file_read(filepath: str) -> Optional[str]:
    """
    Safely read content from a file.

    Args:
        filepath: Source file path

    Returns:
        str: File content if successful, None otherwise
    """
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        logger.info(f"Successfully read from {filepath}")
        return content
    except Exception as e:
        logger.error(f"Failed to read from {filepath}: {str(e)}")
        return None
