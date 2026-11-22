# Carteles de estilo retro (diseño original) y rótulo con el logotipo
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S = sys.argv[1]; T = S + '/tour/tex/'
A = S + '/fonts/Anton.ttf'; I = S + '/fonts/Inter.ttf'
def f(p, s): return ImageFont.truetype(p, s)
def aged(im):
    n = Image.effect_noise(im.size, 18).convert('L')
    return Image.blend(im, Image.merge('RGB', [n] * 3), 0.06).filter(ImageFilter.GaussianBlur(0.6))
def poster(bg, accent, title, sub, year, shape, name):
    im = Image.new('RGB', (800, 1120), bg); d = ImageDraw.Draw(im)
    if shape == 'sun':
        for k in range(14): d.pieslice((100, 230, 700, 830), k * 26, k * 26 + 12, fill=accent)
        d.ellipse((250, 380, 550, 680), fill=bg); d.ellipse((290, 420, 510, 640), fill=accent)
    elif shape == 'stripes':
        for k in range(5): d.polygon([(0, 300 + k * 90), (800, 160 + k * 90), (800, 205 + k * 90), (0, 345 + k * 90)], fill=accent if k % 2 == 0 else (30, 28, 26))
    else:
        d.ellipse((160, 260, 640, 740), outline=accent, width=34); d.ellipse((330, 430, 470, 570), fill=accent)
    d.text((60, 800), title, font=f(A, 150), fill=(30, 28, 26)); d.text((66, 980), sub, font=f(I, 40), fill=(30, 28, 26)); d.text((640, 60), year, font=f(A, 70), fill=accent)
    aged(im).save(T + name)
poster((236, 224, 196), (196, 58, 40), 'MONTESA', 'Trial · Barcelona', '1975', 'sun', 'poster1.png')
poster((228, 214, 182), (46, 84, 64), 'BULTACO', 'Sant Adrià de Besòs', '1972', 'stripes', 'poster2.png')
poster((232, 222, 200), (214, 160, 52), 'VESPA', 'Scooter · 125', '1968', 'ring', 'poster3.png')
