"""Calendario de taller de pared (octubre de 1979, una marca de recambios inventada), envejecido."""
import sys, random, calendar
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S = sys.argv[1]; TR = S + '/tour/tex_real/'
B = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'; Rg = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
W, H = 700, 1000
im = Image.new('RGB', (W, H), (236, 228, 208)); d = ImageDraw.Draw(im)
# ilustración superior: un poster pintado (degradado + carretera de montaña)
for y in range(520):
    k = y / 520; d.line([(30, 30 + y), (W - 30, 30 + y)], fill=(int(230 - 90 * k), int(150 - 40 * k), int(80 + 40 * k)))
d.polygon([(30, 420), (200, 260), (330, 360), (480, 220), (670, 400), (670, 550), (30, 550)], fill=(70, 80, 70))
d.polygon([(250, 550), (420, 550), (360, 420), (330, 420)], fill=(55, 52, 50))
d.line([(340, 550), (345, 425)], fill=(220, 200, 120), width=4)
d.ellipse([480, 70, 600, 190], fill=(250, 220, 150))
d.rectangle([30, 470, W - 30, 550], fill=(150, 30, 28))
f = ImageFont.truetype(B, 44); t = 'RECAMBIOS COSTA'; d.text((W / 2 - d.textlength(t, font=f) / 2, 485), t, font=f, fill=(245, 235, 210))
f = ImageFont.truetype(B, 34); t = 'OCTUBRE 1979'; d.text((W / 2 - d.textlength(t, font=f) / 2, 575), t, font=f, fill=(40, 35, 32))
f = ImageFont.truetype(B, 20); days = 'L M X J V S D'.split()
for i, dd in enumerate(days): d.text((70 + i * 85, 635), dd, font=f, fill=(150, 30, 28) if i == 6 else (60, 55, 50))
f = ImageFont.truetype(Rg, 28)
for r, wk in enumerate(calendar.Calendar().monthdayscalendar(1979, 10)):
    for c, n in enumerate(wk):
        if n: d.text((62 + c * 85, 675 + r * 58), str(n), font=f, fill=(150, 30, 28) if c == 6 else (45, 40, 38))
d.ellipse([140, 723, 200, 763], outline=(30, 60, 160), width=3)   # un día marcado a boli
random.seed(3)
for _ in range(1400):   # manchas de grasa y amarilleo
    x, y = random.randrange(W), random.randrange(H); r = random.choice((1, 1, 2, 3))
    g = random.randint(150, 200); d.ellipse([x - r, y - r, x + r, y + r], fill=(g, g - 15, g - 40))
ov = Image.new('L', (W, H), 0); od = ImageDraw.Draw(ov)
for _ in range(10):
    x, y = random.randrange(W), random.randrange(H); r = random.randint(15, 60); od.ellipse([x - r, y - r, x + r, y + r], fill=random.randint(40, 90))
ov = ov.filter(ImageFilter.GaussianBlur(18)); im = Image.composite(Image.new('RGB', (W, H), (120, 95, 60)), im, ov)
d = ImageDraw.Draw(im); d.ellipse([W / 2 - 9, 6, W / 2 + 9, 24], fill=(30, 30, 30))
im.filter(ImageFilter.GaussianBlur(0.6)).save(TR + 'calendario.jpg', quality=92)
print('ok')
