import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import figma_svg  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402


def test_export_makes_editable_layers(tmp_path, monkeypatch):
    d = tmp_path / "icerik" / "x"
    d.mkdir(parents=True)
    (d / "post.json").write_text('{"kind": "story"}', encoding="utf-8")
    css = (Path(figma_svg.ROOT) / "sablon" / "brand.css").as_uri()
    (d / "story-1.html").write_text(
        f'<html><head><link rel="stylesheet" href="{css}"></head><body><div class="zemin">'
        '<h1 class="baslik">Merhaba <em>dünya</em></h1><div class="kart">kutu</div></div></body></html>', encoding="utf-8")
    monkeypatch.setattr(figma_svg, "ROOT", tmp_path)
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        [p] = figma_svg.export(d, b.new_page())
        b.close()
    svg = p.read_text(encoding="utf-8")
    assert svg.startswith("<svg") and 'width="1080" height="1920"' in svg
    assert re.search(r"<text[^>]*>.*Merhaba.*dünya.*</text>", svg)  # yazı metin katmanı, görsel değil
    assert 'id="Izgara"' in svg and 'id="kart"' in svg
    assert "<image" not in svg
