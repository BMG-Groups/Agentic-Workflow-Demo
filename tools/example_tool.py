#!/usr/bin/env python3
"""
Example Tool - Template for creating new tools

This tool demonstrates the standard structure:
- Environment variable loading
- Argument parsing
- Error handling
- Logging
- Clear exit codes
"""

import os
import sys
import argparse
import logging
from dotenv import load_dotenv
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.utils.common import ensure_tmp_dir, safe_file_write

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Example tool demonstrating WAT framework structure'
    )
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Input parameter'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='.tmp/output.txt',
        help='Output file path (default: .tmp/output.txt)'
    )
    return parser.parse_args()


def validate_environment():
    """
    Validate required environment variables.

    Returns:
        bool: True if all required variables are set, False otherwise
    """
    # Example: Check for a required API key
    # Uncomment and modify as needed for your tools
    # required_vars = ['REQUIRED_API_KEY']
    # missing = [var for var in required_vars if not os.getenv(var)]
    #
    # if missing:
    #     logger.error(f"Missing required environment variables: {', '.join(missing)}")
    #     return False

    # For this example tool, no environment variables are required
    return True


def process(input_data, output_path):
    """
    Main processing logic.

    Args:
        input_data: Input parameter
        output_path: Where to write output

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Processing input: {input_data}")

        # Your tool logic here
        result = f"Processed: {input_data}"

        # Ensure output directory exists
        ensure_tmp_dir()

        # Write output
        success = safe_file_write(output_path, result)

        if success:
            logger.info(f"Output written to: {output_path}")
            return True
        else:
            logger.error("Failed to write output")
            return False

    except Exception as e:
        logger.error(f"Processing failed: {str(e)}", exc_info=True)
        return False


def main():
    """Main entry point."""
    args = parse_arguments()

    # Validate environment
    if not validate_environment():
        sys.exit(1)

    # Process
    success = process(args.input, args.output)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
