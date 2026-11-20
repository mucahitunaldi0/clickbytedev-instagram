import json
import shutil
import struct
import subprocess
import sys
import zlib
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check import check  # noqa: E402


def img(path: Path, w: int, h: int):
    from PIL import Image
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (w, h)).save(path)


def post(tmp_path, caption="Liste kasıyorsa ListView.builder kullanın.", kind="carousel",
         slide="<div class='baslik'>const ile rebuild'i kesin</div>", size=(1080, 1350), medya=None):
    d = tmp_path / "p"
    d.mkdir()
    (d / "slide-1.html").write_text(f"<html><body>{slide}</body></html>", encoding="utf-8")
    img(d / "out" / "slide-1.jpg", *size)
    (d / "post.json").write_text(json.dumps({
        "id": "p", "kind": kind, "yayin": "2026-12-01T12:00:00+03:00", "caption": caption,
        "medya": medya or ["out/slide-1.jpg"], "muzik": None, "sutun": "ipucu", "uygulama": None,
    }), encoding="utf-8")
    return d


def test_clean_post_passes(tmp_path):
    assert check(str(post(tmp_path))) == []


def test_code_block_exclamation_allowed(tmp_path):
    d = post(tmp_path, slide="<pre class='kod'>if (a != b) x!.y();</pre>")
    assert check(str(d)) == []


def test_secret_in_slide_html_fails(tmp_path):
    d = post(tmp_path, slide="<pre class='kod'>api_key = \"AIzaSyA1b2C3d4E5f6G7h8I9j0KlMnOpQrStUvW\"</pre>")
    assert any("gizli" in s for s in check(str(d)))


def test_secret_private_key_fails(tmp_path):
    d = post(tmp_path, slide="<pre>-----BEGIN PRIVATE KEY-----</pre>")
    assert any("gizli" in s for s in check(str(d)))


def test_two_emojis_fails(tmp_path):
    assert any("emoji" in s for s in check(str(post(tmp_path, caption="Hazır 🚀 deneyin 🔥"))))


def test_two_exclamations_fails(tmp_path):
    assert any("ünlem" in s for s in check(str(post(tmp_path, caption="Hazır! Deneyin!"))))


def test_banned_word_fails(tmp_path):
    assert any("yasak" in s for s in check(str(post(tmp_path, caption="Bu en iyi yöntem."))))


def test_app_store_not_banned(tmp_path):
    assert check(str(post(tmp_path, caption="iOS sürümü App Store'da yakında."))) == []


def test_brand_spelling_fails(tmp_path):
    assert any("yazım" in s for s in check(str(post(tmp_path, caption="Clickbytedev olarak yaptık."))))


def test_wrong_png_size_fails(tmp_path):
    assert any("boyut" in s for s in check(str(post(tmp_path, size=(1080, 1080)))))


def test_png_media_rejected(tmp_path):
    d = post(tmp_path, medya=["out/slide-1.png"])
    img(d / "out" / "slide-1.png", 1080, 1350)
    assert any("JPEG" in s for s in check(str(d)))


def test_missing_media_fails(tmp_path):
    assert any("yok" in s for s in check(str(post(tmp_path, medya=["out/slide-9.jpg"]))))


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg yok")
def test_reel_too_long_fails(tmp_path):
    d = post(tmp_path, kind="reel", medya=["out/reel.mp4"])
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=black:s=1080x1920:d=50:r=30",
                    "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "50", "-c:v", "libx264", "-c:a", "aac",
                    "-pix_fmt", "yuv420p", str(d / "out" / "reel.mp4")], check=True)
    assert any("süre" in s for s in check(str(d)))


@pytest.mark.skipif(not shutil.which("dart"), reason="dart yok")
def test_dart_error_fails(tmp_path):
    d = post(tmp_path)
    (d / "kod.dart").write_text('void main() { int x = "a"; print(x); }', encoding="utf-8")
    assert any("dart" in s for s in check(str(d)))


def _has_flutter():
    from check import _tool
    return _tool("flutter") is not None


@pytest.mark.skipif(not _has_flutter(), reason="flutter yok (bulutta setup-cloud.sh kurar)")
def test_flutter_snippet_passes_and_error_fails(tmp_path):
    d = post(tmp_path)
    (d / "kod.dart").write_text("import 'package:flutter/widgets.dart';\nconst w = Text('Merhaba');\n", encoding="utf-8")
    assert check(str(d)) == []
    (d / "kod.dart").write_text("import 'package:flutter/widgets.dart';\nconst Text w = 3;\n", encoding="utf-8")
    assert any("flutter" in s for s in check(str(d)))


def test_flutter_snippet_without_flutter_fails(tmp_path, monkeypatch):
    import check as c
    monkeypatch.setattr(c, "_tool", lambda n: None)
    d = post(tmp_path)
    (d / "kod.dart").write_text("import 'package:flutter/widgets.dart';\n", encoding="utf-8")
    assert any("flutter bulunamadı" in s for s in c.check(str(d)))
