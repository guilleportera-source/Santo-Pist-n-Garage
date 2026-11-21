"""Reel final Santo Pistón Garage · 1080x1920 · 30 fps · 35 s · estilo vídeo de móvil."""
import sys, subprocess, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

S, OUT, LOGO = sys.argv[1], sys.argv[2], sys.argv[3]
P = S + '/photos/'; G = S + '/gen/'; R = S + '/restored/'
W, H, FPS, DUR = 1080, 1920, 30, 50 * 60 / 105
CREAM = (246, 241, 230); GOLD = (226, 179, 60)
INTER = S + '/fonts/Inter.ttf'; ANTON = S + '/fonts/Anton.ttf'

def font(path, size, wght=None):
    f = ImageFont.truetype(path, size)
    if wght:
        try: f.set_variation_by_axes([wght])
        except Exception: pass
    return f

def photo(name): return Image.open(P + name + '.jpg').convert('RGB')

def gen(name):
    im = Image.open(G + name + '.jpg').convert('RGB')
    im = im.crop((0, 0, im.width, im.height - 46))           # fuera la marca de agua
    im = im.resize((im.width * 2, im.height * 2), Image.LANCZOS)
    im = im.filter(ImageFilter.UnsharpMask(2, 60, 2))
    return ImageEnhance.Color(im).enhance(1.05)

def crop(im, cx, cy, zoom, dx=0.0, dy=0.0, rot=0.0):
    iw, ih = im.size
    ch = ih / zoom; cw = ch * W / H
    if cw > iw / zoom: cw = iw / zoom; ch = cw * H / W
    x0 = min(max(cx * iw - cw / 2 + dx * cw, 0), iw - cw); y0 = min(max(cy * ih - ch / 2 + dy * ch, 0), ih - ch)
    OW, OH = int(W * 1.04), int(H * 1.04)
    out = im.resize((OW, OH), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))
    if rot: out = out.rotate(rot, Image.BICUBIC, expand=False)
    l, t = (OW - W) // 2, (OH - H) // 2
    return out.crop((l, t, l + W, t + H))

# temblor de mano suave y reproducible
rng = np.random.default_rng(7)
def smooth_noise(n, k):
    x = rng.normal(0, 1, n + 2 * k); w = np.hanning(2 * k + 1); w /= w.sum()
    return np.convolve(x, w, 'valid')[:n]
N = int(DUR * FPS)
SX, SY, SR = smooth_noise(N, 26) * 0.006, smooth_noise(N, 26) * 0.006, smooth_noise(N, 30) * 0.35

def ease(t): t = min(max(t, 0), 1); return t * t * (3 - 2 * t)

F_CAP = font(INTER, 60, 700); F_SUB = font(INTER, 40, 500); F_TAG = font(INTER, 30, 600)
def caption(img, text, sub=None, alpha=1.0, y=1310):
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    tw = d.textlength(text, font=F_CAP); x = (W - tw) / 2
    d.text((x, y), text, font=F_CAP, fill=(255, 255, 255, int(255 * alpha)))
    if sub:
        sw = d.textlength(sub, font=F_SUB); d.text(((W - sw) / 2, y + 80), sub, font=F_SUB, fill=(*CREAM, int(235 * alpha)))
    bw = max(tw, d.textlength(sub, font=F_SUB) if sub else 0) + 64
    pill = Image.new('RGBA', img.size, (0, 0, 0, 0)); pd = ImageDraw.Draw(pill)
    pd.rounded_rectangle(((W - bw) / 2, y - 14, (W + bw) / 2, y + (140 if sub else 86)), 26, fill=(30, 26, 22, int(160 * alpha)))
    img.paste(pill, (0, 0), pill)
    sh = layer.split()[3].filter(ImageFilter.GaussianBlur(5)).point(lambda p: int(p * 0.6))
    img.paste((0, 0, 0), (2, 3), sh)
    img.paste(layer, (0, 0), layer)

def small_tag(img, text, y=262):
    d = ImageDraw.Draw(img, 'RGBA'); tw = d.textlength(text, font=F_TAG)
    d.rounded_rectangle((900 - tw - 36, y, 900, y + 52), 26, fill=(30, 26, 22, 150))
    d.text((900 - tw - 18, y + 7), text, font=F_TAG, fill=(255, 255, 255, 235))

# ---------- material ----------
scoopy = photo('68c868d9c3e9643fd413ca0f0232a392'); escudo = photo('94a6e97d5c8f4b96940933b32e4e7690')
mt_tank = photo('69c3ef9505da637b71b6e910cbb3d7bb'); garage = photo('d2be5fb28b4f7c465cc707b65b7378ab')
endu = photo('fefa418530536a7638b7a25e2e4a8f3f'); fiat = photo('2f4234cc38b8a21d404d5f08a6ea597c')
ride = photo('31114f831e31734fb3782cf928c2eff4')
c_before = Image.open(R + 'cota_antes.jpg').convert('RGB'); c_after = Image.open(R + 'cota_despues_v2.jpg').convert('RGB')
logo = Image.open(LOGO).convert('RGB')
# máscara del logo a partir del propio disco (sin halo blanco)
la = np.asarray(logo).astype(int); nonwhite = (la.min(axis=2) < 225)
ys, xs = np.nonzero(nonwhite); cx0, cy0 = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
rr = min(xs.max() - xs.min(), ys.max() - ys.min()) / 2 - 3
lmask = Image.new('L', logo.size, 0); ImageDraw.Draw(lmask).ellipse((cx0 - rr, cy0 - rr, cx0 + rr, cy0 + rr), fill=255)
lmask = lmask.filter(ImageFilter.GaussianBlur(1.2))
logo_c = logo.crop((int(cx0 - rr), int(cy0 - rr), int(cx0 + rr), int(cy0 + rr))); lmask_c = lmask.crop((int(cx0 - rr), int(cy0 - rr), int(cx0 + rr), int(cy0 + rr)))

BADGE = dict(cx=0.585, cy=0.33, zoom=4.0)     # emblema del depósito
TANKW = dict(cx=0.572, cy=0.39)                # depósito entero

# mapa de pulsos: 105 BPM; la música arranca en el fotograma 0 con un pulso
BEAT = 60 / 105
def B(k): return k * BEAT
SHOTS = [  # (pulso de entrada, id)
    (0, 'before'), (2, 'after'), (4, 'garage'), (8, 'scoopy'), (15, 'escudo'), (17, 'mtank'), (20, 'mlift'),
    (24, 'enduA'), (27, 'enduB'), (30, 'llego'), (33, 'quedo'), (36, 'fiat'), (40, 'ride'), (44, 'end')]
STARTS = [B(k) for k, _ in SHOTS] + [DUR]
def which(t):
    for n in range(len(SHOTS)):
        if t < STARTS[n + 1]: return n
    return len(SHOTS) - 1
def fadein(t, t0): return min(max((t - t0 - 0.1) / 0.25, 0), 1)

CREAMBG = (243, 238, 228); INK = (34, 29, 25)
def end_card(t, t0):
    im = Image.new('RGB', (W, H), CREAMBG)
    u = t - t0
    s = 1.0 if u > 0.35 else 0.9 + 0.1 * (1 - math.exp(-u / 0.06)) * (1 + 0.04 * math.sin(u * 30) * math.exp(-u / 0.12))
    size = int(520 * s * (1 + 0.012 * u))
    L = logo_c.resize((size, size), Image.LANCZOS); M = lmask_c.resize((size, size), Image.LANCZOS)
    im.paste(L, ((W - size) // 2, 560 - (size - 520) // 2), M)
    d = ImageDraw.Draw(im, 'RGBA')
    f = font(ANTON, 92); tx = 'SANTO PISTÓN GARAGE'
    a = min(max((u - BEAT * 0.5) / 0.2, 0), 1)
    d.text(((W - d.textlength(tx, font=f)) / 2, 1130 + 20 * (1 - a)), tx, font=f, fill=(*INK, int(255 * a)))
    f = font(INTER, 46, 600)
    for k, tx in enumerate(['¿Tienes una clásica para restaurar?', 'Escríbenos.']):
        a = min(max((u - BEAT * (1.5 + k)) / 0.2, 0), 1)
        d.text(((W - d.textlength(tx, font=f)) / 2, 1265 + k * 66 + 14 * (1 - a)), tx, font=f, fill=(*((184, 53, 42) if k else INK), int(255 * a)))
    return im

def shot(t, i):
    n = which(t); sid = SHOTS[n][1]; t0, t1 = STARTS[n], STARTS[n + 1]
    u = (t - t0) / (t1 - t0); e = ease(u)
    j = dict(dx=SX[i], dy=SY[i], rot=SR[i])
    if sid == 'before': return crop(c_before, BADGE['cx'], BADGE['cy'], BADGE['zoom'] - 0.15 * u, **j)
    if sid == 'after':
        im = crop(c_after, BADGE['cx'], BADGE['cy'], BADGE['zoom'] - 0.15 * (1 + u), **j); small_tag(im, 'Recreación digital'); return im
    if sid == 'garage': return crop(garage, 0.30 + 0.25 * e, 0.42, 1.25 - 0.08 * u, **j)
    if sid == 'scoopy':
        im = crop(scoopy, 0.36 + 0.24 * e, 0.6, 1.22 - 0.04 * u, **j); caption(im, 'Honda Scoopy 75', 'Dos unidades', fadein(t, t0)); return im
    if sid == 'escudo':
        im = crop(escudo, 0.5, 0.42, 1.1 + 0.12 * u, **j); caption(im, 'Honda Scoopy 75'); return im
    if sid == 'mtank':
        im = crop(mt_tank, 0.55, 0.375, 1.9 - 0.3 * e, **j); caption(im, 'Montesa', alpha=fadein(t, t0)); return im
    if sid == 'mlift':
        im = crop(garage, 0.45, 0.55, 1.15 - 0.1 * e, **j); caption(im, 'Montesa'); return im
    if sid == 'enduA':
        im = crop(endu, 0.55, 0.40, 1.6 - 0.2 * e, **j); caption(im, 'Montesa', alpha=fadein(t, t0)); return im
    if sid == 'enduB':
        im = crop(endu, 0.46, 0.36, 1.15 + 0.06 * u, **j); caption(im, 'Montesa'); return im
    if sid == 'llego':
        im = crop(c_before, 0.6, 0.5, 1.0 + 0.06 * u, **j); caption(im, 'Montesa', 'Así llegó', fadein(t, t0)); return im
    if sid == 'quedo':
        im = crop(c_after, 0.572, 0.32, 3.0 - 0.1 * e, **j); caption(im, 'Montesa', 'Así quedó', y=380); small_tag(im, 'Recreación digital', y=560); return im
    if sid == 'fiat':
        im = crop(fiat, 0.45 + 0.1 * e, 0.5, 1.12 - 0.06 * u, **j); caption(im, 'Fiat 126', alpha=fadein(t, t0)); return im
    if sid == 'ride': return crop(ride, 0.55, 0.55, 1.15 - 0.1 * e, **j)
    return end_card(t, t0)

grain = [Image.fromarray(np.clip(rng.normal(128, 9, (H // 2, W // 2)), 0, 255).astype('uint8')).resize((W, H)) for _ in range(6)]
def finish(im, i):
    im = Image.blend(im, Image.merge('RGB', [grain[i % 6]] * 3), 0.035)  # grano de sensor de móvil
    return im

# ---------- audio ----------
SR_A = 48000
def tone_noise(n): return rng.normal(0, 1, n)
fx = np.zeros(int(DUR * SR_A))
def add(t, sig, g):
    k = int(t * SR_A); fx[k:k + len(sig)] += sig[:len(fx) - k] * g
def click():   # interruptor seco
    n = int(0.03 * SR_A); e = np.exp(-np.arange(n) / (0.003 * SR_A)); return tone_noise(n) * e
def drawer():  # cajón metálico que cierra
    n = int(0.35 * SR_A); tt = np.arange(n) / SR_A
    thud = np.sin(2 * np.pi * 85 * tt) * np.exp(-tt / 0.06)
    ring = sum(np.sin(2 * np.pi * f * tt) for f in (1240, 1873, 2611)) * np.exp(-tt / 0.12) * 0.15
    return thud + ring + tone_noise(n) * np.exp(-tt / 0.01) * 0.4
def ratchet():
    out = np.zeros(int(0.5 * SR_A))
    for k in range(9):
        c = click() * 0.6; s = int(k * 0.05 * SR_A); out[s:s + len(c)] += c
    return out
add(B(2) - 0.004, click(), 0.9); add(B(8), drawer(), 0.3); add(B(17), ratchet(), 0.22); add(B(33), click(), 0.45); add(B(44), drawer(), 0.25)
amb = np.convolve(tone_noise(len(fx)), np.ones(400) / 400, 'same') * 0.05      # aire del local
fx += amb
import wave
with wave.open(S + '/fx.wav', 'w') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR_A)
    w.writeframes((np.clip(fx, -1, 1) * 30000).astype('<i2').tobytes())

MUSIC = S + '/music/Funk_Game_Loop.mp3'
out = OUT + '/santo_piston_reel_1080x1920.mp4'
# música: entra en 1,4 s (tras el clic), fundido final de 2 s, por debajo de los efectos
afilter = ('[1:a]atrim=0.22,asetpts=PTS-STARTPTS,volume=0.85,afade=t=in:st=0:d=0.05,afade=t=out:st=%.3f:d=1.6[m];' % (DUR - 1.6) + ''
           '[2:a]volume=1.0[f];[m][f]amix=inputs=2:normalize=0,alimiter=limit=0.95,loudnorm=I=-14:TP=-1.5:LRA=11[a]')
ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                       '-i', MUSIC, '-i', S + '/fx.wav', '-filter_complex', afilter, '-map', '0:v', '-map', '[a]',
                       '-c:v', 'libx264', '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'slow',
                       '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-t', str(DUR), '-movflags', '+faststart', out], stdin=subprocess.PIPE)
checks = {int((STARTS[n] + STARTS[n + 1]) / 2 * FPS) for n in range(len(SHOTS))} | {int((DUR - 0.2) * FPS)}
for i in range(N):
    fr = finish(shot(i / FPS, i), i)
    ff.stdin.write(fr.tobytes())
    if i in checks: fr.resize((270, 480)).save(f'{S}/fc_{i:04d}.jpg')
ff.stdin.close(); ff.wait()

# portada
cov = crop(endu, 0.42, 0.42, 1.35); d = ImageDraw.Draw(cov, 'RGBA'); d.rectangle((0, 0, W, H), fill=(14, 12, 10, 90))
L = logo_c.resize((520, 520), Image.LANCZOS); cov.paste(L, (280, 440), lmask_c.resize((520, 520), Image.LANCZOS))
d = ImageDraw.Draw(cov); f = font(ANTON, 92); tx = 'SANTO PISTÓN GARAGE'
d.text(((W - d.textlength(tx, font=f)) / 2, 1050), tx, font=f, fill=CREAM)
f = font(INTER, 40, 600); tx = 'Restauración de motos clásicas · Maresme'
d.text(((W - d.textlength(tx, font=f)) / 2, 1200), tx, font=f, fill=GOLD)
cov.save(OUT + '/portada_santo_piston.jpg', quality=93)
print('ok')
