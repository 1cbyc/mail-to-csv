#!/usr/bin/env bash
# Create a local release archive from the current git tag.
# Usage: ./scripts/release.sh [tag]   (default: latest annotated tag)

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

TAG="${1:-}"
if [[ -z "$TAG" ]]; then
  TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
fi
if [[ -z "$TAG" ]]; then
  echo "No tag found. Create one first, e.g.: git tag -a v1.0.0 -m 'v1.0.0'"
  exit 1
fi

mkdir -p releases
ARCHIVE="releases/mail-to-csv-${TAG}.tar.gz"
git archive --format=tar.gz --prefix="mail-to-csv-${TAG}/" -o "$ARCHIVE" "$TAG"
echo "Local release archive: $ARCHIVE"
shasum -a 256 "$ARCHIVE" | tee "releases/mail-to-csv-${TAG}.sha256"
