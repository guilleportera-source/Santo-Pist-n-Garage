import json, os, sys, urllib.request
OUT = sys.argv[1]
def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'garage-render'}), timeout=120).read()
def save(url, path):
    if os.path.exists(path): return
    os.makedirs(os.path.dirname(path), exist_ok=True); open(path, 'wb').write(get(url))
MODELS = sys.argv[2].split(',') if len(sys.argv) > 2 and sys.argv[2] else []
TEX = sys.argv[3].split(',') if len(sys.argv) > 3 and sys.argv[3] else []
HDRI = sys.argv[4].split(',') if len(sys.argv) > 4 and sys.argv[4] else []
for m in MODELS:
    try:
        f = json.loads(get(f'https://api.polyhaven.com/files/{m}'))
        g = f['gltf']['1k']['gltf']; base = f'{OUT}/models/{m}/'
        save(g['url'], base + os.path.basename(g['url']))
        for rel, inc in g.get('include', {}).items(): save(inc['url'], base + rel)
        print('model', m)
    except Exception as e: print('FAIL model', m, e)
for t in TEX:
    try:
        f = json.loads(get(f'https://api.polyhaven.com/files/{t}'))
        for mp, key in [('Diffuse', 'diff'), ('nor_gl', 'nor'), ('Rough', 'rough'), ('AO', 'ao'), ('Displacement', 'disp')]:
            if mp in f and '2k' in f[mp]:
                save(f[mp]['2k']['jpg']['url'], f'{OUT}/tex/{t}/{key}.jpg')
        print('tex', t)
    except Exception as e: print('FAIL tex', t, e)
for h in HDRI:
    try:
        f = json.loads(get(f'https://api.polyhaven.com/files/{h}'))
        save(f['hdri']['2k']['hdr']['url'], f'{OUT}/hdri/{h}.hdr'); print('hdri', h)
    except Exception as e: print('FAIL hdri', h, e)
