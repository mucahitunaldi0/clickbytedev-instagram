# Figma'ya aktarım

Her klasör bir gönderi; her `.svg` bir kare (carousel 1080x1350, story/reel 1080x1920).

**İçe aktarma:** Figma dosyasını açın, bir klasördeki `.svg` dosyalarını seçip tuvale sürükleyin. Her dosya ayrı bir çerçeve olur.

**Neler düzenlenebilir:**
- Yazılar metin katmanıdır; her satır ayrı bir katmandır. Kelime değiştirmek için çift tıklayın.
- Kutular, zemin ve ızgara vektördür. Rengi ve köşe yuvarlaklığı değiştirilebilir.
- Ekran görüntüleri ve ikonlar ayrı görsel katmanlarıdır. "Ekran" katmanının dolgusunu değiştirerek başka bir ekran koyabilirsiniz.

**Fontlar:** Bricolage Grotesque (ExtraBold), DM Sans, JetBrains Mono. Hepsi Google Fonts'ta var ve Figma'da hazır gelir.

**Bilinen eksik:** Telefonların arkasındaki mavi parıltı gölgesi aktarılmaz. Gerekirse Figma'da "Drop shadow" efektiyle eklenebilir.

**Reel'ler:** Animasyonun son karesi aktarılır.

Yeniden üretmek için:

```powershell
python scripts/figma_svg.py
```
