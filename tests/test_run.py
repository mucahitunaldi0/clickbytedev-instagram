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
    mk(tmp_path, "a", "2026-12-01T10:00:00+03:00")
    (tmp_path / "gunluk.jsonl").write_text(json.dumps({"id": "a", "durum": "yayinlandi"}) + "\n", encoding="utf-8")
    assert run.due(NOW, root=tmp_path) == []


def test_failed_not_retried(tmp_path):
    mk(tmp_path, "a", "2026-12-01T10:00:00+03:00")
    (tmp_path / "gunluk.jsonl").write_text(json.dumps({"id": "a", "durum": "hata"}) + "\n", encoding="utf-8")
    assert run.due(NOW, root=tmp_path) == []


def test_publish_calls_with_pages_urls(tmp_path, monkeypatch):
    mk(tmp_path, "a", "2026-12-01T10:00:00+03:00")
    calls = []
    monkeypatch.setattr(run, "check", lambda d: [])
    monkeypatch.setattr(run.ig, "wait_for_url", lambda u, timeout_s=600: None)
    monkeypatch.setattr(run.ig, "publish", lambda k, urls, cap="": calls.append((k, urls, cap)) or "m1")
    res = run.publish_due(NOW, "https://u.github.io/repo", root=tmp_path)
    assert calls == [("carousel", ["https://u.github.io/repo/icerik/a/out/slide-1.png",
                                   "https://u.github.io/repo/icerik/a/out/slide-2.png"], "c")]
    assert res[0]["durum"] == "yayinlandi" and log(tmp_path)[0]["media_id"] == "m1"


def test_story_frames_published_one_by_one(tmp_path, monkeypatch):
    mk(tmp_path, "s", "2026-12-01T10:00:00+03:00", kind="story", medya=("out/story-1.png", "out/story-2.png"))
    calls = []
    monkeypatch.setattr(run, "check", lambda d: [])
    monkeypatch.setattr(run.ig, "wait_for_url", lambda u, timeout_s=600: None)
    monkeypatch.setattr(run.ig, "publish", lambda k, urls, cap="": calls.append(urls) or "m")
    run.publish_due(NOW, "https://b", root=tmp_path)
    assert calls == [["https://b/icerik/s/out/story-1.png"], ["https://b/icerik/s/out/story-2.png"]]


def test_check_failure_logs_atlandi_and_skips_publish(tmp_path, monkeypatch):
    mk(tmp_path, "a", "2026-12-01T10:00:00+03:00")
    monkeypatch.setattr(run, "check", lambda d: ["gizli bilgi"])
    monkeypatch.setattr(run.ig, "publish", lambda *a: (_ for _ in ()).throw(AssertionError("çağrılmamalı")))
    run.publish_due(NOW, "https://b", root=tmp_path)
    assert log(tmp_path)[0]["durum"] == "atlandi" and "gizli" in log(tmp_path)[0]["neden"]


def test_publish_error_logs_hata_and_continues(tmp_path, monkeypatch):
    mk(tmp_path, "a", "2026-12-01T09:00:00+03:00")
    mk(tmp_path, "b", "2026-12-01T10:00:00+03:00")
    monkeypatch.setattr(run, "check", lambda d: [])
    monkeypatch.setattr(run.ig, "wait_for_url", lambda u, timeout_s=600: None)

    def pub(k, urls, cap=""):
        if "/a/" in urls[0]:
            raise run.ig.IgError("patladı")
        return "m2"
    monkeypatch.setattr(run.ig, "publish", pub)
    run.publish_due(NOW, "https://b", root=tmp_path)
    assert [(e["id"], e["durum"]) for e in log(tmp_path)] == [("a", "hata"), ("b", "yayinlandi")]
