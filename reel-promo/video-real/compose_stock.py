"""Reel con vídeo real de stock (Mixkit, licencia libre) · 1080x1920 · 23,976 fps.
Uso: python3 compose_stock.py <scratchpad> <carpeta_salida> <logo> [check]"""
import sys, subprocess, math, wave, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S, OUT, LOGO = sys.argv[1], sys.argv[2], sys.argv[3]
CHECK = len(sys.argv) > 4 and sys.argv[4] == 'check'
C = S + '/stock/clips/'
W, H = 1080, 1920; FPS = 24000 / 1001
BEAT = 60 / 105
CREAM = (246, 241, 230); GOLD = (226, 179, 60)
INTER = S + '/fonts/Inter.ttf'; ANTON = S + '/fonts/Anton.ttf'
def font(path, size, wght=None):
    f = ImageFont.truetype(path, size)
    if wght:
        try: f.set_variation_by_axes([wght])
        except Exception: pass
    return f

# (clip, inicio en el clip (s), centro horizontal del recorte (0-1), pulsos, texto)
PLAN = [
    (41927, 1.2, 0.56, 5, 'Motos clásicas'),
    (41926, 4.4, 0.50, 4, None),
    (41928, 1.0, 0.55, 4, 'Mecánica de verdad'),
    (41933, 11.0, 0.45, 5, None),
    (41929, 5.6, 0.50, 4, None),
    (41934, 3.0, 0.42, 3, None),
    (41935, 2.0, 0.45, 3, None),
    (41937, 1.6, 0.50, 4, None),
    (41943, 2.2, 0.55, 5, 'Puesta a punto'),
    (41944, 2.6, 0.40, 6, 'Cada detalle cuenta'),
    (41939, 6.0, 0.55, 4, None),
]
END_BEATS = 5
starts = np.cumsum([0] + [p[3] for p in PLAN]) * BEAT
DUR = starts[-1] + END_BEATS * BEAT
fi = lambda t: int(round(t * FPS))

def clip_frames(cid, t_in, cx, n):
    """Recorte vertical 9:16 del 4K, escalado a 1080x1920 con un empuje de cámara muy leve."""
    src = C + f'{cid}.mp4'
    cw = 1215; x0 = int(min(max(cx * 3840 - cw / 2, 0), 3840 - cw))
    vf = f'crop={cw}:2160:{x0}:0,scale={W}:{H}:flags=lanczos,eq=contrast=1.04:saturation=0.95'
    p = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t_in:.3f}', '-i', src, '-frames:v', str(n), '-vf', vf,
                        '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    fr = np.frombuffer(p, np.uint8).reshape(-1, H, W, 3)
    if len(fr) < n: fr = np.concatenate([fr, np.repeat(fr[-1:], n - len(fr), 0)])
    return fr

F_TXT = font(INTER, 64, 700)
def fade(t, t0, d=0.3): return min(max((t - t0) / d, 0), 1)
def caption(img, text, t, t0, t1):
    if not text: return img
    a = fade(t, t0 + 0.15) * (1 - fade(t, t1 - 0.25, 0.25))
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    tw = d.textlength(text, font=F_TXT); y = 1180
    d.text(((W - tw) / 2, y), text, font=F_TXT, fill=(255, 255, 255, int(255 * a)))
    sh = layer.split()[3].filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(14)).point(lambda p: min(255, int(p * 1.1)))
    img.paste((0, 0, 0), (0, 3), sh); img.paste(layer, (0, 0), layer); return img

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

if CHECK:
    ims = []
    for k, (cid, t_in, cx, beats, text) in enumerate(PLAN):
        n = fi(starts[k + 1]) - fi(starts[k])
        fr = clip_frames(cid, t_in, cx, n)
        for j in (0, n // 2, n - 1):
            ims.append(Image.fromarray(fr[j]).resize((180, 320)))
    cols = 9; rows = math.ceil(len(ims) / cols); sheet = Image.new('RGB', (cols * 180, rows * 320))
    for i, im in enumerate(ims): sheet.paste(im, ((i % cols) * 180, (i // cols) * 320))
    sheet.save(S + '/stock/check.jpg', quality=85); print('check', len(PLAN)); sys.exit()

# ---- audio: música + ambiente de taller ----
SR_ = 48000; arng = np.random.default_rng(3)
fx = np.zeros(int(DUR * SR_) + SR_)
fx += np.convolve(arng.normal(0, 1, len(fx)), np.ones(400) / 400, 'same') * 0.04
with wave.open(S + '/stock/fx.wav', 'w') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR_); w.writeframes((np.clip(fx, -1, 1) * 30000).astype('<i2').tobytes())
MUSIC = S + '/music/Funk_Game_Loop.mp3'
out = OUT + '/santo_piston_taller_video_real_1080x1920.mp4'
af = ('[1:a]atrim=0.22,asetpts=PTS-STARTPTS,volume=0.75,afade=t=in:st=0:d=0.05,afade=t=out:st=%.3f:d=1.6[m];'
      '[2:a]volume=1.0[f];[m][f]amix=inputs=2:normalize=0,alimiter=limit=0.95,loudnorm=I=-14:TP=-1.5:LRA=11[a]') % (DUR - 1.6)
ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '24000/1001', '-i', '-',
                       '-i', MUSIC, '-i', S + '/stock/fx.wav', '-filter_complex', af, '-map', '0:v', '-map', '[a]',
                       '-c:v', 'libx264', '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-crf', '19', '-maxrate', '14M', '-bufsize', '28M', '-preset', 'slow',
                       '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-t', '%.3f' % DUR, '-movflags', '+faststart', out], stdin=subprocess.PIPE)
last = None; cover_src = None
for k, (cid, t_in, cx, beats, text) in enumerate(PLAN):
    t0, t1 = starts[k], starts[k + 1]
    n = fi(t1) - fi(t0)
    frames = clip_frames(cid, t_in, cx, n)
    for j in range(n):
        t = (fi(t0) + j) / FPS
        base = Image.fromarray(frames[j])
        img = caption(base.copy(), text, t, t0, t1)
        ff.stdin.write(img.tobytes()); last = base
        if j == n // 2:
            img.resize((360, 640)).save(S + f'/stock/chk_{k:02d}.jpg')
            if cid == 41944: cover_src = base
n_end = fi(DUR) - fi(starts[-1])
for j in range(n_end):
    img = end_card(last, j / FPS); ff.stdin.write(img.tobytes())
img.resize((360, 640)).save(S + '/stock/chk_99.jpg')
ff.stdin.close(); ff.wait()

# portada
cov = Image.fromarray(clip_frames(41944, 7.0, 0.40, 1)[0])
g = Image.new('L', (1, 256)); g.putdata([int(min(255, max(0, (i - 60) * 1.6))) for i in range(256)])
band = Image.new('RGB', (W, 700), (14, 11, 9)); cov.paste(band, (0, H - 700), g.resize((W, 700)))
L = logo_c.resize((300, 300), Image.LANCZOS); cov.paste(L, (390, 1180), lm_c.resize((300, 300), Image.LANCZOS))
d = ImageDraw.Draw(cov); f = font(ANTON, 100); tx = 'SANTO PISTÓN GARAGE'
d.text(((W - d.textlength(tx, font=f)) / 2, 1500), tx, font=f, fill=(255, 255, 255))
f = font(INTER, 44, 600); tx = 'Motos clásicas · Mecánica de verdad'
d.text(((W - d.textlength(tx, font=f)) / 2, 1630), tx, font=f, fill=GOLD)
cov.save(OUT + '/portada_taller_video_real.jpg', quality=93)
print('ok', round(DUR, 2))
