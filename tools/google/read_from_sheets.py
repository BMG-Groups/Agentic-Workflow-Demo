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
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from tools.utils.common import ensure_tmp_dir

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']


def get_sheets_service():
    """
    Authenticate and return Google Sheets service.

    Returns:
        Google Sheets API service object
    """
    creds = None

    # Token file stores user's access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If no valid credentials, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                logger.error("credentials.json not found. Please download it from Google Cloud Console.")
                logger.error("See README.md for setup instructions.")
                sys.exit(1)

            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save credentials for next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('sheets', 'v4', credentials=creds)


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
        service = get_sheets_service()

        # Read data
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()

        values = result.get('values', [])

        if not values:
            logger.warning("No data found in the specified range")
            return False

        # Ensure output directory exists
        ensure_tmp_dir()
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

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
