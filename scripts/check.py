"""Yayın öncesi kontroller. Boş liste = geçti.

CLI: python scripts/check.py <icerik_klasoru>   (çıkış kodu 0/1)
"""
import json
import re
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
TEXT_EXT = {".md", ".json", ".txt"}
# Instagram API en/boy oranı aralıkları (görseller kullanıcıdan gelir; boyut serbest)
ORAN = {"carousel": (0.8, 1.91), "image": (0.8, 1.91), "story": (0.5, 0.6), "reel": (0.5, 0.6)}


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


def _img_size(p: Path):
    from PIL import Image
    try:
        with Image.open(p) as im:
            return im.size
    except OSError:
        return None


def _probe(p: Path) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "stream=codec_type,codec_name,width,height:format=duration", "-of", "json", str(p)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return json.loads(r.stdout or "{}")


def check(content_dir: str) -> list:
    d = Path(content_dir)
    issues = []
    try:
        post = json.loads((d / "post.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return [f"post.json okunamadı: {e}"]
    kind = post.get("kind")
    if kind not in ORAN:
        issues.append(f"bilinmeyen kind: {kind}")

    # gizli bilgi: klasördeki metin dosyaları
    for f in sorted(d.rglob("*")):
        if f.is_file() and f.suffix.lower() in TEXT_EXT:
            src = f.read_text(encoding="utf-8", errors="replace")
            for p in SECRET_PATTERNS:
                if re.search(p, src):
                    issues.append(f"{f.name}: gizli bilgi şüphesi /{p[:30]}/")
                    break

    # metin kuralları
    issues += _text_rules("caption", post.get("caption", ""))
    if len(post.get("caption", "")) > 2200:
        issues.append("caption: 2200 karakteri aşıyor")

    # medya
    lo, hi = ORAN.get(kind, (0, 99))
    oran_ok = lambda w, h: w >= 320 and lo <= w / h <= hi  # noqa: E731
    for m in post.get("medya", []):
        p = d / m
        if not p.exists():
            issues.append(f"medya yok: {m}")
            continue
        if p.suffix.lower() == ".png":
            issues.append(f"{m}: Instagram API yalnızca JPEG görsel kabul eder (.jpg kullanın)")
        elif p.suffix.lower() in (".jpg", ".jpeg"):
            size = _img_size(p)
            if not size or not oran_ok(*size):
                issues.append(f"{m}: boyut {size} uygun değil (en/boy {lo}-{hi}, genişlik ≥320)")
        elif p.suffix.lower() == ".mp4":
            info = _probe(p)
            v = [s for s in info.get("streams", []) if s.get("codec_type") == "video"]
            dur = float(info.get("format", {}).get("duration", 0))
            if not v or not oran_ok(v[0].get("width", 0), v[0].get("height", 1)) or v[0].get("codec_name") not in ("h264", "hevc"):
                issues.append(f"{m}: video boyut/codec hatalı (9:16, H.264/HEVC)")
            if kind == "reel" and not (3 <= dur <= 900):
                issues.append(f"{m}: süre {dur:.1f} sn (3 sn - 15 dk olmalı)")
            if kind == "story" and dur > 60:
                issues.append(f"{m}: süre {dur:.1f} sn (story en fazla 60)")
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
