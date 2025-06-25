# Changelog

All notable changes to this project are documented in this file.

## [1.1.0] - 2025-06-25

### Added

- `.env.example` and `mail_to_csv_env.py` for shared configuration
- `data/` output directory with Makefile targets (`gmail`, `yahoo`, `extract`, `wallet-pipeline`)
- `WORKFLOW.md` with pipeline steps and recommended next tasks
- `python-dotenv` dependency
- Gmail `--token` flag and env-driven defaults for both providers

### Changed

- Default CSV outputs go under `data/` instead of project root
- Yahoo `--username` optional when `YAHOO_USERNAME` is set in `.env`
- `.gitignore` keeps `.env.example` tracked while ignoring `data/*.csv`

## [1.0.0] - 2025-06-22

### Added

- Gmail sent-mail export via Gmail API with OAuth2 and incremental CSV writing
- Yahoo Mail export via IMAP (app password) with sent-folder detection and phrase search
- Wallet field extractor with analyze mode
- Setup and OAuth troubleshooting helpers
- Local release script (`scripts/release.sh`)

### Fixed

- Gmail body extraction walks nested `multipart/*` MIME trees

### Security

- Credentials, tokens, `.env`, and CSV exports are excluded from git
