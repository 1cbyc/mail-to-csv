#!/usr/bin/env python3
"""
Wallet Data Extractor

This script extracts wallet-related data from Gmail CSV exports.
It looks for specific fields like Phrase, Keystore, Keystore Pass, and Private Key.
"""

import csv
import re
import argparse
import os
from typing import Dict, List, Optional

from mail_to_csv_env import load_env, ensure_data_dir, DATA_DIR

def extract_wallet_data(text: str) -> Dict[str, str]:
    """
    Extract wallet data from email body text with robust multi-line support.
    
    Args:
        text: Email body text
        
    Returns:
        Dictionary with extracted wallet data
    """
    data = {
        'phrase': '',
        'keystore': '',
        'keystore_pass': '',
        'private_key': ''
    }
    
    if not text:
        return data
    
    # Split text into lines and clean them
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Find the sections for each field
    sections = {}
    current_section = None
    current_content = []
    
    for line in lines:
        # Check if this line starts a new section
        if line.startswith('Phrase:'):
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = 'phrase'
            current_content = []
            # Extract content from the same line if it exists
            content = line[7:].strip()  # Remove "Phrase:"
            if content:
                current_content.append(content)
        elif line.startswith('Keystore:'):
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = 'keystore'
            current_content = []
            # Extract content from the same line if it exists
            content = line[9:].strip()  # Remove "Keystore:"
            if content:
                current_content.append(content)
        elif line.startswith('Keystore Pass:'):
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = 'keystore_pass'
            current_content = []
            # Extract content from the same line if it exists
            content = line[14:].strip()  # Remove "Keystore Pass:"
            if content:
                current_content.append(content)
        elif line.startswith('Private Key:'):
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = 'private_key'
            current_content = []
            # Extract content from the same line if it exists
            content = line[12:].strip()  # Remove "Private Key:"
            if content:
                current_content.append(content)
        elif line.startswith('Email sent'):
            # End of wallet data
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            break
        elif current_section:
            # This line belongs to the current section
            current_content.append(line)
    
    # Don't forget the last section
    if current_section and current_content:
        sections[current_section] = '\n'.join(current_content).strip()
    
    # Map sections to data
    if 'phrase' in sections:
        data['phrase'] = sections['phrase']
    if 'keystore' in sections:
        data['keystore'] = sections['keystore']
    if 'keystore_pass' in sections:
        data['keystore_pass'] = sections['keystore_pass']
    if 'private_key' in sections:
        data['private_key'] = sections['private_key']
    
    # Alternative extraction method for complex patterns
    if not any(data.values()):
        # Try regex-based extraction for more complex patterns
        normalized_text = text.replace('\n', ' ').replace('\r', ' ')
        
        # Extract Phrase - look for various patterns
        phrase_patterns = [
            r'Phrase:\s*([^K]+?)(?=\s*Keystore:)',
            r'Phrase:\s*([^K]+?)(?=\s*Keystore Pass:)',
            r'Phrase:\s*([^P]+?)(?=\s*Private Key:)',
            r'Phrase:\s*([^E]+?)(?=\s*Email sent)',
            r'Phrase:\s*(.+?)(?=\s*Email sent)',
            r'Phrase:\s*([^\n]+)'
        ]
        
        for pattern in phrase_patterns:
            phrase_match = re.search(pattern, normalized_text, re.IGNORECASE | re.DOTALL)
            if phrase_match:
                data['phrase'] = phrase_match.group(1).strip()
                break
        
        # Extract Keystore - look for various patterns
        keystore_patterns = [
            r'Keystore:\s*([^K]+?)(?=\s*Keystore Pass:)',
            r'Keystore:\s*([^P]+?)(?=\s*Private Key:)',
            r'Keystore:\s*([^E]+?)(?=\s*Email sent)',
            r'Keystore:\s*(.+?)(?=\s*Email sent)',
            r'Keystore:\s*([^\n]+)'
        ]
        
        for pattern in keystore_patterns:
            keystore_match = re.search(pattern, normalized_text, re.IGNORECASE | re.DOTALL)
            if keystore_match:
                data['keystore'] = keystore_match.group(1).strip()
                break
        
        # Extract Keystore Pass - look for various patterns
        keystore_pass_patterns = [
            r'Keystore Pass:\s*([^P]+?)(?=\s*Private Key:)',
            r'Keystore Pass:\s*([^E]+?)(?=\s*Email sent)',
            r'Keystore Pass:\s*(.+?)(?=\s*Email sent)',
            r'Keystore Pass:\s*([^\n]+)'
        ]
        
        for pattern in keystore_pass_patterns:
            keystore_pass_match = re.search(pattern, normalized_text, re.IGNORECASE | re.DOTALL)
            if keystore_pass_match:
                data['keystore_pass'] = keystore_pass_match.group(1).strip()
                break
        
        # Extract Private Key - look for various patterns
        private_key_patterns = [
            r'Private Key:\s*([^E]+?)(?=\s*Email sent)',
            r'Private Key:\s*(.+?)(?=\s*Email sent)',
            r'Private Key:\s*([^\n]+)'
        ]
        
        for pattern in private_key_patterns:
            private_key_match = re.search(pattern, normalized_text, re.IGNORECASE | re.DOTALL)
            if private_key_match:
                data['private_key'] = private_key_match.group(1).strip()
                break
    
    return data

def extract_from_csv(input_file: str, output_file: str) -> Dict[str, int]:
    """
    Extract wallet data from CSV file and create new CSV with extracted data.
    
    Args:
        input_file: Input CSV file path
        output_file: Output CSV file path
        
    Returns:
        Dictionary with statistics about the extraction
    """
    stats = {
        'total_emails': 0,
        'emails_with_phrase': 0,
        'emails_with_keystore': 0,
        'emails_with_keystore_pass': 0,
        'emails_with_private_key': 0,
        'emails_with_any_data': 0
    }
    
    extracted_data = []
    
    try:
        with open(input_file, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            
            for row in reader:
                stats['total_emails'] += 1
                
                # Extract wallet data from body
                wallet_data = extract_wallet_data(row.get('body', ''))
                
                # Add email metadata
                extracted_row = {
                    'email_id': row.get('id', ''),
                    'subject': row.get('subject', ''),
                    'from': row.get('from', ''),
                    'date': row.get('date', ''),
                    'phrase': wallet_data['phrase'],
                    'keystore': wallet_data['keystore'],
                    'keystore_pass': wallet_data['keystore_pass'],
                    'private_key': wallet_data['private_key']
                }
                
                # Update statistics
                if wallet_data['phrase']:
                    stats['emails_with_phrase'] += 1
                if wallet_data['keystore']:
                    stats['emails_with_keystore'] += 1
                if wallet_data['keystore_pass']:
                    stats['emails_with_keystore_pass'] += 1
                if wallet_data['private_key']:
                    stats['emails_with_private_key'] += 1
                if any(wallet_data.values()):
                    stats['emails_with_any_data'] += 1
                
                extracted_data.append(extracted_row)
        
        # Write extracted data to new CSV
        if extracted_data:
            with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
                fieldnames = ['email_id', 'subject', 'from', 'date', 'phrase', 'keystore', 'keystore_pass', 'private_key']
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(extracted_data)
            
            print(f"Successfully extracted data to '{output_file}'")
        else:
            print("No data found to extract")
            
    except FileNotFoundError:
        print(f"Input file '{input_file}' not found")
        return stats
    except Exception as e:
        print(f"Error processing file: {e}")
        return stats
    
    return stats

def analyze_csv_structure(input_file: str) -> None:
    """
    Analyze the CSV structure and show available fields.
    
    Args:
        input_file: Input CSV file path
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            
            # Get first few rows to analyze
            rows = []
            for i, row in enumerate(reader):
                if i >= 5:  # Analyze first 5 rows
                    break
                rows.append(row)
            
            if not rows:
                print("No data found in CSV file")
                return
            
            print("CSV Structure Analysis:")
            print("=" * 50)
            
            # Show available columns
            print(f"Available columns: {', '.join(rows[0].keys())}")
            print()
            
            # Show sample data
            for i, row in enumerate(rows, 1):
                print(f"Email {i}:")
                print(f"  Subject: {row.get('subject', 'N/A')}")
                print(f"  From: {row.get('from', 'N/A')}")
                print(f"  Date: {row.get('date', 'N/A')}")
                
                body = row.get('body', '')
                if body:
                    print(f"  Body preview: {body[:150]}...")
                    
                    # Show detected wallet fields
                    wallet_data = extract_wallet_data(body)
                    if any(wallet_data.values()):
                        print("   Detected wallet data:")
                        for field, value in wallet_data.items():
                            if value:
                                print(f"     {field}: {repr(value)}")
                            else:
                                print(f"     {field}: (empty)")
                    else:
                        print("   No wallet data detected")
                else:
                    print("   No body content")
                print()
                
    except FileNotFoundError:
        print(f"File '{input_file}' not found")
    except Exception as e:
        print(f"Error analyzing file: {e}")

def main():
    load_env()
    ensure_data_dir()
    default_input = str(DATA_DIR / os.getenv('GMAIL_EXPORT_CSV', 'gmail_sent.csv'))
    default_output = str(DATA_DIR / os.getenv('WALLET_EXPORT_CSV', 'wallet_data.csv'))

    parser = argparse.ArgumentParser(description='Extract wallet data from Gmail CSV exports')
    parser.add_argument('input', nargs='?', default=default_input, help='Input CSV file path')
    parser.add_argument('--output', '-o', default=default_output, help='Output CSV file path')
    parser.add_argument('--analyze', '-a', action='store_true', help='Analyze CSV structure without extracting')
    
    args = parser.parse_args()
    
    print("Wallet Data Extractor")
    print("=" * 30)
    
    if args.analyze:
        analyze_csv_structure(args.input)
    else:
        print(f"Processing: {args.input}")
        print(f"Output: {args.output}")
        print()
        
        stats = extract_from_csv(args.input, args.output)
        
        print("\nExtraction Statistics:")
        print("=" * 30)
        print(f"Total emails processed: {stats['total_emails']}")
        print(f"Emails with phrase: {stats['emails_with_phrase']}")
        print(f"Emails with keystore: {stats['emails_with_keystore']}")
        print(f"Emails with keystore pass: {stats['emails_with_keystore_pass']}")
        print(f"Emails with private key: {stats['emails_with_private_key']}")
        print(f"Emails with any wallet data: {stats['emails_with_any_data']}")

if __name__ == '__main__':
    main() 