"""İçerik HTML'lerini Figma'ya sürüklenebilir, düzenlenebilir SVG'lere çevirir.

Her yazı satırı ayrı <text> (metin katmanı), kutular <rect>, görseller gömülü <image> olur.
Reel'lerde animasyonun son karesi alınır.

CLI: python scripts/figma_svg.py [icerik_klasoru ...]   (boşsa tüm icerik/*) -> figma/<id>/<ad>.svg
"""
import base64
import json
import sys
from html import escape
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).parent))
from render import SIZES  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

# Sayfadan çizim listesi çıkarır. Dönüşümler geçici olarak kapatılıp ölçülür, sonra matrisle geri uygulanır.
EXTRACT_JS = r"""
() => {
  const out = [];
  const all = [...document.querySelectorAll('body *')];
  const tf = new Map();
  for (const el of all) {
    const cs = getComputedStyle(el);
    if (cs.transform && cs.transform !== 'none') {
      tf.set(el, {m: cs.transform, o: cs.transformOrigin});
      el.style.setProperty('transform', 'none', 'important');
    }
  }
  const groupOf = el => { // en yakın dönüşümlü ata
    for (let e = el; e && e !== document.body; e = e.parentElement) if (tf.has(e)) return e;
    return null;
  };
  const gid = new Map(); let gi = 0;
  const groups = [];
  for (const [el, t] of tf) {
    const r = el.getBoundingClientRect();
    const [ox, oy] = t.o.split(' ').map(parseFloat);
    gid.set(el, gi++);
    groups.push({m: t.m.replace('matrix(', '').replace(')', '').split(',').map(Number), cx: r.left + ox, cy: r.top + oy});
  }
  const opac = el => { let o = 1; for (let e = el; e && e !== document.body; e = e.parentElement) o *= parseFloat(getComputedStyle(e).opacity); return o; };
  const g = el => { const a = groupOf(el); return a ? gid.get(a) : -1; };
  const ctx = document.createElement('canvas').getContext('2d');

  for (const el of all) {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    const o = opac(el); if (o < 0.01) continue;
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    const rad = parseFloat(cs.borderTopLeftRadius) || 0;
    if (el.tagName === 'IMG') {
      out.push({t: 'img', g: g(el), o, x: r.left, y: r.top, w: r.width, h: r.height, rad, src: el.currentSrc,
                fit: cs.objectFit, pos: cs.objectPosition, name: el.closest('.telefon') ? 'Ekran' : 'İkon'});
      continue;
    }
    const bg = cs.backgroundColor, bi = cs.backgroundImage, bw = parseFloat(cs.borderTopWidth) || 0;
    const grid = el.classList.contains('zemin');
    if (grid || (bg && !bg.endsWith(', 0)') && bg !== 'transparent') || (bi && bi.includes('gradient')) || bw > 0) {
      out.push({t: 'box', g: g(el), o, x: r.left, y: r.top, w: r.width, h: r.height, rad, bg, bi: grid ? '' : bi,
                bw, bc: cs.borderTopColor, grid, name: (el.className || el.tagName).toString().split(' ')[0] || 'kutu'});
    }
  }
  // yazılar: her karakterin kutusundan satırlar çıkarılır
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const lines = new Map();
  let n;
  while ((n = walker.nextNode())) {
    const el = n.parentElement; const cs = getComputedStyle(el);
    if (!n.data.trim() || cs.display === 'none') continue;
    const o = opac(el); if (o < 0.01) continue;
    if (el.closest('script,style')) continue;
    const fam = cs.fontFamily.split(',')[0].replace(/["']/g, '').trim();
    ctx.font = `${cs.fontStyle} ${cs.fontWeight} ${cs.fontSize} "${fam}"`;
    const asc = ctx.measureText('Hg').fontBoundingBoxAscent;
    const block = el.closest('h1,h2,h3,p,pre,div,span.logo,span') ;
    const tr = cs.textTransform;
    const range = document.createRange();
    let cur = null;
    const flush = () => {
      if (!cur) return;
      const txt = cur.s.replace(/\s+$/, '');
      if (txt.trim()) {
        const key = (block ? [...document.querySelectorAll('*')].indexOf(block) : 0) + ':' + Math.round(cur.top);
        if (!lines.has(key)) lines.set(key, {g: g(el), y: cur.top + asc, runs: [], o, blockName: block ? (block.className || block.tagName).toString().split(' ')[0] : 'yazi'});
        lines.get(key).runs.push({x: cur.x, s: tr === 'lowercase' ? txt.toLocaleLowerCase('tr') : txt,
          fam, w: cs.fontWeight, size: parseFloat(cs.fontSize), fill: cs.color,
          ls: cs.letterSpacing === 'normal' ? 0 : parseFloat(cs.letterSpacing), italic: cs.fontStyle === 'italic'});
      }
      cur = null;
    };
    for (let i = 0; i < n.data.length; i++) {
      const ch = n.data[i];
      if (ch === '\n') { flush(); continue; }
      range.setStart(n, i); range.setEnd(n, i + 1);
      const rs = range.getClientRects(); if (!rs.length) continue;
      const rc = rs[0];
      if (cur && Math.abs(rc.top - cur.top) > 2) flush();
      if (!cur) { if (ch === ' ') continue; cur = {x: rc.left, top: rc.top, s: ''}; }
      cur.s += ch;
    }
    flush();
  }
  return {items: out, lines: [...lines.values()], groups};
}
"""


def _uri(src: str) -> str:
    p = Path(src.replace("file:///", "").replace("%20", " "))
    from urllib.parse import unquote
    p = Path(unquote(src[len("file:///"):])) if src.startswith("file:///") else p
    mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def _color(c: str):
    """'rgb(a, b, c)' / 'rgba(a, b, c, x)' -> ('rgb(a,b,c)', opaklık)"""
    v = c[c.index("(") + 1:-1].split(",")
    return f"rgb({','.join(x.strip() for x in v[:3])})", float(v[3]) if len(v) > 3 else 1.0


def _gradient(bi: str, gid: str):
    # yalnızca brand.css'teki 'linear-gradient(160deg, renk, renk N%)' biçimi
    import math
    import re
    body = bi[bi.index("(") + 1:bi.rindex(")")]
    ang = re.match(r"\s*(\d+)deg", body)
    a = math.radians(int(ang.group(1)) if ang else 180)
    stops = re.findall(r"(rgba?\([^)]*\))\s*(\d+%)?", body)
    dx, dy = math.sin(a) / 2, -math.cos(a) / 2
    s = "".join(f'<stop offset="{p or (str(round(i / max(1, len(stops) - 1) * 100)) + "%")}" stop-color="{_color(c)[0]}" stop-opacity="{_color(c)[1]}"/>'
                for i, (c, p) in enumerate(stops))
    return (f'<linearGradient id="{gid}" x1="{0.5 - dx:.3f}" y1="{0.5 - dy:.3f}" x2="{0.5 + dx:.3f}" y2="{0.5 + dy:.3f}">{s}</linearGradient>')


def to_svg(data: dict, w: int, h: int) -> str:
    defs, layers = [], {}
    add = lambda gi, s: layers.setdefault(gi, []).append(s)  # noqa: E731
    for i, it in enumerate(data["items"]):
        x, y, bw, bh, r = (round(it[k], 2) for k in ("x", "y", "w", "h", "rad"))
        op = f' opacity="{it["o"]:.2f}"' if it["o"] < 0.99 else ""
        if it["t"] == "box":
            if it["grid"]:
                fill, a = _color(it["bg"])
                lines = "".join(f'<line x1="{gx}" y1="0" x2="{gx}" y2="{h}"/>' for gx in range(0, w, 36))
                lines += "".join(f'<line x1="0" y1="{gy}" x2="{w}" y2="{gy}"/>' for gy in range(0, h, 36))
                add(it["g"], f'<rect id="Zemin" width="{w}" height="{h}" fill="{fill}"/>'
                             f'<g id="Izgara" stroke="#ffffff" stroke-opacity="0.03" stroke-width="1">{lines}</g>')
                continue
            if "gradient" in it["bi"]:
                defs.append(_gradient(it["bi"], f"gr{i}"))
                fill = f'url(#gr{i})'
                fo = ""
            else:
                fill, a = _color(it["bg"]) if it["bg"] and not it["bg"].endswith(", 0)") else ("none", 1)
                fo = f' fill-opacity="{a}"' if a < 1 else ""
            st = ""
            if it["bw"] > 0:
                sc, sa = _color(it["bc"])
                st = f' stroke="{sc}" stroke-width="{it["bw"]}"' + (f' stroke-opacity="{sa}"' if sa < 1 else "")
            add(it["g"], f'<rect id="{escape(it["name"])}" x="{x}" y="{y}" width="{bw}" height="{bh}" rx="{r}" fill="{fill}"{fo}{st}{op}/>')
        else:
            defs.append(f'<clipPath id="c{i}"><rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="{r}"/></clipPath>')
            par = "none"
            if it["fit"] == "cover":
                par = ("xMidYMin" if it["pos"].split()[-1] in ("0%", "0px", "top") else "xMidYMid") + " slice"
            elif it["fit"] == "contain":
                par = "xMidYMid meet"
            add(it["g"], f'<image id="{it["name"]}" x="{x}" y="{y}" width="{bw}" height="{bh}" preserveAspectRatio="{par}" '
                         f'clip-path="url(#c{i})" xlink:href="{_uri(it["src"])}"{op}/>')
    for ln in data["lines"]:
        sp = []
        for run in ln["runs"]:
            fill, a = _color(run["fill"])
            attrs = (f'x="{run["x"]:.2f}" font-family="{escape(run["fam"])}" font-weight="{run["w"]}" '
                     f'font-size="{run["size"]}" fill="{fill}"')
            if a < 1:
                attrs += f' fill-opacity="{a}"'
            if run["ls"]:
                attrs += f' letter-spacing="{run["ls"]:.2f}"'
            if run["italic"]:
                attrs += ' font-style="italic"'
            sp.append(f'<tspan {attrs}>{escape(run["s"])}</tspan>')
        op = f' opacity="{ln["o"]:.2f}"' if ln["o"] < 0.99 else ""
        add(ln["g"], f'<text id="{escape(ln["blockName"])}" y="{ln["y"]:.2f}" xml:space="preserve"{op}>{"".join(sp)}</text>')
    body = "".join(layers.get(-1, []))
    for gi, grp in enumerate(data["groups"]):
        if gi not in layers:
            continue
        m, cx, cy = grp["m"], grp["cx"], grp["cy"]
        tr = f'translate({cx:.2f} {cy:.2f}) matrix({" ".join(f"{v:.5f}" for v in m)}) translate({-cx:.2f} {-cy:.2f})'
        body += f'<g id="Telefon" transform="{tr}">{"".join(layers[gi])}</g>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<defs>{"".join(defs)}</defs>{body}</svg>')


def export(d: Path, page) -> list:
    post = json.loads((d / "post.json").read_text(encoding="utf-8"))
    kind = post["kind"]
    if kind == "image":
        return []  # kullanıcının kendi görseli
    w, h = SIZES[kind]
    page.set_viewport_size({"width": w, "height": h})
    files = sorted(d.glob("reel.html" if kind == "reel" else "*-*.html"))
    out_dir = ROOT / "figma" / d.name
    out_dir.mkdir(parents=True, exist_ok=True)
    res = []
    for f in files:
        page.goto(f.resolve().as_uri(), wait_until="networkidle")
        page.evaluate("document.fonts.ready")
        if kind == "reel":
            page.wait_for_function("window.gsap && window.oynat")
            page.evaluate("() => { const tl = window.oynat(); tl.progress(1); tl.pause(); }")
        svg = to_svg(page.evaluate(EXTRACT_JS), w, h)
        p = out_dir / f"{f.stem}.svg"
        p.write_text(svg, encoding="utf-8")
        res.append(p)
    return res


if __name__ == "__main__":
    dirs = [Path(a) for a in sys.argv[1:]] or sorted(p for p in (ROOT / "icerik").iterdir() if (p / "post.json").exists())
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page()
        for d in dirs:
            for p in export(d, pg):
                print(p.relative_to(ROOT), f"{p.stat().st_size // 1024} KB")
        b.close()
