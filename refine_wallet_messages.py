#!/usr/bin/env python3
"""Refine exported Gmail rows to messages with Trust Wallet phrase text."""

import argparse
import csv
import sys
from typing import Dict, List

from parsers.trust_drop import extract_trust_drop

csv.field_size_limit(sys.maxsize)

SUBJECT_KEYWORDS = ['new', 'wallet', 'drop']
BODY_MARKERS = ['Key Phrase:', 'Wallet Name:']

FIELDNAMES = [
    'email_id',
    'subject',
    'from',
    'date',
    'wallet_name',
    'key_phrase_raw',
    'phrase',
    'body',
]


def subject_matches(subject: str, keywords: List[str]) -> bool:
    subject_lower = (subject or '').lower()
    return any(keyword.lower() in subject_lower for keyword in keywords)


def body_matches(body: str, markers: List[str]) -> bool:
    return all(marker.lower() in (body or '').lower() for marker in markers)


def refine(input_file: str, output_file: str, keywords: List[str], markers: List[str]) -> int:
    rows = []
    with open(input_file, newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            subject = row.get('subject', '')
            body = row.get('body', '')
            if not subject_matches(subject, keywords):
                continue
            if not body_matches(body, markers):
                continue

            trust = extract_trust_drop(body)
            rows.append({
                'email_id': row.get('id', ''),
                'subject': subject,
                'from': row.get('from', ''),
                'date': row.get('date', ''),
                'wallet_name': trust.get('wallet_name', ''),
                'key_phrase_raw': trust.get('key_phrase_raw', ''),
                'phrase': trust.get('phrase', ''),
                'body': body,
            })

    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f'Wrote {len(rows)} refined rows to {output_file}')
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description='Refine Gmail CSV to Trust Wallet message text')
    parser.add_argument('input', help='Input CSV from gmail_to_csv.py')
    parser.add_argument('output', help='Output CSV for refined rows')
    parser.add_argument(
        '--keywords',
        default=','.join(SUBJECT_KEYWORDS),
        help='Comma-separated subject keywords (default: new,wallet,drop)',
    )
    parser.add_argument(
        '--markers',
        default='|'.join(BODY_MARKERS),
        help='Pipe-separated body markers that must all appear',
    )
    args = parser.parse_args()

    keywords = [value.strip() for value in args.keywords.split(',') if value.strip()]
    markers = [value.strip() for value in args.markers.split('|') if value.strip()]
    refine(args.input, args.output, keywords, markers)


if __name__ == '__main__':
    main()
