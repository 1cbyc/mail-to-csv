"""Detect wallet-like secrets in email bodies."""

import re
from typing import Dict


LABELED_PATTERNS = [
    r'\bphrase\s*:',
    r'\bkey phrase\s*:',
    r'\bkeystore\s*:',
    r'\bkeystore pass\s*:',
    r'\bprivate key\s*:',
    r'\bseed phrase\s*:',
    r'\brecovery phrase\s*:',
    r'\bsecret phrase\s*:',
    r'\bwallet name\s*:',
    r'\bpassword\s*:',
    r'\bpassphrase\s*:',
]

# 64-char hex private key (with or without 0x)
HEX_PRIVATE_KEY = re.compile(r'\b(?:0x)?[a-fA-F0-9]{64}\b')

# Trust-wallet style: 1mixture 2bracket ... (12+ indexed words)
NUMBERED_MNEMONIC = re.compile(
    r'(?:\b(?:[1-9]|1[0-2])[a-zA-Z]{3,}\b\s*){12,}'
)

# 12-24 space-separated lowercase words (rough mnemonic check)
WORD_LIST_MNEMONIC = re.compile(
    r'\b(?:[a-z]{3,}\s+){11,23}[a-z]{3,}\b'
)


def scan_body(body: str) -> Dict[str, bool]:
    text = body or ''
    lower = text.lower()
    return {
        'labeled_fields': any(re.search(p, lower) for p in LABELED_PATTERNS),
        'private_key_hex': bool(HEX_PRIVATE_KEY.search(text)),
        'numbered_mnemonic': bool(NUMBERED_MNEMONIC.search(text)),
        'word_list_mnemonic': bool(WORD_LIST_MNEMONIC.search(lower)),
        'keystore_json': 'crypto' in lower and '"ciphertext"' in lower,
    }


def body_has_secrets(body: str) -> bool:
    flags = scan_body(body)
    if flags['labeled_fields'] or flags['private_key_hex'] or flags['numbered_mnemonic']:
        return True
    if flags['keystore_json']:
        return True
    # Plain word-list only when a wallet label is nearby
    if flags['word_list_mnemonic'] and flags['labeled_fields']:
        return True
    return False


def secret_types(body: str) -> str:
    flags = scan_body(body)
    hits = [name for name, ok in flags.items() if ok]
    return ','.join(hits)
