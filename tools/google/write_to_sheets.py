#!/usr/bin/env python3
"""
Write data to Google Sheets.

This tool demonstrates Google API integration following WAT principles.
"""

import os
import sys
import argparse
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


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
        service = get_sheets_service()

        body = {'values': values}
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()

        updated_cells = result.get('updatedCells', 0)
        logger.info(f"Successfully updated {updated_cells} cells")
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
        help='Semicolon-separated rows, comma-separated values (e.g., "A1,B1;A2,B2")'
    )

    args = parser.parse_args()

    # Parse CSV data into 2D list
    values = [row.split(',') for row in args.data.split(';')]

    success = write_data(args.spreadsheet_id, args.range, values)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
