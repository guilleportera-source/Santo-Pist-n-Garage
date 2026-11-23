"""Ambienta el local del vídeo original sin tocar la acción:
- chapas de época clavadas en la pared, con seguimiento de cámara, luz de la pared y detrás de la persona;
- etalonaje cálido de taller clásico (blancos crema, negros suaves, grano, viñeta).
Uso: python3 local.py <scratchpad> <video> <salida.mp4> [preview]
"""
import sys, subprocess, numpy as np, cv2
from PIL import Image
S, V, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
PREV = len(sys.argv) > 4
TR = S + '/tour/tex_real/'
cap = cv2.VideoCapture(V); FPS = cap.get(cv2.CAP_PROP_FPS)
fr = []
while True:
    ok, f = cap.read()
    if not ok: break
    fr.append(f)
fr = np.array(fr); n, h, w = fr.shape[:3]
M = np.concatenate([np.load(S + '/v3/m0.npy'), np.load(S + '/v3/m1.npy')])[:n].astype(np.float32) / 255
gray = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in fr]

KEY = 1042
WALL = np.float32([[0, 0], [464, 0], [464, 340], [0, 340]])        # zona de pared en el fotograma clave
PAINT_TOP, PAINT_BOT = 34, 228          # banda de pared pintada (por encima de mesa y motos)
PAINT_X = (-60, 470)
PAINT = (0.16, 0.25, 0.20)              # verde inglés de taller, mate
STRIPE = (0.60, 0.09, 0.07); STRIPE_H = 5   # filete rojo bajo la pintura
SIGNS = [  # textura, esquinas en el fotograma clave (sup-izq, sup-der, inf-der, inf-izq)
    ('b_montesa', [[92, 150], [176, 151], [176, 198], [92, 197]]),
    ('b_motul', [[300, 52], [366, 53], [366, 119], [300, 118]]),
    ('b_campsa', [[262, 142], [450, 145], [450, 200], [262, 197]]),
    ('b_castrol', [[380, 60], [452, 61], [452, 97], [380, 96]]),
]

def step(a, b, poly):
    m = np.zeros((h, w), np.uint8); cv2.fillPoly(m, [poly.astype(np.int32)], 255)
    m[cv2.dilate((M[a] > 0.3).astype(np.uint8), np.ones((15, 15), np.uint8)) > 0] = 0
    p = cv2.goodFeaturesToTrack(gray[a], 500, 0.01, 6, mask=m)
    if p is None or len(p) < 20: return None
    q, st, _ = cv2.calcOpticalFlowPyrLK(gray[a], gray[b], p, None, winSize=(25, 25), maxLevel=4)
    ok = st.ravel() == 1
    if ok.sum() < 20: return None
    Hm, inl = cv2.findHomography(p[ok], q[ok], cv2.RANSAC, 2.5)
    if Hm is None or inl.sum() < 15: return None
    return Hm
import os
HC = S + '/v3/hs.npy'
Hs = [None] * n; Hs[KEY] = np.eye(3)
if os.path.exists(HC):
    arr = np.load(HC); Hs = [None if np.isnan(x).any() else x for x in arr]
for rng_, d in ([] if os.path.exists(HC) else ((range(KEY + 1, n), -1), (range(KEY - 1, -1, -1), 1))):
    for i in rng_:
        prev = i + d
        if Hs[prev] is None: break
        poly = cv2.perspectiveTransform(WALL[None], Hs[prev])[0]
        Hm = step(prev, i, poly)
        if Hm is None: break
        Hs[i] = Hm @ Hs[prev]
        # si la pared sale casi del encuadre, se deja de seguir
        c = cv2.perspectiveTransform(WALL[None], Hs[i])[0]
        if c[:, 1].max() < 20 or c[:, 0].max() < 20 or c[:, 0].min() > w - 20: Hs[i] = None; break
np.save(HC, np.array([x if x is not None else np.full((3, 3), np.nan) for x in Hs]))
print('seguimiento', sum(h_ is not None for h_ in Hs), 'de', n)

tex = {}
for name, _ in SIGNS:
    im = Image.open(TR + name + '.png').convert('RGBA'); im = im.resize((400, int(400 * im.height / im.width)), Image.LANCZOS); tex[name] = np.asarray(im).astype(np.float32) / 255

# etalonaje de taller clásico
yy, xx = np.mgrid[0:1920, 0:1080]; rr = ((xx - 540) / 540) ** 2 + ((yy - 960) / 960) ** 2
VIG = (1 - 0.22 * (rr / 2) ** 1.4)[..., None].astype(np.float32)
def grade(x):
    l = x.mean(axis=2, keepdims=True)
    x = l + (x - l) * 0.92
    hi = np.clip((l - 0.45) / 0.55, 0, 1)                        # blancos -> crema cálido
    x = x * (1 - hi * np.array([0.0, 0.05, 0.15], np.float32))
    x = x * np.array([1.03, 1.0, 0.93], np.float32)              # tungsteno suave
    x = 0.035 + 0.94 * x                                          # negros algo levantados
    x = np.clip(x, 0, 1); x = x * x * (3 - 2 * x) * 0.35 + x * 0.65   # curva en S suave
    return x

def frame_out(i):
    f = fr[i].astype(np.float32) / 255
    if Hs[i] is not None:
        # pintura: se recolorea la pared real conservando su luz, juntas y textura
        g0 = cv2.cvtColor(fr[i], cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
        hsv = cv2.cvtColor(fr[i], cv2.COLOR_BGR2HSV).astype(np.float32)
        sat = hsv[..., 1] / 255
        def band(y0, y1):
            q = np.float32([[PAINT_X[0], y0], [PAINT_X[1], y0], [PAINT_X[1], y1], [PAINT_X[0], y1]])
            m = np.zeros((h * 4, w * 4), np.uint8)
            pp = cv2.perspectiveTransform(q[None], Hs[i])[0] * 4
            cv2.fillPoly(m, [np.round(pp).astype(np.int32)], 255, lineType=cv2.LINE_AA)
            return cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
        wallness = np.clip((g0 - 0.28) / 0.2, 0, 1) * np.clip((0.36 - sat) / 0.1, 0, 1)
        wallness = cv2.GaussianBlur(wallness, (0, 0), 0.8)
        keep = (1 - np.clip(M[i] * 1.5, 0, 1))
        shade = np.clip(g0 / 0.84, 0.25, 1.2)[..., None] ** 1.15
        for (y0, y1, col) in ((PAINT_TOP, PAINT_BOT, PAINT), (PAINT_BOT, PAINT_BOT + STRIPE_H, STRIPE)):
            a_ = (band(y0, y1) * wallness * keep)[..., None]
            paint = np.array(col[::-1], np.float32) * shade
            f = f * (1 - a_) + paint * a_
        lum = cv2.GaussianBlur(cv2.cvtColor(fr[i], cv2.COLOR_BGR2GRAY).astype(np.float32) / 255, (0, 0), 6)
        for name, q in SIGNS:
            t = tex[name]; th, tw = t.shape[:2]
            src = np.float32([[0, 0], [tw, 0], [tw, th], [0, th]])
            dst = cv2.perspectiveTransform(np.float32(q)[None], Hs[i])[0]
            Hp = cv2.getPerspectiveTransform(src, dst)
            wt = cv2.warpPerspective(t, Hp, (w, h), flags=cv2.INTER_LINEAR)
            a = wt[..., 3] * (1 - np.clip(M[i] * 1.4, 0, 1))
            rgb = wt[..., [2, 1, 0]]
            shade = np.clip(lum / 0.82, 0.45, 1.08)[..., None]              # la luz de la pared cae sobre la chapa
            rgb = rgb * shade * np.array([0.96, 0.95, 0.92], np.float32)
            sh = cv2.GaussianBlur(np.roll(np.roll(a, 2, 0), 2, 1), (0, 0), 2.0) * 0.28   # sombrita de la chapa en la pared
            f = f * (1 - sh[..., None])
            f = f * (1 - a[..., None]) + rgb * a[..., None]
    big = cv2.resize(f, (1080, 1920), interpolation=cv2.INTER_LANCZOS4)[..., ::-1]
    big = grade(np.clip(big, 0, 1)) * VIG
    g = np.random.default_rng(i).normal(0, 0.014, (960, 540, 1)).astype(np.float32).repeat(2, 0).repeat(2, 1)
    return (np.clip(big + g, 0, 1) * 255).astype(np.uint8)

if PREV:
    for i in (20, 200, 450, 700, 1042, 1180):
        Image.fromarray(frame_out(i)).resize((360, 640)).save(S + f'/v3/prev_{i}.jpg')
    sys.exit()
p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1080x1920', '-r', f'{FPS}', '-i', '-',
                      '-i', V, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '19', '-maxrate', '14M', '-bufsize', '28M',
                      '-preset', 'slow', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-shortest', OUT], stdin=subprocess.PIPE)
for i in range(n): p.stdin.write(frame_out(i).tobytes())
p.stdin.close(); p.wait(); print('ok', n)
