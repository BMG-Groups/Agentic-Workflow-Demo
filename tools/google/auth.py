#!/usr/bin/env python3
"""
Shared Google authentication module for WAT framework tools.

Both read_from_sheets.py and write_to_sheets.py import from here.
Centralising auth means: update once, both tools benefit automatically.
"""

import time
import logging
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# Absolute paths — always found regardless of which directory runs the script
_PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
TOKEN_PATH = _PROJECT_ROOT / "token.json"
CREDENTIALS_PATH = _PROJECT_ROOT / "credentials.json"

SCOPES_WRITE = ['https://www.googleapis.com/auth/spreadsheets']
SCOPES_READ  = ['https://www.googleapis.com/auth/spreadsheets.readonly']


def get_sheets_service(scopes=None):
    """
    Authenticate and return a Google Sheets API service object.

    Args:
        scopes: OAuth scopes list. Defaults to SCOPES_WRITE.

    Returns:
        Google Sheets API service object.
    """
    if scopes is None:
        scopes = SCOPES_WRITE

    creds = None

    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                raise FileNotFoundError(
                    f"credentials.json not found at {CREDENTIALS_PATH}. "
                    "Download it from Google Cloud Console and place it in the project root."
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH), scopes
            )
            creds = flow.run_local_server(port=0)

        with open(str(TOKEN_PATH), 'w') as token:
            token.write(creds.to_json())

    return build('sheets', 'v4', credentials=creds)


def call_with_retry(fn, max_attempts=3, delay=5):
    """
    Call fn() up to max_attempts times, retrying on transient Google API errors.

    Retries on HTTP 429 (rate limit) and 503 (service unavailable).
    Raises immediately on any other error.

    Args:
        fn: Zero-argument callable that makes the API call.
        max_attempts: Maximum number of attempts (default: 3).
        delay: Seconds to wait between attempts (default: 5).

    Returns:
        The return value of fn() on success.
    """
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except HttpError as e:
            if e.resp.status in (429, 503) and attempt < max_attempts:
                logger.warning(
                    f"Google API returned {e.resp.status}. "
                    f"Retrying in {delay}s... (attempt {attempt}/{max_attempts})"
                )
                time.sleep(delay)
            else:
                raise
