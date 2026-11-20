"""HTML -> PNG / MP4.

carousel/image: slide-*.html -> out/slide-*.jpg (1080x1350)
story:          story-*.html -> out/story-*.jpg (1080x1920)
reel:           reel.html    -> out/reel.mp4  (1080x1920, 30 fps, H.264 + AAC)

Reel sayfası sözleşmesi: window.REEL_SURE_MS (sayı) ve window.oynat() GSAP zaman çizelgesini kurup DÖNDÜRÜR.
Animasyon yalnızca GSAP ile yapılmalı (CSS animasyonu kare kare yakalanmaz).
CLI: python scripts/render.py <icerik_klasoru>
"""
import json
import re
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
FPS = 30
BRAND_FONTS = {"Bricolage Grotesque", "DM Sans", "JetBrains Mono"}
SIZES = {"carousel": (1080, 1350), "image": (1080, 1350), "story": (1080, 1920), "reel": (1080, 1920)}


def _num(p: Path):
    m = re.search(r"(\d+)", p.stem)
    return int(m.group(1)) if m else 0


def _open(browser, w, h, html: Path):
    page = browser.new_page(viewport={"width": w, "height": h})
    page.goto(html.resolve().as_uri(), wait_until="networkidle")
    page.evaluate("document.fonts.ready.then(() => 1)")  # FontFaceSet'i döndürmek sayfayı çökertiyor
    # fontlar yalnızca kullanılınca yüklenir; ağ engelliyse sessizce varsayılan fonta düşmesin
    faces = page.evaluate("[...document.fonts].map(f => [f.family.replace(/\"/g, ''), f.status])")
    failed = sorted({fam for fam, st in faces if st == "error"})
    if failed or not BRAND_FONTS & {fam for fam, st in faces if st == "loaded"}:
        raise RuntimeError(f"marka fontu yüklenmedi: hatalı={failed} ({html.name})")
    return page


OVERFLOW_JS = """() => [...document.querySelectorAll('body *')].filter(e => {
  const r = e.getBoundingClientRect();
  return r.width && (r.right > innerWidth + 1 || r.bottom > innerHeight + 1 || r.left < -1
    || e.scrollWidth > e.clientWidth + 2
    || (e.matches('.kod') && e.scrollHeight > e.clientHeight + 2));
}).map(e => e.className || e.tagName).slice(0, 3)"""


def _check_overflow(page, html: Path):
    bad = page.evaluate(OVERFLOW_JS)
    if bad:
        raise RuntimeError(f"{html.name}: içerik kadrajdan taşıyor ({', '.join(map(str, bad))}); yazıyı kısaltın ya da küçültün")


def _render_reel(browser, d: Path, post: dict) -> str:
    w, h = SIZES["reel"]
    page = _open(browser, w, h, d / "reel.html")
    page.wait_for_function("window.gsap && window.oynat && window.REEL_SURE_MS")
    dur_ms = page.evaluate(
        "() => { window.__tl = window.oynat(); if (!window.__tl || !window.__tl.seek) throw new Error('oynat() timeline döndürmeli');"
        " window.__tl.pause(0); return window.REEL_SURE_MS; }")
    frames = int(dur_ms / 1000 * FPS)
    out = d / "out" / "reel.mp4"
    out.parent.mkdir(exist_ok=True)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-"]
    muzik = post.get("muzik")
    dur = frames / FPS
    if muzik:
        cmd += ["-i", str(ROOT / muzik), "-af", f"afade=t=out:st={max(dur - 1, 0):.2f}:d=1", "-c:a", "aac", "-b:a", "160k"]
    else:  # Instagram sessiz reel'i kabul eder ama check aac ister: sessiz ses kanalı
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-c:a", "aac"]
    cmd += ["-t", f"{dur:.3f}", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "18",
            "-r", str(FPS), "-movflags", "+faststart", str(out)]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for i in range(frames):
            page.evaluate(f"window.__tl.seek({i / FPS}, false), 0")  # timeline'ı döndürmek sayfayı çökertir
            ff.stdin.write(page.screenshot(type="jpeg", quality=92))
    finally:
        ff.stdin.close()
        if ff.wait() != 0:
            raise RuntimeError("ffmpeg reel üretimi başarısız")
    page.close()
    return str(out)


def render(content_dir: str) -> list:
    d = Path(content_dir)
    post = json.loads((d / "post.json").read_text(encoding="utf-8"))
    kind = post["kind"]
    out = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            if kind == "reel":
                out.append(_render_reel(browser, d, post))
            else:
                w, h = SIZES[kind]
                prefix = "story" if kind == "story" else "slide"
                (d / "out").mkdir(exist_ok=True)
                for html in sorted(d.glob(f"{prefix}-*.html"), key=_num):
                    page = _open(browser, w, h, html)
                    _check_overflow(page, html)
                    target = d / "out" / f"{html.stem}.jpg"  # Instagram API yalnızca JPEG kabul eder
                    page.screenshot(path=str(target), type="jpeg", quality=95)
                    page.close()
                    out.append(str(target))
        finally:
            browser.close()
    if not out:
        raise RuntimeError(f"render edilecek dosya yok: {d}")
    return out


if __name__ == "__main__":
    print("\n".join(render(sys.argv[1])))
