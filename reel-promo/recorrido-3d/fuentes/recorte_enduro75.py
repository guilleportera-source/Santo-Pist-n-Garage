import sys, numpy as np, cv2
S = sys.argv[1]
im = cv2.imread(S + '/photos2/enduro75_IMG_2755.jpg'); H, W = im.shape[:2]
m = np.zeros((H, W), np.uint8)
def poly(pts): cv2.fillPoly(m, [(np.array(pts) * 2).astype(np.int32)], 255)
def ell(c, ax, ang=0): cv2.ellipse(m, (c[0] * 2, c[1] * 2), (ax[0] * 2, ax[1] * 2), ang, 0, 360, 255, -1)
ell((205, 625), (205, 178))                    # rueda trasera
ell((1020, 673), (128, 200), -4)               # rueda delantera
poly([(100, 262), (200, 255), (520, 318), (535, 330), (528, 448), (130, 445), (100, 420)])   # asiento
poly([(528, 335), (600, 305), (760, 290), (850, 300), (880, 360), (870, 425), (700, 440), (528, 452)])  # depósito
poly([(240, 445), (530, 445), (790, 445), (810, 470), (770, 645), (680, 705), (500, 725), (330, 690), (250, 520)])  # chasis y motor
poly([(476, 700), (675, 700), (682, 912), (470, 912)])          # caballete
poly([(870, 318), (912, 318), (968, 560), (928, 565)])          # barra izq.
poly([(955, 330), (1000, 330), (1102, 705), (1060, 712)])       # barra der.
ell((922, 242), (92, 95))                                       # faro/porta números
poly([(556, 222), (700, 222), (820, 230), (860, 205), (995, 145), (1162, 140), (1170, 232), (1060, 205), (990, 262), (860, 262), (700, 250), (556, 248)])  # manillar
ell((645, 162), (36, 34)); poly([(640, 190), (660, 190), (712, 232), (690, 240)])   # retrovisor
poly([(1100, 140), (1165, 210), (1158, 232), (1095, 160)])
poly([(880, 540), (945, 540), (945, 660), (885, 660)])          # guardabarros
hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
blue = (hsv[..., 0] > 95) & (hsv[..., 0] < 130) & (hsv[..., 1] > 70)
m[blue] = 0
# termómetro Citroën y radiador fuera
for x0, y0, x1, y1 in [(632, 165, 700, 300), (1150, 300, 1290, 620), (980, 260, 1060, 480)]:
    sub = m[y0 * 2:y1 * 2, x0 * 2:x1 * 2]
    # dentro de estas cajas solo se queda lo oscuro/saturado (piezas de la moto)
    hv = hsv[y0 * 2:y1 * 2, x0 * 2:x1 * 2]
    light = (hv[..., 2] > 150) & (hv[..., 1] < 60)
    sub[light] = 0
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
a = cv2.GaussianBlur(m, (5, 5), 0)
ys, xs = np.nonzero(a > 20); x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
rgba = np.dstack([im, a])[y0:y1 + 1, x0:x1 + 1]
cv2.imwrite(S + '/cutouts/enduro75.png', rgba)
prev = rgba.astype(float); bg = np.zeros_like(prev[..., :3]); bg[:] = (205, 205, 200)
al = prev[..., 3:] / 255; comp = prev[..., :3] * al + bg * (1 - al)
cv2.imwrite(S + '/e75prev.jpg', cv2.resize(comp.astype(np.uint8), None, fx=0.4, fy=0.4))
print(rgba.shape, 'ground_y', y1 - y0)
