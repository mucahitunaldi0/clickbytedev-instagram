# clickbytedev Instagram Otomasyonu — Uygulama Planı

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bulutta zamanlanmış Claude ajanlarının @clickbytedev hesabı için içerik planlayıp ürettiği, kontrol ettiği ve resmi Graph API ile paylaştığı, tam otomatik bir sistem.

**Architecture:** Herkese açık tek bir GitHub reposu (`clickbytedev-instagram`) hem sistemin hafızası hem de medya sunucusudur (GitHub Pages). Repoda üç küçük Python betiği bulunur: `ig.py` (Graph API), `render.py` (HTML'den PNG/MP4) ve `check.py` (yayın öncesi kontroller). Bunların dışındaki her şeyi (plan, metin, slayt HTML'i, yorum yanıtı) bulut ajanı, repodaki talimat dosyalarına göre üretir. Yerel Claude oturumları geliştirme notlarını `bilgi-bankasi/` klasörüne push ederek bulut ajanını haberdar eder.

**Tech Stack:** Python 3.11 (Graph API çağrıları için standart kütüphanedeki urllib), Playwright (Chromium), ffmpeg, Dart SDK (`dart analyze`), GSAP 3.12.5 (CDN), pytest, GitHub Pages, Claude Code bulut routine'leri.

**Spec:** `docs/2026-11-19-clickbytedev-instagram-design.md`

## Global Constraints

- Paylaşım yalnızca `https://graph.instagram.com/v22.0` üzerinden yapılır. Şifreyle giriş yapan veya resmi olmayan hiçbir kütüphane kullanılmaz.
- Repoda hiçbir zaman token veya gizli bilgi bulunmaz. `IG_TOKEN` ve `IG_USER_ID` yalnızca ortam değişkeni olarak tutulur.
- Bir günde en fazla 25 API paylaşımı yapılır (sistemin hedefi günde en fazla 6: 1 akış gönderisi ve 5 Story).
- Boyutlar: carousel ve görsel 1080×1350 PNG; Story ve Reel 1080×1920; Reel MP4 (H.264 ve AAC, 15-45 sn).
- Renkler: Gece `#07090D`, Kart `#0D1118`, Kâğıt `#E8ECF3`, Sis `#8B94A7`, Camgöbeği `#4FD8E6`, Byte mavisi `#3D7BFF`, çizgi `#232A37`. Gradyan: `linear-gradient(135deg, #FCD02D, #FBB03B 30%, #FF84FF 62%, #8A4CFF)`.
- Fontlar: Bricolage Grotesque 800/700, DM Sans 400/700, JetBrains Mono 400 (Google Fonts).
- Metin kuralları: en fazla 1 emoji, en fazla 1 `!`. Yasak ifadeler: `en iyi`, `mükemmel`, `devrim`, `kullanıcı dostu`, `app`, `Clickbytedev`, `Click Byte Dev`, `CBD`. Marka adı `ClickByteDev`, alan adı `clickbytedev.com`.
- Saat dilimi Europe/Istanbul. Routine cron ifadeleri UTC'dir (İstanbul = UTC+3).
- İçerik dağılımı: yaklaşık %70 ipucu/süreç, %30 uygulama. Haftada 2 Reel, 2 carousel; her gün 3-5 kare Story.

## Review Focus

1. **Medya henüz Pages'te yayında değilken paylaşım denenmesi:** `ig.py` adres 200 dönene kadar bekler (en fazla 10 dk), dönmezse içeriği atlar ve günlüğe yazar. Task 2 testi: `test_wait_for_url_times_out`.
2. **Reel container'ının `ERROR` durumuna düşmesi veya sonsuza kadar `IN_PROGRESS` kalması:** zaman aşımı (10 dk) ve hata günlüğe yazılır; aynı içerik ikinci kez denenmez. Task 2 testi: `test_publish_reel_error_status_raises`.
3. **Aynı içeriğin iki kez paylaşılması** (routine yeniden çalıştığında): `gunluk.jsonl`'de yayınlanmış `id` varsa atlanır. Task 5 testi: `test_already_published_skipped`.
4. **Token'ın 60 günde sona ermesi:** `ig.py token-check` kalan günü yazdırır; 10 günden az kaldıysa günlük routine raporun başına uyarı ekler. Task 2 testi: `test_token_days_left`.
5. **Kod görselinde gizli bilgi:** `check.py`, PNG'ye dönüştürülmeden önce kaynak HTML/MD metnini tarar (AWS/Google anahtarı, `-----BEGIN`, `sk-`, `ghp_`, 32+ karakterlik hex/base64 değerine atama). Task 3 testi: `test_secret_in_slide_html_fails`.

---

### Task 0: Kullanıcının elle yapacağı kurulum (Claude yapamaz)

Hesap açma, şifre girme ve doğrulama adımlarını kullanıcı yapar. Claude her adım için ekran ekran rehberlik eder.

- [ ] Instagram'da @clickbytedev hesabını **Creator** hesabına çevir.
- [ ] developers.facebook.com üzerinde bir uygulama oluştur. "Instagram API with Instagram Login" ürününü ekle; izinler: `instagram_business_basic`, `instagram_business_content_publish`, `instagram_business_manage_comments`, `instagram_business_manage_insights`. Hesabı tester olarak ekle ve uzun ömürlü token üret.
- [ ] GitHub'da **herkese açık** `clickbytedev-instagram` reposunu oluştur ve Pages'i aç (`main` / root).
- [ ] claude.ai/code üzerinde bir bulut ortamı oluştur: repo `clickbytedev-instagram`, gizli değişkenler `IG_TOKEN` ve `IG_USER_ID`, kurulum betiği olarak `scripts/setup-cloud.sh`.
- [ ] Doğrulama: `curl "https://graph.instagram.com/v22.0/me?fields=user_id,username&access_token=$IG_TOKEN"` komutu `clickbytedev` döndürmeli.

### Task 1: Repo iskeleti, marka CSS'i ve kurulum betiği

**Files:**
- Create: `D:\Mücahit Ünaldı\is-modelleri\clickbytedev-instagram\` (yerel klon), `README.md`, `docs/` (spec ve plan buraya taşınır), `sablon/brand.css`, `sablon/ornek-carousel.html`, `sablon/ornek-story.html`, `sablon/ornek-reel.html`, `scripts/setup-cloud.sh`, `requirements.txt` (`playwright==1.48.2`, `pytest==8.3.3`), `gunluk.jsonl` (boş), `bilgi-bankasi/.gitkeep`, `icerik/.gitkeep`, `.nojekyll`

**Interfaces:**
- Produces: `sablon/brand.css` CSS değişkenleri `--gece --kart --kagit --sis --camgobegi --mavi --cizgi --gradyan`, sınıflar `.zemin` (36 px grid, `#ffffff08` çizgi), `.etiket` (mono, camgöbeği, küçük harf), `.baslik`, `.govde`, `.kod` (JetBrains Mono, kart zemin, 12 px köşe). Reel sayfaları `window.REEL_SURE_MS` (sayı) tanımlar ve zaman çizelgesini `window.oynat()` ile başlatır.

- [ ] **Step 1:** Spec'teki marka değerleriyle `brand.css` ve üç örnek şablonu yaz. `ornek-reel.html`, GSAP 3.12.5 (`https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js`) ile 10 sn'lik "kod yazılıyor" animasyonu içerir.
- [ ] **Step 2:** `setup-cloud.sh`: `pip install -r requirements.txt && playwright install --with-deps chromium && apt-get install -y ffmpeg` ve Dart SDK (apt `dart` paketi).
- [ ] **Step 3:** Doğrulama: `bash scripts/setup-cloud.sh && dart --version && ffmpeg -version` hatasız çalışmalı.
- [ ] **Step 4:** Commit: `git commit -m "feat: repo iskeleti ve marka şablonları"`

### Task 2: `ig.py` — Graph API istemcisi

**Files:**
- Create: `scripts/ig.py`, `tests/test_ig.py`

**Interfaces:**
- Consumes: ortam değişkenleri `IG_TOKEN`, `IG_USER_ID`
- Produces (Python ve CLI):
  - `api(method: str, path: str, **params) -> dict`: hata durumunda `IgError(message)` fırlatır.
  - `wait_for_url(url: str, timeout_s: int = 600) -> None`: 200 gelmezse `IgError`.
  - `publish(kind: str, media_urls: list[str], caption: str = "") -> str`: `kind` ∈ `image|carousel|reel|story`; yayınlanan media id'yi döndürür. Container'ın `status_code` değeri `FINISHED` olana kadar 10 sn arayla, en fazla 10 dk yoklanır. `ERROR` gelirse `IgError` fırlatır.
  - `comments(since_hours: int = 24) -> list[dict]`: son 10 gönderinin yorumları (`id`, `text`, `username`, `media_id`, `replied: bool`).
  - `reply(comment_id: str, text: str) -> str`
  - `insights(days: int = 31) -> list[dict]`: gönderi başına `reach`, `likes`, `comments`, `saved`, `shares`, `views`.
  - `token_days_left() -> int`: `debug` ucu veya `refresh_access_token` yanıtındaki `expires_in` değerinden hesaplanır.
  - CLI: `python scripts/ig.py publish <kind> <caption_file> <url>...` / `comments` / `reply <id> <text>` / `insights [--days N]` / `token-check`; çıktı JSON olarak stdout'a yazılır.

- [ ] **Step 1: Failing testler** (`urllib.request.urlopen` monkeypatch ile taklit edilir):
  - `test_publish_image_two_calls`: `/media` (`image_url`, `caption`) çağrısı, ardından `/media_publish` (`creation_id`) çağrısı yapılır; dönen id `"999"` olur.
  - `test_publish_carousel_children`: 3 URL için 3 adet `is_carousel_item=true` çağrısı ve `media_type=CAROUSEL&children=a,b,c` yapılır.
  - `test_publish_reel_polls_until_finished`: `IN_PROGRESS`, `IN_PROGRESS` ve `FINISHED` dönüşlerinin ardından publish çağrılır (`time.sleep` taklit edilir).
  - `test_publish_reel_error_status_raises`: `ERROR` dönerse `IgError` fırlatılır ve publish çağrılmaz.
  - `test_publish_story_media_type`: `.mp4` için `media_type=STORIES&video_url=...`, `.png` için `image_url` kullanılır.
  - `test_wait_for_url_times_out`: her zaman 404 dönen adres, `timeout_s=0` ile `IgError` fırlatır.
  - `test_token_days_left`: `expires_in=864000` ise sonuç `10` olur.
- [ ] **Step 2:** `pytest tests/test_ig.py -v` → FAIL
- [ ] **Step 3:** `ig.py`'yi standart kütüphaneyle yaz (urllib, json, time, os).
- [ ] **Step 4:** `pytest tests/test_ig.py -v` → PASS
- [ ] **Step 5:** Gerçek doğrulama (Task 0 tamamlandıysa): `python scripts/ig.py token-check` bir gün sayısı yazdırmalı.
- [ ] **Step 6:** Commit.

### Task 3: `check.py` — yayın öncesi kontroller

**Files:**
- Create: `scripts/check.py`, `tests/test_check.py`

**Interfaces:**
- Consumes: Task 5'teki içerik klasörü biçimi (`icerik/<id>/post.json`, `*.html`, `*.dart`, render edilmiş `out/*.png|mp4`)
- Produces: `check(content_dir: str) -> list[str]` (boş liste = geçti); CLI `python scripts/check.py <dir>` çıkış kodu 0/1, sorunlar stdout'a yazılır.

Kontroller: gizli bilgi kalıpları (Review Focus 5), metin kuralları (Global Constraints) `post.json` içindeki `caption` ve tüm `*.html` görünür metninde uygulanır, `*.dart` dosyaları için `dart analyze` (dart yoksa hata verir, sessizce geçmez), PNG boyutları (IHDR başlığından), MP4 için `ffprobe` ile boyut, süre (15-45 sn) ve codec kontrolü.

- [ ] **Step 1: Failing testler:**
  - `test_clean_post_passes`: kurallara uyan carousel → `[]`
  - `test_secret_in_slide_html_fails`: `api_key = "AIzaSy..."` içeren slayt → içinde `gizli` geçen bir sorun
  - `test_two_emojis_fails`, `test_two_exclamations_fails`, `test_banned_word_fails` (`"en iyi"`), `test_brand_spelling_fails` (`"Clickbytedev"`)
  - `test_wrong_png_size_fails`: 1080×1080 PNG → boyut sorunu
  - `test_reel_too_long_fails`: 50 sn'lik MP4 (testte ffmpeg ile üretilir) → süre sorunu
  - `test_dart_error_fails`: `void main() { int x = "a"; }` → dart sorunu
- [ ] **Step 2:** FAIL doğrula. **Step 3:** Yaz. **Step 4:** `pytest tests/test_check.py -v` → PASS. **Step 5:** Commit.

### Task 4: `render.py` — HTML'den PNG ve MP4'e

**Files:**
- Create: `scripts/render.py`, `tests/test_render.py`, `muzik/` (2-3 adet CC0 lisanslı parça ve lisans notu, `muzik/LISANS.md`)

**Interfaces:**
- Produces: `render(content_dir: str) -> list[str]`: `post.json` dosyasındaki `kind` değerine göre `slide-*.html` dosyalarını 1080×1350 (`story-*.html` için 1080×1920) PNG olarak `out/` klasörüne yazar. `reel.html` dosyasını 1080×1920 boyutunda Playwright `record_video` ile `REEL_SURE_MS` süresince kaydeder, ffmpeg ile H.264'e çevirir ve `post.json` içindeki `muzik` dosyasını AAC olarak ekler (`-shortest`, bitişte 1 sn fade). Çıktı yollarını sıralı döndürür. CLI: `python scripts/render.py <dir>`.

- [ ] **Step 1: Failing testler:** `test_render_carousel_pngs` (2 slayt → 2 adet 1080×1350 PNG), `test_render_story_size` (1080×1920), `test_render_reel_mp4` (5 sn'lik örnek reel → MP4, ffprobe ile 1080×1920, h264 ve aac, süre 4.5-6 sn).
- [ ] **Step 2:** FAIL. **Step 3:** Yaz. Fontların yüklenmesini beklemek için `document.fonts.ready` kullan. **Step 4:** PASS. **Step 5:** `sablon/ornek-*` için render çalıştır, çıktıları göz ile kontrol et. **Step 6:** Commit.

### Task 5: İçerik biçimi ve yayın akışı `run.py`

**Files:**
- Create: `scripts/run.py`, `tests/test_run.py`

**Interfaces:**
- Consumes: `ig.publish`, `ig.wait_for_url`, `check.check`
- Produces: `icerik/<id>/post.json` şeması: `{"id": "2026-11-24-flutter-const", "kind": "reel|carousel|image|story", "yayin": "2026-11-24T19:00:00+03:00", "caption": "...", "medya": ["out/slide-1.png", ...], "muzik": "muzik/x.mp3"|null, "sutun": "ipucu|surec|uygulama", "uygulama": "Snapburn"|null}`. `gunluk.jsonl` satırı: `{"id", "zaman", "durum": "yayinlandi|atlandi|hata", "media_id"|null, "neden"|null}`.
  - `due(now: datetime) -> list[str]`: yayın zamanı gelmiş ve günlükte `yayinlandi` olarak geçmeyen içerik id'leri.
  - `publish_due(now, pages_base: str) -> list[dict]`: her içerik için önce `check`, sonra `wait_for_url`, sonra `publish` çalıştırılır ve günlüğe yazılır. Hata olsa bile diğer içerikler denenir.
  - CLI: `python scripts/run.py publish-due` (Pages adresi `PAGES_BASE` ortam değişkeninden okunur).

- [ ] **Step 1: Failing testler:** `test_due_only_past_items`, `test_already_published_skipped`, `test_check_failure_logs_atlandi_and_skips_publish`, `test_publish_error_logs_hata_and_continues`.
- [ ] **Step 2:** FAIL. **Step 3:** Yaz. **Step 4:** `pytest -v` (tüm testler) → PASS. **Step 5:** Commit.

### Task 6: Ajan talimatları (routine prompt'ları)

**Files:**
- Create: `ajan/AYLIK.md`, `ajan/GUNLUK.md`, `ajan/MARKA.md`, `ajan/SUTUNLAR.md`

**Interfaces:**
- Consumes: Task 2-5 CLI'ları, `bilgi-bankasi/*.md`, `gunluk.jsonl`
- Produces: Bulut routine'lerinin okuyacağı talimatlar.

- [ ] **Step 1:** `MARKA.md`: spec'teki renk, font, ses tonu ve yazım kuralları; iyi ve kötü caption örneği.
- [ ] **Step 2:** `SUTUNLAR.md`: 5 içerik sütunu, uygulama listesi ve linkleri (`clickbytedev.com/uygulamalar/<slug>`), %70/%30 kuralı, hook formülü için `ig-reel` skill'ine atıf.
- [ ] **Step 3:** `AYLIK.md` (her ayın 1'i): `ig.py insights --days 31` ile geçen ayın kısa analizi yapılır ve `raporlar/YYYY-MM.md` dosyasına yazılır (`ig-audit` yaklaşımı: en iyi ve en kötü 3 gönderi, hangi sütun ve hook işe yaradı). Konular son 31 günün `bilgi-bankasi/` notlarından seçilir, yetmezse SUTUNLAR'dan. Ayın takvimi `takvim/YYYY-MM.md` dosyasına tablo olarak yazılır: haftada 2 Reel, 2 carousel ve her gün 3-5 kare Story (yayın saatleri: Reel Salı/Cuma 19:00, carousel Pazartesi/Perşembe 12:00, Story her gün 10:00). İçerikler hafta hafta `icerik/` klasörüne üretilir; her içerik için `render.py` → `check.py` çalışır. Kontrolden geçemeyen içerik bir kez düzeltilir, yine geçemezse yerine yedek konu üretilir ve rapora yazılır. Her hafta ayrı commit ve push edilir; böylece uzun çalışma yarıda kesilirse yapılan iş kaybolmaz. Önceki ayların yayınlanmış medyası (`icerik/*/out/`) silinir, `post.json` ve günlük kalır.
- [ ] **Step 4:** `GUNLUK.md` (her gün): `git pull` → `takvim/YYYY-MM.md` dosyasında olup `icerik/` klasöründe bulunmayan içerik varsa (aylık çalışma yarıda kaldıysa) önce üretilir, render ve check'ten geçer → `run.py publish-due` → `ig.py comments` → yanıt hak eden yorumlara `ig-reply` üslubu ve MARKA kurallarıyla `ig.py reply`. Spam ve hakaret içeren yorumlar yanıtlanmaz. Ardından `ig.py token-check`; 10 günden az kaldıysa `raporlar/UYARI.md` yazılır. Son olarak commit ve push.
- [ ] **Step 5:** Doğrulama: bulut ortamında `AYLIK.md` bir kez elle çalıştırılır. Takvim, render, kontrol ve push hatasız tamamlanmalı ve Pages adresleri 200 dönmeli.
- [ ] **Step 6:** Commit.

### Task 7: Bulut routine'leri

- [ ] **Step 1:** `schedule` skill'i ile iki routine oluştur. **aylik**: cron `0 6 1 * *` (her ayın 1'i, İstanbul saatiyle 09:00), prompt `ajan/AYLIK.md`'yi okuyup uygulamak. **gunluk**: cron `0 6,7,9,11,16,18 * * *` (İstanbul saatiyle 09, 10, 12, 14, 19 ve 21), prompt `ajan/GUNLUK.md`. Yorum turu yalnızca İstanbul saatiyle 09, 14 ve 21 çalışmalarında yapılır. Günde 6 çalışma, maliyeti düşük tutar.
- [ ] **Step 2:** Doğrulama: `gunluk` routine'ini elle tetikle. Yayın zamanı gelmiş test içeriği (`kind=story`) Instagram'da görünmeli ve `gunluk.jsonl`'e `yayinlandi` olarak yazılmalı.

### Task 8: Yerel bilgi bankası köprüsü

**Files:**
- Modify: `C:\Users\mucah\.claude\CLAUDE.md` (**kullanıcı onayıyla**, kalıcı ayar)
- Create: `bilgi-bankasi/SABLON.md`

- [ ] **Step 1:** `SABLON.md`: ön bilgi alanları `tarih`, `uygulama`, `konu`, `etiketler`; gövde: "ne yaptık, hangi sorunu nasıl çözdük" (3-6 cümle) ve en fazla 30 satırlık temizlenmiş kod parçası.
- [ ] **Step 2:** Global CLAUDE.md'ye kural ekle: "`D:\Mücahit Ünaldı\is-modelleri\google-play-console` altındaki bir projede anlamlı bir özellik veya düzeltme bittiğinde, `D:\Mücahit Ünaldı\is-modelleri\clickbytedev-instagram\bilgi-bankasi\` klasörüne SABLON'a uygun bir not yaz; `python scripts/check.py` gizli bilgi taramasından geçir; commit ve push yap."
- [ ] **Step 3:** Doğrulama: mevcut projelerden (Snapburn, Movyra, Otonot, Pixel POP) 4 başlangıç notu üret, check'ten geçir ve push et. İlk `aylik` çalışması (elle tetiklenir) bu notlardan konu seçmeli.

### Task 9: Profil hazırlığı

API ile bio ve profil fotoğrafı değiştirilemez; Claude dosyaları hazırlar, kullanıcı telefondan yükler.

- [ ] **Step 1:** Profil fotoğrafı: Gece zemin üzerinde işaret, alanın %62'si, 1080×1080 PNG (`render.py` ile).
- [ ] **Step 2:** `ig-profile` skill'i ile isim alanı, bio (ses tonu kurallarına uygun) ve link (`clickbytedev.com`) metinleri `profil/PROFIL.md` dosyasına yazılır.
- [ ] **Step 3:** İlk 3 sabitlenecek gönderi (tanıtım carousel'i, uygulama vitrini, en güçlü ipucu Reel'i) ilk aylık çalışmada üretilir.
