#!/usr/bin/env python3
"""
Read data from Google Sheets.

This tool fetches data from a Google Sheet and saves it to a local file.
"""

import os
import sys
import argparse
import logging
import csv
from pathlib import Path

# Ensure project root is on path so auth module can be imported when run as a script
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from tools.google.auth import get_sheets_service, call_with_retry, SCOPES_READ
from tools.utils.common import ensure_tmp_dir

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def read_data(spreadsheet_id, range_name, output_path):
    """
    Read data from Google Sheets and save to CSV.

    Args:
        spreadsheet_id: ID of source spreadsheet
        range_name: Range in A1 notation (e.g., 'Sheet1!A:Z')
        output_path: Where to save the CSV file

    Returns:
        bool: True if successful
    """
    try:
        service = get_sheets_service(SCOPES_READ)

        def _call():
            return service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()

        result = call_with_retry(_call)
        values = result.get('values', [])

        if not values:
            logger.warning("No data found in the specified range")
            return False

        # Ensure output directory exists
        ensure_tmp_dir()
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # Write to CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(values)

        logger.info(f"Successfully read {len(values)} rows and saved to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to read from sheets: {str(e)}", exc_info=True)
        return False


def main():
    parser = argparse.ArgumentParser(description='Read data from Google Sheets')
    parser.add_argument(
        '--spreadsheet-id',
        required=True,
        help='Spreadsheet ID (from URL)'
    )
    parser.add_argument(
        '--range',
        required=True,
        help='Range in A1 notation (e.g., Sheet1!A:Z)'
    )
    parser.add_argument(
        '--output',
        default='.tmp/sheet_data.csv',
        help='Output CSV file path (default: .tmp/sheet_data.csv)'
    )

    args = parser.parse_args()

    success = read_data(args.spreadsheet_id, args.range, args.output)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
