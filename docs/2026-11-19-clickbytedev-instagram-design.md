# clickbytedev Instagram Otomasyonu — Tasarım

## Amaç
@clickbytedev hesabını Claude'un uçtan uca yönettiği, Türkçe bir yazılımcı hesabına dönüştürmek. Takipçi kod ipuçları ve geliştirme süreci için gelir (%70), bu içerikler içinden stüdyonun Google Play uygulamalarını keşfeder (%30).

## Hedefler
- İçerik planı, görsel, Reels ve Story üretimi ile paylaşımı Claude yapar.
- Paylaşım yalnızca resmi Instagram Graph API üzerinden yapılır.
- Her ayın 1'inde geçen ayın istatistikleri okunur ve yeni ayın tamamı planlanıp üretilir.
- Uygulama tanıtımı çoğunlukla gerçek geliştirme hikâyelerinin içine gömülür ("SnapBurn'de bunu böyle çözdük").

## Hedef dışı
- Otomatik takip/takipten çıkma, toplu beğeni, toplu DM, takipçi satın alma.
- Yüz/ses içeren video, AI sunucu (B seçeneği; ileride ara sıra görsel için Higgsfield kullanılabilir).
- İngilizce içerik.

## Anti-hedefler (çalışsa bile başarısızlık sayılır)
- Hesabın kısıtlanması/kapanması (şifreyle giriş yapan, resmi olmayan araçlar yasak).
- Kod görsellerinde API anahtarı, token, keystore, müşteri verisi gibi gizli bilgi sızması.
- "AI içerik" gibi görünen, jenerik, yanlış veya çalışmayan kod.
- Başkasının içeriğini yeniden paylaşmak.

## Kısıtlar
- Hesap Creator/Business olmalı ve bir Meta uygulamasına bağlanmalı. Meta hesabı/uygulama oluşturma, şifre ve doğrulama adımlarını kullanıcı yapar.
- Graph API: 24 saatte en fazla 25 API paylaşımı. Medya, herkese açık HTTPS adresinde olmalı.
- API ile Story paylaşılabilir ama anket, soru, link gibi etiketler (sticker) eklenemez. Etiketli Story gerekiyorsa kullanıcı telefondan elle ekler.
- Müzik kütüphanesi API'de yok. Reels'te telifsiz müzik videonun içine gömülür.

## Yaklaşımlar
- **A) Yüzsüz, kod tabanlı (SEÇİLDİ):** HTML şablonundan PNG üretilen carousel ve Story'ler, HTML+GSAP ile hazırlanıp MP4'e dönüştürülen kod animasyonlu Reels. Konular gerçek repolardan çıkar. Tam otomatik, neredeyse bedava. Reels'in viral olma tavanı daha düşük.
- B) Higgsfield AI sunucu videosu: daha "insan" Reels; kredi maliyeti ve AI algısı riski var. Reddedildi, ara sıra görsel için kullanılabilir.
- C) Hibrit (kullanıcı çeker, Claude kurgular): en güçlü büyüme, ama tam otomatik değil. Reddedildi.

## Seçilen tasarım

### İçerik karışımı (Claude'un önerisi)
- Haftada 4 akış gönderisi: 2 Reels ve 2 carousel.
- Her gün 3-5 kare Story: haftanın içeriğine yönlendirme, "bugün ne kodladık", mini quiz (etiketsiz; cevap sonraki karede).
- Dağılım: yaklaşık %70 ipucu/süreç, %30 uygulama odaklı. Her uygulama gönderisi yine öğretici bir açıdan anlatılır.
- İçerik sütunları: Flutter/Dart ipuçları, Play Store yayın süreci/ASO, hata ayıklama hikâyeleri, "uygulamamı böyle yaptım", araç ve verimlilik.

### Kaynaklar
- Kullanıcının yerel proje klasörleri (snapburn, movyra, otonot, pixel-pop, Kelime Mıknatısı, CRM, çağrı kaydetme). Yalnızca okunur. Kod parçaları paylaşmadan önce gizli bilgi taramasından geçer.
- Uygulamaların Play Store bağlantıları (bio linki ve caption).

### Üretim hattı
1. **Plan:** `ig-plan` ile aylık takvim, konu başına `ig-reel` / `ig-carousel` / `ig-story`, metin için `ig-caption` ve `ig-human`.
2. **Görsel:** HTML/CSS marka şablonları → headless Chrome ile PNG (1080×1350 carousel, 1080×1920 Story).
3. **Reels:** HTML+GSAP kod animasyonu (`bang-motion` skill) → MP4 (1080×1920, 15-45 sn), gömülü telifsiz müzik.
4. **Barındırma:** Medya herkese açık bir HTTPS adresine yüklenir (en sade seçenek: herkese açık bir GitHub reposu ve raw/Pages adresi).
5. **Paylaşım:** Instagram MCP sunucusu (resmi Graph API) ile reel, carousel ve story yayını.
6. **Etkileşim:** Kendi gönderilerindeki yorumlara `ig-reply` ile yanıt.
7. **Ölçüm:** Aylık insights → `ig-audit` → bir sonraki ayın planı.

### Zamanlama
Claude zamanlanmış görevleri: aylık plan, üretim ve rapor (her ayın 1'i, 09:00); günlük paylaşım ve yorum turu.

### Marka (kaynak: clickbytedev.com/kurumsal/kurumsalkimlik)
- Renkler: Gece `#07090D` (zemin, yaklaşık %70), Kart `#0D1118` (yaklaşık %15), Kâğıt `#E8ECF3` (metin), Sis `#8B94A7` (ikincil metin), Camgöbeği `#4FD8E6` (etiketler), Byte mavisi `#3D7BFF` (vurgu, yaklaşık %10), çizgiler `#232A37`. İşaret gradyanı: `#FCD02D → #FBB03B → #FF84FF → #8A4CFF`. İşaret renkleri az kullanılır ve üzerlerine küçük yazı konmaz.
- Fontlar: başlık Bricolage Grotesque 800 (harf aralığı -1 ile -3%), gövde DM Sans 400/700, kod ve etiketler JetBrains Mono.
- Görsel dil: 36 px grid çizgili koyu zemin (beyaz, %3 opaklık), kod yorumu gibi küçük harfli etiketler (`// flutter ipucu`), kartlarda 12 px köşe, gölge yok, 1 px çizgi.
- Logo: "clickbytedev" yazımı, "byte" her zaman mavi, büyük harfe çevrilmez, gölge eklenmez. Profil fotoğrafı: Gece zemin üzerinde işaret, alanın yaklaşık %62'sini kaplar.
- Ses tonu: "işini bilen, lafı uzatmayan geliştirici arkadaş". Şirket için "biz", okuyucu için "siz". Kısa cümleler, önce sonuç, somut iddialar ("3 dokunuşta"). En fazla 1 emoji ve 1 ünlem. Kullanılmayacak kelimeler: "en iyi", "mükemmel", "app", "kullanıcı dostu".
- Yazım: "ClickByteDev", ekler "ClickByteDev'in", alan adı "clickbytedev.com".
- Uygulamalar (site): Movyra, Matematik Heyecanı, Otonot, Pixel POP, Snapburn, CepİK, Kelime Ustası.

## Kararlar
- **Onay modu: baştan tam otomatik** (kullanıcının kararı). İnsan kontrolü olmadığı için her gönderi yayından önce otomatik kontrollerden geçer: gizli bilgi taraması, gönderide geçen kod parçasının derlenmesi/analizi (`dart analyze`), `ig-human` metin kontrolü, marka kuralları kontrolü (yasak kelimeler, emoji ve ünlem sayısı), görsel boyutları. Kontrolden geçemeyen gönderi atlanır, yedek içerik paylaşılır ve aylık raporda bildirilir.
- **Çalışma yeri: bulut** (kullanıcının kararı: bilgisayar kapalıyken de çalışmalı). Zamanlanmış bulut ajanları (Claude Code routines) bir GitHub reposu üzerinde çalışır.
- **Tek repo: `clickbytedev-instagram`** (herkese açık; içinde hiç gizli bilgi bulunmaz). Repoda tasarım, marka şablonları, içerik takvimi, paylaşım günlüğü, render edilen medya ve bilgi bankası yer alır. Medya raw/Pages adresinden Graph API'ye verilir. Instagram token'ı repoda değil, bulut ortamının gizli değişkeninde tutulur.
- **"Burada yapılanlardan haberi olsun":** Uygulama projelerinin çoğu GitHub'da değil (yalnızca pixel-pop orada), bu yüzden bulut ajanı onları doğrudan okuyamaz. Çözüm `bilgi-bankasi/` klasörü: yerelde bir uygulama üzerinde çalışma bittiğinde, o oturum kısa bir geliştirme notu ve temizlenmiş kod parçası yazıp repoya push eder. Bunun için kullanıcının global CLAUDE.md dosyasına bir kural eklenir (kullanıcı onayıyla). Bulut ajanı her çalıştığında içerik konularını önce bu klasörden seçer. Uygulama kaynak kodunun tamamı bilgisayardan çıkmaz.

## Kurucuya bırakılanlar
- Hangi Instagram MCP sunucusunun kullanılacağı (bakım durumu ve gereken araçlar karşılaştırılarak).
- Şablon detayları, animasyon stili, dosya ve klasör düzeni.
- Gizli bilgi tarama yöntemi.
