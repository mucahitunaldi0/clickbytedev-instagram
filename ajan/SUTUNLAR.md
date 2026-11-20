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

**Görsel kuralı:** uygulama içeriğinin her karesinde gerçek görsel olur; yalnız yazı kartı yok. Varlıklar `assets/uygulamalar/<slug>/`:
- `ikon.png` (hepsinde), `ekran-N.jpg` = ham ekran görüntüsü (otonot, cepik, movyra, matematik-heyecani) → `<div class="telefon"><img src="../../assets/uygulamalar/<slug>/ekran-N.jpg"></div>`
- `magaza-N.jpg` = içinde telefon olan hazır mağaza görseli (snapburn, kelime-ustasi, pixelpop) → `<img class="magaza" src="...">` (telefon çerçevesine koyma)
- Sınıflar `sablon/brand.css`: `.telefon`/`.magaza` (560px; story'de `buyuk` ile 900px), `.telefonlar` (yan yana), `.uygulama-ad` (ikon + ad), `.ikon`, `.ikon.buyuk-ikon`, `.ikonlar`. Örnek: `icerik/2026-11-30-carousel-uygulama-vitrini`, `icerik/2026-11-24-story-otonot-hatirlatici`.
- Yazı görselin anlattığıyla tutarlı olmalı; ekranda olmayan özelliği o ekranla anlatma. Yeni ekran gerekiyorsa uydurma, raporda iste.

Android uygulamaları Google Play'de ücretsiz; iOS "yakında App Store'da".
Bir ayda her uygulama en fazla 2 kez öne çıkar; yeni güncellemesi olan (bilgi bankasında notu olan) önceliklidir.
