#!/usr/bin/env bash
set -euo pipefail

# GLIBC compatibility note:
# Recent official c2patool Linux binaries require newer glibc than Debian Bookworm.
# Run this script on Debian Trixie/Ubuntu 24.04+ or build c2patool from source.
C2PATOOL_VERSION="${C2PATOOL_VERSION:-0.26.59}"
if command -v apt-get >/dev/null; then
  sudo apt-get update
  sudo apt-get install -y exiftool qpdf ghostscript ffmpeg libreoffice poppler-utils curl tar
  if ! command -v c2patool >/dev/null; then
    tmp="$(mktemp -d)"
    curl -fsSL -o "$tmp/c2patool.tar.gz" "https://github.com/contentauth/c2pa-rs/releases/download/c2patool-v${C2PATOOL_VERSION}/c2patool-v${C2PATOOL_VERSION}-x86_64-unknown-linux-gnu.tar.gz"
    tar -xzf "$tmp/c2patool.tar.gz" -C "$tmp"
    sudo find "$tmp" -type f -name c2patool -exec install -m 0755 {} /usr/local/bin/c2patool \;
    rm -rf "$tmp"
  fi
else
  echo "Install ExifTool, qpdf, Ghostscript, FFmpeg, LibreOffice and c2patool for your OS."
fi
