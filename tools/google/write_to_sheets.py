#!/usr/bin/env python3
"""
Write data to Google Sheets.

This tool demonstrates Google API integration following WAT principles.
"""

import sys
import json
import argparse
import logging
from pathlib import Path

# Ensure project root is on path so auth module can be imported when run as a script
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from tools.google.auth import get_sheets_service, call_with_retry, SCOPES_WRITE

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def write_data(spreadsheet_id, range_name, values):
    """
    Write data to Google Sheets.

    Args:
        spreadsheet_id: ID of target spreadsheet
        range_name: Range in A1 notation (e.g., 'Sheet1!A1:B2')
        values: 2D list of values to write

    Returns:
        bool: True if successful
    """
    try:
        service = get_sheets_service(SCOPES_WRITE)
        body = {'values': values}

        def _call():
            return service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()

        result = call_with_retry(_call)
        logger.info(f"Successfully updated {result.get('updatedCells', 0)} cells")
        return True

    except Exception as e:
        logger.error(f"Failed to write to sheets: {str(e)}", exc_info=True)
        return False


def main():
    parser = argparse.ArgumentParser(description='Write data to Google Sheets')
    parser.add_argument(
        '--spreadsheet-id',
        required=True,
        help='Spreadsheet ID (from URL)'
    )
    parser.add_argument(
        '--range',
        required=True,
        help='Range in A1 notation (e.g., Sheet1!A1)'
    )
    parser.add_argument(
        '--data',
        required=True,
        help=(
            'Data to write. '
            'CSV format (default): semicolon-separated rows, comma-separated values e.g. "A1,B1;A2,B2". '
            'JSON format: 2D array e.g. \'[["hello, world","test"]]\'. '
            'Use --format json when values contain commas.'
        )
    )
    parser.add_argument(
        '--format',
        choices=['csv', 'json'],
        default='csv',
        help='Input format: csv (default) or json. Use json when values contain commas.'
    )

    args = parser.parse_args()

    if args.format == 'json':
        values = json.loads(args.data)
    else:
        values = [row.split(',') for row in args.data.split(';')]

    success = write_data(args.spreadsheet_id, args.range, values)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
