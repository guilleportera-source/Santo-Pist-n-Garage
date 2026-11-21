"""Reel final Santo Pistón Garage · 1080x1920 · 30 fps · 35 s · estilo vídeo de móvil."""
import sys, subprocess, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

S, OUT, LOGO = sys.argv[1], sys.argv[2], sys.argv[3]
P = S + '/photos/'; G = S + '/gen/'; R = S + '/restored/'
W, H, FPS, DUR = 1080, 1920, 30, 35.0
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
    out = im.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))
    if rot: out = out.rotate(rot, Image.BICUBIC, expand=False).crop((0, 0, W, H))
    return out

# temblor de mano suave y reproducible
rng = np.random.default_rng(7)
def smooth_noise(n, k):
    x = rng.normal(0, 1, n + 2 * k); w = np.hanning(2 * k + 1); w /= w.sum()
    return np.convolve(x, w, 'valid')[:n]
N = int(DUR * FPS)
SX, SY, SR = smooth_noise(N, 18) * 0.010, smooth_noise(N, 18) * 0.010, smooth_noise(N, 25) * 0.6

def ease(t): t = min(max(t, 0), 1); return t * t * (3 - 2 * t)

F_CAP = font(INTER, 58, 700); F_SUB = font(INTER, 36, 500); F_TAG = font(INTER, 24, 500)
def caption(img, text, sub=None, alpha=1.0):
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    y = 1360
    tw = d.textlength(text, font=F_CAP); x = (W - tw) / 2
    d.text((x, y), text, font=F_CAP, fill=(255, 255, 255, int(255 * alpha)))
    if sub:
        sw = d.textlength(sub, font=F_SUB); d.text(((W - sw) / 2, y + 80), sub, font=F_SUB, fill=(*CREAM, int(235 * alpha)))
    bw = max(tw, d.textlength(sub, font=F_SUB) if sub else 0) + 64
    pill = Image.new('RGBA', img.size, (0, 0, 0, 0)); pd = ImageDraw.Draw(pill)
    pd.rounded_rectangle(((W - bw) / 2, y - 14, (W + bw) / 2, y + (140 if sub else 86)), 26, fill=(10, 9, 8, int(150 * alpha)))
    img.paste(pill, (0, 0), pill)
    sh = layer.split()[3].filter(ImageFilter.GaussianBlur(5)).point(lambda p: int(p * 0.6))
    img.paste((0, 0, 0), (2, 3), sh)
    img.paste(layer, (0, 0), layer)

def small_tag(img, text):
    d = ImageDraw.Draw(img, 'RGBA'); tw = d.textlength(text, font=F_TAG)
    d.rounded_rectangle((W - tw - 90, 300, W - 60, 342), 21, fill=(0, 0, 0, 110))
    d.text((W - tw - 75, 307), text, font=F_TAG, fill=(255, 255, 255, 220))

# ---------- material ----------
scoopy = photo('68c868d9c3e9643fd413ca0f0232a392'); escudo = photo('94a6e97d5c8f4b96940933b32e4e7690')
mt_tank = photo('69c3ef9505da637b71b6e910cbb3d7bb'); mt_lift = photo('d2be5fb28b4f7c465cc707b65b7378ab')
endu = photo('fefa418530536a7638b7a25e2e4a8f3f')
c_before = Image.open(R + 'cota_antes.jpg').convert('RGB'); c_after = Image.open(R + 'cota_despues.jpg').convert('RGB')
g_room, g_bench, g_draw, g_car, g_light = gen('k6_9'), gen('k4_8'), gen('h1_6'), gen('h3_7'), gen('k6_10')
logo = Image.open(LOGO).convert('RGB')
lmask = Image.new('L', logo.size, 0); ImageDraw.Draw(lmask).ellipse((14, 30, logo.width - 14, logo.height - 30), fill=255)
# encuadre del depósito de la moto de trial (mismo recorte en antes y después)
TANK = dict(cx=0.585, cy=0.33, zoom=3.3)

# mapa de pulsos: 105 BPM, la música entra en 1,4 s sobre un pulso
BEAT = 60 / 105
def B(k): return 1.4 + k * BEAT
C = dict(opening=B(3), bench=B(7), scoopy=B(10), escudo=B(16), mtank=B(19), mlift=B(23), endu=B(29), cota=B(38), cota2=B(41), draw=B(46), car=B(49), close=B(53), logo=B(54))
def shot(t, i):
    j = lambda s: dict(dx=SX[i] * s, dy=SY[i] * s, rot=SR[i] * s)
    if t < 1.4:   return crop(c_before, **TANK, **j(0.6))
    if t < C['opening']:
        im = crop(c_after, **TANK, **j(0.6)); small_tag(im, 'Recreación digital'); return im
    if t < C['bench']:   u = ease((t - C['opening']) / (C['bench'] - C['opening'])); return crop(g_room, 0.5, 0.55, 1.0 + 0.18 * u, **j(1))
    if t < C['scoopy']:   u = ease((t - C['bench']) / (C['scoopy'] - C['bench'])); return crop(g_bench, 0.42 + 0.1 * u, 0.5, 1.15, **j(1))
    if t < C['escudo']:
        u = ease((t - C['scoopy']) / (C['escudo'] - C['scoopy'])); im = crop(scoopy, 0.36 + 0.24 * u, 0.6, 1.2, **j(1))
        caption(im, 'Honda Scoopy 75', 'Dos unidades', min((t - C['scoopy'] - 0.2) / 0.3, 1) if t > C['scoopy'] + 0.2 else 0); return im
    if t < C['mtank']:
        u = ease((t - C['escudo']) / (C['mtank'] - C['escudo'])); im = crop(escudo, 0.5, 0.45, 1.1 + 0.1 * u, **j(1.4)); caption(im, 'Honda Scoopy 75'); return im
    if t < C['mlift']:
        u = ease((t - C['mtank']) / (C['mlift'] - C['mtank'])); im = crop(mt_tank, 0.55, 0.34, 1.9 - 0.3 * u, **j(1)); caption(im, 'Montesa', alpha=min((t - C['mtank'] - 0.2) / 0.3, 1) if t > C['mtank'] + 0.2 else 0); return im
    if t < C['endu']:
        u = ease((t - C['mlift']) / (C['endu'] - C['mlift'])); im = crop(mt_lift, 0.42, 0.55, 1.12 - 0.1 * u, **j(1)); caption(im, 'Montesa'); return im
    if t < C['cota']:
        u = ease((t - C['endu']) / (C['cota'] - C['endu'])); im = crop(endu, 0.56 - 0.1 * u, 0.42, 1.35 - 0.15 * u, **j(1))
        caption(im, 'Montesa', alpha=min((t - C['endu'] - 0.2) / 0.3, 1) if t > C['endu'] + 0.2 else 0); return im
    if t < C['cota2']:
        im = crop(c_before, 0.6, 0.5, 1.0 + 0.05 * ease((t - C['cota']) / 1.7), **j(0.5)); caption(im, 'Montesa', 'Así llegó'); return im
    if t < C['draw']:
        u = ease((t - C['cota2']) / (C['draw'] - C['cota2'])); im = crop(c_after, 0.585, 0.33, 3.3 - 0.3 * u, **j(0.5)); caption(im, 'Montesa', 'Así quedó'); small_tag(im, 'Recreación digital'); return im
        if t < C['close']:  u = ease((t - C['draw']) / (C['close'] - C['draw'])); return crop(g_car, 0.5 - 0.06 * u, 0.5, 1.1, **j(1))
    # cierre
    u = ease((t - C['close']) / (DUR - C['close'])); im = crop(g_light, 0.5, 0.5, 1.12 - 0.08 * u, **j(0.7))
    if t >= C['logo']:
        a = min((t - C['logo']) / 0.5, 1)
        d = ImageDraw.Draw(im, 'RGBA'); d.rectangle((0, 0, W, H), fill=(14, 12, 10, int(175 * a)))
        L = logo.resize((440, int(440 * logo.height / logo.width)))
        im.paste(L, ((W - L.width) // 2, 520), lmask.resize(L.size).point(lambda p: int(p * a)))
        d = ImageDraw.Draw(im, 'RGBA')
        f = font(ANTON, 98); tx = 'SANTO PISTÓN GARAGE'
        d.text(((W - d.textlength(tx, font=f)) / 2, 1030), tx, font=f, fill=(*CREAM, int(255 * a)))
        f = font(INTER, 46, 600)
        for k, tx in enumerate(['¿Tienes una clásica para restaurar?', 'Escríbenos.']):
            d.text(((W - d.textlength(tx, font=f)) / 2, 1185 + k * 66), tx, font=f, fill=(*(GOLD if k else CREAM), int(255 * a)))
    return im

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
add(1.4, click(), 0.9); add(C['scoopy'], drawer(), 0.35); add(C['mtank'], ratchet(), 0.25); add(C['cota2'], click(), 0.4); add(C['draw'], drawer(), 0.25)
amb = np.convolve(tone_noise(len(fx)), np.ones(400) / 400, 'same') * 0.05      # aire del local
fx += amb
import wave
with wave.open(S + '/fx.wav', 'w') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR_A)
    w.writeframes((np.clip(fx, -1, 1) * 30000).astype('<i2').tobytes())

MUSIC = S + '/music/Funk_Game_Loop.mp3'
out = OUT + '/santo_piston_reel_1080x1920.mp4'
# música: entra en 1,4 s (tras el clic), fundido final de 2 s, por debajo de los efectos
afilter = ('[1:a]atrim=0.22:33.82,asetpts=PTS-STARTPTS,adelay=1400|1400,volume=0.85,afade=t=in:st=1.4:d=0.25,afade=t=out:st=33:d=2[m];'
           '[2:a]volume=1.0[f];[m][f]amix=inputs=2:normalize=0,alimiter=limit=0.95,loudnorm=I=-14:TP=-1.5:LRA=11[a]')
ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                       '-i', MUSIC, '-i', S + '/fx.wav', '-filter_complex', afilter, '-map', '0:v', '-map', '[a]',
                       '-c:v', 'libx264', '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'slow',
                       '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-t', str(DUR), '-movflags', '+faststart', out], stdin=subprocess.PIPE)
checks = {int(t * FPS) for t in (0.7, 2.2, 4, 6, 9, 11.3, 13, 16, 20, 24, 26.5, 28.8, 30.7, 34)}
for i in range(N):
    fr = finish(shot(i / FPS, i), i)
    ff.stdin.write(fr.tobytes())
    if i in checks: fr.resize((270, 480)).save(f'{S}/fc_{i:04d}.jpg')
ff.stdin.close(); ff.wait()

# portada
cov = crop(endu, 0.42, 0.42, 1.35); d = ImageDraw.Draw(cov, 'RGBA'); d.rectangle((0, 0, W, H), fill=(14, 12, 10, 120))
L = logo.resize((560, int(560 * logo.height / logo.width))); cov.paste(L, (260, 420), lmask.resize(L.size))
d = ImageDraw.Draw(cov); f = font(ANTON, 112); tx = 'SANTO PISTÓN GARAGE'
d.text(((W - d.textlength(tx, font=f)) / 2, 1050), tx, font=f, fill=CREAM)
f = font(INTER, 44, 600); tx = 'Restauración de motos clásicas · Maresme'
d.text(((W - d.textlength(tx, font=f)) / 2, 1200), tx, font=f, fill=GOLD)
cov.save(OUT + '/portada_santo_piston.jpg', quality=93)
print('ok')
