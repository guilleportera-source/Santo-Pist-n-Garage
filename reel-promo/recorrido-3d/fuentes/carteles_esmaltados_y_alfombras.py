import sys, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
S = sys.argv[1]; T = S + '/tour/tex/'
ANTON = S + '/fonts/Anton.ttf'; INTER = S + '/fonts/Inter.ttf'
def F(p, s): return ImageFont.truetype(p, s)
rnd = random.Random(7)

# ---------- alfombras persas (originales, procedurales) ----------
def rug(fn, base, border, accent, light, seed):
    r = random.Random(seed); W, H = 1600, 1000
    im = Image.new('RGB', (W, H), base); d = ImageDraw.Draw(im)
    # bordes concéntricos
    for k, (m, c) in enumerate([(0, light), (18, border), (70, accent), (82, border), (150, light), (160, base)]):
        d.rectangle((m, m, W - m, H - m), fill=c)
    # greca en la banda del borde
    for x in range(30, W - 30, 44):
        for y in (44, H - 44):
            d.polygon([(x, y - 14), (x + 14, y), (x, y + 14), (x - 14, y)], fill=accent)
    for y in range(30, H - 30, 44):
        for x in (44, W - 44):
            d.polygon([(x, y - 14), (x + 14, y), (x, y + 14), (x - 14, y)], fill=accent)
    for x in range(100, W - 100, 60):
        for y in (115, H - 115):
            d.ellipse((x - 16, y - 10, x + 16, y + 10), fill=light); d.ellipse((x - 6, y - 4, x + 6, y + 4), fill=base)
    for y in range(110, H - 110, 60):
        for x in (115, W - 115):
            d.ellipse((x - 10, y - 16, x + 10, y + 16), fill=light); d.ellipse((x - 4, y - 6, x + 4, y + 6), fill=base)
    # medallón central
    cx, cy = W // 2, H // 2
    for k, (rx, c) in enumerate([(330, border), (300, light), (270, accent), (200, base), (150, border), (90, light), (50, accent)]):
        ry = rx * 0.62
        d.polygon([(cx - rx, cy), (cx, cy - ry), (cx + rx, cy), (cx, cy + ry)], fill=c)
    # esquinas
    for sx in (1, -1):
        for sy in (1, -1):
            px, py = cx + sx * (W / 2 - 160), cy + sy * (H / 2 - 160)
            d.polygon([(px, py), (px - sx * 260, py), (px, py - sy * 180)], fill=border)
            d.polygon([(px, py), (px - sx * 180, py), (px, py - sy * 120)], fill=light)
    # motivos florales sueltos
    for _ in range(140):
        x = r.randint(180, W - 180); y = r.randint(180, H - 180)
        if abs(x - cx) / 340 + abs(y - cy) / 215 < 1.05: continue
        s = r.randint(6, 12); c = r.choice([light, accent, border])
        d.ellipse((x - s, y - s, x + s, y + s), fill=c)
    a = np.asarray(im).astype(np.float32)
    # desgaste y fibra
    n = np.random.default_rng(seed).normal(0, 1, (H, W, 1)) * 10
    wear = np.asarray(Image.effect_noise((W // 8, H // 8), 60).resize((W, H), Image.BICUBIC)).astype(np.float32)[..., None] / 255
    a = a * (0.82 + 0.25 * wear) + n
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))
    # flecos
    out = Image.new('RGBA', (W + 80, H), (0, 0, 0, 0)); out.paste(im, (40, 0))
    d = ImageDraw.Draw(out)
    for y in range(4, H - 4, 9):
        for x0 in (0, W + 40):
            d.line((x0 + 2, y, x0 + 40, y + r.randint(-2, 2)), fill=(225, 215, 190, 255), width=3)
    out.save(T + fn)
rug('rug1.png', (120, 22, 24), (22, 28, 60), (196, 150, 70), (230, 214, 180), 1)
rug('rug2.png', (30, 38, 78), (128, 24, 26), (190, 140, 60), (226, 210, 176), 2)
rug('rug3.png', (140, 40, 30), (60, 30, 22), (40, 70, 90), (222, 200, 160), 3)

# ---------- carteles esmaltados (marcas inventadas) ----------
def enamel(fn, W, H, bg, fg, lines, border=None, shape='rect', icon=None):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if shape == 'oval':
        d.ellipse((0, 0, W - 1, H - 1), fill=border or fg); d.ellipse((22, 22, W - 23, H - 23), fill=bg)
    else:
        d.rounded_rectangle((0, 0, W - 1, H - 1), 34, fill=border or fg)
        d.rounded_rectangle((20, 20, W - 21, H - 21), 22, fill=bg)
        for x, y in ((40, 40), (W - 40, 40), (40, H - 40), (W - 40, H - 40)):
            d.ellipse((x - 10, y - 10, x + 10, y + 10), fill=(60, 60, 60)); d.ellipse((x - 5, y - 5, x + 3, y + 3), fill=(170, 170, 170))
    if icon: icon(d)
    for (txt, font, y, col) in lines:
        tw = d.textlength(txt, font=font); d.text(((W - tw) / 2, y), txt, font=font, fill=col)
    a = np.asarray(im).astype(np.float32)
    # óxido y desconchones
    rng = np.random.default_rng(len(fn))
    mask = np.asarray(Image.effect_noise((W // 6, H // 6), 90).resize((W, H), Image.BICUBIC)).astype(np.float32) / 255
    chips = (mask > 0.86) & (a[..., 3] > 0)
    rust = np.array([96, 52, 28], np.float32)
    a[chips, :3] = a[chips, :3] * 0.2 + rust * 0.8
    edge = np.asarray(Image.fromarray((a[..., 3] > 0).astype(np.uint8) * 255).filter(ImageFilter.MinFilter(31))).astype(np.float32) / 255
    e2 = (1 - edge) * (a[..., 3] / 255) * (mask > 0.55)
    a[..., :3] = a[..., :3] * (1 - 0.6 * e2[..., None]) + rust * 0.6 * e2[..., None]
    a[..., :3] *= 0.9 + 0.1 * mask[..., None]
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(T + fn)

Y = (238, 190, 40); R_ = (176, 30, 26); K = (24, 22, 20); C = (236, 226, 200); G = (30, 90, 60); B = (24, 60, 120)
enamel('sign_aceite.png', 1400, 560, Y, R_, [('ACEITES', F(ANTON, 120), 70, R_), ('PISTÓN SANTO', F(ANTON, 210), 170, K), ('SUPER MOTOR OIL · 1962', F(INTER, 52), 430, R_)], border=R_)
enamel('sign_bujias.png', 900, 900, K, Y, [('BUJÍAS', F(ANTON, 170), 150, Y), ('RAYO', F(ANTON, 300), 330, C), ('ENCENDIDO SEGURO', F(INTER, 50), 720, Y)], border=Y, shape='oval',
       icon=lambda d: d.polygon([(470, 80), (400, 140), (450, 140), (410, 200), (500, 130), (450, 130)], fill=Y))
enamel('sign_gasolina.png', 1500, 500, G, C, [('GASOLINA', F(ANTON, 150), 50, C), ('COSTA MARESME', F(ANTON, 130), 230, Y), ('SERVICIO · LUBRICANTES', F(INTER, 46), 410, C)], border=C)
enamel('sign_neumaticos.png', 1300, 460, B, C, [('NEUMÁTICOS', F(ANTON, 150), 50, C), ('LA RUEDA DE ORO', F(ANTON, 110), 230, Y), ('desde 1958', F(INTER, 46), 380, C)], border=Y)
enamel('sign_taller.png', 1300, 420, C, K, [('TALLER', F(ANTON, 110), 40, R_), ('MOTOS CLÁSICAS', F(ANTON, 150), 160, K), ('REPARACIÓN · RESTAURACIÓN', F(INTER, 44), 340, R_)], border=K)
print('ok')
