"""Chapas esmaltadas de marcas de la época (recreación tipográfica) con óxido fotoescaneado."""
import sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
S = sys.argv[1]; OUT = S + '/tour/tex_real/'
ANTON = S + '/fonts/Anton.ttf'; INTER = S + '/fonts/Inter.ttf'
def F(p, s, w=None):
    f = ImageFont.truetype(p, s)
    if w:
        try: f.set_variation_by_axes([w])
        except Exception: pass
    return f
RUST = np.asarray(Image.open(S + '/ph/tex/rusty_metal/diff.jpg').convert('RGB')).astype(np.float32)
RUST2 = np.asarray(Image.open(S + '/ph/tex/rust_coarse_01/diff.jpg').convert('RGB')).astype(np.float32)
def ctext(d, txt, f, cy, col, W, cx=None, skew=False):
    cx = W / 2 if cx is None else cx
    bb = d.textbbox((0, 0), txt, font=f); tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.text((cx - tw / 2 - bb[0], cy - th / 2 - bb[1]), txt, font=f, fill=col)
def italic_text(im, txt, f, cy, col, shear=0.22, stroke=0, stroke_col=None):
    W = im.width; t = Image.new('RGBA', im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(t)
    bb = d.textbbox((0, 0), txt, font=f, stroke_width=stroke); tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.text(((W - tw) / 2 - bb[0], cy - th / 2 - bb[1]), txt, font=f, fill=col, stroke_width=stroke, stroke_fill=stroke_col)
    t = t.transform(t.size, Image.AFFINE, (1, shear, -shear * cy, 0, 1, 0), Image.BICUBIC)
    im.alpha_composite(t)
def weather(im, seed, chips=0.10, edge=1.0):
    """Desconchones de esmalte con óxido real, óxido en bordes y agujeros de tornillo."""
    W, H = im.size; a = np.asarray(im).astype(np.float32)
    rng = np.random.default_rng(seed)
    oy, ox = rng.integers(0, 2048 - min(H, 2048)) if H < 2048 else 0, rng.integers(0, 2048 - min(W, 2048)) if W < 2048 else 0
    def tile(src):
        reps = (math.ceil(H / 2048) + 1, math.ceil(W / 2048) + 1, 1)
        return np.tile(src, reps)[oy:oy + H, ox:ox + W]
    rust = tile(RUST if seed % 2 else RUST2)
    alpha = a[..., 3] / 255
    inside = Image.fromarray((alpha * 255).astype(np.uint8))
    dist = np.asarray(inside.filter(ImageFilter.MinFilter(41)).filter(ImageFilter.GaussianBlur(25))).astype(np.float32) / 255
    n1 = np.asarray(Image.effect_noise((W // 10 + 1, H // 10 + 1), 100).resize((W, H), Image.BICUBIC)).astype(np.float32) / 255
    n2 = np.asarray(Image.effect_noise((W // 3 + 1, H // 3 + 1), 120).resize((W, H), Image.BICUBIC)).astype(np.float32) / 255
    n3 = np.asarray(Image.effect_noise((W // 40 + 2, H // 40 + 2), 110).resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(6))).astype(np.float32) / 255
    m = n3 * 0.85 + n1 * 0.15
    chip = np.clip((m - (1 - chips)) * 25, 0, 1) * alpha * (1.2 - dist * 0.6)
    edger = np.clip((1 - dist) * edge * 1.4 - (1 - m) * 0.6, 0, 1) * alpha
    rmask = np.clip(np.maximum(chip, edger), 0, 1)
    rmask = np.asarray(Image.fromarray((rmask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255
    # suciedad y amarilleo general
    a[..., :3] = a[..., :3] * (0.9 + 0.1 * n3[..., None]) * np.array([1.0, 0.97, 0.9])
    a[..., :3] = a[..., :3] * (1 - rmask[..., None]) + rust * 0.9 * rmask[..., None]
    # tornillos
    d = ImageDraw.Draw(img := Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))
    r = max(8, int(min(W, H) * 0.018))
    for (x, y) in [(0.04, 0.08), (0.96, 0.08), (0.04, 0.92), (0.96, 0.92)]:
        px, py = int(x * W), int(y * H)
        if alpha[min(py, H - 1), min(px, W - 1)] > 0.5:
            d.ellipse((px - r, py - r, px + r, py + r), fill=(70, 62, 55, 255)); d.ellipse((px - r * .5, py - r * .5, px + r * .3, py + r * .3), fill=(140, 130, 118, 255))
    rough = (0.22 + 0.6 * rmask + 0.12 * n3) * 255
    return img, Image.fromarray(np.clip(rough, 0, 255).astype(np.uint8))
def save(name, im, seed, **kw):
    col, rough = weather(im, seed, **kw)
    col.save(OUT + name + '.png'); rough.save(OUT + name + '_r.png'); print(name, im.size)
def plate(W, H, bg, border=None, bw=0, radius=30, shape='rect'):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if shape == 'oval':
        d.ellipse((0, 0, W - 1, H - 1), fill=border or bg); d.ellipse((bw, bw, W - 1 - bw, H - 1 - bw), fill=bg)
    elif shape == 'circle':
        d.ellipse((0, 0, W - 1, H - 1), fill=border or bg); d.ellipse((bw, bw, W - 1 - bw, H - 1 - bw), fill=bg)
    else:
        d.rounded_rectangle((0, 0, W - 1, H - 1), radius, fill=border or bg)
        if bw: d.rounded_rectangle((bw, bw, W - 1 - bw, H - 1 - bw), max(radius - bw // 2, 4), fill=bg)
    return im, d
RED = (190, 28, 30, 255); WHITE = (238, 234, 224, 255); BLACK = (22, 22, 22, 255); NAVY = (20, 40, 92, 255)
YEL = (246, 196, 0, 255); GREEN = (0, 120, 70, 255); BLUE = (20, 70, 160, 255)

# MONTESA: óvalo blanco con rótulo rojo
im, d = plate(1600, 900, WHITE, RED, 40, shape='oval')
italic_text(im, 'Montesa', F(INTER, 300, 900), 430, RED, 0.18)
d = ImageDraw.Draw(im); ctext(d, 'SERVICIO OFICIAL', F(INTER, 70, 700), 680, BLACK, 1600)
save('b_montesa', im, 1)
# BULTACO: rectángulo rojo, texto blanco
im, d = plate(1800, 700, RED, WHITE, 26, 40)
ctext(d, 'BULTACO', F(ANTON, 360), 300, WHITE, 1800)
ctext(d, 'SERVICIO · RECAMBIOS', F(INTER, 70, 700), 560, WHITE, 1800)
save('b_bultaco', im, 2)
# OSSA: azul con letras blancas
im, d = plate(1400, 700, NAVY, WHITE, 24, 36)
ctext(d, 'OSSA', F(ANTON, 400), 320, WHITE, 1400)
ctext(d, 'MOTOCICLETAS', F(INTER, 66, 700), 580, YEL, 1400)
save('b_ossa', im, 3)
# DERBI: blanco con rojo
im, d = plate(1400, 600, WHITE, RED, 30, 30)
italic_text(im, 'DERBI', F(ANTON, 330), 270, RED, 0.2)
d = ImageDraw.Draw(im); ctext(d, 'MOLLET · BARCELONA', F(INTER, 54, 700), 500, BLACK, 1400)
save('b_derbi', im, 4)
# SANGLAS
im, d = plate(1800, 520, (232, 222, 196, 255), NAVY, 22, 24)
ctext(d, 'SANGLAS', F(ANTON, 300), 250, NAVY, 1800)
ctext(d, 'MOTOCICLETAS 350 · 400 · 500', F(INTER, 48, 600), 450, RED, 1800)
save('b_sanglas', im, 5)
# CAMPSA: alargado, rojo y azul
im, d = plate(2400, 700, WHITE, BLUE, 30, 20)
d.rectangle((30, 30, 2370, 330), fill=RED)
ctext(d, 'CAMPSA', F(ANTON, 260), 180, WHITE, 2400)
ctext(d, 'GASOLINAS · LUBRICANTES', F(INTER, 110, 800), 500, BLUE, 2400)
save('b_campsa', im, 6)
# CASTROL: verde, rótulo rojo con contorno blanco
im, d = plate(1700, 850, GREEN, WHITE, 22, 30)
italic_text(im, 'Castrol', F(INTER, 330, 900), 380, RED, 0.12, stroke=14, stroke_col=WHITE)
d = ImageDraw.Draw(im); ctext(d, 'MOTOR OIL', F(ANTON, 130), 680, WHITE, 1700)
save('b_castrol', im, 7)
# CHAMPION: pajarita roja sobre negro
im, d = plate(1600, 700, BLACK, None, 0, 18)
d.polygon([(80, 120), (800, 230), (1520, 120), (1520, 580), (800, 470), (80, 580)], fill=RED)
d.polygon([(80, 120), (800, 230), (1520, 120), (1520, 580), (800, 470), (80, 580)], outline=WHITE, width=16)
ctext(d, 'CHAMPION', F(ANTON, 230), 350, WHITE, 1600)
ctext(d, 'BUJÍAS', F(INTER, 60, 800), 640, YEL, 1600)
save('b_champion', im, 8)
# MICHELIN: azul con amarillo
im, d = plate(2000, 640, (30, 50, 120, 255), YEL, 20, 20)
ctext(d, 'MICHELIN', F(ANTON, 330), 300, YEL, 2000)
ctext(d, 'NEUMÁTICOS', F(INTER, 64, 800), 540, WHITE, 2000)
save('b_michelin', im, 9)
# PIRELLI: amarillo con rojo
im, d = plate(1500, 600, YEL, BLACK, 18, 24)
ctext(d, 'PIRELLI', F(ANTON, 300), 280, RED, 1500)
ctext(d, 'NEUMÁTICOS DE MOTO', F(INTER, 56, 800), 500, BLACK, 1500)
save('b_pirelli', im, 10)
# MOTUL: redondo
im, d = plate(1000, 1000, WHITE, RED, 50, shape='circle')
d.rectangle((60, 380, 940, 620), fill=RED)
ctext(d, 'MOTUL', F(ANTON, 230), 495, WHITE, 1000)
ctext(d, 'ACEITES', F(INTER, 70, 800), 260, BLACK, 1000)
ctext(d, 'DESDE 1853', F(INTER, 56, 700), 740, BLACK, 1000)
save('b_motul', im, 11)
# AMAL
im, d = plate(1500, 560, (210, 30, 30, 255), WHITE, 20, 20)
ctext(d, 'AMAL', F(ANTON, 300), 240, WHITE, 1500)
ctext(d, 'CARBURADORES', F(INTER, 64, 800), 470, WHITE, 1500)
save('b_amal', im, 12)
