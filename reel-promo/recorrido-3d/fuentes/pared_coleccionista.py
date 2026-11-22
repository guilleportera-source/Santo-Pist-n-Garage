import sys, glob
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageEnhance
S = sys.argv[1]; T = S + '/tour/tex/'; C = S + '/cutouts/'
ANTON = S + '/fonts/Anton.ttf'; INTER = S + '/fonts/Inter.ttf'
def F(p, s): return ImageFont.truetype(p, s)
def ctext(d, txt, f, y, col, W):
    d.text(((W - d.textlength(txt, font=f)) / 2, y), txt, font=f, fill=col)
def age(im, amt=0.25, seed=1):
    a = np.asarray(im.convert('RGB')).astype(np.float32)
    paper = np.array([235, 222, 190], np.float32)
    a = a * (1 - amt * 0.4) + paper * amt * 0.4
    n = np.asarray(Image.effect_noise((im.width // 4, im.height // 4), 50).resize(im.size, Image.BICUBIC)).astype(np.float32)[..., None] / 255
    a *= 0.9 + 0.12 * n
    yy, xx = np.mgrid[0:im.height, 0:im.width]
    v = 1 - 0.25 * (((xx / im.width - .5) * 2) ** 4 + ((yy / im.height - .5) * 2) ** 4)
    return Image.fromarray(np.clip(a * v[..., None], 0, 255).astype(np.uint8))
def silhouette(name, w, col):
    c = Image.open(C + name + '.png').convert('RGBA'); c = c.crop(c.getbbox())
    c = c.resize((w, int(c.height * w / c.width)), Image.LANCZOS)
    s = Image.new('RGBA', c.size, col); s.putalpha(c.getchannel('A')); return s

# 1) Cartel de carrera: Gran Premio Costa del Maresme 1971 (silueta Bultaco)
W, H = 1000, 1400; im = Image.new('RGB', (W, H), (232, 220, 190)); d = ImageDraw.Draw(im)
for k in range(14):
    ang0 = -90 + k * 26
    d.pieslice((W / 2 - 1400, 560 - 1400, W / 2 + 1400, 560 + 1400), ang0, ang0 + 13, fill=(214, 92, 40))
d.ellipse((W / 2 - 230, 330, W / 2 + 230, 790), fill=(240, 176, 50))
d.rectangle((0, 820, W, H), fill=(26, 52, 74))
sil = silhouette('bultaco_chispa', 600, (20, 18, 16)); im.paste(sil, ((W - sil.width) // 2, 840 - sil.height), sil)
ctext(d, 'GRAN PREMIO', F(ANTON, 130), 40, (26, 52, 74), W); ctext(d, 'COSTA DEL MARESME', F(ANTON, 92), 190, (176, 30, 26), W)
ctext(d, '1971', F(ANTON, 260), 870, (240, 176, 50), W)
ctext(d, 'CAMPEONATO DE MOTOCICLISMO', F(INTER, 44), 1180, (232, 220, 190), W); ctext(d, '18 · 19 SEPTIEMBRE', F(INTER, 52), 1250, (240, 176, 50), W)
age(im, 0.3).save(T + 'w_gp.jpg', quality=92)

# 2) Cartel de trial: Trial de la Serra 1974 (silueta moto de trial)
W, H = 900, 1260; im = Image.new('RGB', (W, H), (30, 30, 28)); d = ImageDraw.Draw(im)
d.polygon([(0, 900), (220, 640), (380, 760), (600, 520), (900, 820), (900, 1260), (0, 1260)], fill=(70, 96, 60))
d.polygon([(0, 1000), (300, 820), (560, 940), (900, 760), (900, 1260), (0, 1260)], fill=(46, 66, 42))
sil = silhouette('cota', 640, (238, 224, 190)); im.paste(sil, ((W - sil.width) // 2 + 30, 760 - sil.height), sil)
ctext(d, 'TRIAL', F(ANTON, 230), 40, (238, 224, 190), W); ctext(d, 'DE LA SERRA', F(ANTON, 110), 300, (226, 120, 40), W)
ctext(d, '7 ABRIL 1974 · 6 ZONAS', F(INTER, 46), 1110, (238, 224, 190), W)
age(im, 0.22, 2).save(T + 'w_trial.jpg', quality=92)

# 3) Portada de revista de época con foto de la Scoopy
W, H = 900, 1200; im = Image.new('RGB', (W, H), (240, 232, 214)); d = ImageDraw.Draw(im)
ph = Image.open(S + '/photos2/scoopy_roja_IMG_6041.jpg'); ph = ImageOps.exif_transpose(ph).convert('RGB')
ph = ImageOps.fit(ph, (820, 820)); ph = ImageEnhance.Color(ph).enhance(0.75); im.paste(ph, (40, 300))
d.rectangle((0, 0, W, 260), fill=(176, 30, 26)); ctext(d, 'MOTO REVISTA', F(ANTON, 170), 20, (240, 232, 214), W)
d.text((40, 1140), 'Nº 112 · MAYO 1966 · 15 PTAS', font=F(INTER, 34), fill=(30, 28, 24))
d.rectangle((40, 1050, 560, 1120), fill=(240, 176, 50)); d.text((56, 1056), 'PRUEBA: SCOOTER 75 cc', font=F(ANTON, 52), fill=(30, 28, 24))
age(im, 0.28, 3).save(T + 'w_revista.jpg', quality=92)

# 4) Foto antigua en sepia (Enduro 75)
ph = ImageOps.exif_transpose(Image.open(S + '/photos2/enduro75_IMG_2757.jpg')).convert('L')
ph = ImageOps.fit(ph, (900, 680)); ph = ImageOps.colorize(ImageOps.autocontrast(ph, 2), (40, 28, 18), (236, 218, 180))
bord = Image.new('RGB', (980, 760), (236, 228, 208)); bord.paste(ph, (40, 40))
age(bord, 0.3, 4).save(T + 'w_sepia.jpg', quality=92)

# 5) Chapa troquelada de mecánico (diseño propio)
W, H = 700, 1000; im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
d.polygon([(0, 0), (W, 0), (W, 760), (W / 2, H), (0, 760)], fill=(240, 196, 40))
d.polygon([(18, 18), (W - 18, 18), (W - 18, 750), (W / 2, H - 26), (18, 750)], outline=(176, 30, 26), width=10)
d.ellipse((230, 110, 470, 350), fill=(232, 190, 150)); d.chord((215, 80, 485, 250), 180, 360, fill=(36, 60, 50)); d.rectangle((205, 160, 495, 190), fill=(20, 30, 26))
d.ellipse((290, 210, 310, 230), fill=(20, 20, 20)); d.ellipse((390, 210, 410, 230), fill=(20, 20, 20)); d.arc((300, 250, 400, 310), 10, 170, fill=(120, 30, 20), width=8)
d.polygon([(140, 640), (190, 380), (510, 380), (560, 640)], fill=(36, 60, 50)); d.rectangle((330, 380, 370, 640), fill=(230, 220, 200))
ctext(d, 'SERVICIO', F(ANTON, 90), 650, (176, 30, 26), W); ctext(d, 'CON UNA SONRISA', F(INTER, 34), 770, (30, 28, 24), W)
a = np.asarray(im).astype(np.float32); m = np.asarray(Image.effect_noise((W // 5, H // 5), 90).resize((W, H), Image.BICUBIC)).astype(np.float32) / 255
ch = (m > 0.87) & (a[..., 3] > 0); a[ch, :3] = a[ch, :3] * 0.25 + np.array([96, 52, 28]) * 0.75
Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(T + 'w_chapa.png')

# 6) Chapa redonda: Lubricantes Rayo (estrella) y anuncio de ropa de época
W = 800; im = Image.new('RGBA', (W, W), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
d.rectangle((0, 0, W, W), fill=(236, 228, 210)); d.ellipse((60, 60, W - 60, W - 60), fill=(176, 30, 26)); d.ellipse((190, 190, W - 190, W - 190), fill=(236, 228, 210))
import math
pts = [(W / 2 + (150 if k % 2 == 0 else 60) * math.cos(math.radians(-90 + 36 * k)), W / 2 + (150 if k % 2 == 0 else 60) * math.sin(math.radians(-90 + 36 * k))) for k in range(10)]
d.polygon(pts, fill=(176, 30, 26)); ctext(d, 'R', F(ANTON, 120), 300, (30, 90, 60), W)
f = F(ANTON, 70)
for i, ch_ in enumerate('LUBRICANTES'):
    ang = math.radians(-160 + i * 14); x = W / 2 + 270 * math.cos(ang); y = W / 2 + 270 * math.sin(ang)
    g = Image.new('RGBA', (90, 90), (0, 0, 0, 0)); ImageDraw.Draw(g).text((20, 0), ch_, font=f, fill=(255, 255, 255)); g = g.rotate(-math.degrees(ang) - 90, resample=Image.BICUBIC)
    im.paste(g, (int(x - 45), int(y - 45)), g)
for i, ch_ in enumerate('RAYO · MOTOR'):
    ang = math.radians(150 - i * 12); x = W / 2 + 270 * math.cos(ang); y = W / 2 + 270 * math.sin(ang)
    g = Image.new('RGBA', (90, 90), (0, 0, 0, 0)); ImageDraw.Draw(g).text((20, 0), ch_, font=f, fill=(255, 255, 255)); g = g.rotate(-math.degrees(ang) + 90, resample=Image.BICUBIC)
    im.paste(g, (int(x - 45), int(y - 45)), g)
age(im, 0.25, 6).save(T + 'w_lubri.jpg', quality=92)

W, H = 800, 1100; im = Image.new('RGB', (W, H), (226, 214, 186)); d = ImageDraw.Draw(im)
d.text((60, 40), 'Sastrería', font=F(INTER, 80), fill=(120, 40, 30)); d.text((60, 140), 'del Puerto', font=F(INTER, 80), fill=(120, 40, 30))
for k, (x, c) in enumerate([(200, (150, 130, 100)), (520, (40, 44, 52))]):
    d.ellipse((x - 60, 300, x + 60, 420), fill=(222, 186, 150)); d.rectangle((x - 80, 270, x + 80, 300), fill=(60, 50, 40)); d.ellipse((x - 120, 285, x + 120, 315), fill=(60, 50, 40))
    d.polygon([(x - 130, 460), (x + 130, 460), (x + 110, 820), (x - 110, 820)], fill=c); d.rectangle((x - 90, 820, x - 15, 1020), fill=c); d.rectangle((x + 15, 820, x + 90, 1020), fill=c)
    d.polygon([(x - 25, 440), (x + 25, 440), (x, 560)], fill=(240, 236, 226)); d.rectangle((x - 70, 420, x + 70, 465), fill=c)
d.text((60, 1040), 'Trajes a medida · desde 1949', font=F(INTER, 36), fill=(60, 50, 40))
age(im, 0.35, 7).save(T + 'w_sastre.jpg', quality=92)
print('ok')
