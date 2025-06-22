#!/usr/bin/env python3
"""
Yahoo Sent Emails to CSV Exporter

This script exports sent emails from Yahoo Mail to a CSV file using IMAP (SSL).
It includes login with an app password, mailbox detection, optional phrase
filtering, pagination-like batching, and incremental CSV writing.

Notes:
- Yahoo requires an App Password (not your normal account password) for IMAP.
- Create one at: Account Security > Generate app password.
"""

import os
import csv
import ssl
import imaplib
import email
from email.message import Message
import argparse
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import time

IMAP_HOST = 'imap.mail.yahoo.com'
IMAP_PORT = 993

class YahooExporter:
    def __init__(self, username: str, password: str, mailbox_hint: Optional[str] = None):
        self.username = username
        self.password = password
        self.mailbox_hint = mailbox_hint
        self.conn: Optional[imaplib.IMAP4_SSL] = None

    def connect(self) -> bool:
        try:
            context = ssl.create_default_context()
            self.conn = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT, ssl_context=context)
            typ, _ = self.conn.login(self.username, self.password)
            if typ != 'OK':
                print('Login failed.')
                return False
            return True
        except imaplib.IMAP4.error as e:
            print(f"IMAP error during login: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error during login: {e}")
            return False

    def close(self) -> None:
        try:
            if self.conn is not None:
                try:
                    self.conn.close()
                except Exception:
                    pass
                self.conn.logout()
        except Exception:
            pass

    def _list_mailboxes(self) -> List[str]:
        if self.conn is None:
            return []
        typ, boxes = self.conn.list()
        if typ != 'OK' or boxes is None:
            return []
        mailbox_names: List[str] = []
        for raw in boxes:
            # raw is like: b'(\\HasNoChildren) "/" "[Yahoo]/Sent"'
            try:
                parts = raw.decode('utf-8', errors='ignore').split(' "')
                if len(parts) >= 2:
                    name = parts[-1].rstrip('"')
                    mailbox_names.append(name)
            except Exception:
                continue
        return mailbox_names

    def _detect_sent_mailbox(self) -> Optional[str]:
        if self.conn is None:
            return None
        if self.mailbox_hint:
            # Try the provided mailbox first
            typ, _ = self.conn.select(self.mailbox_hint, readonly=True)
            if typ == 'OK':
                return self.mailbox_hint
        # Fallback: discover likely Sent folders
        candidates = ['[Yahoo]/Sent', 'Sent', 'Sent Items', 'Sent Mail']
        mailboxes = self._list_mailboxes()
        lower_to_actual = {m.lower(): m for m in mailboxes}
        for c in candidates:
            if c.lower() in lower_to_actual:
                mbox = lower_to_actual[c.lower()]
                typ, _ = self.conn.select(mbox, readonly=True)
                if typ == 'OK':
                    return mbox
        # Heuristic: any mailbox containing 'sent'
        for m in mailboxes:
            if 'sent' in m.lower():
                typ, _ = self.conn.select(m, readonly=True)
                if typ == 'OK':
                    return m
        return None

    def _search_uids(self, phrase: Optional[str]) -> List[bytes]:
        if self.conn is None:
            return []
        
        print(f"Searching for messages{' with phrase: ' + phrase if phrase else ''}...")
        
        # Try multiple search strategies to get all messages
        all_uids = set()
        
        # Strategy 1: Search with phrase if provided
        if phrase:
            criteria = ['TEXT', f'"{phrase}"']
            try:
                typ, data = self.conn.uid('SEARCH', *criteria)
                if typ == 'OK' and data and len(data) > 0:
                    uids = data[0].split()
                    all_uids.update(uids)
                    print(f"Found {len(uids)} messages with phrase '{phrase}'")
            except Exception as e:
                print(f"Phrase search error: {e}")
        
        # Strategy 2: Get ALL messages (no date filter)
        try:
            typ, data = self.conn.uid('SEARCH', 'ALL')
            if typ == 'OK' and data and len(data) > 0:
                all_uids_list = data[0].split()
                print(f"Total messages in mailbox: {len(all_uids_list)}")
                
                # If we have a phrase, filter the results
                if phrase:
                    # We need to check each message for the phrase
                    print(f"Filtering {len(all_uids_list)} messages for phrase '{phrase}'...")
                    filtered_uids = []
                    for uid in all_uids_list:
                        try:
                            # Fetch just headers and body to check for phrase
                            typ, msg_data = self.conn.uid('FETCH', uid, '(RFC822)')
                            if typ == 'OK' and msg_data:
                                for part in msg_data:
                                    if isinstance(part, tuple):
                                        try:
                                            msg = email.message_from_bytes(part[1])
                                            # Check subject and body for phrase
                                            subject = msg.get('Subject', '') or ''
                                            body = self._extract_body(msg)
                                            if phrase.lower() in (subject + body).lower():
                                                filtered_uids.append(uid)
                                                break
                                        except Exception:
                                            continue
                        except Exception:
                            continue
                    all_uids = set(filtered_uids)
                    print(f"After filtering: {len(all_uids)} messages contain '{phrase}'")
                else:
                    all_uids = set(all_uids_list)
        except Exception as e:
            print(f"ALL search error: {e}")
        
        # Strategy 3: Try date-based searches if we still have few results
        if len(all_uids) < 1000:  # If we have very few results, try broader searches
            print("Trying broader date-based searches...")
            date_ranges = [
                ('BEFORE', '2025-01-01'),  # Before 2025
                ('SINCE', '2024-01-01'),   # Since 2024
                ('SINCE', '2023-01-01'),   # Since 2023
                ('SINCE', '2022-01-01'),   # Since 2022
            ]
            
            for date_criteria, date_value in date_ranges:
                try:
                    if phrase:
                        criteria = [date_criteria, date_value, 'TEXT', f'"{phrase}"']
                    else:
                        criteria = [date_criteria, date_value]
                    
                    typ, data = self.conn.uid('SEARCH', *criteria)
                    if typ == 'OK' and data and len(data) > 0:
                        uids = data[0].split()
                        all_uids.update(uids)
                        print(f"Found {len(uids)} messages {date_criteria} {date_value}")
                except Exception as e:
                    print(f"Date search error for {date_criteria} {date_value}: {e}")
        
        final_uids = list(all_uids)
        print(f"Total unique messages found: {len(final_uids)}")
        return final_uids

    def _fetch_email(self, uid: bytes) -> Optional[Message]:
        if self.conn is None:
            return None
        try:
            typ, msg_data = self.conn.uid('FETCH', uid, '(RFC822)')
            if typ != 'OK' or not msg_data:
                return None
            for part in msg_data:
                if isinstance(part, tuple):
                    try:
                        return email.message_from_bytes(part[1])
                    except Exception:
                        return None
            return None
        except Exception as e:
            print(f"Error fetching email {uid}: {e}")
            return None

    def _extract_body(self, msg: Message) -> str:
        if msg.is_multipart():
            # Prefer text/plain, fallback to text/html
            for part in msg.walk():
                ctype = part.get_content_type()
                disp = str(part.get('Content-Disposition') or '')
                if ctype == 'text/plain' and 'attachment' not in disp:
                    try:
                        return part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', errors='ignore')
                    except Exception:
                        continue
            for part in msg.walk():
                ctype = part.get_content_type()
                disp = str(part.get('Content-Disposition') or '')
                if ctype == 'text/html' and 'attachment' not in disp:
                    try:
                        return part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', errors='ignore')
                    except Exception:
                        continue
            return ''
        else:
            try:
                payload = msg.get_payload(decode=True)
                if payload is None:
                    return ''
                return payload.decode(msg.get_content_charset() or 'utf-8', errors='ignore')
            except Exception:
                return ''

    def _parse_email(self, uid: bytes, msg: Message) -> Dict:
        headers = msg
        subject = headers.get('Subject', '') or ''
        from_header = headers.get('From', '') or ''
        to_header = headers.get('To', '') or ''
        cc_header = headers.get('Cc', '') or ''
        date_header = headers.get('Date', '') or ''
        # Normalize/format date if possible
        try:
            parsed_date = email.utils.parsedate_to_datetime(date_header)
            formatted_date = parsed_date.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            formatted_date = date_header
        body = self._extract_body(msg)
        return {
            'id': uid.decode('utf-8', errors='ignore'),
            'thread_id': '',  # IMAP does not expose threads in the same way
            'subject': subject,
            'from': from_header,
            'to': to_header,
            'cc': cc_header,
            'date': formatted_date,
            'snippet': body[:120].replace('\n', ' ').replace('\r', ' '),
            'body': body,
            'labels': 'INBOX'
        }

    def export_sent(self, output_file: str, max_results: Optional[int] = None, phrase: Optional[str] = None) -> int:
        if self.conn is None:
            print('Not connected.')
            return 0
        
        # Use the specified mailbox or detect sent mailbox
        if self.mailbox_hint:
            target_mailbox = self.mailbox_hint
        else:
            target_mailbox = self._detect_sent_mailbox()
        
        if not target_mailbox:
            print('Could not find target mailbox.')
            return 0
        
        print(f"Using mailbox: {target_mailbox}")
        
        # Select the mailbox
        typ, _ = self.conn.select(target_mailbox, readonly=True)
        if typ != 'OK':
            print(f"Failed to select mailbox {target_mailbox}")
            return 0

        # Get UIDs
        uids = self._search_uids(phrase)
        if not uids:
            print('No messages found.')
            return 0
        
        # Show total count
        total_found = len(uids)
        print(f"Total messages found: {total_found}")
        
        # Apply max_results limit if specified
        if max_results is not None and max_results > 0:
            uids = uids[:max_results]
            print(f"Processing first {len(uids)} messages (limited by --max-results)")
        
        # Process in batches to avoid timeouts
        batch_size = 50
        count = 0
        errors = 0
        
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['id', 'thread_id', 'subject', 'from', 'to', 'cc', 'date', 'snippet', 'body', 'labels']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                print(f"Writing to '{output_file}' incrementally...")
                
                for i in range(0, len(uids), batch_size):
                    batch = uids[i:i + batch_size]
                    print(f"Processing batch {i//batch_size + 1} ({len(batch)} messages)...")
                    
                    for uid in batch:
                        try:
                            msg = self._fetch_email(uid)
                            if msg is None:
                                errors += 1
                                continue
                            row = self._parse_email(uid, msg)
                            writer.writerow(row)
                            csvfile.flush()
                            count += 1
                            if count % 10 == 0:  # Progress every 10 messages
                                subj_preview = (row.get('subject') or '')[:50]
                                print(f"Processed {count}/{len(uids)}: {subj_preview}...")
                        except Exception as e:
                            print(f"Error processing email {uid}: {e}")
                            errors += 1
                            continue
                    
                    # Small delay between batches to avoid overwhelming the server
                    if i + batch_size < len(uids):
                        time.sleep(0.5)
                        
        except Exception as e:
            print(f"Error writing CSV: {e}")
            return count
        
        print(f"\nExport completed!")
        print(f"Successfully processed: {count} messages")
        print(f"Errors encountered: {errors}")
        print(f"Output file: {output_file}")
        
        return count

def main():
    parser = argparse.ArgumentParser(description='Export Yahoo emails to CSV via IMAP')
    parser.add_argument('--username', required=True, help='Yahoo email address (username)')
    parser.add_argument('--password', help='Yahoo App Password (or set YAHOO_APP_PASSWORD env)')
    parser.add_argument('--mailbox', help='Mailbox name (e.g., "INBOX", "[Yahoo]/Sent")')
    parser.add_argument('--output', default='yahoo_emails.csv', help='Output CSV file path')
    parser.add_argument('--max-results', type=int, help='Maximum number of emails to export (default: all)')
    parser.add_argument('--query', help='Phrase to search for within messages (uses IMAP TEXT search)')

    args = parser.parse_args()

    password = args.password or os.getenv('YAHOO_APP_PASSWORD')
    if not password:
        print('Missing Yahoo App Password. Pass --password or set YAHOO_APP_PASSWORD.')
        return

    print('Yahoo Emails to CSV Exporter')
    print('=' * 40)

    exporter = YahooExporter(username=args.username, password=password, mailbox_hint=args.mailbox)

    print('Connecting to Yahoo IMAP...')
    if not exporter.connect():
        print('Connection or login failed. Exiting.')
        return
    print('Connected!')

    try:
        print('Retrieving and exporting emails...')
        total = exporter.export_sent(
            output_file=args.output,
            max_results=args.max_results,
            phrase=args.query
        )
    finally:
        exporter.close()

if __name__ == '__main__':
    main()
