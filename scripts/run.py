"""Zamanı gelen içerikleri kontrol edip paylaşır ve gunluk.jsonl'e yazar.

Günlükte herhangi bir kaydı olan içerik (yayinlandi/atlandi/hata) bir daha denenmez;
düzeltilen içerik yeni bir id ile tekrar planlanır.
CLI: python scripts/run.py publish-due     (PAGES_BASE ortam değişkeni gerekir)
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import ig
from check import check

ROOT = Path(__file__).resolve().parents[1]


def _logged(root: Path) -> set:
    p = root / "gunluk.jsonl"
    if not p.exists():
        return set()
    return {json.loads(l)["id"] for l in p.read_text(encoding="utf-8").splitlines() if l.strip()}


def _log(root: Path, entry: dict):
    with open(root / "gunluk.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _posts(root: Path):
    for pj in sorted((root / "icerik").glob("*/post.json")):
        yield pj.parent, json.loads(pj.read_text(encoding="utf-8"))


def due(now: datetime, root: Path = ROOT) -> list:
    done = _logged(root)
    out = []
    for _, post in _posts(root):
        if post["id"] not in done and datetime.fromisoformat(post["yayin"]) <= now:
            out.append((post["yayin"], post["id"]))
    return [i for _, i in sorted(out)]


def publish_due(now: datetime, pages_base: str, root: Path = ROOT) -> list:
    ids = set(due(now, root))
    results = []
    for d, post in _posts(root):
        if post["id"] not in ids:
            continue
        entry = {"id": post["id"], "zaman": now.isoformat(), "durum": None, "media_id": None, "neden": None}
        problems = check(str(d))
        if problems:
            entry.update(durum="atlandi", neden="; ".join(problems)[:500])
        else:
            urls = [f"{pages_base.rstrip('/')}/icerik/{d.name}/{m}" for m in post["medya"]]
            try:
                for u in urls:
                    ig.wait_for_url(u)
                if post["kind"] == "story":  # her kare ayrı story
                    ids_ = [ig.publish("story", [u]) for u in urls]
                    entry.update(durum="yayinlandi", media_id=",".join(ids_))
                else:
                    entry.update(durum="yayinlandi", media_id=ig.publish(post["kind"], urls, post.get("caption", "")))
            except ig.IgError as e:
                entry.update(durum="hata", neden=str(e)[:500])
        _log(root, entry)
        results.append(entry)
    return results


if __name__ == "__main__":
    if sys.argv[1:] != ["publish-due"]:
        raise SystemExit(__doc__)
    res = publish_due(datetime.now(timezone.utc), os.environ["PAGES_BASE"])
    print(json.dumps(res, ensure_ascii=False, indent=1))
    sys.exit(1 if any(r["durum"] != "yayinlandi" for r in res) else 0)
