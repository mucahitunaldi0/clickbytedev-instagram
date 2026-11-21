import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check import check  # noqa: E402


def img(path: Path, w: int, h: int):
    from PIL import Image
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (w, h)).save(path)


def post(tmp_path, caption="Liste kasıyorsa ListView.builder kullanın.", kind="carousel",
         size=(1080, 1350), medya=None, notlar=None):
    d = tmp_path / "p"
    d.mkdir()
    if notlar:
        (d / "notlar.md").write_text(notlar, encoding="utf-8")
    img(d / "1.jpg", *size)
    (d / "post.json").write_text(json.dumps({
        "id": "p", "kind": kind, "yayin": "2026-12-01T12:00:00+03:00", "caption": caption,
        "medya": medya or ["1.jpg"], "muzik": None, "sutun": "ipucu", "uygulama": None,
    }), encoding="utf-8")
    return d


def test_clean_post_passes(tmp_path):
    assert check(str(post(tmp_path))) == []


def test_secret_in_notes_fails(tmp_path):
    d = post(tmp_path, notlar='api_key = "AIzaSyA1b2C3d4E5f6G7h8I9j0KlMnOpQrStUvW"')
    assert any("gizli" in s for s in check(str(d)))


def test_secret_private_key_fails(tmp_path):
    d = post(tmp_path, notlar="-----BEGIN PRIVATE KEY-----")
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


def test_square_image_ok_but_tall_image_fails_for_carousel(tmp_path):
    assert check(str(post(tmp_path, size=(1080, 1080)))) == []
    (tmp_path / "b").mkdir()
    assert any("boyut" in s for s in check(str(post(tmp_path / "b", size=(1080, 1920)))))


def test_png_media_rejected(tmp_path):
    d = post(tmp_path, medya=["1.png"])
    img(d / "1.png", 1080, 1350)
    assert any("JPEG" in s for s in check(str(d)))


def test_missing_media_fails(tmp_path):
    assert any("yok" in s for s in check(str(post(tmp_path, medya=["9.jpg"]))))


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg yok")
def test_reel_too_short_fails(tmp_path):
    d = post(tmp_path, kind="reel", medya=["reel.mp4"])
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=black:s=1080x1920:d=2:r=30",
                    "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "2", "-c:v", "libx264", "-c:a", "aac",
                    "-pix_fmt", "yuv420p", str(d / "reel.mp4")], check=True)
    assert any("süre" in s for s in check(str(d)))
