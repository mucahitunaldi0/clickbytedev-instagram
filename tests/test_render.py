import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check import _img_size  # noqa: E402
from render import render  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def mk(tmp_path, kind, files, muzik=None):
    d = tmp_path / "icerik" / "t"
    d.mkdir(parents=True)
    for name, body in files.items():
        (d / name).write_text(body, encoding="utf-8")
    (d / "post.json").write_text(json.dumps({"id": "t", "kind": kind, "muzik": muzik}), encoding="utf-8")
    return d


SLIDE = '<!doctype html><html><head><link rel="stylesheet" href="{css}"></head><body><div class="zemin"><h1 class="baslik">{t}</h1></div></body></html>'
CSS = (ROOT / "sablon" / "brand.css").as_uri()


def test_render_carousel_jpgs(tmp_path):
    d = mk(tmp_path, "carousel", {f"slide-{i}.html": SLIDE.format(css=CSS, t=f"Slayt {i}") for i in (1, 2)})
    out = render(str(d))
    assert [Path(p).name for p in out] == ["slide-1.jpg", "slide-2.jpg"]
    assert all(_img_size(Path(p)) == (1080, 1350) for p in out)


def test_render_story_size(tmp_path):
    d = mk(tmp_path, "story", {"story-1.html": SLIDE.format(css=CSS, t="Story")})
    out = render(str(d))
    assert [Path(p).name for p in out] == ["story-1.jpg"]
    assert _img_size(Path(out[0])) == (1080, 1920)


REEL = """<!doctype html><html><head><link rel="stylesheet" href="{css}">
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script></head>
<body><div class="zemin"><h1 class="baslik" id="b">Reel</h1></div>
<script>window.REEL_SURE_MS = 5000;
window.oynat = () => gsap.timeline().from('#b', {{opacity: 0, y: 80, duration: 2}}).to({{}}, {{duration: 3}});</script>
</body></html>"""


def test_render_reel_mp4(tmp_path):
    d = mk(tmp_path, "reel", {"reel.html": REEL.format(css=CSS)}, muzik="muzik/sakin-1.m4a")
    out = render(str(d))
    assert [Path(p).name for p in out] == ["reel.mp4"]
    info = json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,width,height:format=duration",
         "-of", "json", out[0]], capture_output=True, text=True).stdout)
    codecs = {s["codec_name"] for s in info["streams"]}
    v = [s for s in info["streams"] if s["codec_name"] == "h264"][0]
    assert codecs == {"h264", "aac"}
    assert (v["width"], v["height"]) == (1080, 1920)
    assert 4.5 <= float(info["format"]["duration"]) <= 6


def test_render_fails_without_brand_fonts(tmp_path):
    import pytest
    d = mk(tmp_path, "story", {"story-1.html": "<html><body><h1>fontsuz</h1></body></html>"})
    with pytest.raises(RuntimeError, match="font"):
        render(str(d))


def test_render_fails_on_overflowing_text(tmp_path):
    import pytest
    d = mk(tmp_path, "carousel", {"slide-1.html": SLIDE.format(css=CSS, t="Taşan" + "x" * 80)})
    with pytest.raises(RuntimeError, match="taşıyor"):
        render(str(d))


def test_render_fails_on_clipped_code(tmp_path):
    import pytest
    kod = '<pre class="kod">' + "a" * 90 + "</pre>"
    d = mk(tmp_path, "carousel", {"slide-1.html": SLIDE.format(css=CSS, t="Kod").replace("</h1>", "</h1>" + kod)})
    with pytest.raises(RuntimeError, match="taşıyor"):
        render(str(d))
