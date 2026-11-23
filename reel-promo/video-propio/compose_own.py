"""Reel con material propio de Santo Pistón Garage (fotos y vídeos reales de las restauraciones).
1080x1920 · 30 fps · −14 LUFS.
Uso: python3 compose_own.py <scratchpad> <carpeta_uploads> <carpeta_salida> [check]
"""
import sys, subprocess, math, wave, os
import numpy as np
from PIL import Image, ImageOps, ImageDraw, ImageFont, ImageFilter

S, U, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
CHECK = len(sys.argv) > 4 and sys.argv[4] == 'check'
W, H, FPS = 1080, 1920, 30
BEAT = 60 / 105
CREAM = (246, 241, 230); GOLD = (226, 179, 60); INK = (20, 16, 12)
INTER = S + '/fonts/Inter.ttf'; ANTON = S + '/fonts/Anton.ttf'; LOGO = U + '/e6f113ba-image.jpg'
def font(path, size, wght=None):
    f = ImageFont.truetype(path, size)
    if wght:
        try: f.set_variation_by_axes([wght])
        except Exception: pass
    return f

# matrículas a pixelar (coordenadas en la foto original, ya girada)
PLATES = {
    '98a42998-image.jpg': [(255, 1228, 622, 1332)],
    '096c17d4-image.jpg': [(570, 160, 776, 240), (30, 50, 108, 90)],
    'd85b23d8-image.jpg': [(1615, 1005, 1700, 1085)],
}

# tipo, fuente, pulsos, parámetros, etiqueta (ANTES/DESPUÉS), titular, nombre
# foto: (cx, cy, zoom0, zoom1, dx) · vídeo: (inicio_s, cx)
PLAN = [
    ('foto', 'afc80896-image.jpg', 3, (0.50, 0.55, 1.00, 1.07, 0.0), 'ANTES', 'Así llegó…', None),
    ('foto', '096c17d4-image.jpg', 4, (0.40, 0.58, 1.10, 1.02, 0.0), 'DESPUÉS', '…y así salió.', 'Vespa Primavera 125'),
    ('foto', 'd85b23d8-image.jpg', 4, (0.52, 0.52, 1.00, 1.03, 0.26), 'ANTES', None, 'Honda Scoopy 75'),
    ('foto', '123a944b-image.jpg', 2, (0.50, 0.50, 1.00, 1.06, 0.0), None, 'Desmontada pieza a pieza', None),
    ('foto', '3c7b83f9-image.jpg', 2, (0.45, 0.55, 1.00, 1.07, 0.0), 'ANTES', None, None),
    ('foto', '7ea3b40f-image.jpg', 2, (0.50, 0.52, 1.10, 1.03, 0.0), 'DESPUÉS', None, None),
    ('video', '56363c4d-IMG_6588.mov', 4, (0.2, 0.5), None, 'Pintura a mano', None),
    ('foto', '73843f9a-image.jpg', 2, (0.48, 0.55, 1.00, 1.06, 0.0), None, None, None),
    ('foto', 'de593cc2-image.jpg', 2, (0.45, 0.55, 1.06, 1.00, 0.0), None, None, None),
    ('foto', 'd3f1e186-image.jpg', 3, (0.50, 0.55, 1.00, 1.06, 0.0), 'DESPUÉS', None, None),
    ('video', 'a3db4e71-ea78a411-5108-45e5-9850-7cfdfcaf7036.mov', 3, (44.0, 0.5), None, None, 'Honda Scoopy 75'),
    ('foto', 'b0068035-image.jpg', 3, (0.50, 0.52, 1.00, 1.05, 0.0), None, None, 'Montesa Cota 80'),
    ('foto', '0bca84d0-image.jpg', 3, (0.45, 0.50, 1.00, 1.04, 0.10), None, None, 'Montesa Enduro 75 L'),
    ('foto', '9557d50f-image.jpg', 3, (0.50, 0.48, 1.06, 1.00, 0.0), None, None, 'Bultaco Chispa'),
    ('foto', '98a42998-image.jpg', 3, (0.50, 0.58, 1.00, 1.05, 0.0), None, None, 'Fiat 126'),
    ('foto', 'a1185ca3-image.jpg', 3, (0.48, 0.62, 1.10, 1.02, 0.0), None, None, 'Montesa Impala 2'),
    ('foto', '3139c963-image.jpg', 3, (0.50, 0.55, 1.00, 1.05, 0.0), None, None, None),
    ('foto', '3520ef20-image.jpg', 3, (0.50, 0.52, 1.04, 1.00, -0.04), None, 'Hechas para rodar', None),
]
END_BEATS = 5
starts = np.cumsum([0] + [p[2] for p in PLAN]) * BEAT
DUR = starts[-1] + END_BEATS * BEAT
fi = lambda t: int(round(t * FPS))

# ---------- temblor de mano (suave, reproducible) ----------
rng = np.random.default_rng(7)
NF = fi(DUR) + 10
def smooth_noise(n, sigma):
    x = rng.normal(0, 1, n + 400); k = np.exp(-0.5 * (np.arange(-120, 121) / sigma) ** 2); k /= k.sum()
    y = np.convolve(x, k, 'same')[200:200 + n]; return y / (y.std() + 1e-9)
SX = smooth_noise(NF, 10) * 4 + smooth_noise(NF, 3) * 0.8
SY = smooth_noise(NF, 10) * 3.5 + smooth_noise(NF, 3) * 0.7
SR = smooth_noise(NF, 14) * 0.18

# ---------- etalonaje común (cálido suave, negros algo levantados, grano) ----------
def grade(x):
    x = x.astype(np.float32) / 255
    x = 0.03 + 0.95 * x                                   # negros apenas levantados
    x = x ** np.array([0.97, 0.99, 1.03], np.float32)     # leve calidez
    l = x.mean(axis=2, keepdims=True); x = l + (x - l) * 0.94
    return x
_yy, _xx = np.mgrid[0:H, 0:W]; _rr = (((_xx - W / 2) / (W / 2)) ** 2 + ((_yy - H / 2) / (H / 2)) ** 2) / 2
VIG = (1 - 0.18 * _rr ** 1.6)[..., None].astype(np.float32)
grng = np.random.default_rng(3)
def finish(x):
    x = x * VIG
    g = grng.normal(0, 0.012, (H // 2, W // 2, 1)).astype(np.float32).repeat(2, 0).repeat(2, 1)
    return Image.fromarray((np.clip(x + g, 0, 1) * 255).astype(np.uint8))

def load_photo(name):
    im = ImageOps.exif_transpose(Image.open(U + '/' + name)).convert('RGB')
    for b in PLATES.get(name, []):
        reg = im.crop(b); w, h = reg.size
        im.paste(reg.resize((max(1, w // 14), max(1, h // 6)), Image.BILINEAR).resize((w, h), Image.NEAREST).filter(ImageFilter.GaussianBlur(3)), b[:2])
    k = min(1.0, 2600 / max(im.size))
    if k < 1: im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    return im

def photo_frames(name, prm, n, g0):
    cx, cy, z0, z1, dx = prm
    im = load_photo(name); iw, ih = im.size
    bw, bh = (ih * 9 / 16, ih) if iw / ih > 9 / 16 else (iw, iw * 16 / 9)
    for j in range(n):
        u = j / max(1, n - 1); e = u * u * (3 - 2 * u) * 0.6 + u * 0.4
        z = z0 * (z1 / z0) ** e
        w, h = bw / z, bh / z
        x = cx * iw + dx * iw * (e - 0.5) + SX[g0 + j] * w / W; y = cy * ih + SY[g0 + j] * h / H
        x = min(max(x, w / 2), iw - w / 2); y = min(max(y, h / 2), ih - h / 2)
        fr = im.resize((W, H), Image.BICUBIC, box=(x - w / 2, y - h / 2, x + w / 2, y + h / 2))
        if SR[g0 + j]: fr = fr.rotate(SR[g0 + j], Image.BICUBIC, expand=False, center=(W / 2, H / 2), fillcolor=None)
        yield np.asarray(fr)

def video_frames(name, prm, n):
    t_in, cx = prm
    vf = f'fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H}'
    p = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t_in:.3f}', '-i', U + '/' + name, '-frames:v', str(n), '-vf', vf,
                        '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    fr = np.frombuffer(p, np.uint8).reshape(-1, H, W, 3)
    if len(fr) < n: fr = np.concatenate([fr, np.repeat(fr[-1:], n - len(fr), 0)])
    for f in fr[:n]: yield f

# ---------- rótulos ----------
def fade(t, t0, d=0.25): return min(max((t - t0) / d, 0), 1)
F_HEAD = font(INTER, 66, 750); F_CHIP = font(ANTON, 46); F_NAME = font(ANTON, 92)
def shadow_text(layer, xy, text, f, fill, a):
    d = ImageDraw.Draw(layer); d.text(xy, text, font=f, fill=(*fill, int(255 * a)))
def overlay(img, t, t0, t1, chip, head, name):
    a_in = fade(t, t0 + 0.08, 0.2); a_out = 1 - fade(t, t1 - 0.12, 0.12); a = a_in * a_out
    if a <= 0: return img
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    if chip:
        tw = d.textlength(chip, font=F_CHIP); x, y = 64, 150 - 10 * (1 - a_in)
        d.rounded_rectangle((x, y, x + tw + 44, y + 74), 10, fill=(*GOLD, int(235 * a)))
        d.text((x + 22, y + 6), chip, font=F_CHIP, fill=(*INK, int(255 * a)))
    if head:
        tw = d.textlength(head, font=F_HEAD); y = 1180 + 16 * (1 - a_in)
        d.text(((W - tw) / 2, y), head, font=F_HEAD, fill=(255, 255, 255, int(255 * a)))
    if name:
        tx = name.upper(); tw = d.textlength(tx, font=F_NAME); y = 1500 + 20 * (1 - a_in)
        d.line(((W - 120) / 2, y - 26, (W + 120) / 2, y - 26), fill=(*GOLD, int(255 * a)), width=5)
        d.text(((W - tw) / 2, y), tx, font=F_NAME, fill=(*CREAM, int(255 * a)))
    sh = layer.split()[3].filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.GaussianBlur(16)).point(lambda p: min(255, int(p * 0.95)))
    img.paste((0, 0, 0), (0, 4), sh); img.paste(layer, (0, 0), layer); return img

logo = Image.open(LOGO).convert('RGB'); la = np.asarray(logo).astype(int); ys, xs = np.nonzero(la.min(axis=2) < 225)
cx0, cy0 = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2; rr = min(xs.max() - xs.min(), ys.max() - ys.min()) / 2 - 3
bx = (int(cx0 - rr), int(cy0 - rr), int(cx0 + rr), int(cy0 + rr)); logo_c = logo.crop(bx)
lm = Image.new('L', logo.size, 0); ImageDraw.Draw(lm).ellipse((cx0 - rr, cy0 - rr, cx0 + rr, cy0 + rr), fill=255); lm_c = lm.crop(bx).filter(ImageFilter.GaussianBlur(1))
def end_card(bg, u):
    a0 = fade(u, 0, 0.35)
    im = Image.blend(bg, Image.new('RGB', (W, H), (14, 11, 9)), 0.9 * a0)
    s = 1.0 if u > 0.4 else 0.9 + 0.1 * (1 - math.exp(-u / 0.07))
    size = int(480 * s); L = logo_c.resize((size, size), Image.LANCZOS); M = lm_c.resize((size, size), Image.LANCZOS).point(lambda p: int(p * a0))
    im.paste(L, ((W - size) // 2, 580 - (size - 480) // 2), M)
    d = ImageDraw.Draw(im, 'RGBA'); f = font(ANTON, 92); tx = 'SANTO PISTÓN GARAGE'; a = fade(u, BEAT * 0.5, 0.2)
    d.text(((W - d.textlength(tx, font=f)) / 2, 1110 + 18 * (1 - a)), tx, font=f, fill=(*CREAM, int(255 * a)))
    f = font(INTER, 46, 600)
    for k, tx in enumerate(['¿Tienes una clásica para restaurar?', 'Escríbenos.']):
        a = fade(u, BEAT * (1.2 + 0.8 * k), 0.2)
        d.text(((W - d.textlength(tx, font=f)) / 2, 1245 + k * 66 + 14 * (1 - a)), tx, font=f, fill=(*(GOLD if k else CREAM), int(255 * a)))
    return im

def shot_iter(k):
    kind, src, beats, prm, chip, head, name = PLAN[k]
    n = fi(starts[k + 1]) - fi(starts[k])
    return n, (photo_frames(src, prm, n, fi(starts[k])) if kind == 'foto' else video_frames(src, prm, n))

if CHECK:
    ims = []
    for k in range(len(PLAN)):
        n, it = shot_iter(k); frs = list(it)
        for j in (0, n - 1):
            t = (fi(starts[k]) + j) / FPS
            img = overlay(finish(grade(frs[j])), t if j else starts[k] + 0.5, starts[k], starts[k + 1], *PLAN[k][4:])
            ims.append(img.resize((180, 320)))
    cols = 10; sheet = Image.new('RGB', (cols * 180, math.ceil(len(ims) / cols) * 320))
    for i, im in enumerate(ims): sheet.paste(im, ((i % cols) * 180, (i // cols) * 320))
    sheet.save(S + '/own/check.jpg', quality=85); print('check', round(DUR, 2)); sys.exit()

# ---------- audio: música + sonido real del spray ----------
MUSIC = S + '/music/Funk_Game_Loop.mp3'
k_spray = [i for i, p in enumerate(PLAN) if p[1] == '56363c4d-IMG_6588.mov'][0]
t_spray = starts[k_spray]; spray_in = PLAN[k_spray][3][0]; spray_len = PLAN[k_spray][2] * BEAT
out = OUT + '/santo_piston_restauraciones_1080x1920.mp4'
af = ('[1:a]atrim=0.22,asetpts=PTS-STARTPTS,volume=0.75,afade=t=in:st=0:d=0.05,afade=t=out:st=%.3f:d=1.6[m];'
      '[2:a]atrim=%.3f:%.3f,asetpts=PTS-STARTPTS,volume=0.55,afade=t=in:d=0.05,afade=t=out:st=%.3f:d=0.15,adelay=%d|%d[s];'
      '[m][s]amix=inputs=2:normalize=0,alimiter=limit=0.95,loudnorm=I=-14:TP=-1.5:LRA=11[a]') % (
      DUR - 1.6, spray_in, spray_in + spray_len, spray_len - 0.15, int(t_spray * 1000), int(t_spray * 1000))
ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                       '-i', MUSIC, '-i', U + '/56363c4d-IMG_6588.mov', '-filter_complex', af, '-map', '0:v', '-map', '[a]',
                       '-c:v', 'libx264', '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-crf', '19', '-maxrate', '14M', '-bufsize', '28M', '-preset', 'slow',
                       '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-t', '%.3f' % DUR, '-movflags', '+faststart', out], stdin=subprocess.PIPE)
last = None
for k in range(len(PLAN)):
    n, it = shot_iter(k); t0, t1 = starts[k], starts[k + 1]
    for j, fr in enumerate(it):
        t = (fi(t0) + j) / FPS
        base = finish(grade(fr)); img = overlay(base.copy(), t, t0, t1, *PLAN[k][4:])
        ff.stdin.write(img.tobytes()); last = base
        if j == n // 2: img.resize((360, 640)).save(S + f'/own/chk_{k:02d}.jpg')
n_end = fi(DUR) - fi(starts[-1])
for j in range(n_end):
    img = end_card(last, j / FPS); ff.stdin.write(img.tobytes())
img.resize((360, 640)).save(S + '/own/chk_99.jpg')
ff.stdin.close(); ff.wait()

# ---------- portada: antes / después de la Vespa ----------
a = next(photo_frames('afc80896-image.jpg', (0.42, 0.56, 1.3, 1.3, 0), 1, 0)); b = next(photo_frames('096c17d4-image.jpg', (0.40, 0.56, 1.3, 1.3, 0), 1, 0))
A = finish(grade(a)); B = finish(grade(b))
cov = Image.new('RGB', (W, H)); cov.paste(A.crop((W // 4, 0, 3 * W // 4, H)), (0, 0)); cov.paste(B.crop((W // 4, 0, 3 * W // 4, H)), (W // 2, 0))
d = ImageDraw.Draw(cov); d.rectangle((W // 2 - 3, 0, W // 2 + 3, H), fill=CREAM)
for tx, x in (('ANTES', 64), ('DESPUÉS', W // 2 + 40)):
    tw = d.textlength(tx, font=F_CHIP); d.rounded_rectangle((x, 150, x + tw + 44, 224), 10, fill=GOLD); d.text((x + 22, 156), tx, font=F_CHIP, fill=INK)
g = Image.new('L', (1, 256)); g.putdata([int(min(255, max(0, (i - 60) * 1.6))) for i in range(256)])
cov.paste(Image.new('RGB', (W, 700), (14, 11, 9)), (0, H - 700), g.resize((W, 700)))
cov.paste(logo_c.resize((300, 300), Image.LANCZOS), (390, 1180), lm_c.resize((300, 300), Image.LANCZOS))
d = ImageDraw.Draw(cov); f = font(ANTON, 100); tx = 'SANTO PISTÓN GARAGE'
d.text(((W - d.textlength(tx, font=f)) / 2, 1500), tx, font=f, fill=(255, 255, 255))
f = font(INTER, 44, 600); tx = 'Nuestras restauraciones'
d.text(((W - d.textlength(tx, font=f)) / 2, 1630), tx, font=f, fill=GOLD)
cov.save(OUT + '/portada_restauraciones.jpg', quality=93)
print('ok', round(DUR, 2))
