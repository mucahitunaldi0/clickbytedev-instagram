# Marka kuralları (kaynak: clickbytedev.com/kurumsal/kurumsalkimlik)

Görselleri hesap sahibi hazırlar; aşağıdaki görsel kuralları onun içindir, ajan caption ve planlamada uyar.

## Görsel
- Zemin Gece `#07090D` (alanın ~%70'i), kart `#0D1118` (~%15), vurgu Byte mavisi `#3D7BFF` (~%10).
- Metin Kâğıt `#E8ECF3`, ikincil Sis `#8B94A7`, etiket Camgöbeği `#4FD8E6`, çizgi `#232A37`.
- İşaret gradyanı (`--gradyan`) yalnızca küçük vurgu; üstüne küçük yazı koyma.
- Başlık Bricolage Grotesque 800 (`.baslik`), gövde DM Sans (`.govde`), kod/etiket JetBrains Mono (`.kod`, `.etiket`).
- Etiketler kod yorumu gibi, küçük harf: `// flutter ipucu`, `// play store`, `// bugün ne kodladık`.
- Gölge yok. Kart 12 px köşe, 1 px çizgi. Öne çıkan kart: `.kart.one-cikan`.
- Logo metni: `<span class="logo">click<b>byte</b>dev</span>` — büyük harf yok, "byte" daima mavi.
- Bir slaytta tek fikir. Başlık en fazla ~8 kelime. Kod en fazla 12 satır, 40 karakter genişlik.
- Kod blokları `<pre class="kod">` içinde; `.k` anahtar kelime, `.s` string, `.c` yorum.

## Ses tonu
- "İşini bilen, lafı uzatmayan, yardımsever geliştirici arkadaş."
- Şirket "biz", okuyucu "siz". Kısa cümle, önce sonuç, somut iddia ("3 dokunuşta", "%40 daha az rebuild").
- En fazla 1 emoji, en fazla 1 ünlem (kontrol: `check.py`).
- Yasak: "en iyi", "mükemmel", "devrim", "kullanıcı dostu", "app" (→ "uygulama"), soğuk resmi dil.
- Sevilen kelimeler: uygulama, kolay, sade, dokunuş, ücretsiz, gizlilik, güncelleme, öneri.
- Yazım: "ClickByteDev", "ClickByteDev'in", alan adı "clickbytedev.com" (www yok).

## Caption
- İlk satır "... daha fazla" kesiminden önce tek başına merak uyandırmalı (≤125 karakter).
- Gövde 2-5 kısa satır, tek çağrı (kaydet / takip et / yorumda yaz). Uygulama içeriğinde: "Profildeki linkten ücretsiz indirin."
- En sonda 3 hashtag (ör. `#flutter #mobiluygulama #yazılım`). Toplam ≤2200 karakter.
- Yazdıktan sonra `ig-human` skill'i ile yapay zekâ izlerini temizle (em dash yok, kalıp ifade yok).

İyi: "Liste kasıyorsa sorun büyük ihtimalle ListView. builder'a geçin, sadece ekrandakini çizer."
Kötü: "🚀🔥 Flutter'da MÜKEMMEL performans için en iyi 5 ipucu!!!"
