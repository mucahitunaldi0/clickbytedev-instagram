# İçerik sütunları

Dağılım: ~%70 ipucu/süreç, ~%30 uygulama. Uygulama içerikleri de öğretici açıdan anlatılır ("Snapburn'de kalori taramasını şöyle yaptık").

| Sütun (`sutun`) | Ne | Format önerisi |
|---|---|---|
| `ipucu` | Flutter/Dart ipucu, tek problem tek çözüm | Reel (kod yazılır), carousel |
| `surec` | Play Store yayını, ASO, hata ayıklama hikâyesi, araçlar | carousel, story |
| `uygulama` | Uygulamamızı nasıl yaptık / ne çözer | Reel, carousel |
| `quiz` | "Bu kod ne yazdırır?" (cevap sonraki story karesinde) | story |
| `gunluk` | "Bugün ne kodladık" (bilgi bankasından) | story |

Hook için `ig-reel` skill'indeki formüller; carousel kapağı için `ig-carousel`; story dizisi için `ig-story`.

## Uygulamalar (link: `clickbytedev.com/uygulamalar/<slug>`)
| Uygulama | slug | Ne yapar |
|---|---|---|
| Movyra | movyra | Film keşfi, puanlama, listeler |
| Matematik Heyecanı | matematik-heyecani | Zihinden işlem oyunları |
| Otonot | otonot | Araç hatırlatıcı ve masraf takibi |
| Pixel POP | pixelpop | Renk eşleştirme bulmacası |
| Snapburn | snapburn | Fotoğraftan kalori tarama, kısa ev egzersizleri |
| CepİK | cepik | İzin, köprü tatili, maaş, kıdem hesaplayıcıları |
| Kelime Ustası | kelime-ustasi | Türkçe-İngilizce kelime oyunu |

**Görsel kuralı:** uygulama içeriğinin her karesinde gerçek ekran görüntüsü olur; yalnız yazı kartı yok. Varlıklar `assets/uygulamalar/<slug>/`: `ikon.png` ve `ekran-N.jpg` (hepsi aynı 9:19.5 oranında ham ekran).
- Ekran her zaman telefon çerçevesinde: `<div class="telefon" style="--h:640px"><img src="../../assets/uygulamalar/<slug>/ekran-N.jpg" alt=""></div>`. Aynı karedeki telefonlar aynı `--h` değerini kullanır (carousel 640, story 720-920).
- Hazır şablonları kopyala, düzeni değiştirme: carousel `icerik/2026-11-30-carousel-uygulama-vitrini` (yan yana iki uygulama: `.ikili` + `.kolon`), story `icerik/2026-11-24-story-otonot-hatirlatici` (ortalı), reel `icerik/2026-11-27-reel-snapburn-kalori-tarama`.
- Açıklama satırları tek satıra sığmalı; story metni ortalı ve kısa olur. Render sonrası her kareye bak: telefonlar eşit boy, metin satır sonunda tek kelime kalmıyor, ekran içeriği kesilmiyor.
- Yazı ekranın gösterdiğiyle tutarlı olmalı; ekranda olmayan özelliği o ekranla anlatma. Yeni ekran gerekiyorsa uydurma, raporda iste.

Android uygulamaları Google Play'de ücretsiz; iOS "yakında App Store'da".
Bir ayda her uygulama en fazla 2 kez öne çıkar; yeni güncellemesi olan (bilgi bankasında notu olan) önceliklidir.
