#!/usr/bin/env python3
"""Pixel Pop: Küp Kaçışı mağaza görselleri üretici.

Çalıştır:  python3 magaza/pixelpop/uret.py
Çıktı:     magaza/pixelpop/html/*.html  (Figma'ya aktarılacak statik HTML)

Tasarım oyunun kendisinden alınmıştır (pixel-pop deposu, lib/theme/game_theme.dart,
lib/ui/widgets/chunky.dart): sarı sahne + benek deseni, 3 px mürekkep çizgi,
4,4 sert gölge, konuşma balonu düğmeler, 4 renkli duvarlı çerçeve.
Uygulama içi metinler lib/l10n/app_tr.arb ve app_en.arb ile aynıdır.

Çıktı tamamen statiktir: JS yok, pseudo-element yok. Metinler gerçek metin,
küpler ve çerçeve SVG dikdörtgen/çokgen, arayüz div. html.to.design gibi
eklentilerle Figma'da her parça ayrı, düzenlenebilir katman olur.
"""
import base64
import io
import random
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent / "html"

# ---------------------------------------------------------------- tema (game_theme.dart)
INK, PAPER = "#111111", "#FFFFFF"
SCENE = "#FFE14A"            # GameTheme.pop.bg
YELLOW, SKY, PINK = "#FFD23F", "#4CC9F0", "#FF9ECB"
MINT, RED = "#7BD389", "#E63946"
GREY = "#D9D9D9"
STAR = "#FFC928"
SHADOWS = [RED, SKY, MINT, PINK]  # başlık kartı gölge sırası

# ---------------------------------------------------------------- piksel resimler
# Her resim tam 4 renk; duvarlar (üst, sağ, alt, sol) bu 4 rengin harfleri.
SPRITES = {
    "smiley": dict(
        rows=["....KKKKKK....", "..KKYYYYYYKK..", ".KYYYYYYYYYYK.", ".KYYYYYYYYYYK.",
              "KYYKKYYYYKKYYK", "KYYKKYYYYKKYYK", "KYYYYYYYYYYYYK", "KYRRYYYYYYRRYK",
              "KYRRYYYYYYRRYK", "KYYYKYYYYKYYYK", ".KYYYKKKKYYYK.", ".KYYYYYYYYYYK.",
              "..KKYYYYYYKK..", "....KKKKKK...."],
        pal={"K": "#3B2A1A", "Y": "#FFC928", "R": "#FF5A5F", "W": "#FFFFFF"},
        walls="WRKY"),
    "frog": dict(
        rows=["....KKKKKK....", "....KOOOOK....", "....KOOOOK....", "....KKOOKK....",
              "...KKGGGGKK...", "..KGGGGGGGGK..", ".KGGGGBBGGGGK.", "KGGGGBBBBGGGGK",
              "KGGGGGBBGGGGGK", "KGGKKGGGGKKGGK", "KKK..KGGK..KKK", ".....KKKK....."],
        pal={"K": "#1D1A17", "O": "#FF7B54", "G": "#7BD389", "B": "#6C8CFF"},
        walls="BKOG"),
    "blob": dict(
        rows=[".....KKKKKK.....", "...KKPPPPPPKK...", "..KPPPPPPPPPPK..", ".KPPKKPPPPKKPPK.",
              ".KPPKYPPPPKYPPK.", "KPPPPPPPPPPPPPPK", "KPPPPPKKKKPPPPPK", "KPPCCCCCCCCCCPPK",
              ".KCCCCCCCCCCCCK.", "..KCCKKCCKKCCK..", "...KK..KK..KK..."],
        pal={"K": "#1D1A17", "P": "#FF8FA3", "C": "#8BE9FF", "Y": "#FFE066"},
        walls="CPYK"),
    "strawberry": dict(
        rows=[".....GG.....", "..GGGGGGGG..", ".GGRRGGRRGG.", ".RRRRRRRRRR.",
              "RRTRRRRRRTRR", "RRRRRTRRRRRR", "RRRRRRRRRTRR", ".RRTRRRRRRR.",
              ".RRRRRTRRRR.", "..RRRRRRRR..", "...RRDDRR...", "....RDDR....", ".....DD....."],
        pal={"G": "#2EAD4B", "R": "#E63946", "D": "#A4161A", "T": "#FFD23F"},
        walls="GRDT"),
}
for _s in SPRITES.values():
    assert len({len(r) for r in _s["rows"]}) == 1

# Renk körlüğü modu sembolleri (palet sırasına göre)
SYMBOLS = ["circle", "square", "triangle", "diamond"]

# ---------------------------------------------------------------- metinler
METIN = {
    "tr": {
        "shots": [
            "Kaydır, küpler kendi rengini bulsun",
            "1500 bölüm, yıldızları topla",
            "Her renk kendi duvarına",
            "Hamleni önceden gör",
            "Her gün yeni bir bulmaca",
            "Kendi fotoğrafından bölüm yap",
            "Renk körlüğü modu",
            "Sınırsız geri al, 3 yıldız kazan",
        ],
        # uygulama içi (app_tr.arb)
        "play": "Oyna", "daily": "Günlük Bulmaca", "upload": "Fotoğraftan Üret",
        "my": "Benim Bölümlerim", "settings": "Ayarlar", "level": "Bölüm {n}", "levels": "Bölümler",
        "undo": "Geri al", "hint": "İpucu", "preview": "Önizleme", "restart": "Baştan", "skip": "Atla",
        "complete": "Bölüm tamam!", "next": "Sonraki bölüm", "replay": "Tekrar oyna", "menu": "Menü",
        "moves": "Hamle", "par": "Par {n}", "score": "Puan", "best": "En iyi seri",
        "pick": "Fotoğraf seç", "psize": "Piksel boyutu: {n}", "create": "Bölüm oluştur",
        "stays": "Fotoğrafın bu cihazdan çıkmaz.", "streak": "{n} günlük seri",
        "cb_hint": "Her renge bir sembol ekler",
        # mağaza
        "subtitle": "Küp Kaçışı", "pill": "Kaydır · Eşleştir · Temizle",
    },
    "en": {
        "shots": [
            "Swipe and every cube finds its colour",
            "1500 levels, collect the stars",
            "Every colour to its own wall",
            "See your move before you swipe",
            "A new puzzle every day",
            "Turn your photo into a level",
            "Colour-blind mode",
            "Unlimited undo, earn 3 stars",
        ],
        "play": "Play", "daily": "Daily Puzzle", "upload": "Make from Photo",
        "my": "My Levels", "settings": "Settings", "level": "Level {n}", "levels": "Levels",
        "undo": "Undo", "hint": "Hint", "preview": "Preview", "restart": "Restart", "skip": "Skip",
        "complete": "Level complete!", "next": "Next level", "replay": "Play again", "menu": "Menu",
        "moves": "Moves", "par": "Par {n}", "score": "Score", "best": "Best combo",
        "pick": "Choose a photo", "psize": "Pixel size: {n}", "create": "Create level",
        "stays": "Your photo never leaves this device.", "streak": "{n}-day streak",
        "cb_hint": "Adds a symbol to every colour",
        "subtitle": "Cube Escape", "pill": "Swipe · Match · Clear",
    },
}

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Archivo+Black'
         '&family=Roboto:wght@500;700;900&display=swap" rel="stylesheet">')

F_HEAD = "font-family:'Archivo Black',sans-serif;font-weight:400"
F_UI = "font-family:Roboto,sans-serif;font-weight:900"
F_UI5 = "font-family:Roboto,sans-serif;font-weight:500"


class S:
    """Ölçek yardımcısı: p(v) -> 'Npx', p.n(v) -> sayı."""

    def __init__(self, k):
        self.k = k

    def n(self, v):
        return round(v * self.k, 2)

    def __call__(self, v):
        x = self.n(v)
        return f"{int(x) if x == int(x) else x}px"


# ---------------------------------------------------------------- benek deseni
@lru_cache(maxsize=None)
def dots_uri(w, h, step, r, alpha=34):
    """Saydam PNG benek katmanı (Figma'da görsel dolgu olarak gelir, gizlenebilir)."""
    w, h = int(round(w)), int(round(h))
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = step / 2
    while y < h + r:
        x = step / 2
        while x < w + r:
            d.ellipse((x - r, y - r, x + r, y + r), fill=(17, 17, 17, alpha))
            x += step
        y += step
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def dots(w, h, step, r, alpha=34):
    return (f'<img data-name="benek-deseni" alt="" src="{dots_uri(w, h, step, r, alpha)}" '
            f'style="position:absolute;left:0;top:0;width:{int(round(w))}px;height:{int(round(h))}px;'
            f'pointer-events:none">')


# ---------------------------------------------------------------- simgeler (24x24)
ICON = {
    "back": '<path d="M14 5l-7 7 7 7" fill="none" stroke="{c}" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>',
    "play": '<path d="M7 4.5l12 7.5-12 7.5z" fill="{c}"/>',
    "calendar": '<rect x="3.5" y="5" width="17" height="15.5" rx="2.5" fill="none" stroke="{c}" stroke-width="2.6"/>'
                '<rect x="3.5" y="5" width="17" height="4.5" fill="{c}"/><rect x="7" y="2.5" width="2.6" height="4" rx="1" fill="{c}"/>'
                '<rect x="14.4" y="2.5" width="2.6" height="4" rx="1" fill="{c}"/><rect x="7.5" y="12.5" width="4" height="4" fill="{c}"/>',
    "photo": '<rect x="2.5" y="6" width="15" height="15" rx="2" fill="{c}"/><path d="M4.5 18.5l4-5 3 3.5 2-2.5 2.5 4z" fill="#FFFFFF"/>'
             '<rect x="18" y="1.5" width="2.6" height="9" rx="1" fill="{c}"/><rect x="14.8" y="4.7" width="9" height="2.6" rx="1" fill="{c}"/>',
    "gallery": '<rect x="6" y="2.5" width="15.5" height="15.5" rx="2" fill="{c}"/><path d="M8 15.5l3.5-4.5 2.5 3 2-2.5 3 4z" fill="#FFFFFF"/>'
               '<path d="M3 6.5v14.5h14.5" fill="none" stroke="{c}" stroke-width="2.6"/>',
    "gear": '<circle cx="12" cy="12" r="6.6" fill="none" stroke="{c}" stroke-width="4.6" stroke-dasharray="3.2 2"/>'
            '<circle cx="12" cy="12" r="5.2" fill="{c}"/><circle cx="12" cy="12" r="2.4" fill="#FFFFFF"/>',
    "star": '<path d="M12 2.5l2.9 6.2 6.8.8-5 4.7 1.3 6.7L12 17.6l-6 3.3 1.3-6.7-5-4.7 6.8-.8z" fill="{c}"/>',
    "flag": '<rect x="4.5" y="3" width="2.6" height="18.5" rx="1" fill="{c}"/><path d="M7 3.8h12l-3 4.6 3 4.6H7z" fill="{c}"/>',
    "lock": '<rect x="5" y="10.5" width="14" height="10.5" rx="2" fill="{c}"/>'
            '<path d="M8.2 10.5V8a3.8 3.8 0 017.6 0v2.5" fill="none" stroke="{c}" stroke-width="2.6"/>',
    "undo": '<path d="M9 5L4 10l5 5" fill="none" stroke="{c}" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/>'
            '<path d="M4.5 10H14a5.5 5.5 0 010 11h-4" fill="none" stroke="{c}" stroke-width="2.8" stroke-linecap="round"/>',
    "bulb": '<path d="M12 2.5a7 7 0 00-4 12.7V18h8v-2.8a7 7 0 00-4-12.7z" fill="{c}"/>'
            '<rect x="8.5" y="19" width="7" height="2.6" rx="1.2" fill="{c}"/>',
    "eye": '<path d="M1.5 12S5.5 5 12 5s10.5 7 10.5 7-4 7-10.5 7S1.5 12 1.5 12z" fill="{c}"/>'
           '<circle cx="12" cy="12" r="3.6" fill="#FFFFFF"/><circle cx="12" cy="12" r="1.6" fill="{c}"/>',
    "restart": '<path d="M19.5 12a7.5 7.5 0 11-2.2-5.3" fill="none" stroke="{c}" stroke-width="2.8" stroke-linecap="round"/>'
               '<path d="M20.5 3.5v5.5H15" fill="none" stroke="{c}" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/>',
    "skip": '<path d="M5 5l10 7-10 7z" fill="{c}"/><rect x="16.5" y="5" width="3" height="14" rx="1" fill="{c}"/>',
    "cube": '<path d="M12 2.5l8.5 4.5v10L12 21.5 3.5 17V7z" fill="{c}"/><path d="M3.5 7L12 11.5 20.5 7M12 11.5v10" '
            'fill="none" stroke="#FFFFFF" stroke-width="1.6"/>',
    "fire": '<path d="M12 2.5c1 3.5 6 6 6 11a6 6 0 01-12 0c0-2.5 1.5-4 2.5-5 .3 2 1.3 3 2.3 3-.8-3 .2-6.5 1.2-9z" fill="{c}"/>',
}


def icon(name, size_px, color=INK):
    return (f'<svg data-name="ikon-{name}" width="{size_px}" height="{size_px}" viewBox="0 0 24 24" '
            f'style="display:block;flex:none">{ICON[name].replace("{c}", color)}</svg>')


def star(size_px, fill=STAR, stroke=INK, sw=1.6):
    return (f'<svg data-name="yildiz" width="{size_px}" height="{size_px}" viewBox="0 0 24 24" style="display:block;flex:none">'
            f'<path d="M12 2.2l2.9 6.2 6.8.8-5 4.7 1.3 6.7L12 17.3l-6 3.3 1.3-6.7-5-4.7 6.8-.8z" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"/></svg>')


# ---------------------------------------------------------------- neo kutu (chunky.dart)
def neo(p, fill, radius=14, border=3, shadow=(4, 4), shadow_color=INK, bubble=False):
    if bubble:
        rad = f"{p(16)} {p(16)} {p(16)} {p(3)}"
    else:
        rad = p(radius)
    return (f"background:{fill};border:{p(border)} solid {INK};border-radius:{rad};box-sizing:border-box;"
            f"box-shadow:{p(shadow[0])} {p(shadow[1])} 0 {shadow_color};")


# ---------------------------------------------------------------- çerçeve + küpler
def board_svg(sprite, size, symbols=False, badges=None, tilt=0, shadow=None, cleared=()):
    """4 renkli duvarlı çerçeve ve içindeki küpler. size: piksel."""
    sp = SPRITES[sprite]
    rows, pal = sp["rows"], sp["pal"]
    walls = [pal[c] for c in sp["walls"]]  # üst, sağ, alt, sol
    S_ = size
    w = S_ * 0.075
    sw = max(2.0, S_ * 0.0075)
    inner = S_ - 2 * w
    n = max(len(rows), len(rows[0])) + 2
    cell = inner / n
    ox = w + (inner - len(rows[0]) * cell) / 2
    oy = w + (inner - len(rows) * cell) / 2
    g = []
    g.append(f'<rect data-name="ic-alan" x="{w}" y="{w}" width="{inner}" height="{inner}" fill="#FFFFFF"/>')
    keys = list(pal.keys())
    cubes = []
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == "." or (r, c) in cleared:
                continue
            x, y = ox + c * cell, oy + r * cell
            cubes.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{cell:.2f}" height="{cell:.2f}" fill="{pal[ch]}" '
                         f'stroke="{INK}" stroke-width="{max(1, cell * .07):.2f}"/>')
            if symbols:
                cubes.append(symbol_svg(SYMBOLS[keys.index(ch)], x, y, cell, pal[ch]))
    g.append(f'<g data-name="kupler">{"".join(cubes)}</g>')
    polys = [
        (f"0,0 {S_},0 {S_ - w},{w} {w},{w}", "duvar-ust"),
        (f"{S_},0 {S_},{S_} {S_ - w},{S_ - w} {S_ - w},{w}", "duvar-sag"),
        (f"0,{S_} {S_},{S_} {S_ - w},{S_ - w} {w},{S_ - w}", "duvar-alt"),
        (f"0,0 {w},{w} {w},{S_ - w} 0,{S_}", "duvar-sol"),
    ]
    for (pts, nm), col in zip(polys, walls):
        g.append(f'<polygon data-name="{nm}" points="{pts}" fill="{col}" stroke="{INK}" '
                 f'stroke-width="{sw}" stroke-linejoin="round"/>')
    g.append(f'<rect x="{w}" y="{w}" width="{inner}" height="{inner}" fill="none" stroke="{INK}" stroke-width="{sw}"/>')
    if badges:  # önizleme: her duvarda kaç küp yok olur
        bw, bh = S_ * .075, S_ * .055
        spots = [(S_ / 2, w / 2), (S_ - w / 2, S_ / 2), (S_ / 2, S_ - w / 2), (w / 2, S_ / 2)]
        for (cx, cy), val in zip(spots, badges):
            hot = val == max(badges)
            g.append(f'<g data-name="onizleme-{val}"><rect x="{cx - bw / 2}" y="{cy - bh / 2}" width="{bw}" height="{bh}" '
                     f'rx="{bh * .18}" fill="{YELLOW if hot else "#FFFFFF"}" stroke="{INK}" stroke-width="{sw * .8}"/>'
                     f'<text x="{cx}" y="{cy + bh * .3}" text-anchor="middle" font-family="Roboto" font-weight="900" '
                     f'font-size="{bh * .78}" fill="{INK}">{val}</text></g>')
    sh = shadow if shadow is not None else S_ * 0.03
    return (f'<div data-name="cerceve" style="position:relative;width:{S_}px;height:{S_}px;flex:none;'
            f'transform:rotate({tilt}deg);box-shadow:{sh}px {sh}px 0 {INK}">'
            f'<svg width="{S_}" height="{S_}" viewBox="0 0 {S_} {S_}" style="display:block">{"".join(g)}</svg></div>')


def symbol_svg(kind, x, y, cell, color):
    c = "#FFFFFF" if color in ("#1D1A17", "#3B2A1A") else INK
    cx, cy, s = x + cell / 2, y + cell / 2, cell * .26
    if kind == "circle":
        return f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{s:.2f}" fill="{c}"/>'
    if kind == "square":
        return f'<rect x="{cx - s:.2f}" y="{cy - s:.2f}" width="{2 * s:.2f}" height="{2 * s:.2f}" fill="none" stroke="{c}" stroke-width="{cell * .1:.2f}"/>'
    if kind == "triangle":
        return (f'<polygon points="{cx:.2f},{cy - s * 1.1:.2f} {cx + s * 1.1:.2f},{cy + s * .9:.2f} {cx - s * 1.1:.2f},{cy + s * .9:.2f}" '
                f'fill="none" stroke="{c}" stroke-width="{cell * .1:.2f}" stroke-linejoin="round"/>')
    return (f'<polygon points="{cx:.2f},{cy - s * 1.2:.2f} {cx + s * 1.2:.2f},{cy:.2f} {cx:.2f},{cy + s * 1.2:.2f} {cx - s * 1.2:.2f},{cy:.2f}" '
            f'fill="{c}"/>')


def sprite_svg(sprite, size, pad_cells=0):
    """Çerçevesiz piksel resim (logo kartı, fotoğraf önizleme)."""
    sp = SPRITES[sprite]
    rows, pal = sp["rows"], sp["pal"]
    n = max(len(rows), len(rows[0])) + pad_cells * 2
    cell = size / n
    ox = (size - len(rows[0]) * cell) / 2
    oy = (size - len(rows) * cell) / 2
    out = []
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch != ".":
                out.append(f'<rect x="{ox + c * cell:.2f}" y="{oy + r * cell:.2f}" width="{cell:.2f}" height="{cell:.2f}" '
                           f'fill="{pal[ch]}" stroke="{INK}" stroke-width="{max(.8, cell * .07):.2f}"/>')
    return (f'<svg data-name="piksel-resim-{sprite}" width="{size}" height="{size}" viewBox="0 0 {size} {size}" '
            f'style="display:block;flex:none">{"".join(out)}</svg>')


# ---------------------------------------------------------------- telefon arayüzü
def status_bar(p, plat):
    if plat == "ios":
        left = f'<div style="{F_UI};font-size:{p(21)};color:{INK}">9:41</div>'
        mid = (f'<div style="position:absolute;left:50%;top:{p(14)};width:{p(150)};height:{p(42)};'
               f'margin-left:{p(-75)};background:{INK};border-radius:{p(21)}"></div>')
    else:
        left = f'<div style="{F_UI5};font-size:{p(20)};color:{INK}">9:30</div>'
        mid = (f'<div style="position:absolute;left:50%;top:{p(16)};width:{p(26)};height:{p(26)};'
               f'margin-left:{p(-13)};background:{INK};border-radius:50%"></div>')
    bars = "".join(f'<div style="width:{p(5)};height:{p(h)};background:{INK};border-radius:{p(1.5)}"></div>'
                   for h in (7, 10, 13, 16))
    right = (f'<div style="display:flex;align-items:flex-end;gap:{p(3)}">{bars}'
             f'<div style="margin-left:{p(8)};width:{p(36)};height:{p(18)};background:{INK};border-radius:{p(5)}"></div></div>')
    return (f'<div data-name="durum-cubugu" style="position:relative;height:{p(64)};flex:none;display:flex;'
            f'align-items:center;justify-content:space-between;padding:0 {p(40)};box-sizing:border-box">'
            f'{mid}{left}{right}</div>')


def chip(p, text, fill, icon_name=None, color=INK, tilt=0):
    ic = icon(icon_name, p.n(18), color) if icon_name else ""
    return (f'<div data-name="cip" style="{neo(p, fill, radius=10, border=2.5, shadow=(3, 3))}display:flex;'
            f'align-items:center;gap:{p(5)};padding:{p(5)} {p(10)};transform:rotate({tilt}deg);flex:none">'
            f'{ic}<div style="{F_UI};font-size:{p(16)};color:{color};line-height:1">{text}</div></div>')


def back_btn(p):
    return (f'<div style="{neo(p, PAPER, radius=24, border=2.5, shadow=(2, 2))}width:{p(42)};height:{p(42)};'
            f'display:flex;align-items:center;justify-content:center;flex:none">{icon("back", p.n(22))}</div>')


def header(p, title, chips_html):
    return (f'<div data-name="ust-bar" style="display:flex;align-items:center;gap:{p(12)};padding:{p(4)} {p(24)};flex:none">'
            f'{back_btn(p)}<div style="{F_UI};font-size:{p(21)};color:{INK};flex:1;white-space:nowrap">{title}</div>'
            f'{chips_html}</div>')


def tools(p, t, active=None, skip=True, badge=3):
    spec = [("undo", t["undo"], "#E8E8E8", INK), ("bulb", t["hint"], PAPER, INK),
            ("eye", t["preview"], RED, PAPER), ("restart", t["restart"], MINT, INK)]
    if skip:
        spec.append(("skip", t["skip"], PINK, INK))
    items = []
    for name, label, fill, ic in spec:
        if active == name:
            fill, ic = INK, PAPER
        b = ""
        if name == "bulb" and badge:
            b = (f'<div style="position:absolute;right:{p(-6)};top:{p(-6)};width:{p(22)};height:{p(22)};border-radius:50%;'
                 f'background:{RED};border:{p(2)} solid {INK};box-sizing:border-box;display:flex;align-items:center;'
                 f'justify-content:center;{F_UI};font-size:{p(12)};color:{PAPER}">{badge}</div>')
        items.append(
            f'<div data-name="arac-{name}" style="display:flex;flex-direction:column;align-items:center;gap:{p(6)};width:{p(84)}">'
            f'<div style="position:relative;{neo(p, fill, radius=30, border=2.5, shadow=(3, 3))}width:{p(58)};height:{p(58)};'
            f'display:flex;align-items:center;justify-content:center">{icon(name, p.n(28), ic)}{b}</div>'
            f'<div style="{F_UI};font-size:{p(13)};color:{INK};white-space:nowrap">{label}</div></div>')
    return (f'<div data-name="araclar" style="display:flex;justify-content:center;gap:{p(6)};'
            f'padding:{p(10)} 0 {p(40)};flex:none">{"".join(items)}</div>')


def board_area(p, inner_html):
    return (f'<div data-name="oyun-alani" style="flex:1;display:flex;flex-direction:column;align-items:center;'
            f'justify-content:center;gap:{p(26)}">{inner_html}</div>')


def ui_button(p, label, fill, icon_name=None, text=INK, width=500, height=74, tilt=0):
    ic = icon(icon_name, p.n(30), text) if icon_name else ""
    return (f'<div data-name="dugme" style="{neo(p, fill, border=3, shadow=(5, 5), bubble=True)}width:{p(width)};'
            f'height:{p(height)};display:flex;align-items:center;gap:{p(18)};padding:0 {p(28)};'
            f'transform:rotate({tilt}deg);flex:none">{ic}'
            f'<div style="{F_UI};font-size:{p(25)};color:{text};white-space:nowrap">{label}</div></div>')


def scr_home(p, t, plat):
    logo = (f'<div style="{neo(p, PAPER, radius=16, border=3.5, shadow=(8, 8))}padding:{p(14)};flex:none">'
            f'{sprite_svg("smiley", p.n(170))}</div>')
    word = (f'<div style="{neo(p, PAPER, radius=8, border=3.5, shadow=(8, 8), shadow_color=RED)}padding:{p(10)} {p(26)};'
            f'transform:rotate(-2.5deg);{F_HEAD};font-size:{p(44)};color:{INK};letter-spacing:{p(1)};line-height:1.1">PIXEL POP</div>')
    chips = (f'<div style="display:flex;gap:{p(18)}">{chip(p, "242", YELLOW, "star", tilt=-2)}'
             f'{chip(p, "88/1500", PAPER, "flag", tilt=2)}</div>')
    btns = [ui_button(p, t["play"], RED, "play", PAPER, tilt=.6),
            ui_button(p, t["daily"], PAPER, "calendar", tilt=-.4),
            ui_button(p, t["upload"], PAPER, "photo", tilt=.4),
            ui_button(p, t["my"], PAPER, "gallery", tilt=-.5),
            ui_button(p, t["settings"], PAPER, "gear", tilt=.3)]
    body = (f'<div data-name="ana-ekran" style="flex:1;display:flex;flex-direction:column;align-items:center;'
            f'justify-content:center;gap:{p(26)};padding-bottom:{p(30)}">{logo}{word}{chips}'
            f'<div style="display:flex;flex-direction:column;align-items:center;gap:{p(22)};margin-top:{p(10)}">'
            f'{"".join(btns)}</div></div>')
    return status_bar(p, plat) + body


def scr_levels(p, t, plat):
    tiles = []
    for n in range(73, 97):
        if n < 89:
            two = n % 4 == 0
            fill, txt = (PAPER if two else YELLOW), INK
            stars = "".join(star(p.n(17), STAR if i < (2 if two else 3) else "#FFFFFF", INK, 2) for i in range(3))
            inner = (f'<div style="{F_UI};font-size:{p(28)};color:{txt}">{n}</div>'
                     f'<div style="display:flex;gap:{p(1)}">{stars}</div>')
        elif n == 89:
            fill = RED
            stars = "".join(star(p.n(17), "#FFFFFF", INK, 2) for _ in range(3))
            inner = (f'<div style="{F_UI};font-size:{p(28)};color:{PAPER}">{n}</div>'
                     f'<div style="display:flex;gap:{p(1)};opacity:.5">{stars}</div>')
        else:
            fill = "#E4E4E4"
            inner = icon("lock", p.n(30), "#8E8E8E")
        tiles.append(f'<div data-name="bolum-{n}" style="{neo(p, fill, radius=14, border=3, shadow=(4, 4))}width:{p(112)};'
                     f'height:{p(112)};display:flex;flex-direction:column;align-items:center;justify-content:center;'
                     f'gap:{p(6)};transform:rotate({(-1) ** n * .8}deg)">{inner}</div>')
    rows = "".join(f'<div style="display:flex;gap:{p(16)}">{"".join(tiles[i:i + 4])}</div>' for i in range(0, 24, 4))
    grid = (f'<div data-name="bolum-izgara" style="flex:1;display:flex;flex-direction:column;align-items:center;'
            f'justify-content:center;gap:{p(16)};padding-bottom:{p(30)}">{rows}</div>')
    return status_bar(p, plat) + header(p, t["levels"], chip(p, "242", YELLOW, "star")) + grid


def game_chips(p, score="103", moves="0/27"):
    return (f'<div style="display:flex;gap:{p(8)}">{chip(p, score, RED, "star", PAPER)}'
            f'{chip(p, moves, PAPER, "cube")}</div>')


def scr_game(p, t, plat, sprite="frog", level="89", **kw):
    size = p.n(520)
    b = board_svg(sprite, size, symbols=kw.get("symbols", False), badges=kw.get("badges"),
                  tilt=0, shadow=p.n(9), cleared=kw.get("cleared", ()))
    extra = kw.get("below", "")
    title = kw.get("title") or t["level"].format(n=level)
    return (status_bar(p, plat) + header(p, title, game_chips(p, *kw.get("chips", ("103", "0/27")))) +
            board_area(p, b + extra) + tools(p, t, active=kw.get("active"), skip=kw.get("skip", True)))


def scr_photo(p, t, plat):
    card = (f'<div style="{neo(p, PAPER, radius=16, border=3.5, shadow=(8, 8))}padding:{p(18)};flex:none;'
            f'transform:rotate(-1.5deg)">{sprite_svg("strawberry", p.n(250))}</div>')
    pal = SPRITES["strawberry"]["pal"]
    sw = "".join(f'<div style="width:{p(40)};height:{p(40)};background:{c};border:{p(3)} solid {INK};'
                 f'box-sizing:border-box;box-shadow:{p(3)} {p(3)} 0 {INK}"></div>' for c in pal.values())
    slider = (f'<div style="width:{p(470)};display:flex;flex-direction:column;gap:{p(14)}">'
              f'<div style="{F_UI};font-size:{p(19)};color:{INK}">{t["psize"].format(n=24)}</div>'
              f'<div style="position:relative;height:{p(26)}"><div style="position:absolute;left:0;right:0;top:{p(10)};'
              f'height:{p(6)};background:{INK};border-radius:{p(3)}"></div>'
              f'<div style="position:absolute;left:{p(130)};top:0;width:{p(26)};height:{p(26)};border-radius:50%;'
              f'background:{RED};border:{p(3)} solid {INK};box-sizing:border-box"></div></div></div>')
    body = (f'<div data-name="fotograf-ekrani" style="flex:1;display:flex;flex-direction:column;align-items:center;'
            f'justify-content:center;gap:{p(26)};padding-bottom:{p(50)}">{card}'
            f'<div style="display:flex;gap:{p(14)};margin-top:{p(6)}">{sw}</div>'
            f'<div style="{F_UI5};font-size:{p(17)};color:{INK}">{t["stays"]}</div>'
            f'{ui_button(p, t["pick"], SKY, "gallery", width=470, height=70)}{slider}'
            f'{ui_button(p, t["create"], RED, None, PAPER, width=470, height=70)}</div>')
    return status_bar(p, plat) + header(p, t["upload"], "") + body


def scr_complete(p, t, plat):
    base = scr_game(p, t, plat, sprite="smiley", level="1", chips=("1260", "5/4"),
                    cleared={(r, c) for r in range(14) for c in range(14)})

    def row(k, v):
        return (f'<div style="display:flex;justify-content:space-between;{F_UI};font-size:{p(19)};color:{INK}">'
                f'<div>{k}</div><div>{v}</div></div>')
    dlg = (f'<div data-name="bolum-tamam" style="position:absolute;left:{p(64)};top:{p(300)};width:{p(440)};'
           f'{neo(p, PAPER, radius=22, border=4, shadow=(9, 9))}padding:{p(30)} {p(30)} {p(30)};display:flex;'
           f'flex-direction:column;gap:{p(16)};transform:rotate(-1deg)">'
           f'<div style="{F_UI};font-size:{p(30)};color:{INK};text-align:center">{t["complete"]}</div>'
           f'<div style="display:flex;justify-content:center;gap:{p(12)};margin-bottom:{p(6)}">'
           f'{star(p.n(62))}{star(p.n(62))}{star(p.n(62))}</div>'
           f'{row(t["moves"], "5 / " + t["par"].format(n=4))}{row(t["score"], "1260")}{row(t["best"], "x5")}'
           f'<div style="margin-top:{p(8)}">{ui_button(p, t["next"], RED, None, PAPER, width=380, height=62)}</div>'
           f'<div style="display:flex;gap:{p(14)}">'
           f'<div style="{neo(p, SKY, bubble=True, shadow=(4, 4))}flex:1;padding:{p(14)} 0;text-align:center;'
           f'{F_UI};font-size:{p(20)};color:{INK}">{t["replay"]}</div>'
           f'<div style="{neo(p, MINT, bubble=True, shadow=(4, 4))}flex:1;padding:{p(14)} 0;text-align:center;'
           f'{F_UI};font-size:{p(20)};color:{INK}">{t["menu"]}</div></div></div>')
    shade = '<div data-name="karartma" style="position:absolute;left:0;top:0;width:100%;height:100%;background:rgba(17,17,17,.5)"></div>'
    confetti = []
    rnd = random.Random(8)
    for _ in range(22):
        s = rnd.choice((12, 16, 20))
        confetti.append(f'<div style="position:absolute;left:{p(rnd.uniform(20, 540))};top:{p(rnd.uniform(120, 300))};'
                        f'width:{p(s)};height:{p(s * .6)};background:{rnd.choice([YELLOW, SKY, PINK, MINT, RED])};'
                        f'border:{p(2)} solid {INK};transform:rotate({rnd.randint(-40, 40)}deg)"></div>')
    return base + shade + "".join(confetti) + dlg


def screen_inner(p, t, plat, idx):
    if idx == 1:
        return scr_home(p, t, plat)
    if idx == 2:
        return scr_levels(p, t, plat)
    if idx == 3:
        return scr_game(p, t, plat, "frog", "89")
    if idx == 4:
        return scr_game(p, t, plat, "frog", "89", badges=(4, 11, 0, 7), active="eye")
    if idx == 5:
        streak = chip(p, t["streak"].format(n=7), PAPER, "fire", RED, tilt=-2)
        return scr_game(p, t, plat, "blob", title=t["daily"], chips=("256", "0/37"), skip=False, below=streak)
    if idx == 6:
        return scr_photo(p, t, plat)
    if idx == 7:
        note = chip(p, t["cb_hint"], PAPER, "eye", tilt=1.5)
        return scr_game(p, t, plat, "frog", "89", symbols=True, below=note)
    return scr_complete(p, t, plat)


def phone(p, plat, ratio, inner):
    W = 600
    H = W * ratio
    rad = 78 if plat == "ios" else 60
    scr_w, scr_h = p.n(W - 32), p.n(H - 32)
    return (f'<div data-name="telefon" style="position:relative;width:{p(W)};height:{p(H)};box-sizing:border-box;'
            f'padding:{p(16)};background:{INK};border-radius:{p(rad)};box-shadow:{p(22)} {p(22)} 0 rgba(17,17,17,.9)">'
            f'<div data-name="ekran" style="position:relative;width:100%;height:100%;overflow:hidden;'
            f'border-radius:{p(rad - 16)};background:{SCENE};display:flex;flex-direction:column">'
            f'{dots(scr_w, scr_h, p.n(16), p.n(2.2), 26)}{inner}'
            f'<div style="position:absolute;left:50%;bottom:{p(12)};width:{p(170)};height:{p(6)};margin-left:{p(-85)};'
            f'background:{INK};border-radius:{p(3)}"></div></div></div>')


# ---------------------------------------------------------------- kareler
def edges(W, H, e):
    return (f'<div data-name="kenar-ust" style="position:absolute;left:0;top:0;width:{W}px;height:{e}px;background:{SKY}"></div>'
            f'<div data-name="kenar-alt" style="position:absolute;left:0;top:{H - e}px;width:{W}px;height:{e}px;background:{MINT}"></div>'
            f'<div data-name="kenar-sol" style="position:absolute;left:0;top:0;width:{e}px;height:{H}px;background:{PINK}"></div>'
            f'<div data-name="kenar-sag" style="position:absolute;left:{W - e}px;top:0;width:{e}px;height:{H}px;background:{RED}"></div>')


def frame(name, W, H, body, bg=SCENE):
    return (f'<div class="kare" id="{name}" data-name="{name}" style="position:relative;width:{W}px;height:{H}px;'
            f'flex:none;overflow:hidden;background:{bg}">{body}</div>')


def screenshot(plat, lang, idx):
    W, H = (1080, 1920) if plat == "android" else (1320, 2868)
    u = W / 1080
    p = S(u)
    t = METIN[lang]
    title = t["shots"][idx - 1]
    top = 70 if plat == "android" else 150
    card_h = 250 if plat == "android" else 290
    shadow_c = SHADOWS[(idx - 1) % 4]
    tilt = -1.2 if idx % 2 else 1.0
    card = (
        f'<div data-name="baslik-karti" style="position:absolute;left:{p(84)};top:{p(top)};width:{p(912)};height:{p(card_h)};'
        f'{neo(p, PAPER, radius=26, border=7, shadow=(16, 16), shadow_color=shadow_c)}transform:rotate({tilt}deg);'
        f'display:flex;align-items:center;justify-content:center;padding:0 {p(70)}">'
        f'<div data-name="baslik" style="{F_HEAD};font-size:{p(66 if len(title) < 34 else 60)};line-height:1.12;color:{INK};'
        f'text-align:center">{title}</div>'
        f'<div data-name="numara" style="position:absolute;left:{p(-34)};top:{p(-34)};width:{p(88)};height:{p(88)};'
        f'border-radius:50%;background:{INK};display:flex;align-items:center;justify-content:center;'
        f'{F_HEAD};font-size:{p(48)};color:{YELLOW};line-height:1">{idx}</div></div>')
    ratio = 2.07 if plat == "android" else 2.17
    ph_top = top + card_h + (70 if plat == "android" else 110)
    avail = H / u - ph_top - (70 if plat == "android" else 150)
    pw = min(820, avail / ratio)
    k = pw * u / 600
    pp = S(k)
    ph = phone(pp, plat, ratio, screen_inner(pp, t, plat, idx))
    body = (dots(W, H, p.n(44), p.n(9)) + edges(W, H, round(22 * u)) + card +
            f'<div data-name="telefon-konum" style="position:absolute;left:{round((W - pw * u) / 2 - 11 * u)}px;'
            f'top:{p(ph_top)}">{ph}</div>')
    name = f"{'play' if plat == 'android' else 'appstore'}-{lang}-{idx:02d}"
    return name, W, H, frame(name, W, H, body)


def wordmark(p, size, outline=True):
    stroke = (f"-webkit-text-stroke:{p(size * .1)} {INK};paint-order:stroke fill;"
              f"text-shadow:{p(size * .07)} {p(size * .07)} 0 {INK};") if outline else ""
    return (f'<div data-name="logo-yazi" style="{F_HEAD};font-size:{p(size)};line-height:1;color:{PAPER};'
            f'letter-spacing:{p(size * .02)};white-space:nowrap;{stroke}">PIXEL POP</div>')


def tag(p, text, size, shadow_color=RED, tilt=-2):
    return (f'<div data-name="alt-baslik" style="{neo(p, PAPER, radius=6, border=size * .14, shadow=(size * .22, size * .22), shadow_color=shadow_color)}'
            f'padding:{p(size * .28)} {p(size * .7)};transform:rotate({tilt}deg);{F_HEAD};font-size:{p(size)};'
            f'line-height:1.1;color:{INK};white-space:nowrap;display:inline-block">{text}</div>')


def feature_graphic(lang):
    W, H = 1024, 500
    p = S(1)
    t = METIN[lang]
    b = icon_frame(270, tilt=-8)
    # duvara uçan küpler (oyunun mekaniği)
    flying = ""
    for x, y, c, tr in ((668, 66, "#FFC928", 14), (958, 250, "#FF5A5F", -8), (650, 404, "#3B2A1A", 20)):
        flying += (f'<div style="position:absolute;left:{x}px;top:{y}px;width:30px;height:30px;background:{c};'
                   f'border:3px solid {INK};box-sizing:border-box;transform:rotate({tr}deg)"></div>')
    body = (dots(W, H, 40, 8) + edges(W, H, 20) +
            f'<div data-name="sol" style="position:absolute;left:68px;top:0;height:{H}px;width:560px;display:flex;'
            f'flex-direction:column;justify-content:center;align-items:flex-start;gap:34px">'
            f'{wordmark(p, 84)}{tag(p, t["subtitle"], 40)}'
            f'<div style="margin-top:22px;{neo(p, PAPER, radius=16, border=4, shadow=(6, 6))}padding:12px 24px;'
            f'{F_UI};font-size:26px;color:{INK};white-space:nowrap">{t["pill"]}</div></div>'
            f'<div data-name="cerceve-konum" style="position:absolute;left:700px;top:112px">{b}</div>{flying}')
    name = f"kapak-{lang}"
    return name, W, H, frame(name, W, H, body)


def app_icon(size):
    p = S(size / 512)
    body = (dots(size, size, p.n(32), p.n(6.5)) +
            f'<div style="position:absolute;left:{p(68)};top:{p(64)}">{icon_frame(p.n(360))}</div>')
    name = f"ikon-{size}"
    return name, size, size, frame(name, size, size, body)


def icon_frame(size, tilt=-6):
    """Mağaza ikonu çerçevesi: tema renkli duvarlar (gök, kırmızı, nane, pembe) + gülen yüz."""
    sp = dict(SPRITES["smiley"])
    SPRITES["_icon"] = dict(rows=sp["rows"], pal=dict(sp["pal"]), walls="ABCD")
    SPRITES["_icon"]["pal"].update({"A": SKY, "B": RED, "C": MINT, "D": PINK})
    html = board_svg("_icon", size, tilt=tilt, shadow=size * .045)
    del SPRITES["_icon"]
    return html


def logo_frames(lang):
    p = S(1)
    t = METIN[lang]
    out = []
    body = (dots(1600, 640, 44, 9) +
            f'<div style="position:absolute;left:0;top:0;width:1600px;height:640px;display:flex;align-items:center;'
            f'justify-content:center;gap:70px"><div style="flex:none">{icon_frame(380)}</div>'
            f'<div style="display:flex;flex-direction:column;align-items:flex-start;gap:36px">{wordmark(p, 150)}'
            f'{tag(p, t["subtitle"], 64)}</div></div>')
    out.append((f"logo-yatay-{lang}", 1600, 640, frame(f"logo-yatay-{lang}", 1600, 640, body)))
    body = (f'<div style="position:absolute;left:0;top:0;width:1600px;height:640px;display:flex;align-items:center;'
            f'justify-content:center;gap:70px"><div style="flex:none">{icon_frame(380)}</div>'
            f'<div style="display:flex;flex-direction:column;align-items:flex-start;gap:36px">{wordmark(p, 150)}'
            f'{tag(p, t["subtitle"], 64)}</div></div>')
    out.append((f"logo-seffaf-{lang}", 1600, 640, frame(f"logo-seffaf-{lang}", 1600, 640, body, "transparent")))
    return out


def mark_frame():
    body = f'<div style="position:absolute;left:112px;top:100px">{icon_frame(780)}</div>'
    return "isaret-seffaf", 1024, 1024, frame("isaret-seffaf", 1024, 1024, body, "transparent")


# ---------------------------------------------------------------- sayfa
CSS = """
*{margin:0;padding:0}
body{background:#F4F1E6;font-family:Roboto,sans-serif;color:#111;padding:80px}
h1{font-family:'Archivo Black',sans-serif;font-size:56px;margin-bottom:12px}
h2{font-family:'Archivo Black',sans-serif;font-size:40px;margin:110px 0 8px}
.not{font-size:22px;color:#555;max-width:1500px;line-height:1.5}
.sira{display:flex;gap:90px;align-items:flex-start;margin-top:32px}
.etiket{font-family:Roboto,sans-serif;font-weight:700;font-size:24px;color:#555}
"""


def labeled(label, html):
    return (f'<div style="display:flex;flex-direction:column;gap:16px;flex:none">'
            f'<div class="etiket">{label}</div>{html}</div>')


def page(title, sections, note=""):
    parts = [f'<!doctype html><html lang="tr"><head><meta charset="utf-8">'
             f'<meta name="viewport" content="width=device-width,initial-scale=1">'
             f'<title>{title}</title>{FONTS}<style>{CSS}</style></head><body><h1>{title}</h1>']
    if note:
        parts.append(f'<p class="not">{note}</p>')
    for heading, desc, items in sections:
        parts.append(f'<h2>{heading}</h2><p class="not">{desc}</p><div class="sira">')
        parts.extend(labeled(f"{n} · {w}×{h}", f) for n, w, h, f in items)
        parts.append('</div>')
    parts.append('</body></html>')
    return "".join(parts)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    note = ("Her kare gerçek piksel ölçüsündedir. Figma'ya html.to.design ile aktarın; kare adları katman adı olur, "
            "metinler düzenlenebilir metin, küpler ve duvarlar ayrı vektör olarak gelir. Benek deseni ayrı bir görsel "
            "katmandır, gizlenebilir. Dışa aktarırken kareyi 1x PNG alın.")
    logo_sec = ("Logo ve uygulama ikonu",
                "iOS ikonu 1024×1024, Google Play ikonu 512×512: köşesiz ve saydamlıksız (mağazalar maskeyi kendisi uygular). "
                "Yatay logo TR ve EN alt başlıkla, sarı zeminli ve saydam.",
                [app_icon(1024), app_icon(512), mark_frame()] + logo_frames("tr") + logo_frames("en"))
    kapak_sec = ("Kapak görseli (Google Play öne çıkan görsel)",
                 "1024×500. Play bazı yerlerde ortasına oynat düğmesi koyar; yazılar solda tutuldu.",
                 [feature_graphic("tr"), feature_graphic("en")])

    def shots(plat, lang):
        return [screenshot(plat, lang, i) for i in range(1, 9)]

    play_desc = "Telefon ekran görüntüleri 1080×1920 (9:16). Play en az 2, en fazla 8 ister; 8 kare hazır."
    ios_desc = ("iPhone 6.9\" ekran görüntüleri 1320×2868. App Store Connect bu boyutu zorunlu tutar ve küçük "
                "iPhone boyutlarını bundan ölçekler. En fazla 10 kare.")
    groups = {
        "logo-kapak": [logo_sec, kapak_sec],
        "android-tr": [("Google Play · Türkçe", play_desc, shots("android", "tr"))],
        "android-en": [("Google Play · English", play_desc, shots("android", "en"))],
        "ios-tr": [("App Store · Türkçe", ios_desc, shots("ios", "tr"))],
        "ios-en": [("App Store · English", ios_desc, shots("ios", "en"))],
    }
    for fname, secs in groups.items():
        (OUT / f"{fname}.html").write_text(page(f"Pixel Pop · {fname}", secs, note), encoding="utf-8")
    allsecs = [s for secs in groups.values() for s in secs]
    (OUT / "hepsi.html").write_text(page("Pixel Pop · Mağaza görselleri", allsecs, note), encoding="utf-8")
    for f in sorted(OUT.glob("*.html")):
        print(f"{f.name}: {f.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
