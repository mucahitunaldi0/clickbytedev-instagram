"""Yayın öncesi kontroller. Boş liste = geçti.

CLI: python scripts/check.py <icerik_klasoru>   (çıkış kodu 0/1)
"""
import html
import json
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

SECRET_PATTERNS = [
    r"AKIA[0-9A-Z]{16}",
    r"AIza[0-9A-Za-z\-_]{30,}",
    r"-----BEGIN [A-Z ]*(PRIVATE KEY|CERTIFICATE)",
    r"\bsk-[A-Za-z0-9_\-]{20,}",
    r"\bghp_[A-Za-z0-9]{30,}",
    r"\bxox[abp]-[A-Za-z0-9\-]{10,}",
    r"(?i)(key|token|secret|password|passwd|pwd|api)\w*\s*[:=]\s*['\"][^'\"\s]{16,}['\"]",
    r"['\"][A-Fa-f0-9]{32,}['\"]",
    r"['\"][A-Za-z0-9+/]{40,}={0,2}['\"]",
]
BANNED = [r"\ben iyi\b", r"mükemmel", r"devrim", r"kullanıcı dostu", r"\bapp\b(?! store)"]
BRAND_WRONG = [r"\bClickbytedev\b", r"Click Byte Dev", r"\bCBD\b", r"\bClickByteDev\.com\b"]
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿\U0001F000-\U0001F2FF]")
TEXT_EXT = {".html", ".md", ".json", ".dart", ".txt", ".css", ".js"}
SIZES = {"carousel": (1080, 1350), "image": (1080, 1350), "story": (1080, 1920), "reel": (1080, 1920)}


def _visible_text(src: str) -> str:
    src = re.sub(r"(?is)<(script|style|pre)\b.*?</\1>", " ", src)
    return html.unescape(re.sub(r"<[^>]+>", " ", src))


def _text_rules(label: str, text: str) -> list:
    out = []
    if len(EMOJI.findall(text)) > 1:
        out.append(f"{label}: 1'den fazla emoji")
    if text.count("!") > 1:
        out.append(f"{label}: 1'den fazla ünlem")
    low = text.lower()
    for p in BANNED:
        if re.search(p, low):
            out.append(f"{label}: yasak ifade /{p}/")
    for p in BRAND_WRONG:
        if re.search(p, text):
            out.append(f"{label}: marka yazımı hatalı /{p}/")
    return out


def _png_size(p: Path):
    b = p.read_bytes()[:24]
    if b[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", b[16:24])


def _probe(p: Path) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "stream=codec_type,codec_name,width,height:format=duration", "-of", "json", str(p)],
                       capture_output=True, text=True)
    return json.loads(r.stdout or "{}")


def check(content_dir: str) -> list:
    d = Path(content_dir)
    issues = []
    try:
        post = json.loads((d / "post.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return [f"post.json okunamadı: {e}"]
    kind = post.get("kind")
    if kind not in SIZES:
        issues.append(f"bilinmeyen kind: {kind}")

    # gizli bilgi: render edilen her metin kaynağı
    for f in sorted(d.rglob("*")):
        if f.is_file() and f.suffix.lower() in TEXT_EXT:
            src = f.read_text(encoding="utf-8", errors="replace")
            for p in SECRET_PATTERNS:
                if re.search(p, src):
                    issues.append(f"{f.name}: gizli bilgi şüphesi /{p[:30]}/")
                    break

    # metin kuralları: caption + slaytların görünür metni (kod blokları hariç)
    issues += _text_rules("caption", post.get("caption", ""))
    if len(post.get("caption", "")) > 2200:
        issues.append("caption: 2200 karakteri aşıyor")
    for f in sorted(d.glob("*.html")):
        issues += _text_rules(f.name, _visible_text(f.read_text(encoding="utf-8")))

    # dart kod parçaları
    darts = sorted(d.glob("*.dart"))
    if darts:
        dart = shutil.which("dart")
        if not dart:
            issues.append("dart bulunamadı; kod kontrol edilemedi")
        else:
            r = subprocess.run([dart, "analyze", "--fatal-infos", *map(str, darts)],
                               capture_output=True, text=True, cwd=d)
            if r.returncode != 0:
                issues.append("dart analyze hatası: " + (r.stdout + r.stderr).strip()[-400:])

    # medya
    want = SIZES.get(kind)
    for m in post.get("medya", []):
        p = d / m
        if not p.exists():
            issues.append(f"medya yok: {m}")
            continue
        if p.suffix.lower() == ".png":
            if _png_size(p) != want:
                issues.append(f"{m}: boyut {_png_size(p)} ≠ {want}")
        elif p.suffix.lower() == ".mp4":
            info = _probe(p)
            v = [s for s in info.get("streams", []) if s.get("codec_type") == "video"]
            a = [s for s in info.get("streams", []) if s.get("codec_type") == "audio"]
            dur = float(info.get("format", {}).get("duration", 0))
            if not v or (v[0].get("width"), v[0].get("height")) != want or v[0].get("codec_name") != "h264":
                issues.append(f"{m}: video boyut/codec hatalı")
            if kind == "reel" and not (15 <= dur <= 45):
                issues.append(f"{m}: süre {dur:.1f} sn (15-45 olmalı)")
            if kind == "story" and dur > 60:
                issues.append(f"{m}: süre {dur:.1f} sn (story en fazla 60)")
            if kind == "reel" and (not a or a[0].get("codec_name") != "aac"):
                issues.append(f"{m}: aac ses yok")
        else:
            issues.append(f"{m}: desteklenmeyen dosya türü")
    if not post.get("medya"):
        issues.append("medya listesi boş")
    if kind == "carousel" and not (2 <= len(post.get("medya", [])) <= 20) and len(post.get("medya", [])) != 1:
        issues.append("carousel 2-20 medya olmalı")
    return issues


if __name__ == "__main__":
    res = check(sys.argv[1])
    print("\n".join(res) or "OK")
    sys.exit(1 if res else 0)
