"""Garaje Santo Pistón en 3D (Blender 5.3, Cycles). Uso:
python3 scene.py <scratchpad> stills <res_y>      -> un fotograma por plano
python3 scene.py <scratchpad> anim <res_y> <shot> -> fotogramas de un plano
"""
import bpy, sys, os, json, math
from mathutils import Vector

S = sys.argv[1]; MODE = sys.argv[2]; RES_Y = int(sys.argv[3])
T = S + '/tour/tex/'; CUT = S + '/cutouts/'; OUT = S + '/tour/render/'
os.makedirs(OUT, exist_ok=True)
FPS = 30
FPS_R = int(os.environ.get('FPS_R', 10))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

# ---------------- materiales ----------------
def mat(name, color, rough=0.5, metal=0.0, tex=None, noise=None, alpha_img=False):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; p = nt.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*color, 1); p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    if tex:
        im = nt.nodes.new('ShaderNodeTexImage'); im.image = bpy.data.images.load(tex)
        nt.links.new(im.outputs['Color'], p.inputs['Base Color'])
        if alpha_img:
            nt.links.new(im.outputs['Alpha'], p.inputs['Alpha'])
            im.interpolation = 'Cubic'
    if noise:  # variación sutil (hormigón, madera)
        kind, scale, amt = noise
        tc = nt.nodes.new('ShaderNodeTexCoord')
        if kind == 'wood':
            n = nt.nodes.new('ShaderNodeTexWave'); n.inputs['Scale'].default_value = scale
            n.inputs['Distortion'].default_value = 6; n.inputs['Detail'].default_value = 4
            n.bands_direction = 'X'
        else:
            n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = scale; n.inputs['Detail'].default_value = 8
        nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
        mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.inputs['Factor'].default_value = amt
        mix.inputs['A'].default_value = (*color, 1)
        dark = tuple(c * 0.72 for c in color); mix.inputs['B'].default_value = (*dark, 1)
        ramp = nt.nodes.new('ShaderNodeMath'); ramp.operation = 'MULTIPLY'; ramp.inputs[1].default_value = amt
        nt.links.new(n.outputs['Fac'], mix.inputs['Factor'])
        nt.links.new(mix.outputs['Result'], p.inputs['Base Color'])
        if kind == 'concrete':
            bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.05
            nt.links.new(n.outputs['Fac'], bump.inputs['Height']); nt.links.new(bump.outputs['Normal'], p.inputs['Normal'])
    return m

WHITE = mat('pared', (0.80, 0.78, 0.74), 0.85)
CEIL = mat('techo', (0.88, 0.87, 0.84), 0.9)
CONC = mat('hormigon', (0.36, 0.36, 0.35), 0.38, noise=('concrete', 3.0, 0.35))
OAK = mat('roble', (0.48, 0.30, 0.16), 0.45, noise=('wood', 2.2, 0.55))
OLIVE = mat('oliva', (0.17, 0.20, 0.09), 0.42)
BRASS = mat('laton', (0.80, 0.60, 0.30), 0.3, 1.0)
STEEL = mat('acero', (0.03, 0.03, 0.03), 0.35, 0.6)
IRON = mat('hierro', (0.12, 0.16, 0.20), 0.45, 0.4)
BIRCH = mat('panel', (0.72, 0.60, 0.44), 0.6)
TOOL = mat('herramienta', (0.55, 0.56, 0.58), 0.25, 1.0)
RAG = mat('trapo', (0.55, 0.06, 0.04), 0.9)
LAMPM = mat('lampara', (0.02, 0.02, 0.02), 0.4, 0.2)
OUTSIDE = mat('exterior', (0.75, 0.55, 0.40), 0.9)
FRAME = mat('marco', (0.02, 0.02, 0.02), 0.5)

GLASS = bpy.data.materials.new('vidrio'); GLASS.use_nodes = True
nt = GLASS.node_tree; nt.nodes.clear()
o = nt.nodes.new('ShaderNodeOutputMaterial'); tr = nt.nodes.new('ShaderNodeBsdfTransparent'); gl = nt.nodes.new('ShaderNodeBsdfGlossy')
gl.inputs['Roughness'].default_value = 0.05; mx = nt.nodes.new('ShaderNodeMixShader'); mx.inputs[0].default_value = 0.08
nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(gl.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], o.inputs[0])

def emit(name, strength, color=(1, 0.95, 0.88)):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new('ShaderNodeOutputMaterial'); e = nt.nodes.new('ShaderNodeEmission')
    e.inputs['Color'].default_value = (*color, 1); e.inputs['Strength'].default_value = strength
    nt.links.new(e.outputs[0], o.inputs[0]); return m

# ---------------- geometría ----------------
def box(name, cx, cy, cz, sx, sy, sz, m, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=(cx, cy, cz))
    ob = bpy.context.object; ob.name = name; ob.scale = (sx / 2, sy / 2, sz / 2)
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        b = ob.modifiers.new('bv', 'BEVEL'); b.width = bevel; b.segments = 2
    ob.data.materials.append(m); return ob

def cyl(name, loc, r, depth, m, rot=(0, 0, 0), verts=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    ob = bpy.context.object; ob.name = name; ob.data.materials.append(m); bpy.ops.object.shade_smooth(); return ob

def plane_img(name, path, width, height, loc, rot, alpha=True, rough=0.6, flip=True):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    ob = bpy.context.object; ob.name = name; ob.scale = (-width if flip else width, height, 1)
    bpy.ops.object.transform_apply(scale=True)
    ob.data.materials.append(mat(name + '_m', (1, 1, 1), rough, tex=path, alpha_img=alpha)); return ob

W2, D, HT = 3.5, 11.0, 3.4
box('suelo', 0, D / 2, -0.05, 2 * W2 + 0.4, D + 0.4, 0.1, CONC)
box('techo', 0, D / 2, HT + 0.05, 2 * W2 + 0.4, D + 0.4, 0.1, CEIL)
box('pared_izq', -W2 - 0.05, D / 2, HT / 2, 0.1, D, HT, WHITE)
box('pared_der', W2 + 0.05, D / 2, HT / 2, 0.1, D, HT, WHITE)
box('pared_entrada', 0, -0.6, HT / 2, 2 * W2, 0.1, HT, WHITE)
# pared del fondo con portón acristalado (x -1.6..1.6, z 0..2.9)
DW, DH = 1.6, 2.9
box('fondo_izq', -(W2 + DW) / 2, D + 0.05, HT / 2, W2 - DW, 0.1, HT, WHITE)
box('fondo_der', (W2 + DW) / 2, D + 0.05, HT / 2, W2 - DW, 0.1, HT, WHITE)
box('fondo_dintel', 0, D + 0.05, (DH + HT) / 2, 2 * DW, 0.1, HT - DH, WHITE)
box('vidrio', 0, D + 0.05, DH / 2, 2 * DW, 0.01, DH, GLASS)
for k in range(5):
    x = -DW + k * (2 * DW / 4)
    box(f'montante{k}', x, D + 0.02, DH / 2, 0.05, 0.08, DH, FRAME)
for z in (0.02, 1.0, 2.0, DH - 0.02):
    box(f'travesano{z}', 0, D + 0.02, z, 2 * DW, 0.08, 0.05, FRAME)
# exterior: suelo de terracota, muro encalado y luz
box('calle', 0, D + 6, -0.06, 20, 12, 0.1, OUTSIDE)
box('muro_ext', 0, D + 9, 1.5, 20, 0.3, 3, mat('muro', (0.92, 0.90, 0.86), 0.9))
# luminarias lineales en el techo
LED = emit('led', 2.5)
for x in (-1.4, 1.4):
    box(f'led{x}', x, 5.5, HT - 0.03, 0.08, 4.0, 0.04, LED)

# ---- zona de trabajo (izquierda) ----
BX = -W2 + 0.38
box('encimera', BX, 4.6, 0.92, 0.76, 4.2, 0.07, OAK, bevel=0.01)
for k, y in enumerate((3.05, 4.6, 6.15)):
    box(f'cajonera{k}', BX + 0.02, y, 0.43, 0.6, 1.4, 0.84, OLIVE, bevel=0.008)
    for r in range(4):
        z = 0.14 + r * 0.2
        box(f'junta{k}{r}', BX + 0.325, y, z + 0.1, 0.004, 1.36, 0.006, STEEL)
        box(f'tirador{k}{r}', BX + 0.34, y, z + 0.03, 0.02, 0.22, 0.025, BRASS)
# tornillo de banco
box('tornillo_base', BX + 0.2, 3.0, 0.99, 0.18, 0.22, 0.07, IRON)
box('tornillo_mordaza', BX + 0.25, 3.0, 1.1, 0.12, 0.26, 0.16, IRON)
cyl('tornillo_husillo', (BX + 0.42, 3.0, 1.06), 0.015, 0.3, TOOL, rot=(0, math.pi / 2, 0))
# carburador desmontado sobre un trapo rojo
box('trapo', BX + 0.1, 4.2, 0.958, 0.38, 0.45, 0.004, RAG)
cyl('carbu_cuerpo', (BX + 0.08, 4.15, 1.0), 0.05, 0.09, TOOL, rot=(math.pi / 2, 0, 0))
cyl('carbu_cuba', (BX + 0.16, 4.3, 0.985), 0.045, 0.05, TOOL)
for k in range(4): cyl(f'tornillo{k}', (BX + 0.0 + k * 0.05, 4.42, 0.965), 0.007, 0.02, BRASS)
# lámpara articulada
cyl('lamp_base', (BX + 0.12, 5.9, 0.97), 0.08, 0.03, LAMPM)
cyl('lamp_brazo1', (BX + 0.12, 5.9, 1.22), 0.012, 0.5, LAMPM, rot=(0.25, 0, 0))
cyl('lamp_brazo2', (BX + 0.22, 5.75, 1.48), 0.012, 0.42, LAMPM, rot=(1.2, 0, -0.5))
cyl('lamp_pantalla', (BX + 0.38, 5.55, 1.45), 0.09, 0.16, LAMPM, rot=(2.2, 0, -0.5))
box('lamp_bombilla', BX + 0.42, 5.5, 1.39, 0.06, 0.06, 0.02, emit('bombilla', 30, (1, 0.8, 0.55)))
# panel de herramientas de abedul con pocas herramientas
box('panel', -W2 + 0.01, 4.6, 1.62, 0.02, 3.2, 0.95, BIRCH)
for k in range(9):
    y = 3.25 + k * 0.17; L = 0.22 + 0.03 * (k % 3)
    box(f'llave{k}', -W2 + 0.03, y, 1.75 - L / 2, 0.012, 0.035, L, TOOL)
for k in range(3):
    cyl(f'destornillador{k}', (-W2 + 0.04, 5.0 + k * 0.12, 1.55), 0.012, 0.22, mat(f'mango{k}', [(0.6, 0.1, 0.05), (0.8, 0.6, 0.1), (0.1, 0.2, 0.4)][k], 0.4))
box('alicates', -W2 + 0.03, 5.6, 1.6, 0.012, 0.06, 0.26, TOOL)
box('sierra', -W2 + 0.03, 5.85, 1.62, 0.01, 0.16, 0.5, TOOL)
# carteles (diseño original, estilo de época)
for k, y in enumerate((7.4, 8.3, 9.2)):
    box(f'cartel_marco{k}', -W2 + 0.015, y, 1.75, 0.02, 0.66, 0.9, FRAME)
    plane_img(f'cartel{k}', T + f'poster{k + 1}.png', 0.6, 0.84, (-W2 + 0.03, y, 1.75), (math.pi / 2, 0, -math.pi / 2), alpha=False)
# rótulo de Santo Pistón en la pared del fondo
plane_img('rotulo', T + 'logo.png', 0.95, 0.95, (-2.55, D - 0.005, 2.05), (math.pi / 2, 0, math.pi), alpha=True, rough=0.35)
# foto enmarcada de las dos Scoopy (pared derecha)
box('print_marco', W2 - 0.015, 8.2, 1.75, 0.02, 1.36, 1.33, FRAME)
plane_img('print_scoopy', T + 'scoopy_print.jpg', 1.26, 1.23, (W2 - 0.03, 8.2, 1.75), (math.pi / 2, 0, math.pi / 2), alpha=False, rough=0.3)

# ---- vehículos: recortes reales como planos verticales ----
def vehicle(name, x, y, yaw_deg, length_override=None):
    png = CUT + name + '.png'; meta = CUT + name + '_meta.json'
    if not (os.path.exists(png) and os.path.exists(meta)) or os.environ.get('NOVEH'): return None
    md = json.load(open(meta)); w_px, h_px = md['width'], md['height']
    gy = md.get('ground_y', h_px); L = length_override or md['length_m']
    sc_m = L / w_px; width = L; height = h_px * sc_m; below = (h_px - gy) * sc_m
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0), rotation=(math.pi / 2, 0, 0))
    ob = bpy.context.object; ob.name = name; ob.scale = (width, height, 1); bpy.ops.object.transform_apply(scale=True, rotation=True)
    ob.location = (x, y, height / 2 - below); ob.rotation_euler = (0, 0, math.radians(yaw_deg))
    m = mat(name + '_m', (1, 1, 1), 0.5, tex=png, alpha_img=True); ob.data.materials.append(m)
    ob.visible_shadow = True
    # sombra de contacto suave en el suelo
    sh = plane_img(name + '_sombra', T + 'shadow.png', L * 1.05, L * 0.42, (x, y, 0.003), (0, 0, math.radians(yaw_deg)), alpha=True, rough=1.0, flip=False)
    sh.visible_shadow = False
    return ob

VEH = dict(
    scoopy_roja=dict(x=2.25, y=3.2, yaw=-12),
    montesa_lift=dict(x=2.0, y=5.3, yaw=-10),
    enduro75=dict(x=2.05, y=7.3, yaw=-12),
    cota=dict(x=1.5, y=9.5, yaw=-8),
    bultaco_chispa=dict(x=-2.55, y=10.05, yaw=8),
)
# galería de fotos del proceso (pared derecha, sobre las motos)
for k in range(5):
    y = 2.35 + k * 0.78
    box(f'galeria_marco{k}', W2 - 0.015, y, 2.25, 0.02, 0.62, 0.76, FRAME)
    plane_img(f'galeria{k}', T + f'proceso{k}.jpg', 0.58, 0.72, (W2 - 0.03, y, 2.25), (math.pi / 2, 0, math.pi / 2), alpha=False, rough=0.35)
for k, v in VEH.items(): vehicle(k, v['x'], v['y'], v['yaw'])

# ---------------- luz ----------------
world = bpy.data.worlds.new('cielo'); sc.world = world; world.use_nodes = True
bg = world.node_tree.nodes['Background']; bg.inputs['Color'].default_value = (0.75, 0.85, 1.0, 1); bg.inputs['Strength'].default_value = 0.9
sun = bpy.data.lights.new('sol', 'SUN'); sun.energy = 11.0; sun.color = (1.0, 0.9, 0.76); sun.angle = math.radians(1.2)
so = bpy.data.objects.new('sol', sun); sc.collection.objects.link(so)
so.rotation_euler = (math.radians(-71), 0, math.radians(-18))
fill = bpy.data.lights.new('relleno', 'AREA'); fill.energy = 90; fill.size = 4; fill.color = (1, 0.95, 0.88)
fo = bpy.data.objects.new('relleno', fill); sc.collection.objects.link(fo); fo.location = (0, 5.0, HT - 0.1)
door = bpy.data.lights.new('portal', 'AREA'); door.energy = 160; door.size = 3.2; door.shape = 'RECTANGLE'; door.size_y = 2.9
do = bpy.data.objects.new('portal', door); sc.collection.objects.link(do); do.location = (0, D - 0.1, 1.45); do.rotation_euler = (math.radians(-90), 0, 0)

# ---------------- render ----------------
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.cycles.samples = int(os.environ.get('SAMPLES', 48)); sc.cycles.use_denoising = True; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.04
sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 16
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
sc.view_settings.exposure = float(os.environ.get('EXPO', -0.2))
sc.render.resolution_y = RES_Y; sc.render.resolution_x = RES_Y * 9 // 16
sc.render.fps = FPS; sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 92

# ---------------- planos de cámara (recorrido tipo inmobiliaria) ----------------
# cada plano: duración, lente, [ (t, pos, objetivo) ... ]
SHOTS = {
 'entrada':  (4.0, 20, [(0, (0.0, -0.4, 1.55), (0.0, 8, 1.2)), (1, (0.15, 1.0, 1.5), (-0.2, 9, 1.15))]),
 'banco':    (3.0, 28, [(0, (-1.2, 2.3, 1.45), (-3.4, 3.4, 0.95)), (1, (-1.25, 3.4, 1.4), (-3.4, 4.7, 0.95))]),
 'detalle':  (2.0, 45, [(0, (-2.2, 3.7, 1.35), (-3.0, 4.25, 0.95)), (1, (-2.15, 3.95, 1.3), (-3.0, 4.15, 0.97))]),
 'scoopy':   (3.0, 30, [(0, (0.1, 1.9, 1.0), (2.3, 3.2, 0.55)), (1, (0.35, 2.3, 0.95), (2.3, 3.25, 0.55))]),
 'galeria':  (3.0, 30, [(0, (1.3, 2.4, 1.95), (3.5, 3.0, 2.2)), (1, (1.4, 4.2, 1.95), (3.5, 4.8, 2.2))]),
 'fiat':     (2.0, 28, [(0, (0.2, -0.4, 1.55), (2.3, 1.6, 0.45)), (1, (0.45, -0.2, 1.5), (2.3, 1.6, 0.45))]),
 'enduro':   (3.5, 30, [(0, (0.0, 5.6, 1.05), (2.05, 7.3, 0.6)), (1, (0.3, 6.0, 1.0), (2.05, 7.35, 0.6))]),
 'print':    (2.0, 32, [(0, (0.9, 6.9, 1.7), (3.5, 8.2, 1.75)), (1, (1.1, 7.2, 1.7), (3.5, 8.2, 1.75))]),
 'bultaco':  (3.5, 30, [(0, (-0.6, 7.6, 1.5), (-2.55, 10.4, 1.3)), (1, (-0.9, 8.1, 1.45), (-2.55, 10.4, 1.35))]),
 'cota':     (2.5, 32, [(0, (-0.4, 7.9, 1.1), (1.5, 9.5, 0.6)), (1, (-0.2, 8.2, 1.05), (1.5, 9.5, 0.6))]),
 'final':    (3.5, 20, [(0, (-1.5, 0.0, 2.15), (0.6, 9, 0.9)), (1, (-1.2, 0.4, 2.2), (0.6, 9, 0.95))]),
}
ORDER = ['entrada', 'banco', 'detalle', 'scoopy', 'galeria', 'enduro', 'print', 'bultaco', 'cota', 'final']
HIDE = {'galeria': ['scoopy_roja', 'scoopy_roja_sombra']}

def smooth(u): return u * u * (3 - 2 * u)
def setup_cam(name, u):
    for ob in bpy.data.objects: ob.hide_render = ob.name in HIDE.get(name, [])
    dur, lens, keys = SHOTS[name]
    (_, p0, t0), (_, p1, t1) = keys
    e = smooth(u)
    pos = Vector(p0).lerp(Vector(p1), e); tgt = Vector(t0).lerp(Vector(t1), e)
    cam = sc.camera
    cam.location = pos
    cam.rotation_euler = (tgt - pos).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens

camd = bpy.data.cameras.new('cam'); camd.sensor_fit = 'HORIZONTAL'; camd.sensor_width = 36
cam = bpy.data.objects.new('cam', camd); sc.collection.objects.link(cam); sc.camera = cam
camd.dof.use_dof = False

if MODE == 'stills':
    only = sys.argv[4].split(',') if len(sys.argv) > 4 else ORDER
    for name in only:
        setup_cam(name, 0.5)
        sc.render.filepath = OUT + f'still_{name}.jpg'; bpy.ops.render.render(write_still=True)
elif MODE == 'anim':
    name = sys.argv[4]; dur = SHOTS[name][0]; n = int(round(dur * FPS_R)) + 1
    part, parts = (int(sys.argv[5]), int(sys.argv[6])) if len(sys.argv) > 6 else (0, 1)
    os.makedirs(OUT + name, exist_ok=True)
    for i in range(part, n, parts):
        fp = OUT + f'{name}/{i:04d}.jpg'
        if os.path.exists(fp): continue
        setup_cam(name, i / max(n - 1, 1) * (dur * FPS_R) / (dur * FPS_R))
        sc.render.filepath = fp; bpy.ops.render.render(write_still=True)
elif MODE == 'save':
    bpy.ops.wm.save_as_mainfile(filepath=S + '/tour/garaje.blend')
