"""Máscara de persona por fotograma (rembg u2net_human_seg) para que las chapas queden detrás de él."""
import sys, numpy as np, cv2
from rembg import new_session, remove
from PIL import Image
V, OUT, a, b = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
s = new_session('u2net_human_seg')
cap = cv2.VideoCapture(V); cap.set(cv2.CAP_PROP_POS_FRAMES, a)
ms = []
for i in range(a, b):
    ok, f = cap.read()
    if not ok: break
    m = remove(Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)), session=s, only_mask=True)
    ms.append(np.asarray(m))
np.save(OUT, np.array(ms)); print('ok', len(ms))
