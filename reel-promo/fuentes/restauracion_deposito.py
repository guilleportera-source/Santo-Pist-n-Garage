import sys, numpy as np, cv2
S = sys.argv[1]
b = cv2.imread(S + '/restored/cota_antes.jpg'); a = cv2.imread(S + '/restored/cota_despues.jpg')
hsv = cv2.cvtColor(b, cv2.COLOR_BGR2HSV); H, Sa, V = [hsv[..., i].astype(int) for i in range(3)]
# zona del depósito (caja generosa)
box = np.zeros(V.shape, np.uint8); box[150:700, 420:880] = 1
sb = np.zeros_like(box); cv2.fillPoly(sb, [np.array([[640,425],[707,425],[686,566],[628,566]])], 1)
dark = (V < 80) & (sb > 0)                                   # franjas negras
lb = np.zeros_like(box); lb[528:590, 455:690] = 1
red = (((H < 12) | (H > 165)) & (Sa > 90) & (V > 60)) & (lb > 0)   # letras rojas
badge = np.zeros_like(box); cv2.circle(badge, (645, 470), 33, 1, -1)  # emblema (se ajusta abajo)
# localizar emblema: zona dorada/roja más saturada y compacta cerca de las franjas
gold = ((H > 12) & (H < 35) & (Sa > 90) & (V > 110) & (box > 0)).astype(np.uint8)
n, lab, st, cen = cv2.connectedComponentsWithStats(gold)
if False:
    k = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]); cx, cy = cen[k]; r = int(max(st[k, 2], st[k, 3]) * 0.75)
    badge = np.zeros_like(box); cv2.circle(badge, (int(cx), int(cy)), r, 1, -1)
    print('badge', cx, cy, r)
keep = (dark | red | (badge > 0)).astype(np.uint8)
keep = cv2.morphologyEx(keep, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
keep = cv2.GaussianBlur(keep.astype(np.float32), (5, 5), 0)[..., None]
orig = b.astype(np.float32)
# decals originales con más contraste y menos suciedad amarilla
dec = cv2.convertScaleAbs(orig, alpha=1.18, beta=-12).astype(np.float32)
out = a.astype(np.float32) * (1 - keep) + dec * keep
# limpiar el fondo superior derecho con desenfoque (manillar/cables con trama)
tank = ((cv2.cvtColor(a, cv2.COLOR_BGR2HSV)[..., 2] > 200) & (cv2.cvtColor(a, cv2.COLOR_BGR2HSV)[..., 1] < 40)).astype(np.uint8)
tank = cv2.morphologyEx(tank, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
n, lab, st, _ = cv2.connectedComponentsWithStats(tank)
big = (lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
big = np.ones_like(big); big[:300, 700:] = 0; big[:, 800:] = 0
m = cv2.GaussianBlur(big.astype(np.float32), (0, 0), 30)[..., None]
bg = cv2.GaussianBlur(out, (0, 0), 22)
out = out * m + bg * (1 - m)
cv2.imwrite(S + '/restored/cota_despues_v2.jpg', np.clip(out, 0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 95])
c = np.hstack([b[120:760, 400:900], np.clip(out, 0, 255).astype(np.uint8)[120:760, 400:900]])
cv2.imwrite(S + '/qa/tank_v2.jpg', c)
