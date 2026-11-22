"""Montaje del recorrido 3D tipo inmobiliaria · 1080x1920 · 30 fps."""
import sys, subprocess, math, wave, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S, OUT, LOGO = sys.argv[1], sys.argv[2], sys.argv[3]
R = S + '/tour/render/'
W, H, FPS = 1080, 1920, 30
BEAT = 60 / 105
CREAM = (246, 241, 230); GOLD = (226, 179, 60); INK = (34, 29, 25); RED = (184, 53, 42)
INTER = S + '/fonts/Inter.ttf'; ANTON = S + '/fonts/Anton.ttf'

def font(path, size, wght=None):
    f = ImageFont.truetype(path, size)
    if wght:
        try: f.set_variation_by_axes([wght])
        except Exception: pass
    return f

# (plano renderizado, pulsos, rótulo principal, subrótulo, posición)
PLAN = [
    ('entrada', 7, 'SANTO PISTÓN GARAGE', 'Maresme · Barcelona', 'title'),
    ('banco', 5, 'Zona de trabajo', None, 'zone'),
    ('detalle', 3, None, None, None),
    ('scoopy', 5, 'Honda Scoopy 75', None, 'name'),
    ('galeria', 5, 'El proceso', None, 'zone'),
    ('enduro', 6, 'Montesa', None, 'name'),
    ('print', 3, 'Honda Scoopy 75', 'Dos unidades', 'name'),
    ('bultaco', 6, 'Bultaco Chispa', None, 'name'),
    ('cota', 4, 'Montesa', 'Recién llegada', 'name'),
    ('final', 6, None, None, None),
]
END_BEATS = 3
starts = np.cumsum([0] + [b for _, b, *_ in PLAN]) * BEAT
DUR = starts[-1] + END_BEATS * BEAT

def shot_frames(name, n):
    """Interpola el plano de 10 a 30 fps, escala a 1080x1920 y devuelve n fotogramas."""
    tmp = S + f'/tour/{name}_30.mp4'
    if not os.path.exists(tmp):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '10', '-i', R + name + '/%04d.jpg',
                        '-vf', 'minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,scale=1080:1920:flags=lanczos,unsharp=5:5:0.6',
                        '-c:v', 'libx264', '-crf', '14', '-pix_fmt', 'yuv420p', tmp], check=True)
    p = subprocess.run(['ffmpeg', '-v', 'error', '-i', tmp, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    fr = np.frombuffer(p, np.uint8).reshape(-1, H, W, 3)
    if len(fr) < n:  # rellenar con el último si faltara
        fr = np.concatenate([fr, np.repeat(fr[-1:], n - len(fr), 0)])
    # usar el tramo central del plano para que el movimiento no arranque ni frene en seco
    off = (len(fr) - n) // 2
    return fr[off:off + n]

F_TITLE = font(ANTON, 104); F_TSUB = font(INTER, 40, 500)
F_ZONE = font(INTER, 34, 600); F_CAP = font(INTER, 60, 700); F_SUB = font(INTER, 40, 500)

def fade(t, t0, d=0.3): return min(max((t - t0) / d, 0), 1)

def overlay(img, kind, text, sub, t, t0, t1):
    if not kind: return img
    a = fade(t, t0 + 0.15) * (1 - fade(t, t1 - 0.25, 0.25))
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    if kind == 'title':
        y = 1240; tw = d.textlength(text, font=F_TITLE)
        d.text(((W - tw) / 2, y + 16 * (1 - a)), text, font=F_TITLE, fill=(255, 255, 255, int(255 * a)))
        sw = d.textlength(sub, font=F_TSUB); d.text(((W - sw) / 2, y + 128), sub, font=F_TSUB, fill=(*CREAM, int(240 * a)))
        d.line(((W - 120) / 2, y + 112, (W + 120) / 2, y + 112), fill=(*GOLD, int(255 * a)), width=4)
    elif kind == 'zone':   # etiqueta de estancia, arriba a la izquierda (dentro de la zona segura)
        tx = text.upper(); tw = d.textlength(tx, font=F_ZONE)
        d.rounded_rectangle((70, 290, 70 + tw + 56, 352), 31, fill=(30, 26, 22, int(170 * a)))
        d.ellipse((92, 314, 106, 328), fill=(*GOLD, int(255 * a)))
        d.text((118, 300), tx, font=F_ZONE, fill=(255, 255, 255, int(255 * a)))
    else:                  # nombre de la moto abajo
        y = 1310; tw = d.textlength(text, font=F_CAP); bw = max(tw, d.textlength(sub, font=F_SUB) if sub else 0) + 64
        d.rounded_rectangle(((W - bw) / 2, y - 14, (W + bw) / 2, y + (140 if sub else 86)), 26, fill=(30, 26, 22, int(160 * a)))
        d.text(((W - tw) / 2, y), text, font=F_CAP, fill=(255, 255, 255, int(255 * a)))
        if sub:
            sw = d.textlength(sub, font=F_SUB); d.text(((W - sw) / 2, y + 80), sub, font=F_SUB, fill=(*CREAM, int(235 * a)))
    sh = layer.split()[3].filter(ImageFilter.GaussianBlur(6)).point(lambda p: int(p * 0.35))
    img.paste((0, 0, 0), (0, 3), sh); img.paste(layer, (0, 0), layer)
    return img

# logotipo recortado en disco
logo = Image.open(LOGO).convert('RGB'); la = np.asarray(logo).astype(int); ys, xs = np.nonzero(la.min(axis=2) < 225)
cx0, cy0 = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2; rr = min(xs.max() - xs.min(), ys.max() - ys.min()) / 2 - 3
box = (int(cx0 - rr), int(cy0 - rr), int(cx0 + rr), int(cy0 + rr)); logo_c = logo.crop(box)
lm = Image.new('L', logo.size, 0); ImageDraw.Draw(lm).ellipse((cx0 - rr, cy0 - rr, cx0 + rr, cy0 + rr), fill=255); lm_c = lm.crop(box).filter(ImageFilter.GaussianBlur(1))

def end_card(bg, u):
    """bg: último fotograma del recorrido; u: segundos desde el inicio de la tarjeta."""
    a0 = fade(u, 0, 0.35)
    im = Image.blend(bg, Image.new('RGB', (W, H), (243, 238, 228)), 0.93 * a0)
    s = 1.0 if u > 0.4 else 0.9 + 0.1 * (1 - math.exp(-u / 0.07))
    size = int(500 * s); L = logo_c.resize((size, size), Image.LANCZOS); M = lm_c.resize((size, size), Image.LANCZOS).point(lambda p: int(p * a0))
    im.paste(L, ((W - size) // 2, 560 - (size - 500) // 2), M)
    d = ImageDraw.Draw(im, 'RGBA'); f = font(ANTON, 92); tx = 'SANTO PISTÓN GARAGE'; a = fade(u, BEAT * 0.5, 0.2)
    d.text(((W - d.textlength(tx, font=f)) / 2, 1110 + 18 * (1 - a)), tx, font=f, fill=(*INK, int(255 * a)))
    f = font(INTER, 46, 600)
    for k, tx in enumerate(['¿Tienes una clásica para restaurar?', 'Escríbenos.']):
        a = fade(u, BEAT * (1.2 + 0.8 * k), 0.2)
        d.text(((W - d.textlength(tx, font=f)) / 2, 1245 + k * 66 + 14 * (1 - a)), tx, font=f, fill=(*(RED if k else INK), int(255 * a)))
    return im

# ---------- audio ----------
SR = 48000; rng = np.random.default_rng(3)
fx = np.zeros(int(DUR * SR) + SR)
def add(t, sig, g): k = int(t * SR); fx[k:k + len(sig)] += sig[:len(fx) - k] * g
def click():
    n = int(0.03 * SR); return rng.normal(0, 1, n) * np.exp(-np.arange(n) / (0.003 * SR))
def drawer():
    n = int(0.35 * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * 85 * tt) * np.exp(-tt / 0.06) + sum(np.sin(2 * np.pi * f * tt) for f in (1240, 1873, 2611)) * np.exp(-tt / 0.12) * 0.15
def ratchet():
    out = np.zeros(int(0.5 * SR))
    for k in range(9): c = click() * 0.6; s = int(k * 0.05 * SR); out[s:s + len(c)] += c
    return out
add(starts[1], drawer(), 0.28); add(starts[2], ratchet(), 0.2); add(starts[4], click(), 0.3); add(starts[-1], drawer(), 0.22)
fx += np.convolve(rng.normal(0, 1, len(fx)), np.ones(400) / 400, 'same') * 0.04
with wave.open(S + '/tour/fx.wav', 'w') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(fx, -1, 1) * 30000).astype('<i2').tobytes())

MUSIC = S + '/music/Funk_Game_Loop.mp3'
out = OUT + '/santo_piston_garaje_recorrido_1080x1920.mp4'
af = ('[1:a]atrim=0.22,asetpts=PTS-STARTPTS,volume=0.8,afade=t=in:st=0:d=0.05,afade=t=out:st=%.3f:d=1.6[m];'
      '[2:a]volume=1.0[f];[m][f]amix=inputs=2:normalize=0,alimiter=limit=0.95,loudnorm=I=-14:TP=-1.5:LRA=11[a]') % (DUR - 1.6)
ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                       '-i', MUSIC, '-i', S + '/tour/fx.wav', '-filter_complex', af, '-map', '0:v', '-map', '[a]',
                       '-c:v', 'libx264', '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'slow',
                       '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-t', '%.3f' % DUR, '-movflags', '+faststart', out], stdin=subprocess.PIPE)
fi = 0; last = None; checks = []
for k, (name, beats, text, sub, kind) in enumerate(PLAN):
    t0, t1 = starts[k], starts[k + 1]
    n = int(round(t1 * FPS)) - int(round(t0 * FPS))
    frames = shot_frames(name, n)
    for j in range(n):
        t = (int(round(t0 * FPS)) + j) / FPS
        img = overlay(Image.fromarray(frames[j]), kind, text, sub, t, t0, t1)
        ff.stdin.write(img.tobytes()); last = Image.fromarray(frames[j])
        if j == n // 2: img.resize((270, 480)).save(S + f'/tour/chk_{k:02d}.jpg')
n_end = int(round(DUR * FPS)) - int(round(starts[-1] * FPS))
for j in range(n_end):
    img = end_card(last, j / FPS); ff.stdin.write(img.tobytes())
img.resize((270, 480)).save(S + '/tour/chk_99.jpg')
ff.stdin.close(); ff.wait()

# portada
cov = Image.open(R + 'bultaco/0015.jpg').convert('RGB').resize((W, H), Image.LANCZOS)
d = ImageDraw.Draw(cov, 'RGBA'); d.rectangle((0, 0, W, H), fill=(14, 12, 10, 70))
L = logo_c.resize((460, 460), Image.LANCZOS); cov.paste(L, (310, 360), lm_c.resize((460, 460), Image.LANCZOS))
d = ImageDraw.Draw(cov); f = font(ANTON, 92); tx = 'SANTO PISTÓN GARAGE'
d.text(((W - d.textlength(tx, font=f)) / 2, 880), tx, font=f, fill=(255, 255, 255), stroke_width=2, stroke_fill=(30, 26, 22))
f = font(INTER, 42, 600); tx = 'Visita el garaje'
d.text(((W - d.textlength(tx, font=f)) / 2, 1000), tx, font=f, fill=GOLD, stroke_width=2, stroke_fill=(30, 26, 22))
cov.save(OUT + '/portada_garaje_recorrido.jpg', quality=93)
print('ok', round(DUR, 2))
