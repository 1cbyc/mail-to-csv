"""Trust Wallet drop format: Key Phrase (numbered words) + Wallet Name."""

import re
from typing import Dict


def normalize_numbered_phrase(raw: str) -> str:
    pairs = re.findall(r'\b(\d+)\s*\.?\s*([a-zA-Z]+)\b', raw or '')
    if not pairs:
        return ''

    words_by_index = {}
    for number, word in pairs:
        index = int(number)
        words_by_index[index] = word

    return ' '.join(words_by_index[index] for index in sorted(words_by_index))


def extract_trust_drop(text: str) -> Dict[str, str]:
    data = {
        'wallet_name': '',
        'key_phrase_raw': '',
        'phrase': '',
    }
    if not text:
        return data

    name_match = re.search(
        r'Wallet Name:\s*(.+?)(?:\n|$)',
        text,
        re.IGNORECASE,
    )
    if name_match:
        data['wallet_name'] = name_match.group(1).strip()

    phrase_match = re.search(
        r'Key Phrase:\s*(.+?)(?=Wallet Name:|$)',
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if phrase_match:
        raw = phrase_match.group(1).strip()
        data['key_phrase_raw'] = raw
        numbered_phrase = normalize_numbered_phrase(raw)
        if numbered_phrase:
            data['phrase'] = numbered_phrase
        else:
            data['phrase'] = re.sub(r'\s+', ' ', raw).strip()

    return data


def looks_like_trust_drop(text: str, subject: str = '') -> bool:
    blob = f'{subject}\n{text}'.lower()
    return 'key phrase:' in blob or 'trust wallet drop' in blob
