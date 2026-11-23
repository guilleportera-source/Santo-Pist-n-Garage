"""Inserta motos (recortes de fotos reales) en planos de vídeo real de un local, con seguimiento de cámara.
- Quita las marcas superpuestas (detecta lo que queda fijo y blanco mientras la escena se mueve) con inpainting.
- Sigue el suelo con flujo óptico (homografía por plano) y pega la moto con sombra de contacto y reflejo en el suelo brillante.
Uso: python3 track.py <scratchpad> <shot.json> <salida.mp4>
"""
import sys, json, subprocess
import numpy as np, cv2
from PIL import Image, ImageFilter, ImageOps

S, SHOT, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
J = json.load(open(SHOT))
SRC = J['src']; f0, f1 = J['frames']           # rango de fotogramas del plano (30 fps)
W, H = 1080, 1920; K = W / 720

cap = cv2.VideoCapture(SRC); cap.set(cv2.CAP_PROP_POS_FRAMES, f0)
fr = []
for _ in range(f1 - f0):
    ok, f = cap.read()
    if not ok: break
    fr.append(f)
fr = np.array(fr); n = len(fr)

# --- 1. máscara de rótulos fijos (blancos en casi todos los fotogramas) ---
white = (fr.min(axis=3) > J.get('wthr', 185)).mean(axis=0)
mask = np.zeros(fr.shape[1:3], np.uint8)
for (x0, y0, x1, y1) in J['wm_boxes']:
    sub = (white[y0:y1, x0:x1] > 0.7).astype(np.uint8) * 255
    mask[y0:y1, x0:x1] = sub
mask = cv2.dilate(mask, np.ones((9, 9), np.uint8))
clean = np.array([cv2.inpaint(f, mask, 6, cv2.INPAINT_TELEA) for f in fr])

# --- 2. seguimiento del suelo: homografía de cada fotograma respecto al de referencia ---
ref = J.get('ref', n // 2)
gray = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in clean]
tm = np.zeros_like(gray[0]); x0, y0, x1, y1 = J['track_box']; tm[y0:y1, x0:x1] = 255; tm[mask > 0] = 0
Hs = [None] * n; Hs[ref] = np.eye(3)
def step(a, b):
    p = cv2.goodFeaturesToTrack(gray[a], 600, 0.005, 8, mask=tm)
    q, st, _ = cv2.calcOpticalFlowPyrLK(gray[a], gray[b], p, None, winSize=(31, 31), maxLevel=4)
    ok = st.ravel() == 1
    Hm, _ = cv2.findHomography(p[ok], q[ok], cv2.RANSAC, 2.0)
    return Hm
for i in range(ref + 1, n): Hs[i] = step(i - 1, i) @ Hs[i - 1]
for i in range(ref - 1, -1, -1): Hs[i] = step(i + 1, i) @ Hs[i + 1]
Sm = np.diag([K, K, 1.0]); Hs = [Sm @ h @ np.linalg.inv(Sm) for h in Hs]

# --- 3. capa de motos en el fotograma de referencia (1080x1920) ---
def cutout(it):
    im = Image.open(S + '/comp/cut/' + it['png']).convert('RGBA')
    for b in it.get('blur_boxes', []):
        r = im.crop(b); w, h = r.size
        im.paste(r.resize((max(1, w // 12), max(1, h // 5))).resize((w, h), Image.NEAREST).filter(ImageFilter.GaussianBlur(3)), b[:2])
    im = im.crop(im.getchannel('A').point(lambda p: 255 if p > 100 else 0).getbbox())
    if it.get('flip'): im = ImageOps.mirror(im)
    k = it['width'] / im.width; im = im.resize((int(it['width']), int(im.height * k)), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32) / 255
    rgb, al = a[..., :3], a[..., 3]
    al = cv2.erode(al, np.ones((3, 3), np.uint8)); al = cv2.GaussianBlur(al, (3, 3), 0.8)
    g = it.get('gain', J.get('gain', 0.72)); t = np.array(it.get('tint', J.get('tint', (1.0, 0.92, 0.80))), np.float32)
    l = rgb.mean(axis=2, keepdims=True); rgb = l + (rgb - l) * it.get('sat', 0.9)
    rgb = np.clip(rgb ** 1.08 * g * t, 0, 1)
    # luz de arriba algo más intensa que abajo (como el local)
    vy = np.linspace(1.06, 0.86, rgb.shape[0])[:, None, None]; rgb = np.clip(rgb * vy, 0, 1)
    return rgb, al
L_rgb = np.zeros((H, W, 3), np.float32); L_a = np.zeros((H, W), np.float32)
SH = np.zeros((H, W), np.float32); RF = np.zeros((H, W, 3), np.float32); RA = np.zeros((H, W), np.float32)
for it in sorted(J['items'], key=lambda i: i['ground'][1]):
    rgb, al = cutout(it); h, w = al.shape
    gx, gy = it['ground']; x0 = int(gx - w / 2); y0 = int(gy - h)
    def paste(dst, src, x, y, mode='over', a=None):
        H_, W_ = dst.shape[:2]; h_, w_ = src.shape[:2]
        xa, ya, xb, yb = max(0, x), max(0, y), min(W_, x + w_), min(H_, y + h_)
        if xa >= xb or ya >= yb: return
        s = src[ya - y:yb - y, xa - x:xb - x]
        if mode == 'max': dst[ya:yb, xa:xb] = np.maximum(dst[ya:yb, xa:xb], s)
        else:
            aa = a[ya - y:yb - y, xa - x:xb - x][..., None]
            dst[ya:yb, xa:xb] = dst[ya:yb, xa:xb] * (1 - aa) + s * aa
    # reflejo en el suelo brillante: volteado, con desenfoque vertical y desvanecido
    rr = rgb[::-1]; ra = al[::-1] * np.linspace(it.get('refl', 0.30), 0, h)[:, None] ** 1.0
    ra = np.clip(ra, 0, 1); ra[int(h * 0.55):] = 0
    rr = cv2.blur(rr, (3, 15)); ra = cv2.blur(ra, (3, 15))
    paste(RF, rr, x0, gy - 2, a=ra); paste(RA[..., None].repeat(1, 2), ra[..., None], x0, gy - 2, mode='max')
    # sombra: de contacto (bajo las ruedas) + suave alrededor
    cont = np.zeros((H, W), np.float32)
    col = al.max(axis=0) > 0.5; xs = np.nonzero(col)[0]
    sh_w = (xs.max() - xs.min()) if len(xs) else w
    cv2.ellipse(cont, (int(x0 + (xs.min() + xs.max()) / 2), int(gy)), (int(sh_w * 0.52), int(sh_w * it.get('sh_depth', 0.06))), 0, 0, 360, 1.0, -1)
    soft = cv2.GaussianBlur(cont, (0, 0), sh_w * 0.05) * 0.55
    bot = (al[-int(h * 0.06):].max(axis=0) > 0.5).astype(np.float32)   # puntos de apoyo (ruedas)
    tight = np.zeros((H, W), np.float32)
    for xx in np.nonzero(bot)[0][::2]:
        cv2.circle(tight, (int(x0 + xx), int(gy)), int(max(3, sh_w * 0.012)), 1.0, -1)
    tight = cv2.GaussianBlur(tight, (0, 0), max(2, sh_w * 0.008)) * 0.85
    SH = np.maximum(SH, np.clip(soft + tight, 0, 0.92))
    paste(L_rgb, rgb, x0, y0, a=al); paste(L_a[..., None], al[..., None], x0, y0, mode='max')
RA = RA if RA.ndim == 2 else RA[..., 0]

# --- 4. render ---
p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30', '-i', '-',
                      '-c:v', 'libx264', '-crf', '14', '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
order = range(n - 1, -1, -1) if J.get('reverse') else range(n)
for i in order:
    bg = cv2.cvtColor(cv2.resize(clean[i], (W, H), interpolation=cv2.INTER_LANCZOS4), cv2.COLOR_BGR2RGB).astype(np.float32) / 255
    Hm = Hs[i]
    wp = lambda a, inter=cv2.INTER_LINEAR: cv2.warpPerspective(a, Hm, (W, H), flags=inter, borderValue=0)
    sh = wp(SH); ra = wp(RA); rf = wp(RF); la = wp(L_a); lr = wp(L_rgb)
    out = bg * (1 - sh[..., None])
    out = out * (1 - ra[..., None] * 0.9) + rf * ra[..., None] * 0.9 + out * ra[..., None] * 0.1 * 0
    out = out * (1 - la[..., None]) + lr * la[..., None]
    # grano común encima de todo (la moto hereda el ruido del vídeo)
    out = out + np.random.default_rng(i).normal(0, 0.012, (H // 2, W // 2, 1)).repeat(2, 0).repeat(2, 1)
    p.stdin.write((np.clip(out, 0, 1) * 255).astype(np.uint8).tobytes())
    if i == ref: Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(OUT[:-4] + '_ref.jpg', quality=92)
p.stdin.close(); p.wait(); print('ok', n)
