"""Filter exported mail CSV by subject keywords and/or wallet-like body content."""

import argparse
import csv
import sys
from typing import List

from parsers.secrets import body_has_secrets

csv.field_size_limit(sys.maxsize)

DEFAULT_SUBJECT_KEYWORDS = ['new', 'drop', 'trust', 'atomic', 'wallet']


def subject_matches(subject: str, keywords: List[str], match_all: bool) -> bool:
    subject_lower = (subject or '').lower()
    hits = [kw.lower() in subject_lower for kw in keywords]
    return all(hits) if match_all else any(hits)


def filter_csv(
    input_file: str,
    output_file: str,
    keywords: List[str],
    match_all: bool,
    require_body_secrets: bool,
) -> int:
    kept = []
    with open(input_file, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        for row in reader:
            if not subject_matches(row.get('subject', ''), keywords, match_all):
                continue
            if require_body_secrets and not body_has_secrets(row.get('body', '')):
                continue
            kept.append(row)

    if not kept:
        print('No rows matched.')
        return 0

    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(kept)

    print(f'Wrote {len(kept)} rows to {output_file}')
    return len(kept)


def main():
    parser = argparse.ArgumentParser(description='Filter mail CSV by subject and body')
    parser.add_argument('input', help='Input CSV from gmail_to_csv.py')
    parser.add_argument('output', help='Filtered output CSV')
    parser.add_argument(
        '--keywords',
        default=','.join(DEFAULT_SUBJECT_KEYWORDS),
        help='Comma-separated subject words (default: new,drop,trust,atomic,wallet)',
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Require ALL keywords in subject (default: any keyword)',
    )
    parser.add_argument(
        '--require-body-secrets',
        action='store_true',
        help='Also require body to look like mnemonic/key/keystore/password',
    )
    args = parser.parse_args()
    keywords = [k.strip() for k in args.keywords.split(',') if k.strip()]
    filter_csv(
        args.input,
        args.output,
        keywords,
        args.all,
        args.require_body_secrets,
    )


if __name__ == '__main__':
    main()
