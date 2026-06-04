# Run on the other PC (Windows)

Use this when the Gmail account is logged in on a **Windows** machine. OAuth must finish **on that same PC** (browser hits `localhost` on that box).

## 1. Copy and unpack

Copy `mail-to-csv-portable.tar.gz` to the PC (USB, OneDrive, etc.).

**Option A — File Explorer:** Install [7-Zip](https://www.7zip.org/) if needed, right-click the `.tar.gz` → Extract.

**Option B — PowerShell (Windows 10+):**

```powershell
cd $HOME\Downloads
tar -xzf mail-to-csv-portable.tar.gz
cd mail-to-csv-portable
```

You should see `data3\credentials.json` inside the folder.

## 2. Install Python (if needed)

- Download [python.org](https://www.python.org/downloads/) → install → check **"Add python.exe to PATH"**.
- Open **PowerShell** and run: `python --version` (need 3.7+).

## 3. One-time setup

In PowerShell, from the project folder:

```powershell
cd path\to\mail-to-csv-portable
python scripts\cli.py bootstrap
```

That creates `.venv` and installs packages.

## 4. Google Cloud (if login blocked)

In the same Google Cloud project as `data3\credentials.json`:

- Gmail API enabled
- OAuth consent screen → **Test users** → add the Gmail address you are exporting

## 5. Export mail

```powershell
Remove-Item -Force data3\token.json -ErrorAction SilentlyContinue
python scripts\cli.py gmail data3
```

**Do not** paste Mac/bash lines with `\` at the end of each line. PowerShell does not use those. Or use this one line:

```powershell
.\.venv\Scripts\python.exe gmail_to_csv.py --credentials data3\credentials.json --token data3\token.json --output data3\gmail_sent.csv
```

When a URL prints:

1. Copy it into **Chrome/Edge on this Windows PC** (where that Gmail is logged in).
2. Click **Allow**.
3. Browser may show a blank localhost page — that is OK.
4. Terminal should say authentication succeeded and start exporting.

Output: `data3\gmail_sent.csv`

## 6. Wallet fields (optional)

```powershell
.\.venv\Scripts\python.exe extract_wallet_data.py data3\gmail_sent.csv -o data3\wallet_data.csv
```

## 7. Bring results back

Copy the whole `data3` folder (CSV + `token.json`) to your Mac. Do not upload to public cloud if the CSV has sensitive data.

---

## Command prompt (cmd) instead of PowerShell

```cmd
cd path\to\mail-to-csv-portable
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python.exe gmail_to_csv.py --credentials data3\credentials.json --token data3\token.json --output data3\gmail_sent.csv
```

---

## Yahoo on Windows

```cmd
copy .env.example .env
```

Edit `.env` with `YAHOO_USERNAME` and `YAHOO_APP_PASSWORD`, then:

```cmd
.venv\Scripts\python.exe yahoo_to_csv.py
```
