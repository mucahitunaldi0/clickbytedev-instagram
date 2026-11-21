# clickbytedev-instagram

@clickbytedev0 Instagram hesabının paylaşım otomasyonu. Görselleri hesap sahibi verir; planlama, caption ve paylaşım buradan yürür.

- `ajan/` — talimatlar: `AYLIK.md` (rapor + takvim önerisi, görsel gelince gönderi hazırlama), `GUNLUK.md` (paylaşım, yorum yanıtı, token kontrolü), `MARKA.md`, `SUTUNLAR.md`
- `icerik/<id>/` — `post.json` + görseller; `scripts/check.py` yayın öncesi kontrol
- `scripts/run.py publish-due` — zamanı gelen gönderiyi paylaşır, `gunluk.jsonl`'e yazar
- `scripts/ig.py` — Instagram Graph API (paylaşım, yorumlar, istatistik, token kontrolü)
- `takvim/`, `raporlar/`, `bilgi-bankasi/`, `profil/`

Bulut rutinleri (aylık, günlük) şu an **kapalı**; claude.ai/code/routines üzerinden açılır.

Gizli bilgi (token) bu repoya asla girmez: bulutta `graph.facebook.com` ağ gizli anahtarıdır (ajan görmez); yerelde `IG_TOKEN` ortam değişkeni.
