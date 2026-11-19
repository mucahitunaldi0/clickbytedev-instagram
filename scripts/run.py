"""Zamanı gelen içerikleri kontrol edip paylaşır ve gunluk.jsonl'e yazar.

Çift paylaşıma karşı:
- Yayından önce "basladi" kilidi yazılır ve push edilir; aynı içeriği başka bir koşu daha önce
  kilitlediyse paylaşılmaz. Kilidi olan içerik bir daha asla denenmez (sonuç belirsiz olsa bile).
- Medya henüz Pages'te yoksa hiçbir şey yazılmaz; sonraki koşu tekrar dener.
- Yayın zamanından GECIKME'den fazla geçmiş içerik "gecikti" olarak atlanır.
Düzeltilen içerik yeni bir id ile tekrar planlanır.
CLI: python scripts/run.py publish-due     (PAGES_BASE ortam değişkeni gerekir)
"""
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import ig
from check import check

ROOT = Path(__file__).resolve().parents[1]
GECIKME = timedelta(hours=3)
KOSU = uuid.uuid4().hex[:8]


def _entries(root: Path) -> list:
    p = root / "gunluk.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def _log(root: Path, entry: dict):
    with open(root / "gunluk.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _sync(root: Path, msg: str) -> bool:
    """gunluk.jsonl'i commit edip push eder (union merge ile). Git deposu değilse no-op."""
    if not (root / ".git").exists():
        return True
    git = ["git", "-C", str(root)]
    subprocess.run(git + ["add", "gunluk.jsonl"], check=False)
    subprocess.run(git + ["commit", "-q", "-m", msg], check=False, capture_output=True)
    for _ in range(5):
        pulled = subprocess.run(git + ["pull", "-q", "--rebase"], capture_output=True).returncode == 0
        if pulled and subprocess.run(git + ["push", "-q"], capture_output=True).returncode == 0:
            return True
        subprocess.run(git + ["rebase", "--abort"], capture_output=True)
    return False


def _claim(root: Path, id_: str, now: datetime) -> bool:
    _log(root, {"id": id_, "zaman": now.isoformat(), "durum": "basladi", "kosu": KOSU})
    if not _sync(root, f"yayin kilidi: {id_}"):
        return False
    locks = [e for e in _entries(root) if e["id"] == id_ and e["durum"] == "basladi"]
    return min(locks, key=lambda e: (e["zaman"], e.get("kosu", "")))["kosu"] == KOSU


def _posts(root: Path):
    for pj in sorted((root / "icerik").glob("*/post.json")):
        yield pj.parent, json.loads(pj.read_text(encoding="utf-8"))


def due(now: datetime, root: Path = ROOT) -> list:
    done = {e["id"] for e in _entries(root)}
    out = []
    for _, post in _posts(root):
        if post["id"] not in done and datetime.fromisoformat(post["yayin"]) <= now:
            out.append((post["yayin"], post["id"]))
    return [i for _, i in sorted(out)]


def _publish_one(d: Path, post: dict, now: datetime, pages_base: str, root: Path) -> dict:
    entry = {"id": post["id"], "zaman": now.isoformat(), "durum": None, "media_id": None, "neden": None, "kosu": KOSU}
    if now - datetime.fromisoformat(post["yayin"]) > GECIKME:
        entry.update(durum="gecikti", neden="yayın zamanı çok geride kaldı")
        return entry
    problems = check(str(d))
    if problems:
        entry.update(durum="atlandi", neden="; ".join(problems)[:500])
        return entry
    urls = [f"{pages_base.rstrip('/')}/icerik/{d.name}/{m}" for m in post["medya"]]
    try:
        for u in urls:
            ig.wait_for_url(u)
    except ig.IgError as e:
        return {**entry, "durum": "bekliyor", "neden": str(e)}  # loglanmaz: sonraki koşu tekrar dener
    if not _claim(root, post["id"], now):
        return {**entry, "durum": "kilit-yok"}
    published = []
    try:
        if post["kind"] == "story":  # her kare ayrı story
            for u in urls:
                published.append(ig.publish("story", [u]))
        else:
            published.append(ig.publish(post["kind"], urls, post.get("caption", "")))
        entry["durum"] = "yayinlandi"
    except Exception as e:  # ağ/zaman aşımı dahil: kilit yazıldı, asla tekrar denenmez
        entry.update(durum="hata", neden=f"{type(e).__name__}: {e}"[:500])
    entry["media_id"] = ",".join(published) or None
    return entry


def publish_due(now: datetime, pages_base: str, root: Path = ROOT) -> list:
    ids = set(due(now, root))
    results = []
    for d, post in _posts(root):
        if post["id"] not in ids:
            continue
        entry = _publish_one(d, post, now, pages_base, root)
        if entry["durum"] not in ("bekliyor", "kilit-yok"):
            _log(root, entry)
            _sync(root, f"gunluk: {post['id']} {entry['durum']}")
        results.append(entry)
    return results


if __name__ == "__main__":
    if sys.argv[1:] != ["publish-due"]:
        raise SystemExit(__doc__)
    res = publish_due(datetime.now(timezone.utc), os.environ["PAGES_BASE"])
    print(json.dumps(res, ensure_ascii=False, indent=1))
    sys.exit(1 if any(r["durum"] not in ("yayinlandi", "bekliyor") for r in res) else 0)
