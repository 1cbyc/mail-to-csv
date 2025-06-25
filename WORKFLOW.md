# Workflow

End-to-end steps for exporting mail and pulling wallet fields into CSV.

## One-time setup

```bash
pip install -r requirements.txt
make env          # creates .env from .env.example
```

1. Fill in `.env` (Yahoo username + app password at minimum).
2. Place Gmail `credentials.json` in the project root (or set `GMAIL_CREDENTIALS`).
3. Run `make setup` if you still need Google Cloud / OAuth guidance.

## Gmail pipeline

```bash
# Export sent mail (default query: in:sent "Phrase" - override with GMAIL_QUERY in .env)
make gmail
# -> data/gmail_sent.csv

# Extract wallet fields
make extract
# -> data/wallet_data.csv
```

Or in one step:

```bash
make wallet-pipeline
```

Useful overrides:

```bash
python3 gmail_to_csv.py --query 'in:sent after:2024/01/01' --output data/2024_sent.csv --max-results 5000
python3 extract_wallet_data.py data/2024_sent.csv -o data/2024_wallet.csv --analyze
```

## Yahoo pipeline

```bash
make yahoo
# -> data/yahoo_inbox.csv (mailbox and phrase from .env)
```

Examples:

```bash
python3 yahoo_to_csv.py --mailbox "[Yahoo]/Sent" --query "Phrase" --output data/yahoo_sent_phrase.csv
python3 yahoo_to_csv.py --max-results 500
```

## What to do next (recommended order)

| Priority | Task | Why |
|----------|------|-----|
| 1 | Finish Yahoo inbox export with `YAHOO_PHRASE` | Prior inbox export only had a header row; re-run into `data/` |
| 2 | Re-run Gmail phrase export into `data/` | Keeps Gmail and Yahoo outputs in one place for comparison |
| 3 | Run `make extract` on the latest Gmail CSV | Produces structured `wallet_data.csv` |
| 4 | Spot-check with `--analyze` | Confirms body format before bulk extraction |

## Output layout

```
data/
  gmail_sent.csv      # Gmail export (default)
  yahoo_inbox.csv     # Yahoo export (default)
  wallet_data.csv     # Extracted fields
```

Credentials and tokens stay in the project root (or paths in `.env`). They are gitignored.

## Security

- Never commit `.env`, `credentials.json`, `token.json`, or `data/*.csv`.
- Treat `data/wallet_data.csv` like key material: encrypted disk, no cloud sync.
