.PHONY: setup env gmail yahoo extract wallet-pipeline clean

setup:
	python3 setup.py

env:
	@test -f .env || cp .env.example .env
	@echo "Edit .env with your Yahoo app password and Gmail paths."

gmail:
	python3 gmail_to_csv.py

yahoo:
	python3 yahoo_to_csv.py

extract:
	python3 extract_wallet_data.py

wallet-pipeline: gmail extract

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "Removed Python cache. CSV files in data/ are kept."

release:
	./scripts/release.sh $(TAG)
