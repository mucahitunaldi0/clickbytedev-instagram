#!/usr/bin/env bash
# Bulut ortamı kurulumu: Python bağımlılıkları ve ffmpeg (video kontrolü için ffprobe).
# Kurulu olanları atlar; her koşuda güvenle çalıştırılabilir.
# Gerekli ağ erişimi: pypi.org, apt depoları, graph.facebook.com, mucahitunaldi0.github.io.
set -euo pipefail
cd "$(dirname "$0")/.."
SUDO=""; command -v sudo >/dev/null && [ "$(id -u)" != 0 ] && SUDO="sudo"

if ! python -c "import pytest, PIL" 2>/dev/null; then
  python -m pip install -q -r requirements.txt || python -m pip install -q --break-system-packages -r requirements.txt
fi
if ! command -v ffprobe >/dev/null; then
  $SUDO apt-get update -qq && $SUDO apt-get install -y -qq ffmpeg git
fi
ffprobe -version | head -1
