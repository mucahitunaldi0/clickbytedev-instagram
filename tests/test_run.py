import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run  # noqa: E402

NOW = datetime(2026, 12, 1, 12, 5, tzinfo=timezone.utc)


def mk(root: Path, id_, yayin, kind="carousel", medya=("out/slide-1.png", "out/slide-2.png")):
    d = root / "icerik" / id_
    d.mkdir(parents=True)
    (d / "post.json").write_text(json.dumps({"id": id_, "kind": kind, "yayin": yayin, "caption": "c",
                                             "medya": list(medya)}), encoding="utf-8")


def log(root):
    p = root / "gunluk.jsonl"
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines()] if p.exists() else []


def test_due_only_past_items(tmp_path):
    mk(tmp_path, "gecmis", "2026-12-01T14:00:00+03:00")   # 11:00 UTC
    mk(tmp_path, "gelecek", "2026-12-01T19:00:00+03:00")  # 16:00 UTC
    assert run.due(NOW, root=tmp_path) == ["gecmis"]


def test_already_published_skipped(tmp_path):
    mk(tmp_path, "a", "2026-12-01T14:00:00+03:00")
    (tmp_path / "gunluk.jsonl").write_text(json.dumps({"id": "a", "durum": "yayinlandi"}) + "\n", encoding="utf-8")
    assert run.due(NOW, root=tmp_path) == []


def test_failed_not_retried(tmp_path):
    mk(tmp_path, "a", "2026-12-01T14:00:00+03:00")
    (tmp_path / "gunluk.jsonl").write_text(json.dumps({"id": "a", "durum": "hata"}) + "\n", encoding="utf-8")
    assert run.due(NOW, root=tmp_path) == []


def test_publish_calls_with_pages_urls(tmp_path, monkeypatch):
    mk(tmp_path, "a", "2026-12-01T14:00:00+03:00")
    calls = []
    monkeypatch.setattr(run, "check", lambda d: [])
    monkeypatch.setattr(run.ig, "wait_for_url", lambda u, timeout_s=600: None)
    monkeypatch.setattr(run.ig, "publish", lambda k, urls, cap="": calls.append((k, urls, cap)) or "m1")
    res = run.publish_due(NOW, "https://u.github.io/repo", root=tmp_path)
    assert calls == [("carousel", ["https://u.github.io/repo/icerik/a/out/slide-1.png",
                                   "https://u.github.io/repo/icerik/a/out/slide-2.png"], "c")]
    assert res[0]["durum"] == "yayinlandi" and log(tmp_path)[-1]["media_id"] == "m1"


def test_story_frames_published_one_by_one(tmp_path, monkeypatch):
    mk(tmp_path, "s", "2026-12-01T14:00:00+03:00", kind="story", medya=("out/story-1.png", "out/story-2.png"))
    calls = []
    monkeypatch.setattr(run, "check", lambda d: [])
    monkeypatch.setattr(run.ig, "wait_for_url", lambda u, timeout_s=600: None)
    monkeypatch.setattr(run.ig, "publish", lambda k, urls, cap="": calls.append(urls) or "m")
    run.publish_due(NOW, "https://b", root=tmp_path)
    assert calls == [["https://b/icerik/s/out/story-1.png"], ["https://b/icerik/s/out/story-2.png"]]


def test_check_failure_logs_atlandi_and_skips_publish(tmp_path, monkeypatch):
    mk(tmp_path, "a", "2026-12-01T14:00:00+03:00")
    monkeypatch.setattr(run, "check", lambda d: ["gizli bilgi"])
    monkeypatch.setattr(run.ig, "publish", lambda *a: (_ for _ in ()).throw(AssertionError("çağrılmamalı")))
    run.publish_due(NOW, "https://b", root=tmp_path)
    assert log(tmp_path)[0]["durum"] == "atlandi" and "gizli" in log(tmp_path)[0]["neden"]


def test_publish_error_logs_hata_and_continues(tmp_path, monkeypatch):
    mk(tmp_path, "a", "2026-12-01T13:00:00+03:00")
    mk(tmp_path, "b", "2026-12-01T14:00:00+03:00")
    monkeypatch.setattr(run, "check", lambda d: [])
    monkeypatch.setattr(run.ig, "wait_for_url", lambda u, timeout_s=600: None)

    def pub(k, urls, cap=""):
        if "/a/" in urls[0]:
            raise run.ig.IgError("patladı")
        return "m2"
    monkeypatch.setattr(run.ig, "publish", pub)
    run.publish_due(NOW, "https://b", root=tmp_path)
    assert [(e["id"], e["durum"]) for e in log(tmp_path) if e["durum"] != "basladi"] == [("a", "hata"), ("b", "yayinlandi")]


# --- son inceleme bulguları ---

def _fakes(monkeypatch, publish=None):
    monkeypatch.setattr(run, "check", lambda d: [])
    monkeypatch.setattr(run.ig, "wait_for_url", lambda u, timeout_s=600: None)
    monkeypatch.setattr(run.ig, "publish", publish or (lambda k, urls, cap="": "m"))


def test_wait_timeout_not_logged_retried_next_run(tmp_path, monkeypatch):
    mk(tmp_path, "a", "2026-12-01T14:00:00+03:00")
    _fakes(monkeypatch)
    def late(u, timeout_s=600):
        raise run.ig.IgError("medya erişilemiyor")
    monkeypatch.setattr(run.ig, "wait_for_url", late)
    res = run.publish_due(NOW, "https://b", root=tmp_path)
    assert res[0]["durum"] == "bekliyor"
    assert log(tmp_path) == [] and run.due(NOW, root=tmp_path) == ["a"]


def test_stale_item_logged_gecikti(tmp_path, monkeypatch):
    mk(tmp_path, "eski", "2026-11-30T19:00:00+03:00")  # ~20 saat önce
    _fakes(monkeypatch, publish=lambda *a: (_ for _ in ()).throw(AssertionError("çağrılmamalı")))
    run.publish_due(NOW, "https://b", root=tmp_path)
    assert log(tmp_path)[0]["durum"] == "gecikti"


def test_claim_written_before_publish(tmp_path, monkeypatch):
    mk(tmp_path, "a", "2026-12-01T14:00:00+03:00")
    seen = []
    _fakes(monkeypatch, publish=lambda k, urls, cap="": seen.append([e["durum"] for e in log(tmp_path)]) or "m")
    run.publish_due(NOW, "https://b", root=tmp_path)
    assert seen == [["basladi"]]
    assert [e["durum"] for e in log(tmp_path)] == ["basladi", "yayinlandi"]


def test_lost_claim_skips_publish(tmp_path, monkeypatch):
    mk(tmp_path, "a", "2026-12-01T14:00:00+03:00")
    _fakes(monkeypatch, publish=lambda *a: (_ for _ in ()).throw(AssertionError("çağrılmamalı")))

    def other_run_won(root, msg):  # pull sırasında başka koşunun daha erken kilidi geldi
        with open(root / "gunluk.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": "a", "zaman": "2026-12-01T11:00:00+00:00", "durum": "basladi", "kosu": "baska"}) + "\n")
        return True
    monkeypatch.setattr(run, "_sync", other_run_won)
    res = run.publish_due(NOW, "https://b", root=tmp_path)
    assert res[0]["durum"] == "kilit-yok"


def test_unexpected_exception_logged_hata(tmp_path, monkeypatch):
    mk(tmp_path, "a", "2026-12-01T14:00:00+03:00")
    _fakes(monkeypatch, publish=lambda *a: (_ for _ in ()).throw(TimeoutError("okuma zaman aşımı")))
    run.publish_due(NOW, "https://b", root=tmp_path)
    assert [e["durum"] for e in log(tmp_path)] == ["basladi", "hata"]
    assert run.due(NOW, root=tmp_path) == []


def test_story_partial_failure_keeps_published_ids(tmp_path, monkeypatch):
    mk(tmp_path, "s", "2026-12-01T14:00:00+03:00", kind="story", medya=("out/story-1.png", "out/story-2.png"))
    def pub(k, urls, cap=""):
        if urls[0].endswith("story-2.png"):
            raise run.ig.IgError("x")
        return "m1"
    _fakes(monkeypatch, publish=pub)
    run.publish_due(NOW, "https://b", root=tmp_path)
    assert log(tmp_path)[-1]["durum"] == "hata" and log(tmp_path)[-1]["media_id"] == "m1"


def test_publish_due_follows_yayin_order_not_folder_name(tmp_path, monkeypatch):
    mk(tmp_path, "a-ilk-klasor", "2026-12-01T14:02:00+03:00", kind="image", medya=("out/g.jpg",))
    mk(tmp_path, "z-son-klasor", "2026-12-01T14:01:00+03:00", kind="image", medya=("out/g.jpg",))
    order = []
    monkeypatch.setattr(run, "check", lambda d: [])
    monkeypatch.setattr(run.ig, "wait_for_url", lambda u, timeout_s=600: None)
    monkeypatch.setattr(run.ig, "publish", lambda k, urls, cap="": order.append(urls[0]) or "m")
    run.publish_due(NOW, "https://b", root=tmp_path)
    assert [u.split("/")[-3] for u in order] == ["z-son-klasor", "a-ilk-klasor"]
