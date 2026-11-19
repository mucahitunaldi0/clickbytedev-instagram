"""Instagram Graph API (Instagram Login) istemcisi. Yalnızca resmi API; standart kütüphane.

Ortam: IG_TOKEN, IG_USER_ID.
CLI:
  python scripts/ig.py publish <image|carousel|reel|story> <caption_file|-> <url>...
  python scripts/ig.py comments [--hours 24]
  python scripts/ig.py reply <comment_id> <metin_dosyasi>
  python scripts/ig.py insights [--days 31]
  python scripts/ig.py token-check
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

BASE = "https://graph.instagram.com/v22.0"
POLL_S = 10
POLL_TIMEOUT_S = 600


class IgError(Exception):
    pass


def _token():
    return os.environ["IG_TOKEN"]


def _uid():
    return os.environ["IG_USER_ID"]


def _request(url, data=None):
    req = urllib.request.Request(url, data=data, method="POST" if data is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            out = json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            out = json.loads(e.read() or b"{}")
        except Exception:
            raise IgError(f"HTTP {e.code}") from e
    except (urllib.error.URLError, OSError, ValueError) as e:  # ağ, zaman aşımı, bozuk JSON
        raise IgError(f"istek başarısız: {e}") from e
    if isinstance(out, dict) and "error" in out:
        raise IgError(out["error"].get("message", str(out["error"])))
    return out


def _id(resp: dict) -> str:
    if not isinstance(resp, dict) or "id" not in resp:
        raise IgError(f"yanıtta id yok: {str(resp)[:200]}")
    return resp["id"]


def api(method: str, path: str, **params) -> dict:
    params["access_token"] = _token()
    q = urllib.parse.urlencode(params)
    url = f"{BASE}/{path.lstrip('/')}"
    if method == "GET":
        return _request(f"{url}?{q}")
    return _request(url, data=q.encode())


def wait_for_url(url: str, timeout_s: int = 600) -> None:
    """Medya GitHub Pages'te yayına girene kadar bekler."""
    end = time.time() + timeout_s
    while True:
        try:
            with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=30) as r:
                if getattr(r, "status", 200) == 200:
                    return
        except (urllib.error.URLError, OSError):
            pass
        if time.time() >= end:
            raise IgError(f"medya erişilemiyor: {url}")
        time.sleep(15)


def _media_param(url):
    return ("video_url" if url.lower().endswith((".mp4", ".mov")) else "image_url"), url


def _wait_container(cid):
    end = time.time() + POLL_TIMEOUT_S
    while True:
        st = api("GET", cid, fields="status_code").get("status_code")
        if st in ("FINISHED", "PUBLISHED"):
            return
        if st in ("ERROR", "EXPIRED"):
            raise IgError(f"container {cid} durumu {st}")
        if time.time() >= end:
            raise IgError(f"container {cid} zaman aşımı ({st})")
        time.sleep(POLL_S)


def publish(kind: str, media_urls: list, caption: str = "") -> str:
    uid = _uid()
    if kind == "carousel":
        children = []
        for u in media_urls:
            k, v = _media_param(u)
            extra = {"media_type": "VIDEO"} if k == "video_url" else {}
            children.append(_id(api("POST", f"{uid}/media", is_carousel_item="true", **{k: v}, **extra)))
        cid = _id(api("POST", f"{uid}/media", media_type="CAROUSEL", children=",".join(children), caption=caption))
    elif kind == "reel":
        cid = _id(api("POST", f"{uid}/media", media_type="REELS", video_url=media_urls[0], caption=caption))
    elif kind == "story":
        k, v = _media_param(media_urls[0])
        cid = _id(api("POST", f"{uid}/media", media_type="STORIES", **{k: v}))
    elif kind == "image":
        cid = _id(api("POST", f"{uid}/media", image_url=media_urls[0], caption=caption))
    else:
        raise IgError(f"bilinmeyen tür: {kind}")
    _wait_container(cid)
    return _id(api("POST", f"{uid}/media_publish", creation_id=cid))


def _recent_media(limit=10, fields="id,timestamp,caption,media_type,permalink"):
    return api("GET", f"{_uid()}/media", fields=fields, limit=limit).get("data", [])


def comments(since_hours: int = 24) -> list:
    since = datetime.now(timezone.utc) - timedelta(hours=since_hours)
    me = os.environ.get("IG_USERNAME", "clickbytedev")
    out = []
    for m in _recent_media():
        data = api("GET", f"{m['id']}/comments",
                   fields="id,text,username,timestamp,replies{username}").get("data", [])
        for c in data:
            ts = datetime.strptime(c["timestamp"], "%Y-%m-%dT%H:%M:%S%z")
            if ts < since or c.get("username") == me:
                continue
            replied = any(r.get("username") == me for r in c.get("replies", {}).get("data", []))
            out.append({"id": c["id"], "text": c.get("text", ""), "username": c.get("username"),
                        "media_id": m["id"], "replied": replied})
    return out


def reply(comment_id: str, text: str) -> str:
    # yorum metinleri güvenilmez girdi; id yalnızca rakam olabilir
    if not str(comment_id).isdigit():
        raise IgError(f"geçersiz yorum id: {comment_id!r}")
    from check import _text_rules  # marka kuralları yanıtlara da uygulanır
    problems = _text_rules("yanıt", text)
    if re.search(r"https?://|www\.", text, re.I):
        problems.append("yanıtta link olamaz")
    if not text.strip() or len(text) > 300 or problems:
        raise IgError("yanıt reddedildi: " + ("; ".join(problems) or "boş/uzun"))
    return _id(api("POST", f"{comment_id}/replies", message=text))


def insights(days: int = 31) -> list:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    out = []
    for m in _recent_media(limit=60):
        if datetime.strptime(m["timestamp"], "%Y-%m-%dT%H:%M:%S%z") < since:
            continue
        try:
            vals = api("GET", f"{m['id']}/insights",
                       metric="reach,likes,comments,saved,shares,views").get("data", [])
            m["metrics"] = {v["name"]: v["values"][0]["value"] for v in vals}
        except IgError as e:  # story/eski medya bazı metrikleri desteklemez
            m["metrics"] = {"hata": str(e)}
        out.append(m)
    return out


def _refresh() -> dict:
    return _request("https://graph.instagram.com/refresh_access_token?" + urllib.parse.urlencode(
        {"grant_type": "ig_refresh_token", "access_token": _token()}))


def token_days_left() -> int:
    """Token'ı yeniler (süresini uzatır) ve kalan günü döndürür."""
    return int(_refresh()["expires_in"]) // 86400


def token_check() -> dict:
    """Yeniler; Meta farklı bir token döndürdüyse secret'taki token eskir: token_degisti=True."""
    r = _refresh()
    return {"days_left": int(r["expires_in"]) // 86400, "token_degisti": r.get("access_token", _token()) != _token()}


def _main(argv):
    cmd, rest = argv[0], argv[1:]
    if cmd == "publish":
        kind, cap_file, urls = rest[0], rest[1], rest[2:]
        caption = "" if cap_file == "-" else open(cap_file, encoding="utf-8").read()
        res = {"media_id": publish(kind, urls, caption)}
    elif cmd == "comments":
        res = comments(int(rest[1]) if rest[:1] == ["--hours"] else 24)
    elif cmd == "reply":  # metin dosyadan: shell'e yorum kaynaklı metin geçmesin
        res = {"id": reply(rest[0], open(rest[1], encoding="utf-8").read().strip())}
    elif cmd == "insights":
        res = insights(int(rest[1]) if rest[:1] == ["--days"] else 31)
    elif cmd == "token-check":
        res = token_check()
    else:
        raise SystemExit(__doc__)
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    try:
        _main(sys.argv[1:])
    except IgError as e:
        print(json.dumps({"hata": str(e)}, ensure_ascii=False))
        sys.exit(1)
