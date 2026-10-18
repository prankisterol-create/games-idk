"""Build the Blender layout file for INFINITY CRISIS from the shot list.

    python3 build_layout.py [--out infinity_crisis_layout.blend]

Needs the `bpy` module (pip install bpy) or run inside Blender:
    blender -b -P build_layout.py -- --out infinity_crisis_layout.blend

Creates, per the brief's Blender organisation:
  - collections: CHARACTERS, ENVIRONMENTS, LIGHTING, FX, CAMERAS, AUDIO
  - one scene per sequence (SEQ01_THE_SKY_BREAKS ...), 24 fps, 4096 x 1716 (2.39:1)
  - one camera per shot, named after its shot ID, with the shot's focal length, bound to a
    timeline marker at the exact first frame so the scene plays as the cut
  - an Eternity Engine procedural asset (three rings, core, Crown, Root, Heart) in its own
    collection, linked into Sequences 8-11
  - proxy figures for every principal at their real height, named PROXY_<ID> and coloured
    with their power-signature colour, so layout can block before final assets exist
These proxies are placeholders by design and are labelled as such.
"""
import argparse
import math
import os
import re
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
import common as C  # noqa: E402

COLLECTIONS = ['CHARACTERS', 'ENVIRONMENTS', 'LIGHTING', 'FX', 'CAMERAS', 'AUDIO']
PROXY_COLOURS = {
    'THANOS': (0.36, 0.25, 0.55), 'IRONMAN': (0.64, 0.09, 0.11), 'CAP': (0.12, 0.18, 0.31),
    'THOR': (0.6, 0.65, 0.75), 'HULK': (0.36, 0.48, 0.23), 'STRANGE': (1.0, 0.54, 0.12),
    'SPIDEY': (0.7, 0.07, 0.1), 'PANTHER': (0.55, 0.36, 0.96), 'SUPERMAN': (0.12, 0.24, 0.56),
    'BATMAN': (0.16, 0.17, 0.19), 'WW': (0.79, 0.61, 0.23), 'FLASH': (1.0, 0.83, 0.42),
    'GL': (0.09, 0.64, 0.29), 'AQUAMAN': (0.79, 0.58, 0.18), 'CYBORG': (0.61, 0.64, 0.67),
}


def lens_mm(text):
    m = re.search(r'(\d+)\s*mm', str(text))
    return float(m.group(1)) if m else 35.0


def material(name, rgb, emit=0.0):
    mat = bpy.data.materials.new(name)
    if hasattr(mat, 'use_nodes') and not mat.use_nodes:
        mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    if emit:
        bsdf.inputs['Emission Color'].default_value = (*rgb, 1)
        bsdf.inputs['Emission Strength'].default_value = emit
    return mat


def collection(scene, name, parent=None):
    col = bpy.data.collections.new(name)
    (parent or scene.collection).children.link(col)
    return col


def eternity_engine():
    col = bpy.data.collections.new('ASSET_ETERNITY_ENGINE')
    metal = material('MAT_engine_alloy', (0.18, 0.18, 0.21))
    core = material('MAT_engine_core', (0.75, 0.45, 1.0), emit=30)
    # scale: 1 Blender unit = 1 km; rings 1000 / 760 / 540 km
    for i, (r, minor, tilt) in enumerate(((1000, 18, 0), (760, 14, 28), (540, 10, -41))):
        bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=minor, major_segments=192,
                                         minor_segments=12, rotation=(math.radians(tilt), 0, math.radians(i * 37)))
        ring = bpy.context.active_object
        ring.name = 'ENGINE_ring_%d' % (i + 1)
        ring.data.materials.append(metal)
        ring.driver_add('rotation_euler', 2).driver.expression = 'frame * %.5f' % (0.0006 * (1 if i % 2 else -1) * (i + 1))
        for c in ring.users_collection:
            c.objects.unlink(ring)
        col.objects.link(ring)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=300, segments=64, ring_count=32)
    sph = bpy.context.active_object
    sph.name = 'ENGINE_core_HEART'
    sph.data.materials.append(core)
    for c in sph.users_collection:
        c.objects.unlink(sph)
    col.objects.link(sph)
    for name, loc, size in (('ENGINE_anchor_CROWN', (0, 0, 1060), 40), ('ENGINE_anchor_ROOT', (0, 0, -1200), 60)):
        bpy.ops.mesh.primitive_cone_add(radius1=size, depth=size * 4, location=loc,
                                        rotation=(0 if 'CROWN' in name else math.pi, 0, 0))
        o = bpy.context.active_object
        o.name = name
        o.data.materials.append(core)
        for c in o.users_collection:
            c.objects.unlink(o)
        col.objects.link(o)
    return col


def proxy(cid, height, col):
    bpy.ops.mesh.primitive_cylinder_add(radius=height * 0.13, depth=height, location=(0, 0, height / 2))
    o = bpy.context.active_object
    o.name = 'PROXY_%s' % cid
    o.data.materials.append(material('MAT_proxy_%s' % cid, PROXY_COLOURS.get(cid, (0.5, 0.5, 0.5))))
    o['placeholder'] = True
    o['height_m'] = height
    for c in o.users_collection:
        c.objects.unlink(o)
    col.objects.link(o)
    return o


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(HERE, 'infinity_crisis_layout.blend'))
    a = ap.parse_args(argv)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    seqs = C.load_sequences()
    bible = C.load_bible()
    C.timeline(seqs)
    engine = eternity_engine()
    summary = []
    for seq in seqs:
        n = seq['sequence']
        name = 'SEQ%02d_%s' % (n, re.sub(r'[^A-Z0-9]+', '_', seq['title']).strip('_'))[:63]
        sc = bpy.data.scenes.new(name)
        sc.render.fps = C.FPS
        sc.render.resolution_x, sc.render.resolution_y = 4096, 1716
        sc.frame_start, sc.frame_end = 1, seq['frames']
        cols = {k: collection(sc, '%s_%02d' % (k, n)) for k in COLLECTIONS}
        if n >= 8:
            cols['ENVIRONMENTS'].children.link(engine)
        present = sorted({c for shot in seq['shots'] for c in shot.get('characters') or []
                          if c in bible['characters'] and bible['characters'][c]['height'] > 0})
        for i, cid in enumerate(present):
            o = proxy(cid, bible['characters'][cid]['height'], cols['CHARACTERS'])
            o.name = 'PROXY_%s_S%02d' % (cid, n)
            o.location.x = (i - len(present) / 2) * 2.5
        for shot in seq['shots']:
            cam_data = bpy.data.cameras.new(shot['id'])
            cam_data.lens = lens_mm(shot['lens'])
            cam_data.sensor_width = 36
            cam_data.sensor_fit = 'HORIZONTAL'
            cam = bpy.data.objects.new(shot['id'], cam_data)
            cam.location = (0, -12, 1.6)
            cam.rotation_euler = (math.radians(88), 0, 0)
            cam['camera_position'] = shot['camera']
            cam['movement'] = shot['movement']
            cam['framing'] = shot['framing']
            cam['action'] = shot['action']
            cols['CAMERAS'].objects.link(cam)
            mk = sc.timeline_markers.new(shot['id'], frame=shot['seq_in'] + 1)
            mk.camera = cam
        sc.camera = sc.timeline_markers[0].camera
        summary.append((name, len(seq['shots']), seq['frames']))
    for s in list(bpy.data.scenes):
        if not s.name.startswith('SEQ'):
            bpy.data.scenes.remove(s)
    bpy.ops.wm.save_as_mainfile(filepath=a.out)
    for name, shots, fr in summary:
        print('%-50s %3d cameras  %5d frames' % (name, shots, fr))
    print('saved', a.out)


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    main(argv)
