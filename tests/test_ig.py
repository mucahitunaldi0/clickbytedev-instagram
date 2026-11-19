import json
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import ig  # noqa: E402


class FakeApi:
    """urlopen taklidi: her çağrıyı kaydeder, sıradaki yanıtı döndürür."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, req, timeout=None):
        url = req.full_url if hasattr(req, "full_url") else req
        method = req.get_method() if hasattr(req, "get_method") else "GET"
        body = req.data.decode() if getattr(req, "data", None) else ""
        q = urlparse(url)
        params = {k: v[0] for k, v in parse_qs(q.query).items()}
        params.update({k: v[0] for k, v in parse_qs(body).items()})
        self.calls.append((method, q.path, params))
        r = self.responses.pop(0)
        status = r.pop("_status", 200) if isinstance(r, dict) else 200
        return FakeResp(r, status)


class FakeResp:
    def __init__(self, data, status=200):
        self.data, self.status = data, status

    def read(self):
        return json.dumps(self.data).encode()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("IG_TOKEN", "t")
    monkeypatch.setenv("IG_USER_ID", "42")
    monkeypatch.setattr(ig.time, "sleep", lambda s: None)


def use(monkeypatch, responses):
    fake = FakeApi(responses)
    monkeypatch.setattr(ig.urllib.request, "urlopen", fake)
    return fake


def test_publish_image_two_calls(monkeypatch):
    f = use(monkeypatch, [{"id": "c1"}, {"status_code": "FINISHED"}, {"id": "999"}])
    assert ig.publish("image", ["https://x/a.png"], "merhaba") == "999"
    assert f.calls[0][1].endswith("/42/media")
    assert f.calls[0][2]["image_url"] == "https://x/a.png"
    assert f.calls[0][2]["caption"] == "merhaba"
    assert f.calls[-1][1].endswith("/42/media_publish")
    assert f.calls[-1][2]["creation_id"] == "c1"


def test_publish_carousel_children(monkeypatch):
    f = use(monkeypatch, [{"id": "a"}, {"id": "b"}, {"id": "c"},
                          {"id": "car"}, {"status_code": "FINISHED"}, {"id": "999"}])
    ig.publish("carousel", ["https://x/1.png", "https://x/2.png", "https://x/3.png"], "cap")
    items = [c for c in f.calls if c[2].get("is_carousel_item") == "true"]
    assert len(items) == 3
    car = [c for c in f.calls if c[2].get("media_type") == "CAROUSEL"][0]
    assert car[2]["children"] == "a,b,c"
    assert car[2]["caption"] == "cap"


def test_publish_reel_polls_until_finished(monkeypatch):
    f = use(monkeypatch, [{"id": "r"}, {"status_code": "IN_PROGRESS"},
                          {"status_code": "IN_PROGRESS"}, {"status_code": "FINISHED"}, {"id": "999"}])
    assert ig.publish("reel", ["https://x/v.mp4"], "c") == "999"
    assert f.calls[0][2]["media_type"] == "REELS"
    assert f.calls[0][2]["video_url"] == "https://x/v.mp4"
    assert sum(1 for c in f.calls if c[1].endswith("/r")) == 3


def test_publish_reel_error_status_raises(monkeypatch):
    f = use(monkeypatch, [{"id": "r"}, {"status_code": "ERROR"}])
    with pytest.raises(ig.IgError):
        ig.publish("reel", ["https://x/v.mp4"], "c")
    assert not any(c[1].endswith("media_publish") for c in f.calls)


def test_publish_story_media_type(monkeypatch):
    f = use(monkeypatch, [{"id": "s"}, {"status_code": "FINISHED"}, {"id": "1"},
                          {"id": "s2"}, {"status_code": "FINISHED"}, {"id": "2"}])
    ig.publish("story", ["https://x/v.mp4"])
    ig.publish("story", ["https://x/a.png"])
    assert f.calls[0][2]["media_type"] == "STORIES" and f.calls[0][2]["video_url"] == "https://x/v.mp4"
    assert f.calls[3][2]["media_type"] == "STORIES" and f.calls[3][2]["image_url"] == "https://x/a.png"


def test_api_error_raises(monkeypatch):
    use(monkeypatch, [{"error": {"message": "Invalid token"}}])
    with pytest.raises(ig.IgError, match="Invalid token"):
        ig.api("GET", "me")


def test_wait_for_url_times_out(monkeypatch):
    def nope(req, timeout=None):
        raise ig.urllib.error.HTTPError(str(req), 404, "nf", None, None)
    monkeypatch.setattr(ig.urllib.request, "urlopen", nope)
    with pytest.raises(ig.IgError):
        ig.wait_for_url("https://x/yok.png", timeout_s=0)


def test_uses_facebook_graph_host():
    # yeni Meta uygulamaları: Unified Login + sistem kullanıcısı token'ı -> graph.facebook.com
    assert ig.BASE.startswith("https://graph.facebook.com/")


def test_reply_rejects_non_numeric_id(monkeypatch):
    f = use(monkeypatch, [])
    with pytest.raises(ig.IgError):
        ig.reply("123/../42/media_publish", "x")
    assert f.calls == []


def test_network_error_wrapped(monkeypatch):
    def boom(req, timeout=None):
        raise ig.urllib.error.URLError("dns")
    monkeypatch.setattr(ig.urllib.request, "urlopen", boom)
    with pytest.raises(ig.IgError):
        ig.api("GET", "me")


def test_missing_id_wrapped(monkeypatch):
    use(monkeypatch, [{"weird": 1}])
    with pytest.raises(ig.IgError):
        ig.publish("image", ["https://x/a.png"], "c")


def test_reply_rejects_links_and_brand_violations(monkeypatch):
    f = use(monkeypatch, [])
    for bad in ["bakın https://evil.example", "www.evil.example", "Harika 🚀🔥", "en iyi yöntem"]:
        with pytest.raises(ig.IgError):
            ig.reply("123", bad)
    assert f.calls == []


def test_token_check_valid(monkeypatch):
    f = use(monkeypatch, [{"id": "42", "username": "clickbytedev0"}])
    assert ig.token_check() == {"gecerli": True, "username": "clickbytedev0"}
    assert f.calls[0][1].endswith("/42") and f.calls[0][2]["fields"] == "username"


def test_token_check_invalid(monkeypatch):
    use(monkeypatch, [{"error": {"message": "Error validating access token"}}])
    with pytest.raises(ig.IgError):
        ig.token_check()


def test_token_in_header_not_url(monkeypatch):
    seen = []
    monkeypatch.setattr(ig.urllib.request, "urlopen", lambda req, timeout=None: seen.append(req) or FakeResp({"id": "1"}))
    ig.api("GET", "42", fields="username")
    assert seen[0].get_header("Authorization") == "Bearer t"
    assert "access_token" not in seen[0].full_url


def test_no_token_env_leaves_auth_to_proxy(monkeypatch):
    monkeypatch.delenv("IG_TOKEN")
    seen = []
    monkeypatch.setattr(ig.urllib.request, "urlopen", lambda req, timeout=None: seen.append(req) or FakeResp({"id": "1"}))
    ig.api("GET", "42", fields="username")
    assert seen[0].get_header("Authorization") is None
