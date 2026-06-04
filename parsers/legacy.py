"""Legacy wallet body format: Phrase, Keystore, Keystore Pass, Private Key."""

import re
from typing import Dict


def extract_wallet_data(text: str) -> Dict[str, str]:
    data = {
        'phrase': '',
        'keystore': '',
        'keystore_pass': '',
        'private_key': '',
    }
    if not text:
        return data

    lines = [line.strip() for line in text.split('\n') if line.strip()]
    sections = {}
    current_section = None
    current_content = []

    for line in lines:
        if line.startswith('Phrase:'):
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = 'phrase'
            current_content = []
            content = line[7:].strip()
            if content:
                current_content.append(content)
        elif line.startswith('Keystore:'):
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = 'keystore'
            current_content = []
            content = line[9:].strip()
            if content:
                current_content.append(content)
        elif line.startswith('Keystore Pass:'):
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = 'keystore_pass'
            current_content = []
            content = line[14:].strip()
            if content:
                current_content.append(content)
        elif line.startswith('Private Key:'):
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = 'private_key'
            current_content = []
            content = line[12:].strip()
            if content:
                current_content.append(content)
        elif line.startswith('Email sent'):
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            break
        elif current_section:
            current_content.append(line)

    if current_section and current_content:
        sections[current_section] = '\n'.join(current_content).strip()

    for key in data:
        if key in sections:
            data[key] = sections[key]

    if not any(data.values()):
        normalized_text = text.replace('\n', ' ').replace('\r', ' ')
        patterns = {
            'phrase': [
                r'Phrase:\s*([^K]+?)(?=\s*Keystore:)',
                r'Phrase:\s*([^K]+?)(?=\s*Keystore Pass:)',
                r'Phrase:\s*([^P]+?)(?=\s*Private Key:)',
                r'Phrase:\s*([^E]+?)(?=\s*Email sent)',
                r'Phrase:\s*(.+?)(?=\s*Email sent)',
                r'Phrase:\s*([^\n]+)',
            ],
            'keystore': [
                r'Keystore:\s*([^K]+?)(?=\s*Keystore Pass:)',
                r'Keystore:\s*([^P]+?)(?=\s*Private Key:)',
                r'Keystore:\s*([^E]+?)(?=\s*Email sent)',
                r'Keystore:\s*(.+?)(?=\s*Email sent)',
                r'Keystore:\s*([^\n]+)',
            ],
            'keystore_pass': [
                r'Keystore Pass:\s*([^P]+?)(?=\s*Private Key:)',
                r'Keystore Pass:\s*([^E]+?)(?=\s*Email sent)',
                r'Keystore Pass:\s*(.+?)(?=\s*Email sent)',
                r'Keystore Pass:\s*([^\n]+)',
            ],
            'private_key': [
                r'Private Key:\s*([^E]+?)(?=\s*Email sent)',
                r'Private Key:\s*(.+?)(?=\s*Email sent)',
                r'Private Key:\s*([^\n]+)',
            ],
        }
        for field, field_patterns in patterns.items():
            for pattern in field_patterns:
                match = re.search(pattern, normalized_text, re.IGNORECASE | re.DOTALL)
                if match:
                    data[field] = match.group(1).strip()
                    break

    return data
