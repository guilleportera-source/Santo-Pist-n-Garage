"""Montaje del taller realista, aspecto de vídeo grabado con el móvil · 1080x1920 · 30 fps."""
import sys, subprocess, math, wave, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S, OUT, LOGO = sys.argv[1], sys.argv[2], sys.argv[3]
R = S + '/tour/render_real/'
W, H, FPS = 1080, 1920, 30
BEAT = 60 / 105
CREAM = (246, 241, 230); GOLD = (226, 179, 60)
INTER = S + '/fonts/Inter.ttf'; ANTON = S + '/fonts/Anton.ttf'
def font(path, size, wght=None):
    f = ImageFont.truetype(path, size)
    if wght:
        try: f.set_variation_by_axes([wght])
        except Exception: pass
    return f

# (plano, pulsos, texto)
PLAN = [
    ('entrada', 7, 'POV: entras en Santo Pistón Garage'),
    ('banco', 6, 'La zona de trabajo'),
    ('herramientas', 6, None),
    ('tornillo', 4, None),
    ('banco_detalle', 5, None),
    ('carro', 5, None),
    ('carteles', 5, 'Chapas de época'),
    ('coleccion', 5, None),
    ('fondo', 4, None),
    ('final', 3, None),
]
END_BEATS = 3
starts = np.cumsum([0] + [b for _, b, _ in PLAN]) * BEAT
DUR = starts[-1] + END_BEATS * BEAT

def shot_frames(name, n):
    tmp = S + f'/tour/{name}_real30.mp4'
    if not os.path.exists(tmp):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '10', '-i', R + name + '/%04d.jpg',
                        '-vf', 'minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,scale=1152:2048:flags=lanczos',
                        '-c:v', 'libx264', '-crf', '12', '-pix_fmt', 'yuv420p', tmp], check=True)
    p = subprocess.run(['ffmpeg', '-v', 'error', '-i', tmp, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    fr = np.frombuffer(p, np.uint8).reshape(-1, 2048, 1152, 3)
    if len(fr) < n: fr = np.concatenate([fr, np.repeat(fr[-1:], n - len(fr), 0)])
    off = (len(fr) - n) // 2
    return fr[off:off + n]

# ---- temblor de mano: ruido suave a varias frecuencias (reproducible) ----
rng = np.random.default_rng(21)
NF = int(DUR * FPS) + 10
def smooth_noise(n, sigma):
    x = rng.normal(0, 1, n + 200); k = np.exp(-0.5 * (np.arange(-60, 61) / sigma) ** 2); k /= k.sum()
    y = np.convolve(x, k, 'same')[100:100 + n]; return y / (y.std() + 1e-9)
SX = smooth_noise(NF, 9) * 7 + smooth_noise(NF, 2.5) * 1.6
SY = smooth_noise(NF, 9) * 6 + smooth_noise(NF, 2.5) * 1.4
SR = smooth_noise(NF, 12) * 0.28 + smooth_noise(NF, 3) * 0.06
AE = 1 + smooth_noise(NF, 40) * 0.025

_yy, _xx = np.mgrid[0:H, 0:W]; _rr = (((_xx - W / 2) / (W / 2)) ** 2 + ((_yy - H / 2) / (H / 2)) ** 2) / 2
VIG = (1 - 0.16 * _rr ** 1.5)[..., None].astype(np.float32)
def phone(fr, fi):
    """Encuadre con temblor, nitidez y ruido de cámara de móvil."""
    im = Image.fromarray(fr)   # 1152x2048 (6,7 % de margen)
    ang = math.radians(SR[fi]); ca, sa = math.cos(ang), math.sin(ang)
    cx, cy = 1152 / 2 + SX[fi], 2048 / 2 + SY[fi]
    s = 1.0   # recorte de 1080x1920 dentro del fotograma de 1152x2048: margen para el temblor
    a, b = ca * s, -sa * s; d, e = sa * s, ca * s
    c = cx - a * W / 2 - b * H / 2; f = cy - d * W / 2 - e * H / 2
    im = im.transform((W, H), Image.AFFINE, (a, b, c, d, e, f), Image.BICUBIC)
    im = im.filter(ImageFilter.UnsharpMask(radius=1.6, percent=70, threshold=2))
    # aberración cromática lateral leve (lente de móvil): rojo un pelo más grande, azul un pelo más pequeño
    r_, g_, b_ = im.split()
    def _sc(ch, k):
        w2, h2 = int(W * k), int(H * k); c2 = ch.resize((w2, h2), Image.BICUBIC)
        return c2.crop(((w2 - W) // 2, (h2 - H) // 2, (w2 - W) // 2 + W, (h2 - H) // 2 + H))
    im = Image.merge('RGB', (_sc(r_, 1.0024), _sc(g_, 1.0012), b_))
    x = np.asarray(im).astype(np.float32)
    # brillo difuso alrededor de los tubos y lámparas (bloom de sensor pequeño)
    hi = np.clip(x - 215, 0, None)
    hb = np.asarray(Image.fromarray(np.clip(hi * 4, 0, 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(9)).resize((W, H), Image.BILINEAR)).astype(np.float32)
    x = x + hb * 0.22
    x = x * VIG * AE[fi]                             # viñeteado suave y autoexposición que respira
    x = 255 * (np.clip(x / 255, 0, 1) ** 0.97)       # medios un poco más abiertos, como el HDR del móvil
    lum = rng.normal(0, 2.2, (H // 2, W // 2, 1)).repeat(2, 0).repeat(2, 1)
    return Image.fromarray(np.clip(x + lum, 0, 255).astype(np.uint8))

F_TXT = font(INTER, 50, 600)
def fade(t, t0, d=0.3): return min(max((t - t0) / d, 0), 1)
def caption(img, text, t, t0, t1):
    if not text: return img
    a = fade(t, t0 + 0.2) * (1 - fade(t, t1 - 0.3, 0.3))
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    tw = d.textlength(text, font=F_TXT); y = 1150
    d.text(((W - tw) / 2, y), text, font=F_TXT, fill=(255, 255, 255, int(255 * a)))
    sh = layer.split()[3].filter(ImageFilter.GaussianBlur(7)).point(lambda p: int(p * 0.55))
    img.paste((0, 0, 0), (0, 2), sh); img.paste(layer, (0, 0), layer); return img

logo = Image.open(LOGO).convert('RGB'); la = np.asarray(logo).astype(int); ys, xs = np.nonzero(la.min(axis=2) < 225)
cx0, cy0 = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2; rr = min(xs.max() - xs.min(), ys.max() - ys.min()) / 2 - 3
bx = (int(cx0 - rr), int(cy0 - rr), int(cx0 + rr), int(cy0 + rr)); logo_c = logo.crop(bx)
lm = Image.new('L', logo.size, 0); ImageDraw.Draw(lm).ellipse((cx0 - rr, cy0 - rr, cx0 + rr, cy0 + rr), fill=255); lm_c = lm.crop(bx).filter(ImageFilter.GaussianBlur(1))

def end_card(bg, u):
    a0 = fade(u, 0, 0.35)
    im = Image.blend(bg, Image.new('RGB', (W, H), (14, 11, 9)), 0.94 * a0)
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

# ---- audio: música + sonido de taller ----
SR_ = 48000; arng = np.random.default_rng(3)
fx = np.zeros(int(DUR * SR_) + SR_)
def add(t, sig, g): k = int(t * SR_); fx[k:k + len(sig)] += sig[:len(fx) - k] * g
def click():
    n = int(0.03 * SR_); return arng.normal(0, 1, n) * np.exp(-np.arange(n) / (0.003 * SR_))
def drawer():
    n = int(0.35 * SR_); tt = np.arange(n) / SR_
    return np.sin(2 * np.pi * 85 * tt) * np.exp(-tt / 0.06) + sum(np.sin(2 * np.pi * f * tt) for f in (1240, 1873, 2611)) * np.exp(-tt / 0.12) * 0.15
def ratchet():
    out = np.zeros(int(0.5 * SR_))
    for k in range(9): c = click() * 0.6; s = int(k * 0.05 * SR_); out[s:s + len(c)] += c
    return out
add(starts[1], drawer(), 0.25); add(starts[3], ratchet(), 0.22); add(starts[5], drawer(), 0.2); add(starts[-1], click(), 0.3)
fx += np.convolve(arng.normal(0, 1, len(fx)), np.ones(400) / 400, 'same') * 0.05   # ambiente de nave
with wave.open(S + '/tour/fx_real.wav', 'w') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR_); w.writeframes((np.clip(fx, -1, 1) * 30000).astype('<i2').tobytes())

MUSIC = S + '/music/Funk_Game_Loop.mp3'
out = OUT + '/santo_piston_taller_real_1080x1920.mp4'
af = ('[1:a]atrim=0.22,asetpts=PTS-STARTPTS,volume=0.75,afade=t=in:st=0:d=0.05,afade=t=out:st=%.3f:d=1.6[m];'
      '[2:a]volume=1.0[f];[m][f]amix=inputs=2:normalize=0,alimiter=limit=0.95,loudnorm=I=-14:TP=-1.5:LRA=11[a]') % (DUR - 1.6)
ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                       '-i', MUSIC, '-i', S + '/tour/fx_real.wav', '-filter_complex', af, '-map', '0:v', '-map', '[a]',
                       '-c:v', 'libx264', '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-crf', '20', '-maxrate', '13M', '-bufsize', '26M', '-preset', 'slow',
                       '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-t', '%.3f' % DUR, '-movflags', '+faststart', out], stdin=subprocess.PIPE)
last = None; gi = 0
for k, (name, beats, text) in enumerate(PLAN):
    t0, t1 = starts[k], starts[k + 1]
    n = int(round(t1 * FPS)) - int(round(t0 * FPS))
    frames = shot_frames(name, n)
    for j in range(n):
        t = (int(round(t0 * FPS)) + j) / FPS
        base = phone(frames[j], gi); gi += 1
        img = caption(base.copy(), text, t, t0, t1)
        ff.stdin.write(img.tobytes()); last = base
        if j == n // 2: img.resize((360, 640)).save(S + f'/tour/chkr_{k:02d}.jpg')
n_end = int(round(DUR * FPS)) - int(round(starts[-1] * FPS))
for j in range(n_end):
    img = end_card(last, j / FPS); ff.stdin.write(img.tobytes())
img.resize((360, 640)).save(S + '/tour/chkr_99.jpg')
ff.stdin.close(); ff.wait()

# portada: el banco de trabajo
cov = phone(shot_frames('banco', 40)[20], 0)
d = ImageDraw.Draw(cov, 'RGBA')
g = Image.new('L', (1, 256)); g.putdata([int(min(255, max(0, (i - 60) * 1.6))) for i in range(256)])
band = Image.new('RGB', (W, 700), (14, 11, 9)); cov.paste(band, (0, H - 700), g.resize((W, 700)))
L = logo_c.resize((300, 300), Image.LANCZOS); cov.paste(L, (390, 1180), lm_c.resize((300, 300), Image.LANCZOS))
d = ImageDraw.Draw(cov); f = font(ANTON, 100); tx = 'SANTO PISTÓN GARAGE'
d.text(((W - d.textlength(tx, font=f)) / 2, 1500), tx, font=f, fill=(255, 255, 255))
f = font(INTER, 44, 600); tx = 'Así es el taller'
d.text(((W - d.textlength(tx, font=f)) / 2, 1630), tx, font=f, fill=GOLD)
cov.save(OUT + '/portada_taller_real.jpg', quality=93)
print('ok', round(DUR, 2))
