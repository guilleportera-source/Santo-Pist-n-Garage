"""Animática de previsualización del Reel de Santo Pistón Garage (1080x1920, 30 fps)."""
import sys, subprocess, math, wave, struct, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

S = sys.argv[1]           # scratchpad
OUT = sys.argv[2]         # carpeta de salida
P = S + '/photos/'
LOGO = sys.argv[3]
W, H, FPS = 1080, 1920, 30
ANTON = S + '/fonts/Anton.ttf'
INTER = S + '/fonts/Inter.ttf'
CREAM = (242, 236, 222); RED = (184, 53, 42); GOLD = (226, 179, 60); INK = (21, 18, 15)

def font(path, size, wght=None):
    f = ImageFont.truetype(path, size)
    if wght:
        try: f.set_variation_by_axes([wght])
        except Exception: pass
    return f

F_TAG = font(INTER, 26, 600)
F_SMALL = font(INTER, 34, 500)
F_MODEL = font(ANTON, 92)
F_SUB = font(INTER, 38, 500)

def load(name):
    return Image.open(P + name + '.jpg').convert('RGB')

def cover_crop(im, cx, cy, zoom):
    """Recorte 9:16 centrado en (cx,cy) en fracción de la imagen; zoom>=1 acerca."""
    iw, ih = im.size
    ch = ih / zoom; cw = ch * W / H
    if cw > iw / zoom:
        cw = iw / zoom; ch = cw * H / W
    x0 = min(max(cx * iw - cw / 2, 0), iw - cw); y0 = min(max(cy * ih - ch / 2, 0), ih - ch)
    return im.resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))

def tag(d, text, kind):
    col = {'real': (46, 125, 80), 'rec': RED, 'pend': (120, 110, 100)}[kind]
    tw = d.textlength(text, font=F_TAG)
    d.rounded_rectangle((60, 270, 60 + tw + 36, 318), 10, fill=col)
    d.text((78, 279), text, font=F_TAG, fill='white')

def title(img, model, sub=None):
    d = ImageDraw.Draw(img, 'RGBA')
    d.rectangle((0, 1180, W, 1520), fill=(0, 0, 0, 0))
    grad = Image.new('L', (1, 520))
    for y in range(520): grad.putpixel((0, y), int(150 * math.sin(math.pi * y / 520)))
    img.paste(Image.new('RGB', (W, 520), (0, 0, 0)), (0, 1080), grad.resize((W, 520)))
    d = ImageDraw.Draw(img, 'RGBA')
    d.rectangle((72, 1258, 84, 1258 + (150 if sub else 100)), fill=GOLD)
    d.text((108, 1240), model, font=F_MODEL, fill=CREAM)
    if sub: d.text((112, 1360), sub, font=F_SUB, fill=(230, 222, 205))

def ease(t): return t * t * (3 - 2 * t)

# ---------- Dibujo esquemático del taller (storyboard, NO es imagen final) ----------
def sketch_garage(view='entrada'):
    im = Image.new('RGB', (W, H), (247, 244, 238)); d = ImageDraw.Draw(im)
    line = (60, 56, 50); light = (170, 162, 150)
    vx, vy = W // 2, 860   # punto de fuga
    if view == 'entrada':
        bx0, by0, bx1, by1 = 300, 560, 780, 1130      # pared del fondo
        # portón acristalado
        d.rectangle((380, 640, 700, 1130), fill=(222, 233, 238), outline=line, width=4)
        for x in (460, 540, 620): d.line((x, 640, x, 1130), fill=line, width=2)
        for y in (760, 880, 1000): d.line((380, y, 700, y), fill=line, width=2)
        # rayos de luz
        for k in range(6):
            d.polygon([(390 + k * 50, 1130), (420 + k * 50, 1130), (300 + k * 120, 1920), (230 + k * 120, 1920)], fill=(250, 241, 214))
        d.rectangle((bx0, by0, bx1, by1), outline=line, width=4)
        for p in [(bx0, by0, 0, 0), (bx1, by0, W, 0), (bx0, by1, 0, H), (bx1, by1, W, H)]:
            d.line(p, fill=line, width=4)
        # rótulo
        d.ellipse((480, 580, 600, 630), outline=RED, width=5)
        d.text((612, 588), 'RÓTULO', font=F_TAG, fill=RED)
        # banco izquierda
        d.polygon([(0, 1250), (300, 1050), (300, 1090), (0, 1330)], fill=(176, 132, 86), outline=line)
        d.polygon([(0, 1330), (300, 1090), (300, 1130), (0, 1640)], fill=(96, 110, 70), outline=line)
        for i in range(4): d.line((0, 1380 + i * 70, 300, 1100 + i * 9), fill=line, width=2)
        d.text((40, 1150), 'BANCO + CAJONERAS\nVERDE OLIVA', font=F_TAG, fill=line)
        d.line((210, 1100, 240, 960, 290, 930), fill=line, width=5)  # lámpara
        # carteles
        for x, y in ((90, 700), (190, 760)):
            d.rectangle((x, y, x + 70, y + 100), outline=GOLD, width=4)
        # motos derecha
        for k, (x, y, s) in enumerate(((840, 1240, 1.0), (700, 1150, 0.7), (600, 1100, 0.5))):
            r = int(80 * s)
            d.ellipse((x - r, y - r, x + r, y + r), outline=line, width=5)
            d.ellipse((x + int(260 * s) - r, y - r, x + int(260 * s) + r, y + r), outline=line, width=5)
            d.line((x, y, x + int(110 * s), y - int(110 * s), x + int(260 * s), y), fill=line, width=5)
        d.text((720, 1380), 'MOTOS\nTERMINADAS', font=F_TAG, fill=line)
        # aleta de coche (Fiat 126)
        d.pieslice((900, 1500, 1300, 1900), 180, 270, fill=(235, 235, 232), outline=line, width=4)
        d.ellipse((960, 1560, 1020, 1620), outline=line, width=4)
        d.text((880, 1460), 'FIAT 126', font=F_TAG, fill=line)
    else:  # plano general inverso: motos delante, coche al fondo
        d.rectangle((0, 300, W, 1150), fill=(244, 240, 233))
        d.line((0, 1150, W, 1150), fill=line, width=4)
        d.rectangle((120, 560, 360, 1150), fill=(222, 233, 238), outline=line, width=4)   # portón lateral (luz desde izq.)
        d.text((130, 520), 'PORTÓN (LUZ)', font=F_TAG, fill=line)
        d.rounded_rectangle((520, 820, 1000, 1150), 60, fill=(235, 235, 232), outline=line, width=4)
        d.text((640, 760), 'FIAT 126 (FONDO)', font=F_TAG, fill=line)
        d.ellipse((470, 640, 560, 690), outline=RED, width=5)
        for k, x in enumerate((60, 420, 780)):
            y = 1500 + (k % 2) * 60
            d.ellipse((x - 70, y - 70, x + 70, y + 70), outline=line, width=6)
            d.ellipse((x + 160, y - 70, x + 300, y + 70), outline=line, width=6)
            d.line((x, y, x + 100, y - 120, x + 230, y), fill=line, width=6)
        d.text((80, 1680), 'MOTOS EN PRIMER TÉRMINO', font=F_TAG, fill=line)
    return im

def placeholder(label, lines, base=None):
    im = base.copy() if base else Image.new('RGB', (W, H), (34, 30, 27))
    d = ImageDraw.Draw(im, 'RGBA')
    d.rounded_rectangle((60, 640, W - 60, 1120), 24, fill=(21, 18, 15, 225))
    d.text((100, 680), label, font=font(ANTON, 70), fill=GOLD)
    y = 800
    for l in lines:
        d.text((100, y), l, font=F_SMALL, fill=CREAM); y += 52
    return im

# ---------- Plano por plano ----------
logo = Image.open(LOGO).convert('RGB')
lm = Image.new('L', logo.size, 0); ImageDraw.Draw(lm).ellipse((14, 30, logo.width - 14, logo.height - 30), fill=255)

def badge_crop(name, cx, cy, half):
    im = load(name); return im.crop((cx - half, cy - half * 16 / 9, cx + half, cy + half * 16 / 9)).resize((W, H), Image.LANCZOS)

old = badge_crop('00c2c58eb4ef6fd72d2b0142c67620b1', 215, 632, 120).filter(ImageFilter.GaussianBlur(0.6))
new = badge_crop('fefa418530536a7638b7a25e2e4a8f3f', 384, 652, 120)

scoopy = load('68c868d9c3e9643fd413ca0f0232a392')
endu = load('fefa418530536a7638b7a25e2e4a8f3f')
cota = load('0e039c25a16a62d6110322637f0ad7cc')
cota2 = load('a116fb9f41ac17c32d528520d9d191b2')
sk1 = sketch_garage('entrada'); sk2 = sketch_garage('general')

def frame(t):
    if t < 1.4:   # antes (fotograma del vídeo antiguo)
        img = old.copy(); d = ImageDraw.Draw(img); tag(d, 'FOTO REAL · HACE AÑOS (IMG_8106)', 'real')
    elif t < 3.0:
        img = new.copy(); d = ImageDraw.Draw(img); tag(d, 'FOTO REAL · HOY', 'real')
    elif t < 7.0:
        u = ease((t - 3) / 4); img = cover_crop(sk1, 0.5, 0.55, 1.0 + 0.25 * u)
        img = placeholder('PLANO 2 · EL TALLER', ['Recreación generada (pendiente).', 'Entrada → banco a la izquierda →', 'motos a la derecha → rótulo.', 'Boceto de distribución, no imagen final.'], img)
        tag(ImageDraw.Draw(img), 'RECREACIÓN · PENDIENTE DE GENERAR', 'rec')
    elif t < 12.0:
        u = ease((t - 7) / 5); img = cover_crop(scoopy, 0.38 + 0.2 * u, 0.6, 1.2)
        tag(ImageDraw.Draw(img), 'FOTO REAL', 'real'); title(img, 'Honda Scoopy 75', 'Dos unidades')
    elif t < 18.0:
        img = placeholder('MONTESA IMPALA 2', ['No hay ninguna foto identificada', 'de la Impala 2 en el material.', 'Hueco reservado: 6 s.', 'Necesito foto(s) reales de la moto.'])
        tag(ImageDraw.Draw(img), 'FALTA FOTO', 'pend'); title(img, 'Montesa Impala 2')
    elif t < 23.0:
        u = ease((t - 18) / 5); img = cover_crop(endu, 0.55 - 0.08 * u, 0.42, 1.3 - 0.15 * u)
        tag(ImageDraw.Draw(img), 'FOTO REAL', 'real'); title(img, 'Montesa Endurito 75')
    elif t < 28.0:
        src = cota if t < 25.5 else cota2
        img = cover_crop(src, 0.45 if src is cota else 0.3, 0.5, 1.0)
        d = ImageDraw.Draw(img); tag(d, 'FOTO REAL · ASÍ LLEGÓ · MODELO POR CONFIRMAR', 'real')
        title(img, 'Montesa Cota 80', 'Así llegó')
    else:
        u = ease(min((t - 28) / 7, 1)); img = cover_crop(sk2, 0.5, 0.5, 1.12 - 0.1 * u)
        img = placeholder('PLANO 7 · EL CONJUNTO', ['Recreación generada (pendiente).', 'Contraplano: motos delante,', 'Fiat 126 al fondo, misma luz.'], img) if t < 32 else img
        d = ImageDraw.Draw(img, 'RGBA'); tag(d, 'RECREACIÓN · PENDIENTE DE GENERAR', 'rec')
        if t >= 32:
            a = min((t - 32) / 0.5, 1)
            d.rectangle((0, 0, W, H), fill=(15, 13, 11, int(170 * a)))
            L = logo.resize((420, int(420 * logo.height / logo.width)))
            m = lm.resize(L.size)
            img.paste(L, (330, 540), m.point(lambda p: int(p * a)))
            d = ImageDraw.Draw(img, 'RGBA')
            c = (*CREAM, int(255 * a))
            tx = 'SANTO PISTÓN GARAGE'; f = font(ANTON, 96)
            d.text(((W - d.textlength(tx, font=f)) / 2, 1030), tx, font=f, fill=c)
            for i, tx in enumerate(['¿Tienes una clásica para restaurar?', 'Escríbenos.']):
                f = font(INTER, 46, 600)
                d.text(((W - d.textlength(tx, font=f)) / 2, 1180 + i * 64), tx, font=f, fill=(*GOLD, int(255 * a)) if i else c)
    d = ImageDraw.Draw(img, 'RGBA')
    d.text((60, 220), 'PREVISUALIZACIÓN · NO PUBLICAR', font=F_TAG, fill=(255, 255, 255, 210), stroke_width=2, stroke_fill=(0, 0, 0, 160))
    return img

def cover():
    img = cover_crop(endu, 0.42, 0.42, 1.35)
    d = ImageDraw.Draw(img, 'RGBA'); d.rectangle((0, 0, W, H), fill=(15, 13, 11, 120))
    L = logo.resize((560, int(560 * logo.height / logo.width))); img.paste(L, (260, 420), lm.resize(L.size))
    d = ImageDraw.Draw(img); f = font(ANTON, 112); tx = 'SANTO PISTÓN GARAGE'
    d.text(((W - d.textlength(tx, font=f)) / 2, 1050), tx, font=f, fill=CREAM)
    f = font(INTER, 44, 600); tx = 'Restauración de motos clásicas · Maresme'
    d.text(((W - d.textlength(tx, font=f)) / 2, 1200), tx, font=f, fill=GOLD)
    return img

cover().save(OUT + '/portada_santo_piston.jpg', quality=93)

# Audio: solo el clic de interruptor en el corte (1,4 s). La música queda pendiente de licencia.
sr = 48000; n = int(35 * sr); samples = [0.0] * n
random.seed(1)
for i in range(int(0.012 * sr)):
    k = int(1.4 * sr) + i; samples[k] = random.uniform(-1, 1) * math.exp(-i / (0.0025 * sr)) * 0.8
with wave.open(S + '/click.wav', 'w') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes(b''.join(struct.pack('<h', int(s * 32000)) for s in samples))

ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                       '-i', S + '/click.wav', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-preset', 'medium',
                       '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', OUT + '/previsualizacion_reel_santo_piston.mp4'], stdin=subprocess.PIPE)
for i in range(35 * FPS):
    ff.stdin.write(frame(i / FPS).tobytes())
ff.stdin.close(); ff.wait()
for t in (0.5, 2, 5, 9, 15, 20, 24, 27, 30, 34):
    frame(t).resize((360, 640)).save(f'{S}/check_{t}.jpg')
print('ok')
