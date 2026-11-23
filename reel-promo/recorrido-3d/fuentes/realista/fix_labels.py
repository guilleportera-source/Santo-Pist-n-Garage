"""Quita textos de marca/idioma ajenos de las texturas de algunos modelos (spray, extintor)."""
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S = sys.argv[1]; M = S + '/ph/models/'; O = S + '/tour/tex_fix/'
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
import glob
fb = (glob.glob('/usr/share/fonts/**/*Oswald*', recursive=True) + glob.glob('/usr/share/fonts/**/DejaVuSans-Bold.ttf', recursive=True))[0]
def font(sz): return ImageFont.truetype(fb, sz)
# spray: etiqueta «Paint Haven» -> «ESMALTE / SPRAY»
for nm_ in ('spray_paint_bottles_diff_1k.jpg', 'spray_paint_bottles_dirty_diff_1k.jpg'):
  p = M + 'spray_paint_bottles/textures/' + nm_
  im = Image.open(p).convert('RGB'); d = ImageDraw.Draw(im)
  box = (292, 586, 508, 754)
  bg = im.getpixel((300, 600)); d.rectangle(box, fill=(40, 40, 42))
  for txt, y, sz in (('ESMALTE', 615, 44), ('SPRAY', 668, 34), ('secado rápido', 714, 20)):
      w = d.textlength(txt, font=font(sz)); d.text(((box[0] + box[2]) / 2 - w / 2, y), txt, font=font(sz), fill=(225, 225, 222))
  im.save(O + nm_, quality=95)
# extintor: placa «소화기» -> «EXTINTOR»
p = M + 'korean_fire_extinguisher_01/textures/korean_fire_extinguisher_01_body_diff_1k.jpg'
im = Image.open(p).convert('RGB'); d = ImageDraw.Draw(im)
src = im.crop((20, 300, 340, 410)); im.paste(src.resize((330, 112)), (6, 4))
txt = 'EXTINTOR'; f_ = font(50); w = d.textlength(txt, font=f_)
d.text((171 - w / 2, 28), txt, font=f_, fill=(205, 200, 195))
im.save(O + 'korean_fire_extinguisher_01_body_diff_1k.jpg', quality=95)
p = M + 'korean_fire_extinguisher_01/textures/korean_fire_extinguisher_01_paper_diff_1k.jpg'
im = Image.open(p).convert('RGB')
blank = im.crop((520, 356, 992, 996)); im.paste(blank.resize((472, 640)), (16, 20))
d = ImageDraw.Draw(im); f_ = font(30)
for i, t in enumerate(('REVISIÓN', 'EXTINTOR', '', '03/1987  ✓', '09/1988  ✓', '04/1990  ✓')):
    d.text((70, 140 + i * 52), t, font=f_, fill=(60, 60, 70))
im.save(O + 'korean_fire_extinguisher_01_paper_diff_1k.jpg', quality=95)
print('ok', fb)
