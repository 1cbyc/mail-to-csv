#!/usr/bin/env python3
"""
Gmail Sent Emails to CSV Exporter

This script exports sent emails from Gmail to a CSV file using the Gmail API.
It includes authentication, pagination, and proper error handling.
"""

import os
import csv
import base64
import email
from datetime import datetime
from typing import List, Dict, Optional
import argparse
import json

from mail_to_csv_env import load_env, ensure_data_dir, env_path, DATA_DIR

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("Required packages not found. Please install them using:")
    print("pip install -r requirements.txt")
    exit(1)

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailExporter:
    def __init__(self, credentials_file: str = 'credentials.json', token_file: str = 'token.json'):
        """
        Initialize the Gmail exporter.
        
        Args:
            credentials_file: Path to the credentials.json file
            token_file: Path to store the token.json file
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        
    def authenticate(self) -> bool:
        """
        Authenticate with Gmail API.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        creds = None
        
        # Load existing token if available
        if os.path.exists(self.token_file):
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
            except Exception as e:
                print(f"Error loading token: {e}")
                creds = None
        
        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing token: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(self.credentials_file):
                    print(f"Credentials file '{self.credentials_file}' not found.")
                    print("Please download it from Google Cloud Console and place it in the current directory.")
                    return False
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    print(f"Error during authentication: {e}")
                    return False
            
            # Save credentials for next run
            try:
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                print(f"Error saving token: {e}")
        
        # Build the service
        try:
            self.service = build('gmail', 'v1', credentials=creds)
            return True
        except Exception as e:
            print(f"Error building service: {e}")
            return False
    
    def get_sent_emails(self, max_results: int = 1000, query: str = None, output_file: str = None) -> List[Dict]:
        """
        Retrieve sent emails from Gmail and optionally write to CSV incrementally.
        
        Args:
            max_results: Maximum number of emails to retrieve
            query: Gmail search query (optional)
            output_file: CSV file to write to incrementally (optional)
            
        Returns:
            List of email data dictionaries
        """
        if not self.service:
            print("Service not initialized. Please authenticate first.")
            return []
        
        emails = []
        page_token = None
        results_count = 0
        
        # Default query for sent emails
        if not query:
            query = "in:sent"
        
        # Setup CSV writer if output file is specified
        csv_writer = None
        csv_file = None
        if output_file:
            try:
                csv_file = open(output_file, 'w', newline='', encoding='utf-8')
                fieldnames = ['id', 'thread_id', 'subject', 'from', 'to', 'cc', 'date', 'snippet', 'body', 'labels']
                csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                csv_writer.writeheader()
                print(f"Writing to '{output_file}' incrementally...")
            except Exception as e:
                print(f"Error opening CSV file: {e}")
                output_file = None
        
        try:
            while results_count < max_results:
                # Get list of messages
                results = self.service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=min(100, max_results - results_count),
                    pageToken=page_token
                ).execute()
                
                messages = results.get('messages', [])
                if not messages:
                    break
                
                # Get full message details
                for message in messages:
                    if results_count >= max_results:
                        break
                    
                    try:
                        msg = self.service.users().messages().get(
                            userId='me',
                            id=message['id'],
                            format='full'
                        ).execute()
                        
                        email_data = self._parse_email(msg)
                        if email_data:
                            emails.append(email_data)
                            results_count += 1
                            
                            # Write to CSV incrementally
                            if csv_writer:
                                csv_writer.writerow(email_data)
                                csv_file.flush()  # Ensure data is written immediately
                                print(f"Processed email {results_count}: {email_data.get('subject', 'No subject')[:50]}...")
                            
                    except HttpError as error:
                        print(f"Error retrieving message {message['id']}: {error}")
                        continue
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
                    
        except HttpError as error:
            print(f"Error retrieving messages: {error}")
        finally:
            if csv_file:
                csv_file.close()
        
        return emails
    
    def _parse_email(self, msg: Dict) -> Optional[Dict]:
        """
        Parse email message and extract relevant data.
        
        Args:
            msg: Gmail message object
            
        Returns:
            Dictionary with email data or None if parsing fails
        """
        try:
            headers = msg['payload']['headers']
            
            # Extract header information
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            from_header = next((h['value'] for h in headers if h['name'] == 'From'), '')
            to_header = next((h['value'] for h in headers if h['name'] == 'To'), '')
            cc_header = next((h['value'] for h in headers if h['name'] == 'Cc'), '')
            date_header = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Parse date
            try:
                parsed_date = email.utils.parsedate_to_datetime(date_header)
                formatted_date = parsed_date.strftime('%Y-%m-%d %H:%M:%S')
            except:
                formatted_date = date_header
            
            # Extract body
            body = self._extract_body(msg['payload'])
            
            return {
                'id': msg['id'],
                'thread_id': msg['threadId'],
                'subject': subject,
                'from': from_header,
                'to': to_header,
                'cc': cc_header,
                'date': formatted_date,
                'snippet': msg.get('snippet', ''),
                'body': body,
                'labels': ', '.join(msg.get('labelIds', []))
            }
            
        except Exception as e:
            print(f"Error parsing email: {e}")
            return None
    
    def _decode_part_body(self, part: Dict) -> str:
        """Decode a single MIME part body if present."""
        body = part.get('body') or {}
        data = body.get('data')
        if not data:
            return ''
        return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')

    def _extract_body(self, payload: Dict) -> str:
        """
        Extract email body from payload (handles nested multipart).
        Prefers text/plain over text/html.
        """
        plain_parts: List[str] = []
        html_parts: List[str] = []

        def walk(part: Dict) -> None:
            mime = part.get('mimeType', '')
            if mime.startswith('multipart/'):
                for child in part.get('parts', []):
                    walk(child)
                return
            if mime == 'text/plain':
                text = self._decode_part_body(part)
                if text:
                    plain_parts.append(text)
            elif mime == 'text/html':
                text = self._decode_part_body(part)
                if text:
                    html_parts.append(text)

        try:
            walk(payload)
            if plain_parts:
                return '\n'.join(plain_parts)
            if html_parts:
                return '\n'.join(html_parts)
        except Exception as e:
            print(f"Error extracting body: {e}")

        return ''
    
    def export_to_csv(self, emails: List[Dict], output_file: str = 'sent_emails.csv') -> bool:
        """
        Export emails to CSV file (legacy method - use get_sent_emails with output_file instead).
        
        Args:
            emails: List of email dictionaries
            output_file: Output CSV file path
            
        Returns:
            bool: True if export successful, False otherwise
        """
        if not emails:
            print("No emails to export.")
            return False
        
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['id', 'thread_id', 'subject', 'from', 'to', 'cc', 'date', 'snippet', 'body', 'labels']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for email_data in emails:
                    writer.writerow(email_data)
            
            print(f"Successfully exported {len(emails)} emails to '{output_file}'")
            return True
            
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False

def main():
    load_env()
    ensure_data_dir()
    default_output = str(DATA_DIR / os.getenv('GMAIL_EXPORT_CSV', 'gmail_sent.csv'))
    default_query = os.getenv('GMAIL_QUERY', 'in:sent')

    parser = argparse.ArgumentParser(description='Export sent Gmail emails to CSV')
    parser.add_argument(
        '--credentials',
        default=str(env_path('GMAIL_CREDENTIALS', 'credentials.json')),
        help='Path to credentials.json (or GMAIL_CREDENTIALS)',
    )
    parser.add_argument('--token', default=str(env_path('GMAIL_TOKEN', 'token.json')), help='OAuth token file (or GMAIL_TOKEN)')
    parser.add_argument('--output', default=default_output, help='Output CSV file path')
    parser.add_argument('--max-results', type=int, default=1000, help='Maximum number of emails to export')
    parser.add_argument('--query', default=None, help=f'Gmail search query (default: {default_query})')
    parser.add_argument('--no-incremental', action='store_true', help='Disable incremental CSV writing')
    
    args = parser.parse_args()
    if not args.query:
        args.query = default_query
    
    print("Gmail Sent Emails to CSV Exporter")
    print("=" * 40)
    
    # Initialize exporter
    exporter = GmailExporter(credentials_file=args.credentials, token_file=args.token)
    
    # Authenticate
    print("Authenticating with Gmail API...")
    if not exporter.authenticate():
        print("Authentication failed. Exiting.")
        return
    
    print("Authentication successful!")
    
    # Get sent emails with incremental CSV writing
    print(f"Retrieving sent emails (max: {args.max_results})...")
    
    if args.no_incremental:
        # Legacy mode - collect all emails first, then export
        emails = exporter.get_sent_emails(max_results=args.max_results, query=args.query)
        
        if not emails:
            print("No emails found.")
            return
        
        print(f"Found {len(emails)} emails.")
        
        # Export to CSV
        print(f"Exporting to '{args.output}'...")
        if exporter.export_to_csv(emails, args.output):
            print("Export completed successfully!")
        else:
            print("Export failed.")
    else:
        # New incremental mode - write to CSV as emails are processed
        emails = exporter.get_sent_emails(
            max_results=args.max_results, 
            query=args.query, 
            output_file=args.output
        )
        
        if not emails:
            print("No emails found.")
            return
        
        print(f"\nExport completed! Found and exported {len(emails)} emails to '{args.output}'")

if __name__ == '__main__':
    main() 