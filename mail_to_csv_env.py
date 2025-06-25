"""Shared environment and path defaults for mail-to-csv scripts."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("OUTPUT_DIR", PROJECT_ROOT / "data"))


def load_env() -> None:
    """Load .env from project root when python-dotenv is installed."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(PROJECT_ROOT / ".env")


def ensure_data_dir() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def env_path(key: str, default: str) -> Path:
    return Path(os.getenv(key, default))
