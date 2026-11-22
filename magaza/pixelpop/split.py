#!/usr/bin/env python3
"""Pixel Pop Instagram 3'lü split (profil ızgarasında yan yana tek görsel).

Çalıştır:  python3 magaza/pixelpop/split.py
Çıktı:     magaza/pixelpop/html/instagram-split-{tr,en}.html

Instagram profil ızgarası 4:5 gönderiyi (1080×1350) 3:4 kırpar: her yandan ~34 px
görünmez. Bu yüzden panorama, ızgarada görünen 3 × 1012 px alana göre çizilir ve
her kare 34 px taşma payıyla kesilir. Böylece hem ızgarada hem gönderi açıldığında
parçalar birbirine bağlanır. Önemli öğeler ek yerlerinden (x=1046 ve x=2058) uzak tutulur.

Paylaşım sırası: önce 3. kare (sağ), sonra 2., en son 1. kare.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from uret import (INK, PAPER, YELLOW, SKY, PINK, MINT, RED, F_HEAD, F_UI, S,  # noqa: E402
                  dots, neo, wordmark, tag, icon_frame, phone, scr_game, chip, icon, frame, page)

OUT = Path(__file__).resolve().parent / "html"

V, B, H = 1012, 34, 1350          # ızgarada görünen genişlik, taşma payı, yükseklik
TW = V + 2 * B                    # kare genişliği: 1080
PW = 3 * V + 2 * B                # panorama: 3104
SEAMS = (B + V, B + 2 * V)        # 1046, 2058
WALL = 40

T = {
    "tr": {
        "subtitle": "Küp Kaçışı", "pill": "Kaydır · Eşleştir · Temizle", "swipe": "Kaydır!",
        "levels": "1500 bölüm", "head": "Her renk kendi duvarına",
        "bullets": [("cube", "10x10'dan 40x40'a bölümler"), ("undo", "Sınırsız geri al"),
                    ("calendar", "Günlük bulmaca ve seri"), ("photo", "Fotoğrafından bölüm üret")],
        "cta": "Google Play'de ücretsiz", "cta2": "Profildeki linkten indir", "ios": "iOS yakında",
    },
    "en": {
        "subtitle": "Cube Escape", "pill": "Swipe · Match · Clear", "swipe": "Swipe!",
        "levels": "1500 levels", "head": "Every colour to its own wall",
        "bullets": [("cube", "Levels from 10x10 to 40x40"), ("undo", "Unlimited undo"),
                    ("calendar", "Daily puzzle and streak"), ("photo", "Turn your photo into a level")],
        "cta": "Free on Google Play", "cta2": "Download via the link in bio", "ios": "iOS coming soon",
    },
}
UI = {  # telefon içi metinler (app_*.arb)
    "tr": {"level": "Bölüm {n}", "undo": "Geri al", "hint": "İpucu", "preview": "Önizleme",
           "restart": "Baştan", "skip": "Atla"},
    "en": {"level": "Level {n}", "undo": "Undo", "hint": "Hint", "preview": "Preview",
           "restart": "Restart", "skip": "Skip"},
}


def at(x, y, html, name="oge", extra=""):
    return f'<div data-name="{name}" style="position:absolute;left:{x}px;top:{y}px;{extra}">{html}</div>'


def walls():
    """Panoranın tamamı oyundaki gibi tek bir 4 renkli çerçeve."""
    return (f'<div data-name="duvar-ust" style="position:absolute;left:0;top:0;width:{PW}px;height:{WALL}px;'
            f'background:{SKY};border-bottom:5px solid {INK};box-sizing:border-box"></div>'
            f'<div data-name="duvar-alt" style="position:absolute;left:0;top:{H - WALL}px;width:{PW}px;height:{WALL}px;'
            f'background:{MINT};border-top:5px solid {INK};box-sizing:border-box"></div>'
            f'<div data-name="duvar-sol" style="position:absolute;left:0;top:0;width:{B + WALL}px;height:{H}px;'
            f'background:{PINK};border-right:5px solid {INK};box-sizing:border-box"></div>'
            f'<div data-name="duvar-sag" style="position:absolute;left:{PW - B - WALL}px;top:0;width:{B + WALL}px;'
            f'height:{H}px;background:{RED};border-left:5px solid {INK};box-sizing:border-box"></div>')


def cube(color, size=62, rot=0):
    return (f'<div style="width:{size}px;height:{size}px;background:{color};border:5px solid {INK};'
            f'box-sizing:border-box;box-shadow:6px 6px 0 {INK};transform:rotate({rot}deg)"></div>')


def speed_lines(length):
    return "".join(f'<div style="position:absolute;right:0;top:{y}px;width:{w}px;height:6px;background:{INK};'
                   f'border-radius:3px"></div>' for y, w in ((6, length), (28, length * .6), (50, length * .85)))


def trail():
    """Sağa kayan küpler; kırmızı olan kırmızı duvara çarpıp patlar."""
    y, s = 1222, 62
    out = []
    for x, c in ((430, SKY), (1180, MINT), (1690, PINK), (2290, YELLOW), (2700, SKY)):
        out.append(at(x - 150, y, speed_lines(130), "hiz-cizgisi", "width:140px;height:62px"))
        out.append(at(x, y, cube(c, s), "kayan-kup"))
    rx = PW - B - WALL - s - 18
    out.append(at(rx - 150, y, speed_lines(130), "hiz-cizgisi", "width:140px;height:62px"))
    out.append(at(rx, y, cube(RED, s, 12), "patlayan-kup"))
    for dx, dy, w, h in ((-20, -40, 16, 30), (20, -58, 16, 34), (64, -36, 30, 16), (-48, -8, 30, 16),
                         (72, 8, 26, 14)):
        out.append(at(rx + dx + 22, y + dy + 10, '', "kivilcim",
                      f"width:{w}px;height:{h}px;background:{YELLOW};border:4px solid {INK};box-sizing:border-box;"))
    return "".join(out)


def panorama(lang):
    t, ui = T[lang], UI[lang]
    p1 = S(1)
    parts = [dots(PW, H, 44, 9), walls()]

    # 1. kare: logo
    x1 = B + 100
    parts.append(at(x1 + 10, 104, icon_frame(300, tilt=-6), "ikon"))
    parts.append(at(x1 + 380, 150, tag(p1, t["subtitle"], 54, RED, 3), "alt-baslik"))
    word = (f'<div style="display:flex;flex-direction:column;gap:0">{wordmark(p1, 205)}</div>')
    word = word.replace("PIXEL POP", "PIXEL<br>POP").replace("white-space:nowrap", "white-space:normal;line-height:.98")
    parts.append(at(x1, 470, word, "logo-yazi"))
    parts.append(at(x1 + 4, 966, f'<div style="{neo(p1, PAPER, radius=18, border=5, shadow=(8, 8))}padding:18px 34px;'
                                f'{F_UI};font-size:38px;color:{INK};white-space:nowrap;transform:rotate(-1.5deg)">'
                                f'{t["pill"]}</div>', "slogan"))

    # 2. kare: telefon
    pw = 500
    k = pw / 600
    pp = S(k)
    ph = phone(pp, "android", 2.07, scr_game(pp, ui, "android", "frog", "89"))
    cx = SEAMS[0] + V / 2
    parts.append(at(round(cx - pw / 2 - 10), 104, ph, "telefon"))
    parts.append(at(SEAMS[0] + 36, 760, chip(p1, t["levels"], YELLOW, "star", tilt=-6)
                    .replace("font-size:16px", "font-size:34px").replace('width="18"', 'width="34"')
                    .replace('height="18"', 'height="34"'), "rozet-bolum"))
    bubble = (f'<div style="{neo(p1, PAPER, border=5, shadow=(8, 8), bubble=True)}padding:16px 28px;'
              f'transform:rotate(7deg);{F_HEAD};font-size:46px;color:{INK};white-space:nowrap">{t["swipe"]}</div>')
    parts.append(at(round(cx + pw / 2 - 70), 236, bubble, "balon-kaydir"))

    # 3. kare: başlık, özellikler, çağrı
    x3 = SEAMS[1] + 62
    w3 = V - 124
    parts.append(at(x3, 112, f'<div style="width:{w3}px;{neo(p1, PAPER, radius=26, border=7, shadow=(16, 16), shadow_color=SKY)}'
                             f'transform:rotate(1.2deg);padding:40px 48px;{F_HEAD};font-size:70px;line-height:1.1;'
                             f'color:{INK};text-align:center">{t["head"]}</div>', "baslik-karti"))
    fills = [PAPER, PAPER, PAPER, PAPER]
    for i, ((ic, txt), fill) in enumerate(zip(t["bullets"], fills)):
        row = (f'<div style="width:{w3 - 40}px;{neo(p1, fill, radius=16, border=5, shadow=(7, 7))}display:flex;'
               f'align-items:center;gap:24px;padding:18px 28px;transform:rotate({(-1) ** i * .8}deg)">'
               f'<div style="width:58px;height:58px;border-radius:50%;background:{[YELLOW, MINT, SKY, PINK][i]};'
               f'border:4px solid {INK};box-sizing:border-box;display:flex;align-items:center;justify-content:center;flex:none">'
               f'{icon(ic, 32)}</div><div style="{F_UI};font-size:38px;color:{INK};white-space:nowrap">{txt}</div></div>')
        parts.append(at(x3 + 20, 440 + i * 112, row, f"ozellik-{i + 1}"))
    cta = (f'<div style="width:{w3}px;{neo(p1, RED, border=6, shadow=(10, 10), bubble=True)}padding:26px 40px;'
           f'transform:rotate(-1deg);display:flex;flex-direction:column;gap:6px">'
           f'<div style="{F_HEAD};font-size:50px;line-height:1.1;color:{PAPER}">{t["cta"]}</div>'
           f'<div style="{F_UI};font-size:32px;color:{PAPER}">{t["cta2"]}</div></div>')
    parts.append(at(x3, 928, cta, "cagri"))
    parts.append(at(x3 + w3 - 250, 900, chip(p1, t["ios"], YELLOW, tilt=6)
                    .replace("font-size:16px", "font-size:28px"), "rozet-ios"))
    parts.append(at(PW - B - WALL - 300, 1112,
                    f'<div style="{F_HEAD};font-size:84px;line-height:1;color:{YELLOW};-webkit-text-stroke:9px {INK};'
                    f'paint-order:stroke fill;text-shadow:7px 7px 0 {INK};transform:rotate(-8deg)">POP!</div>', "pop"))

    parts.append(trail())
    return "".join(parts)


def guides():
    g = []
    for i in range(3):
        g.append(f'<div style="position:absolute;left:{i * V}px;top:0;width:{TW}px;height:{H}px;'
                 f'border:3px dashed rgba(17,17,17,.5);box-sizing:border-box"></div>')
    for x in SEAMS:
        g.append(f'<div style="position:absolute;left:{x - 2}px;top:0;width:4px;height:{H}px;background:#FF00AA"></div>')
    return f'<div data-name="kilavuz (dışa aktarmadan önce gizle)" style="position:absolute;left:0;top:0">{"".join(g)}</div>'


def build(lang):
    body = panorama(lang)
    master = frame(f"split-ana-{lang}", PW, H, body + guides())
    tiles = []
    for i in range(3):
        inner = f'<div data-name="panorama" style="position:absolute;left:{-i * V}px;top:0;width:{PW}px;height:{H}px">{body}</div>'
        name = f"instagram-{lang}-{i + 1}"
        tiles.append((name, TW, H, frame(name, TW, H, inner)))
    sections = [
        ("Ana panorama (düzenleme için)",
         f"{PW}×{H}. Pembe çizgiler ızgaradaki ek yerleri, kesikli kutular 1080×1350 kareler. "
         "Burada düzenleyip karelere kopyalayabilirsiniz; kılavuz katmanını dışa aktarmadan önce gizleyin.",
         [(f"split-ana-{lang}", PW, H, master)]),
        ("Paylaşılacak 3 kare",
         "1080×1350 (4:5). Paylaşım sırası: önce 3, sonra 2, en son 1; profilde soldan sağa 1-2-3 dizilir. "
         "Izgara her yandan 34 px kırptığı için kareler o kadar taşma payı içerir.",
         tiles),
    ]
    note = ("Pixel Pop Instagram 3'lü split. Figma'ya html.to.design ile aktarın; metinler, küpler ve kartlar "
            "ayrı düzenlenebilir katman olarak gelir.")
    title = f"Pixel Pop · Instagram split · {lang.upper()}"
    (OUT / f"instagram-split-{lang}.html").write_text(page(title, sections, note), encoding="utf-8")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for lang in ("tr", "en"):
        build(lang)
        f = OUT / f"instagram-split-{lang}.html"
        print(f.name, f.stat().st_size // 1024, "KB")
