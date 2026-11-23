"""Escalado x4 con Real-ESRGAN (realesr-general-x4v3, SRVGGNetCompact) en CPU.
Lee fotogramas crudos y escribe fotogramas 1080x1920 en bruto por stdout... (aquí: a archivos PNG por trozos).
Uso: python3 sr.py <video> <pesos.pth> <carpeta_salida> <inicio> <fin>
"""
import sys, os, numpy as np, cv2, torch, torch.nn as nn, torch.nn.functional as F
V, Wt, OUT, a, b = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
torch.set_num_threads(int(os.environ.get('THREADS', 2)))

class SRVGGNetCompact(nn.Module):
    def __init__(self, num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=32, upscale=4):
        super().__init__()
        self.upscale = upscale
        self.body = nn.ModuleList([nn.Conv2d(num_in_ch, num_feat, 3, 1, 1), nn.PReLU(num_parameters=num_feat)])
        for _ in range(num_conv):
            self.body.append(nn.Conv2d(num_feat, num_feat, 3, 1, 1)); self.body.append(nn.PReLU(num_parameters=num_feat))
        self.body.append(nn.Conv2d(num_feat, num_out_ch * upscale * upscale, 3, 1, 1))
        self.upsampler = nn.PixelShuffle(upscale)
    def forward(self, x):
        out = x
        for m in self.body: out = m(out)
        out = self.upsampler(out)
        return out + F.interpolate(x, scale_factor=self.upscale, mode='nearest')

net = SRVGGNetCompact()
sd = torch.load(Wt, map_location='cpu'); sd = sd.get('params', sd.get('params_ema', sd))
net.load_state_dict(sd); net.eval()
os.makedirs(OUT, exist_ok=True)
cap = cv2.VideoCapture(V); cap.set(cv2.CAP_PROP_POS_FRAMES, a)
with torch.inference_mode():
    for i in range(a, b):
        ok, f = cap.read()
        if not ok: break
        dst = f'{OUT}/{i:05d}.jpg'
        if os.path.exists(dst): continue
        x = torch.from_numpy(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)).permute(2, 0, 1)[None].float() / 255
        y = net(x).clamp(0, 1)[0].permute(1, 2, 0).numpy()
        y = cv2.resize(y, (1080, 1920), interpolation=cv2.INTER_AREA)
        cv2.imwrite(dst, cv2.cvtColor((y * 255 + 0.5).astype(np.uint8), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 97])
print('ok', a, b)
