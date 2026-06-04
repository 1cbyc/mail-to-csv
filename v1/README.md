# v1 — legacy wallet email format

Emails from the older pipeline use labeled blocks in the body:

```
Phrase:
...
Keystore:
...
Keystore Pass:
...
Private Key:
...
```

Usually exported from **sent** mail with `GMAIL_QUERY=in:sent "Phrase"`.

Run the legacy extractor only:

```bash
python v1/extract_wallet_data.py data/gmail_sent.csv -o data/wallet_data_v1.csv
```

Or from project root with the main script:

```bash
python extract_wallet_data.py data/gmail_sent.csv --format v1
```
