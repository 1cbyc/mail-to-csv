# Changelog

All notable changes to this project are documented in this file.

## [1.0.0] - 2025-06-22

### Added

- Gmail sent-mail export via Gmail API with OAuth2 and incremental CSV writing
- Yahoo Mail export via IMAP (app password) with sent-folder detection and phrase search
- Wallet field extractor (`Phrase`, `Keystore`, `Keystore Pass`, `Private Key`) with analyze mode
- Setup and OAuth troubleshooting helpers (`setup.py`, `fix_oauth.py`)
- Local release script (`scripts/release.sh`) for tags and source archives

### Fixed

- Gmail body extraction now walks nested `multipart/*` MIME trees (not only top-level parts)

### Security

- Credentials, tokens, `.env`, CSV exports, and `data*/` directories are excluded from git
