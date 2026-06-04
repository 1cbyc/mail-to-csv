#!/usr/bin/env python3
"""Project helpers: venv setup, per-account Gmail export, portable package, release archive."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PORTABLE_FILES = (
    "gmail_to_csv.py",
    "yahoo_to_csv.py",
    "extract_wallet_data.py",
    "mail_to_csv_env.py",
    "fix_oauth.py",
    "setup.py",
    "requirements.txt",
    "Makefile",
    "README.md",
    "WORKFLOW.md",
    "TROUBLESHOOTING.md",
    "CHANGELOG.md",
    ".env.example",
    ".gitignore",
)
PORTABLE_DIRS = ("data", "scripts", "parsers", "v1")


def venv_python() -> Path:
    if sys.platform == "win32":
        return ROOT / ".venv" / "Scripts" / "python.exe"
    return ROOT / ".venv" / "bin" / "python"


def cmd_bootstrap(_: argparse.Namespace) -> int:
    python = sys.executable
    venv_dir = ROOT / ".venv"
    if not venv_dir.exists():
        subprocess.check_call([python, "-m", "venv", str(venv_dir)], cwd=ROOT)
    pip = venv_python().parent / ("pip.exe" if sys.platform == "win32" else "pip")
    subprocess.check_call([str(pip), "install", "-U", "pip"], cwd=ROOT)
    subprocess.check_call([str(pip), "install", "-r", "requirements.txt"], cwd=ROOT)
    print("Ready. Examples:")
    print(f"  {venv_python()} gmail_to_csv.py")
    print(f"  {venv_python()} scripts/cli.py gmail data3")
    return 0


def cmd_gmail(args: argparse.Namespace) -> int:
    account = Path(args.account)
    if not account.is_absolute():
        account = ROOT / account
    creds = account / "credentials.json"
    token = account / "token.json"
    output = account / args.output

    if not creds.is_file():
        print(f"Missing {creds}", file=sys.stderr)
        return 1

    py = venv_python()
    if not py.is_file():
        print("No .venv — run: python scripts/cli.py bootstrap", file=sys.stderr)
        return 1

    print(f"Account folder: {account.relative_to(ROOT)}")
    print("Open the OAuth URL on this machine when prompted.\n")
    return subprocess.call(
        [
            str(py),
            str(ROOT / "gmail_to_csv.py"),
            "--credentials",
            str(creds),
            "--token",
            str(token),
            "--output",
            str(output),
            *args.extra,
        ],
        cwd=ROOT,
    )


def cmd_package(args: argparse.Namespace) -> int:
    name = "mail-to-csv-portable"
    releases = ROOT / "releases"
    releases.mkdir(parents=True, exist_ok=True)
    archive = releases / f"{name}.tar.gz"
    stage = ROOT / "releases" / f".{name}-stage"
    if stage.exists():
        shutil.rmtree(stage)
    dest = stage / name
    dest.mkdir(parents=True)

    for filename in PORTABLE_FILES:
        src = ROOT / filename
        if src.is_file():
            shutil.copy2(src, dest / filename)

    for dirname in PORTABLE_DIRS:
        src = ROOT / dirname
        if not src.is_dir():
            continue
        target = dest / dirname
        target.mkdir(parents=True, exist_ok=True)
        for path in src.rglob("*"):
            if path.is_dir():
                continue
            rel = path.relative_to(src)
            if rel.parts and rel.parts[0] == "__pycache__":
                continue
            out = target / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, out)

    optional = Path(args.account) if args.account else None
    if optional:
        creds = ROOT / optional / "credentials.json"
        if creds.is_file():
            acct_dest = dest / optional
            acct_dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(creds, acct_dest / "credentials.json")
            print(f"Bundled {optional}/credentials.json for offline OAuth setup (no token).")
        else:
            print(f"No credentials at {creds}; skipped account bundle.", file=sys.stderr)

    with tarfile.open(archive, "w:gz") as tar:
        tar.add(dest, arcname=name)
    shutil.rmtree(stage)

    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum_file = releases / f"{name}.sha256"
    checksum_file.write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    print(f"Packaged: {archive}")
    print(f"Checksum: {checksum_file}")
    return 0


def cmd_release(args: argparse.Namespace) -> int:
    tag = args.tag
    if not tag:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print("No tag found. Example: git tag -a v1.1.0 -m 'v1.1.0'", file=sys.stderr)
            return 1
        tag = result.stdout.strip()

    releases = ROOT / "releases"
    releases.mkdir(parents=True, exist_ok=True)
    archive = releases / f"mail-to-csv-{tag}.tar.gz"
    prefix = f"mail-to-csv-{tag}/"
    with tarfile.open(archive, "w:gz") as tar:
        proc = subprocess.Popen(
            ["git", "archive", "--format=tar", tag],
            cwd=ROOT,
            stdout=subprocess.PIPE,
        )
        assert proc.stdout is not None
        with tarfile.open(fileobj=proc.stdout, mode="r|") as git_tar:
            for member in git_tar:
                member.name = prefix + member.name.lstrip("./")
                tar.addfile(member, git_tar.extractfile(member))
        proc.wait()
        if proc.returncode != 0:
            return proc.returncode

    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum = releases / f"mail-to-csv-{tag}.sha256"
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    print(f"Local release archive: {archive}")
    print(f"Checksum: {checksum}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="mail-to-csv project helpers")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("bootstrap", help="Create .venv and install requirements")

    gmail_p = sub.add_parser("gmail", help="Gmail export for a per-account folder")
    gmail_p.add_argument("account", help="Folder with credentials.json, e.g. data3")
    gmail_p.add_argument(
        "--output",
        default="gmail_sent.csv",
        help="Output CSV filename inside the account folder",
    )
    gmail_p.add_argument("extra", nargs=argparse.REMAINDER, help="Extra args for gmail_to_csv.py")

    pack_p = sub.add_parser("package", help="Build portable tarball under releases/")
    pack_p.add_argument(
        "--account",
        metavar="FOLDER",
        help="Optionally bundle FOLDER/credentials.json for another PC (local use only)",
    )

    rel_p = sub.add_parser("release", help="git-archive tarball for a tag")
    rel_p.add_argument("tag", nargs="?", help="Tag name (default: latest tag)")

    args = parser.parse_args()
    os.chdir(ROOT)
    handlers = {
        "bootstrap": cmd_bootstrap,
        "gmail": cmd_gmail,
        "package": cmd_package,
        "release": cmd_release,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
