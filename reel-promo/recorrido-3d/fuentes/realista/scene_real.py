"""Taller Santo Pistón, versión realista (Blender 5.3, Cycles).
Materiales y objetos fotoescaneados de Poly Haven (CC0). Sin motos (por ahora).
Uso:
  python3 scene_real.py <scratchpad> stills <res_y> [planos]
  python3 scene_real.py <scratchpad> anim <res_y> <plano>
"""
import bpy, sys, os, json, math, glob
from mathutils import Vector, Euler

S = sys.argv[1]; MODE = sys.argv[2]; RES_Y = int(sys.argv[3])
PH = S + '/ph/'; TR = S + '/tour/tex_real/'; T = S + '/tour/tex/'
OUT = S + '/tour/render_real/'; os.makedirs(OUT, exist_ok=True)
FPS_R = int(os.environ.get('FPS_R', 10))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
R = math.radians

# ---------------- materiales ----------------
def _img(nt, path, srgb=True):
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(path, check_existing=True)
    if not srgb: n.image.colorspace_settings.name = 'Non-Color'
    n.projection = 'BOX'; n.projection_blend = 0.25
    return n

def pbr(name, tex, size_m, tint=None, rough_add=0.0, nor_str=1.0, coord='Object', rot=0.0):
    """Material PBR con proyección en caja a escala real (size_m = metros que cubre la textura)."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; p = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1 / size_m,) * 3; mp.inputs['Rotation'].default_value = (0, 0, rot)
    nt.links.new(tc.outputs[coord], mp.inputs['Vector'])
    d = PH + 'tex/' + tex + '/'
    col = _img(nt, d + 'diff.jpg'); nt.links.new(mp.outputs[0], col.inputs[0])
    out_col = col.outputs['Color']
    if os.path.exists(d + 'ao.jpg'):
        ao = _img(nt, d + 'ao.jpg', False); nt.links.new(mp.outputs[0], ao.inputs[0])
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 0.6
        nt.links.new(out_col, mx.inputs['A']); nt.links.new(ao.outputs['Color'], mx.inputs['B']); out_col = mx.outputs['Result']
    if tint:
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
        mx.inputs['B'].default_value = (*tint, 1); nt.links.new(out_col, mx.inputs['A']); out_col = mx.outputs['Result']
    nt.links.new(out_col, p.inputs['Base Color'])
    r = _img(nt, d + 'rough.jpg', False); nt.links.new(mp.outputs[0], r.inputs[0])
    if rough_add:
        ma = nt.nodes.new('ShaderNodeMath'); ma.operation = 'ADD'; ma.use_clamp = True; ma.inputs[1].default_value = rough_add
        nt.links.new(r.outputs['Color'], ma.inputs[0]); nt.links.new(ma.outputs[0], p.inputs['Roughness'])
    else:
        nt.links.new(r.outputs['Color'], p.inputs['Roughness'])
    n = _img(nt, d + 'nor.jpg', False); nt.links.new(mp.outputs[0], n.inputs[0])
    nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = nor_str
    nt.links.new(n.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], p.inputs['Normal'])
    return m

def flat(name, color, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*color, 1); p.inputs['Roughness'].default_value = rough; p.inputs['Metallic'].default_value = metal
    return m

def emit(name, strength, color=(1, 0.93, 0.82)):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new('ShaderNodeOutputMaterial'); e = nt.nodes.new('ShaderNodeEmission')
    e.inputs['Color'].default_value = (*color, 1); e.inputs['Strength'].default_value = strength
    nt.links.new(e.outputs[0], o.inputs[0]); return m

def sign_mat(name, base):
    """Chapa esmaltada: color + rugosidad propias, ligera metalicidad en el óxido."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; p = nt.nodes['Principled BSDF']
    c = nt.nodes.new('ShaderNodeTexImage'); c.image = bpy.data.images.load(TR + base + '.png'); c.interpolation = 'Cubic'
    r = nt.nodes.new('ShaderNodeTexImage'); r.image = bpy.data.images.load(TR + base + '_r.png'); r.image.colorspace_settings.name = 'Non-Color'
    nt.links.new(c.outputs['Color'], p.inputs['Base Color']); nt.links.new(c.outputs['Alpha'], p.inputs['Alpha'])
    nt.links.new(r.outputs['Color'], p.inputs['Roughness'])
    p.inputs['Coat Weight'].default_value = 0.25; p.inputs['Coat Roughness'].default_value = 0.25
    b = nt.nodes.new('ShaderNodeBump'); b.inputs['Strength'].default_value = 0.08
    nt.links.new(r.outputs['Color'], b.inputs['Height']); nt.links.new(b.outputs['Normal'], p.inputs['Normal'])
    return m

def grime(m, ao_dist=0.0, stain_scale=0.0, stain_amt=0.0, base_z=0.0, dark=(0.32, 0.29, 0.26), oil_rough=None, seed=0.0, ramp=(0.58, 0.72)):
    """Suciedad realista: oscurece rincones (AO), manchas de aceite (ruido) y salpicaduras en la base de la pared."""
    nt = m.node_tree; p = nt.nodes['Principled BSDF']
    if p.inputs['Base Color'].links: src = p.inputs['Base Color'].links[0].from_socket
    else:
        rgb = nt.nodes.new('ShaderNodeRGB'); rgb.outputs[0].default_value = p.inputs['Base Color'].default_value; src = rgb.outputs[0]
    fac = None
    def add(a, b):
        mth = nt.nodes.new('ShaderNodeMath'); mth.operation = 'ADD'; mth.use_clamp = True
        nt.links.new(a, mth.inputs[0]); nt.links.new(b, mth.inputs[1]); return mth.outputs[0]
    if ao_dist:
        ao = nt.nodes.new('ShaderNodeAmbientOcclusion'); ao.samples = 6; ao.inputs['Distance'].default_value = ao_dist
        inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'MULTIPLY_ADD'; inv.inputs[1].default_value = -1.1; inv.inputs[2].default_value = 1.1
        nt.links.new(ao.outputs['AO'], inv.inputs[0]); fac = inv.outputs[0]
    stain = None
    if stain_scale:
        geo = nt.nodes.new('ShaderNodeNewGeometry')
        nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = stain_scale; nz.inputs['Detail'].default_value = 8; nz.inputs['Roughness'].default_value = 0.62
        nz.noise_dimensions = '4D'; nz.inputs['W'].default_value = seed
        nt.links.new(geo.outputs['Position'], nz.inputs['Vector'])
        cr = nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].position = ramp[0]; cr.color_ramp.elements[1].position = ramp[1]
        nt.links.new(nz.outputs['Fac'], cr.inputs[0])
        sm = nt.nodes.new('ShaderNodeMath'); sm.operation = 'MULTIPLY'; sm.inputs[1].default_value = stain_amt
        nt.links.new(cr.outputs['Color'], sm.inputs[0]); stain = sm.outputs[0]
        fac = add(fac, stain) if fac else stain
    if base_z:
        geo = nt.nodes.new('ShaderNodeNewGeometry'); sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(geo.outputs['Position'], sx.inputs[0])
        mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.0; mr.inputs['From Max'].default_value = base_z
        mr.inputs['To Min'].default_value = 0.55; mr.inputs['To Max'].default_value = 0.0
        nt.links.new(sx.outputs['Z'], mr.inputs['Value'])
        nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 9; nz.inputs['Detail'].default_value = 6
        nt.links.new(geo.outputs['Position'], nz.inputs['Vector'])
        mu = nt.nodes.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'; nt.links.new(mr.outputs[0], mu.inputs[0]); nt.links.new(nz.outputs['Fac'], mu.inputs[1])
        mu2 = nt.nodes.new('ShaderNodeMath'); mu2.operation = 'MULTIPLY'; mu2.inputs[1].default_value = 1.6; nt.links.new(mu.outputs[0], mu2.inputs[0])
        fac = add(fac, mu2.outputs[0]) if fac else mu2.outputs[0]
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
    mx.inputs['B'].default_value = (*dark, 1); nt.links.new(fac, mx.inputs['Factor']); nt.links.new(src, mx.inputs['A'])
    nt.links.new(mx.outputs['Result'], p.inputs['Base Color'])
    if oil_rough is not None and stain is not None:   # el aceite brilla
        rs = p.inputs['Roughness'].links[0].from_socket
        mr = nt.nodes.new('ShaderNodeMix'); mr.data_type = 'FLOAT'; mr.inputs['B'].default_value = oil_rough
        nt.links.new(stain, mr.inputs['Factor']); nt.links.new(rs, mr.inputs['A']); nt.links.new(mr.outputs[0], p.inputs['Roughness'])
    return m

BRICK = pbr('ladrillo', 'factory_brick', 1.5)
FLOOR = pbr('suelo', 'garage_floor', 1.9, nor_str=0.6)
CEIL = pbr('techo', 'plaster_grey_04', 1.5, tint=(1.0, 0.98, 0.95))
BEAM = pbr('viga', 'dark_wood', 1.0)
DARKWALL = pbr('pared_gris', 'plaster_grey_04', 1.5, tint=(0.13, 0.14, 0.15))
TOP = pbr('tablero', 'wood_table_worn', 0.55, tint=(0.82, 0.8, 0.76), rough_add=0.05)
grime(BRICK, base_z=0.6, dark=(0.45, 0.4, 0.36))
grime(FLOOR, ao_dist=0.6, stain_scale=1.1, stain_amt=1.0, dark=(0.2, 0.19, 0.18), oil_rough=0.2, seed=1.7, ramp=(0.52, 0.68))
grime(TOP, stain_scale=4.0, stain_amt=0.75, dark=(0.35, 0.3, 0.26), oil_rough=0.3, seed=4.2)
SHELFW = pbr('balda', 'wood_table_worn', 0.55, tint=(0.7, 0.66, 0.6), rough_add=0.1)
STEEL = flat('acero_pintado', (0.06, 0.1, 0.08), 0.42)
FRAME = flat('marco', (0.02, 0.02, 0.02), 0.5)
GLASS = bpy.data.materials.new('vidrio'); GLASS.use_nodes = True
_nt = GLASS.node_tree; _p = _nt.nodes['Principled BSDF']
_p.inputs['Transmission Weight'].default_value = 1.0; _p.inputs['Roughness'].default_value = 0.16; _p.inputs['IOR'].default_value = 1.45
PEG = bpy.data.materials.new('perforado'); PEG.use_nodes = True
_nt = PEG.node_tree; _p = _nt.nodes['Principled BSDF']; _p.inputs['Roughness'].default_value = 0.75
_tc = _nt.nodes.new('ShaderNodeTexCoord'); _mp = _nt.nodes.new('ShaderNodeMapping'); _mp.inputs['Scale'].default_value = (2.0,) * 3
_im = _nt.nodes.new('ShaderNodeTexImage'); _im.image = bpy.data.images.load(TR + 'pegboard.jpg'); _im.projection = 'BOX'
_nt.links.new(_tc.outputs['Object'], _mp.inputs[0]); _nt.links.new(_mp.outputs[0], _im.inputs[0]); _nt.links.new(_im.outputs['Color'], _p.inputs['Base Color'])

# ---------------- geometría básica ----------------
def box(name, cx, cy, cz, sx, sy, sz, m, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=(cx, cy, cz))
    ob = bpy.context.object; ob.name = name; ob.scale = (sx / 2, sy / 2, sz / 2)
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        b = ob.modifiers.new('bv', 'BEVEL'); b.width = bevel; b.segments = 2
    ob.data.materials.append(m); return ob

def plane_img(name, mat_, w, h, loc, rot):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    ob = bpy.context.object; ob.name = name; ob.scale = (-w, h, 1); bpy.ops.object.transform_apply(scale=True)
    ob.data.materials.append(mat_); return ob

# ---------------- modelos Poly Haven ----------------
def model(name, loc, rot=(0, 0, 0), fit=None, anchor='bottom', tag=None, only=None):
    """Importa un glTF, lo agrupa en un vacío, lo recentra (base o centro) y lo escala si se pide fit=(eje|'max', metros)."""
    path = glob.glob(PH + 'models/' + name + '/*.gltf')[0]
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in [o for o in new if o.type == 'MESH' and (not o.data.materials or (only and only not in o.name))]:   # auxiliares del rig
        new.remove(o); bpy.data.objects.remove(o, do_unlink=True)
    for im in bpy.data.images:   # texturas retocadas (sin rótulos ajenos)
        fx = S + '/tour/tex_fix/' + os.path.basename(im.filepath)
        if im.filepath and os.path.exists(fx) and im.filepath != fx:
            nw = bpy.data.images.load(fx); nw.colorspace_settings.name = im.colorspace_settings.name; im.user_remap(nw)
    root = bpy.data.objects.new((tag or name) + '_root', None); sc.collection.objects.link(root)
    tops = [o for o in new if o.parent is None]
    for o in tops: o.parent = root
    bpy.context.view_layer.update()
    mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
    for o in new:
        if o.type != 'MESH': continue
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c); mn = Vector(map(min, mn, w)); mx = Vector(map(max, mx, w))
    size = mx - mn
    k = 1.0
    if fit:
        ax, val = fit
        k = val / (max(size) if ax == 'max' else size['xyz'.index(ax)])
    ctr = (mn + mx) / 2
    off = Vector((-ctr.x, -ctr.y, -mn.z)) if anchor == 'bottom' else -ctr
    for o in tops:
        o.location = (o.location + off) * k; o.scale = o.scale * k
    root.location = loc; root.rotation_euler = Euler(tuple(R(a) for a in rot), 'XYZ')
    return root

# ================= ESTRUCTURA =================
W2, D, HT = 3.5, 11.0, 3.4
box('suelo', 0, D / 2, -0.05, 2 * W2 + 0.4, D + 0.4, 0.1, FLOOR)
box('techo', 0, D / 2, HT + 0.05, 2 * W2 + 0.4, D + 0.4, 0.1, CEIL)
box('pared_izq', -W2 - 0.05, D / 2, HT / 2, 0.1, D, HT, BRICK)
box('pared_der', W2 + 0.05, D / 2, HT / 2, 0.1, D, HT, BRICK)
box('pared_entrada', 0, -0.6, HT / 2, 2 * W2, 0.1, HT, BRICK)
DW, DH = 1.6, 2.9
box('fondo_izq', -(W2 + DW) / 2, D + 0.05, HT / 2, W2 - DW, 0.1, HT, BRICK)
box('fondo_der', (W2 + DW) / 2, D + 0.05, HT / 2, W2 - DW, 0.1, HT, BRICK)
box('fondo_dintel', 0, D + 0.05, (DH + HT) / 2, 2 * DW, 0.1, HT - DH, BRICK)
box('vidrio', 0, D + 0.05, DH / 2, 2 * DW, 0.008, DH, GLASS)
for k in range(5):
    box(f'montante{k}', -DW + k * (2 * DW / 4), D + 0.03, DH / 2, 0.05, 0.08, DH, FRAME)
for z in (0.03, 1.0, 2.0, DH - 0.03):
    box(f'travesano{z}', 0, D + 0.03, z, 2 * DW, 0.08, 0.05, FRAME)
# zócalo de hormigón (rodapié) y vigas
for k in range(9):
    box(f'viga{k}', 0, 0.4 + k * 1.3, HT - 0.12, 2 * W2, 0.18, 0.24, BEAM)
box('viga_long', 0, D / 2, HT - 0.30, 0.22, D, 0.14, BEAM)

# ================= ZONA DE TRABAJO (pared izquierda) =================
BX0 = -W2                       # pared
BD, BZ, BY0, BY1 = 0.76, 0.92, 2.05, 4.75   # fondo, altura de tablero, extremos
BXC = BX0 + BD / 2 + 0.02
box('banco_tablero', BXC, (BY0 + BY1) / 2, BZ + 0.03, BD, BY1 - BY0, 0.06, TOP, bevel=0.006)
for y in (BY0 + 0.06, BY1 - 0.06, (BY0 + BY1) / 2):
    for x in (BX0 + 0.08, BX0 + BD - 0.04):
        box(f'pata{x:.2f}{y:.2f}', x, y, BZ / 2, 0.05, 0.05, BZ, STEEL, bevel=0.004)
box('larguero_f', BX0 + BD - 0.04, (BY0 + BY1) / 2, BZ - 0.06, 0.05, BY1 - BY0 - 0.1, 0.06, STEEL)
box('larguero_t', BX0 + 0.08, (BY0 + BY1) / 2, BZ - 0.06, 0.05, BY1 - BY0 - 0.1, 0.06, STEEL)
box('balda_inf', BXC, (BY0 + BY1) / 2, 0.18, BD - 0.06, BY1 - BY0 - 0.12, 0.03, SHELFW)
box('peto', BX0 + 0.04, (BY0 + BY1) / 2, BZ + 0.2, 0.02, BY1 - BY0, 0.28, SHELFW)
# panel perforado
box('panel', BX0 + 0.012, 3.4, 1.62, 0.012, 2.5, 1.05, PEG)
for y in (2.15, 4.65):
    box(f'listón{y}', BX0 + 0.02, y, 1.62, 0.025, 0.04, 1.1, SHELFW)
# balda superior con luz de trabajo debajo
box('balda_sup', BX0 + 0.16, 3.4, 2.28, 0.3, 2.7, 0.03, SHELFW, bevel=0.003)
for y in (2.2, 4.6):
    box(f'escuadra{y}', BX0 + 0.12, y, 2.2, 0.2, 0.02, 0.14, STEEL)
box('tubo_trabajo', BX0 + 0.25, 3.4, 2.245, 0.035, 1.5, 0.03, emit('tubo_t', 18, (1, 0.92, 0.8)))
tl = bpy.data.lights.new('luz_banco', 'AREA'); tl.energy = 70; tl.size = 1.5; tl.shape = 'RECTANGLE'; tl.size_y = 0.08; tl.color = (1, 0.88, 0.74)
tlo = bpy.data.objects.new('luz_banco', tl); sc.collection.objects.link(tlo); tlo.location = (BX0 + 0.27, 3.4, 2.22); tlo.rotation_euler = (0, 0, R(90))

# herramientas colgadas: (modelo, y, z, rotación, escala opcional)
TOP_Z = BZ + 0.06
PX = BX0 + 0.03
HANG = [
    ('handsaw_wood', 2.65, 1.93, (0, 0, 0)),
    ('rusted_hacksaw', 2.62, 1.55, (0, 0, 90)),
    ('pipe_wrench', 3.08, 1.6, (0, 0, 90)),
    ('cross_pein_hammer', 3.3, 1.66, (0, 0, 90)),
    ('wooden_hammer_01', 3.48, 1.66, (0, 0, 90)),
    ('adjustable_wrench', 3.66, 1.72, (0, 0, 90)),
    ('ratchet_wrench', 3.8, 1.72, (0, 0, 90)),
    ('pliers', 3.62, 1.33, (0, 0, 90)),
    ('tongue_groove_pliers', 3.82, 1.33, (90, 0, 90)),
    ('screwdriver', 3.1, 1.25, (0, 0, 0)),
    ('flathead_screwdriver', 3.2, 1.25, (0, 0, 0)),
    ('screwdriver', 3.3, 1.24, (0, 0, 0)),
]
for i, (nm, y, z, rot) in enumerate(HANG):
    r = model(nm, (PX + 0.035, y, z), rot, anchor='center', tag=f'colg{i}')
for i, s_ in enumerate((0.62, 0.72, 0.84, 0.96, 1.1)):   # juego de llaves combinadas
    model('combination_wrench', (PX + 0.02, 4.0 + i * 0.09, 1.72), (90, 0, 90), fit=('max', 0.34 * s_ * 0.75), anchor='center', tag=f'llave{i}')

# sobre el banco
model('bench_vice_01', (BX0 + BD - 0.12, 2.4, TOP_Z), (0, 0, 90), tag='tornillo')
model('metal_toolbox', (BX0 + 0.3, 4.38, TOP_Z), (0, 0, 90))
model('oil_tin', (BX0 + 0.2, 4.0, TOP_Z), (0, 0, 15))
model('small_oil_can_01', (BX0 + 0.42, 3.92, TOP_Z), (0, 0, 70))
model('lubricant_spray', (BX0 + 0.16, 3.78, TOP_Z), (0, 0, 0))
model('spray_paint_bottles', (BX0 + 0.18, 3.6, TOP_Z), (0, 0, 80))
model('screwdrivers_02', (BX0 + 0.5, 3.05, TOP_Z), (0, 0, 20))
model('measuring_tape_01', (BX0 + 0.55, 3.35, TOP_Z), (0, 0, -30))
model('adjustable_wrench', (BX0 + 0.6, 2.85, TOP_Z + 0.015), (90, 0, 60), anchor='center', tag='llave_banco')
model('pliers', (BX0 + 0.42, 2.78, TOP_Z + 0.01), (90, 0, -25), anchor='center', tag='alicate_banco')
model('Drill_01', (BX0 + 0.45, 3.55, TOP_Z + 0.025), (90, 0, 140), anchor='center', tag='taladro')
model('can_rusted', (BX0 + 0.16, 2.72, TOP_Z))
model('cleaner_tin_01', (BX0 + 0.15, 4.62, TOP_Z))
# bajo el banco
model('cardboard_box_01', (BX0 + 0.38, 2.6, 0.195), (0, 0, 85))
model('plastic_crate_01', (BX0 + 0.38, 3.35, 0.195), (0, 0, 90))
model('metal_jerrycan', (BX0 + 0.4, 4.25, 0.195), (0, 0, 95))
model('metal_stool_01', (-2.45, 3.75, 0), (0, 0, 20))
# carro de herramientas con cofre encima
cart = model('tool_cart', (BX0 + 0.42, 5.6, 0), (0, 0, 90))
model('metal_tool_chest', (BX0 + 0.3, 5.6, 0.955), (0, 0, 90))
model('old_drill_press', (BX0 + 0.35, 6.75, 0), (0, 0, 90))
model('plastic_broom', (BX0 + 0.12, 1.55, 0), (8, 0, 90))
model('power_box_01', (BX0 + 0.04, 1.2, 1.55), (0, 0, 90), anchor='center')
# rincón del fondo izquierdo
model('Barrel_01', (-2.95, 8.35, 0), (0, 0, 10))
model('Barrel_01', (-2.98, 9.0, 0), (0, 0, 70), tag='bidon2')
model('cardboard_box_01', (-3.05, 9.7, 0), (0, 0, 5), tag='caja2')
model('cardboard_box_01', (-3.05, 9.7, 0.34), (0, 0, 20), tag='caja3')
model('tire_pump', (-2.6, 9.75, 0), (0, 0, 30))
# rincón del fondo derecho
model('old_military_compressor', (2.85, 10.1, 0), (0, 0, 0))
for k in range(4):
    model('old_tyre', (2.95, 5.75, 0.085 + k * 0.17), (90, 0, k * 37), anchor='center', tag=f'neum{k}')
model('old_tyre', (3.32, 7.95, 0.3), (0, 0, 90), anchor='center', tag='neum_pared')

# ================= DECORACIÓN RETRO =================
RW = (R(90), 0, R(-90))   # pared izquierda
LW = (R(90), 0, R(90))    # pared derecha
BK = (R(90), 0, R(180))   # pared del fondo
SIGNS = [
    ('b_campsa', 2.0, 0.583, (BX0 + 0.012, 3.4, 2.72), RW),
    ('b_champion', 1.0, 0.4375, (BX0 + 0.012, 5.75, 2.35), RW),
    ('b_amal', 0.95, 0.355, (BX0 + 0.012, 6.95, 2.25), RW),
    ('b_motul', 0.7, 0.7, (BX0 + 0.012, 8.0, 2.1), RW),
    ('b_ossa', 1.0, 0.5, (W2 - 0.012, 2.4, 2.25), LW),
    ('b_bultaco', 1.25, 0.486, (W2 - 0.012, 3.75, 2.4), LW),
    ('b_pirelli', 1.0, 0.4, (W2 - 0.012, 5.6, 1.75), LW),
    ('b_derbi', 0.95, 0.407, (W2 - 0.022, 7.05, 2.45), LW),
    ('b_sanglas', 1.05, 0.303, (W2 - 0.022, 7.05, 1.65), LW),
    ('b_montesa', 1.2, 0.675, (W2 - 0.022, 8.35, 2.1), LW),
    ('b_castrol', 1.0, 0.5, (W2 - 0.022, 9.6, 2.3), LW),
    ('b_michelin', 1.4, 0.448, (2.5, D - 0.012, 2.55), BK),
    ('b_champion', 0.8, 0.35, (W2 - 0.022, 8.3, 1.3), LW),
    ('b_pirelli', 0.75, 0.3, (W2 - 0.022, 9.6, 0.95), LW),
    ('b_ossa', 0.6, 0.3, (W2 - 0.022, 7.05, 1.05), LW),
]
for nm, w, h, loc, rot in SIGNS:
    ob = plane_img(nm, sign_mat(nm + '_m', nm), w, h, loc, rot)
    so = ob.modifiers.new('esp', 'SOLIDIFY'); so.thickness = 0.004; so.offset = 1
# tramo de pared de coleccionista (gris oscuro) con moldura
box('pared_gris', W2 - 0.006, 8.3, 1.6, 0.012, 3.2, 3.2, DARKWALL)
box('moldura', W2 - 0.03, 8.3, 3.12, 0.06, 3.2, 0.1, flat('moldura_b', (0.82, 0.8, 0.76), 0.5), bevel=0.015)
# tapacubos cromado
CHROME = flat('cromo', (0.92, 0.92, 0.94), 0.06, 1.0)
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.2, depth=0.035, location=(W2 - 0.03, 9.6, 1.45), rotation=(0, R(90), 0))
hub = bpy.context.object; hub.data.materials.append(CHROME); bpy.ops.object.shade_smooth()
bv = hub.modifiers.new('bv', 'BEVEL'); bv.width = 0.012; bv.segments = 4
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.075, location=(W2 - 0.05, 9.6, 1.45)); c_ = bpy.context.object; c_.scale = (0.45, 1, 1); c_.data.materials.append(CHROME); bpy.ops.object.shade_smooth()
# rótulo de Santo Pistón (pared del fondo)
LOGO = bpy.data.materials.new('logo_m'); LOGO.use_nodes = True
_nt = LOGO.node_tree; _p = _nt.nodes['Principled BSDF']; _im = _nt.nodes.new('ShaderNodeTexImage'); _im.image = bpy.data.images.load(T + 'logo.png')
_nt.links.new(_im.outputs['Color'], _p.inputs['Base Color']); _nt.links.new(_im.outputs['Alpha'], _p.inputs['Alpha']); _p.inputs['Roughness'].default_value = 0.3; _p.inputs['Coat Weight'].default_value = 0.4
ob = plane_img('rotulo', LOGO, 0.95, 0.95, (-2.5, D - 0.012, 2.15), BK); ob.modifiers.new('esp', 'SOLIDIFY').thickness = 0.01

# ================= VIDA DE TALLER (más objetos, cables, puerta) =================
model('korean_fire_extinguisher_01', (W2 - 0.17, 1.15, 0.72), (0, 0, -90), tag='extintor')
box('soporte_ext', W2 - 0.02, 1.15, 1.1, 0.03, 0.1, 0.12, STEEL)
model('wall_clock', (BX0 + 0.03, 1.25, 2.5), (0, 0, 90), anchor='center', tag='reloj')
CAL = bpy.data.materials.new('calendario_m'); CAL.use_nodes = True
_nt = CAL.node_tree; _p = _nt.nodes['Principled BSDF']; _im = _nt.nodes.new('ShaderNodeTexImage'); _im.image = bpy.data.images.load(TR + 'calendario.jpg')
_nt.links.new(_im.outputs['Color'], _p.inputs['Base Color']); _p.inputs['Roughness'].default_value = 0.8
cal = plane_img('calendario', CAL, 0.35, 0.5, (W2 - 0.01, 1.2, 1.75), (R(91.5), 0, R(90)))
model('portable_welding_cart', (2.95, 4.35, 0), (0, 0, -80), tag='soldadura')
model('garden_gloves_01', (BX0 + 0.55, 4.1, TOP_Z), (0, 0, 35), tag='guantes')
model('propane_torch', (BX0 + 0.13, 3.22, TOP_Z), (0, 0, 0), tag='soplete')
model('retro_multimeter', (BX0 + 0.25, 2.98, TOP_Z), (0, 0, 75), fit=('z', 0.2), tag='polimetro')
model('plastic_bottle_gallon', (BX0 + 0.14, 2.32, 2.295), (0, 0, 90), tag='garrafa')
model('multi_cleaner_5_litre', (BX0 + 0.14, 4.55, 2.295), (0, 0, 90), tag='bidon5')
model('oil_tin', (BX0 + 0.14, 4.32, 2.295), (0, 0, 60), tag='lata_sup')
model('bolt_cutters_01', (BX0 + 0.1, 1.78, 0.42), (0, -10, 90), anchor='center', tag='cizalla')
model('crowbar_01', (BX0 + 0.08, 1.92, 0.3), (0, -12, 0), anchor='center', tag='palanca')
model('metal_jerrycan_green', (-2.45, 8.7, 0), (0, 0, 75), tag='bidon_verde')
model('worn_metal_rack', (2.6, -0.25, 0), (0, 0, 180), tag='estanteria')
for k, (nm, z_) in enumerate((('cardboard_box_01', 0.02), ('multi_cleaner_5_litre', 0.02), ('plastic_bottle_gallon', 0.02))):
    model(nm, (2.35 + k * 0.28, -0.22, z_), (0, 0, 15 * k), tag=f'est{k}')
model('hand_truck', (1.35, -0.3, 0), (0, 0, 180), tag='carretilla')
model('dustpan', (BX0 + 0.25, 1.4, 0), (0, 0, 70), tag='recogedor')
# trapo de taller sobre el banco (tela arrugada)
bpy.ops.mesh.primitive_grid_add(x_subdivisions=60, y_subdivisions=60, size=0.26, location=(BX0 + 0.62, 2.62, TOP_Z + 0.002))
rag = bpy.context.object; rag.rotation_euler = (0, 0, R(23)); rag.scale = (1, 0.8, 1)
tx = bpy.data.textures.new('arrugas', 'CLOUDS'); tx.noise_scale = 0.035; tx.noise_depth = 3
dp = rag.modifiers.new('arr', 'DISPLACE'); dp.texture = tx; dp.strength = 0.03; dp.mid_level = 0.0
sw = rag.modifiers.new('pliegue', 'SIMPLE_DEFORM'); sw.deform_method = 'BEND'; sw.angle = R(40); sw.deform_axis = 'Y'
bpy.ops.object.shade_smooth()
RAG = flat('trapo', (0.42, 0.38, 0.33), 0.95); grime(RAG, stain_scale=14, stain_amt=0.8, dark=(0.25, 0.22, 0.2), seed=2.0)
rag.data.materials.append(RAG); rag.hide_render = True   # descartado: no quedaba realista
# canalización eléctrica vista (tubo gris por la pared) y cable alargador por el suelo
PVC = flat('tubo_pvc', (0.42, 0.42, 0.4), 0.55)
def tube(p0, p1, r=0.011, m=PVC):
    v = Vector(p1) - Vector(p0); c = (Vector(p0) + Vector(p1)) / 2
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=r, depth=v.length, location=c)
    o = bpy.context.object; o.rotation_euler = v.to_track_quat('Z', 'Y').to_euler(); o.data.materials.append(m); return o
tube((BX0 + 0.02, -0.5, 2.95), (BX0 + 0.02, D, 2.95))
tube((BX0 + 0.02, 1.2, 2.95), (BX0 + 0.02, 1.2, 1.75))
tube((BX0 + 0.02, 4.95, 2.95), (BX0 + 0.02, 4.95, 1.2))
box('enchufe', BX0 + 0.025, 4.95, 1.15, 0.035, 0.09, 0.12, flat('baquelita', (0.75, 0.73, 0.68), 0.4), bevel=0.008)
tube((W2 - 0.02, -0.5, 2.95), (W2 - 0.02, D, 2.95))
tube((W2 - 0.02, 0.6, 2.95), (W2 - 0.02, 0.6, 1.35))
box('interruptor', W2 - 0.025, 0.6, 1.3, 0.035, 0.08, 0.1, flat('baquelita2', (0.75, 0.73, 0.68), 0.4), bevel=0.008)
RUB = flat('goma', (0.02, 0.02, 0.02), 0.6)
import random as _r; _r.seed(5)
pts = [(BX0 + 0.05, 4.95, 1.12), (BX0 + 0.06, 4.95, 0.02)]
y = 4.95
while y < 6.55:
    y += 0.18; pts.append((BX0 + 0.35 + _r.uniform(-0.12, 0.12), y, 0.006))
pts.append((BX0 + 0.3, 6.65, 0.006))
cu = bpy.data.curves.new('cable', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0045; cu.bevel_resolution = 2
sp = cu.splines.new('NURBS'); sp.points.add(len(pts) - 1); sp.order_u = 4; sp.use_endpoint_u = True
for i, q in enumerate(pts): sp.points[i].co = (*q, 1)
cb = bpy.data.objects.new('cable', cu); sc.collection.objects.link(cb); cu.materials.append(RUB)
# cara interior de la puerta enrollable de chapa en la pared de entrada
CHAPA = flat('chapa_puerta', (0.36, 0.37, 0.37), 0.42, 0.75); grime(CHAPA, stain_scale=3.0, stain_amt=0.7, base_z=0.5, dark=(0.45, 0.4, 0.34), seed=7.0, ramp=(0.5, 0.75))
_tcp = CHAPA.node_tree.nodes.new('ShaderNodeTexCoord')
_ntc = CHAPA.node_tree; _pc = _ntc.nodes['Principled BSDF']
_wv = _ntc.nodes.new('ShaderNodeTexWave'); _wv.wave_type = 'BANDS'; _wv.bands_direction = 'Z'; _wv.wave_profile = 'SIN'; _wv.inputs['Scale'].default_value = 1.0
_mpw = _ntc.nodes.new('ShaderNodeMapping'); _mpw.inputs['Scale'].default_value = (1, 1, 1 / 0.09 * 0.5)
_ntc.links.new(_tcp.outputs['Object'], _mpw.inputs[0]); _ntc.links.new(_mpw.outputs[0], _wv.inputs[0])
_bp = _ntc.nodes.new('ShaderNodeBump'); _bp.inputs['Strength'].default_value = 0.6; _bp.inputs['Distance'].default_value = 0.01
_ntc.links.new(_wv.outputs['Fac'], _bp.inputs['Height']); _ntc.links.new(_bp.outputs['Normal'], _pc.inputs['Normal'])
_pc.inputs['Metallic'].default_value = 0.6
box('persiana', 0, -0.53, 1.4, 3.0, 0.02, 2.8, CHAPA)
box('cajon_persiana', 0, -0.4, 2.98, 3.2, 0.3, 0.36, STEEL, bevel=0.01)
for x_ in (-1.53, 1.53):
    box(f'guia{x_}', x_, -0.5, 1.4, 0.07, 0.06, 2.8, STEEL)
box('cerrojo', 0, -0.5, 0.25, 0.25, 0.03, 0.06, CHROME_ := flat('cerrojo_m', (0.6, 0.6, 0.6), 0.3, 1.0))

# ================= LUZ =================
world = bpy.data.worlds.new('cielo'); sc.world = world; world.use_nodes = True
wn = world.node_tree; env = wn.nodes.new('ShaderNodeTexEnvironment'); env.image = bpy.data.images.load(PH + 'hdri/courtyard.hdr')
mp = wn.nodes.new('ShaderNodeMapping'); tc = wn.nodes.new('ShaderNodeTexCoord'); mp.inputs['Rotation'].default_value = (0, 0, R(200))
wn.links.new(tc.outputs['Generated'], mp.inputs[0]); wn.links.new(mp.outputs[0], env.inputs[0])
wn.links.new(env.outputs['Color'], wn.nodes['Background'].inputs['Color']); wn.nodes['Background'].inputs['Strength'].default_value = 1.2
sun = bpy.data.lights.new('sol', 'SUN'); sun.energy = 6.0; sun.color = (1.0, 0.92, 0.8); sun.angle = R(0.8)
so = bpy.data.objects.new('sol', sun); sc.collection.objects.link(so); so.rotation_euler = (R(-68), 0, R(-15))
TUBE = emit('tubo_fluo', 9, (1, 0.96, 0.9))
# regletas fluorescentes en el techo, con su luz
for k, y in enumerate((1.7, 4.3, 6.9, 9.5)):
    for x in (-1.5, 1.5):
        box(f'regleta{k}{x}', x, y, HT - 0.27, 0.16, 1.28, 0.06, flat('chapa_blanca', (0.75, 0.75, 0.72), 0.45), bevel=0.01)
        for dx in (-0.04, 0.04):
            bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.014, depth=1.2, location=(x + dx, y, HT - 0.315), rotation=(R(90), 0, 0))
            bpy.context.object.data.materials.append(TUBE)
        a = bpy.data.lights.new(f'fl{k}{x}', 'AREA'); a.energy = 55; a.shape = 'RECTANGLE'; a.size = 0.6; a.size_y = 0.9; a.color = (1, 0.95, 0.88)
        ao = bpy.data.objects.new(f'fl{k}{x}', a); sc.collection.objects.link(ao); ao.location = (x, y, HT - 0.34)
# lámparas industriales colgantes
for k, y in enumerate((3.0, 6.4, 9.0)):
    model('hanging_industrial_lamp', (0.9 if k != 1 else -0.9, y, HT - 0.24), anchor='center', tag=f'colg_lamp{k}')
    pl = bpy.data.lights.new(f'colgante{k}', 'POINT'); pl.energy = 60; pl.color = (1, 0.76, 0.5); pl.shadow_soft_size = 0.05
    po = bpy.data.objects.new(f'colgante{k}', pl); sc.collection.objects.link(po); po.location = (0.9 if k != 1 else -0.9, y, HT - 1.05)
# fluorescentes: tubos emisivos (los materiales del modelo con «tube/light/bulb» pasan a emitir)
for m in bpy.data.materials:
    if any(w in m.name.lower() for w in ('tube', 'bulb', 'glass_light', 'emiss')) and m.use_nodes:
        p = m.node_tree.nodes.get('Principled BSDF')
        if p: p.inputs['Emission Color'].default_value = (1, 0.95, 0.88, 1); p.inputs['Emission Strength'].default_value = 6

# ================= RENDER =================
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.cycles.samples = int(os.environ.get('SAMPLES', 32)); sc.cycles.use_denoising = True
sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.03
sc.cycles.max_bounces = 6; sc.cycles.glossy_bounces = 3; sc.cycles.transmission_bounces = 4; sc.cycles.transparent_max_bounces = 8
sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False; sc.cycles.blur_glossy = 1.0
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Base Contrast'
sc.view_settings.exposure = float(os.environ.get('EXPO', 0.0))
sc.render.resolution_y = RES_Y; sc.render.resolution_x = RES_Y * 9 // 16
sc.render.fps = 30; sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.6; sc.render.motion_blur_position = 'START'
sc.cycles.rolling_shutter_type = 'TOP'; sc.cycles.rolling_shutter_duration = 0.15
sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 93

# ================= CÁMARA (móvil en mano) =================
# lente ~35 mm con sensor de 36 mm en el lado corto = gran angular de móvil en vertical
SHOTS = {
 'entrada':      (4.0, 30, ((0.2, 0.15, 1.55), (-0.3, 8.0, 1.25)), ((0.05, 1.1, 1.53), (-1.1, 6.5, 1.2))),
 'banco':        (4.0, 34, ((-0.9, 1.7, 1.6), (-3.3, 3.0, 1.15)), ((-1.05, 2.9, 1.58), (-3.4, 3.9, 1.2))),
 'herramientas': (3.5, 38, ((-2.2, 2.75, 1.65), (-3.5, 3.0, 1.55)), ((-2.2, 3.7, 1.63), (-3.5, 4.0, 1.55))),
 'tornillo':     (2.5, 42, ((-2.3, 2.0, 1.35), (-2.95, 2.45, 1.0)), ((-2.25, 2.35, 1.3), (-2.95, 2.75, 1.0))),
 'banco_detalle':(3.0, 40, ((-2.35, 4.6, 1.45), (-3.1, 3.7, 1.0)), ((-2.3, 4.2, 1.42), (-3.2, 3.4, 1.0))),
 'carro':        (3.0, 34, ((-1.4, 4.9, 1.5), (-3.1, 5.7, 0.95)), ((-1.35, 5.6, 1.48), (-3.1, 6.3, 1.0))),
 'carteles':     (3.5, 30, ((1.3, 1.0, 1.65), (3.5, 2.4, 2.1)), ((1.3, 2.4, 1.63), (3.5, 3.9, 2.15))),
 'coleccion':    (3.5, 30, ((1.0, 6.4, 1.6), (3.5, 7.6, 1.9)), ((1.0, 7.8, 1.6), (3.5, 9.0, 1.9))),
 'fondo':        (3.0, 30, ((0.2, 7.4, 1.58), (2.4, 10.8, 1.2)), ((-0.2, 7.9, 1.56), (-2.0, 10.8, 1.5))),
 'final':        (3.5, 28, ((1.2, 9.6, 1.6), (-0.6, 2.0, 1.2)), ((1.0, 8.6, 1.58), (-1.0, 1.0, 1.25))),
}
def smooth(u): return u * u * (3 - 2 * u)
camd = bpy.data.cameras.new('cam'); camd.sensor_fit = 'HORIZONTAL'; camd.sensor_width = 36
cam = bpy.data.objects.new('cam', camd); sc.collection.objects.link(cam); sc.camera = cam
def setup_cam(name, u):
    dur, lens, (p0, t0), (p1, t1) = SHOTS[name]
    e = 0.25 * u + 0.75 * smooth(u)   # arranque y parada suaves, como al caminar con el móvil
    t = u * dur
    pos = Vector(p0).lerp(Vector(p1), e); tgt = Vector(t0).lerp(Vector(t1), e)
    bob = Vector((0.006 * math.sin(2 * math.pi * 0.9 * t), 0, 0.008 * math.sin(2 * math.pi * 1.8 * t + 0.6)))   # paso al caminar
    cam.location = pos + bob
    eu = (tgt - pos).to_track_quat('-Z', 'Y').to_euler()
    eu.y += R(0.8 * math.sin(2 * math.pi * 0.45 * t + 1.1))   # leve alabeo de la mano
    cam.rotation_euler = eu; camd.lens = lens

if MODE == 'stills':
    only = sys.argv[4].split(',') if len(sys.argv) > 4 else list(SHOTS)
    for name in only:
        setup_cam(name, 0.5); sc.render.filepath = OUT + f'still_{name}.jpg'; bpy.ops.render.render(write_still=True)
elif MODE == 'anim':
    name = sys.argv[4]; dur = SHOTS[name][0]; n = int(round(dur * FPS_R)) + 1
    os.makedirs(OUT + name, exist_ok=True)
    for i in range(n):
        fp = OUT + f'{name}/{i:04d}.jpg'
        if os.path.exists(fp): continue
        u = i / (n - 1); du = 1.0 / (30.0 * dur)
        cam.animation_data_clear(); camd.animation_data_clear()
        for f_, uu in ((1, u), (2, u + du)):
            setup_cam(name, uu); cam.keyframe_insert('location', frame=f_); cam.keyframe_insert('rotation_euler', frame=f_)
        sc.frame_set(1); sc.render.filepath = fp; bpy.ops.render.render(write_still=True)
elif MODE == 'save':
    bpy.ops.wm.save_as_mainfile(filepath=S + '/tour/taller_real.blend')
