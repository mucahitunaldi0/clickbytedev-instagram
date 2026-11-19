#!/usr/bin/env bash
# Bulut ortamı kurulumu: Python bağımlılıkları, Chromium, ffmpeg, Flutter SDK (Dart dahil).
# Kurulu olanları atlar; her koşuda güvenle çalıştırılabilir.
# Gerekli ağ erişimi: pypi.org, playwright.azureedge.net, apt depoları, github.com (flutter),
# storage.googleapis.com + pub.dev (flutter paketleri), cdnjs.cloudflare.com (GSAP),
# fonts.googleapis.com + fonts.gstatic.com, graph.facebook.com, mucahitunaldi0.github.io.
set -euo pipefail
cd "$(dirname "$0")/.."
SUDO=""; command -v sudo >/dev/null && [ "$(id -u)" != 0 ] && SUDO="sudo"

if ! python -c "import playwright, pytest" 2>/dev/null; then
  pip install -q -r requirements.txt || pip install -q --break-system-packages -r requirements.txt
fi
if ! ls ~/.cache/ms-playwright/chromium* >/dev/null 2>&1; then
  python -m playwright install --with-deps chromium
fi
if ! command -v ffmpeg >/dev/null; then
  $SUDO apt-get update -qq && $SUDO apt-get install -y -qq ffmpeg git unzip xz-utils
fi
if [ ! -x "$HOME/flutter/bin/flutter" ]; then
  git clone -q --depth 1 -b stable https://github.com/flutter/flutter.git "$HOME/flutter"
  "$HOME/flutter/bin/flutter" config --no-analytics >/dev/null
  "$HOME/flutter/bin/flutter" precache --no-android --no-ios --no-web --no-linux --no-windows --no-macos --no-fuchsia
fi
# check.py, flutter/dart'ı PATH'te ya da ~/flutter/bin altında bulur
"$HOME/flutter/bin/dart" --version && ffmpeg -version | head -1
