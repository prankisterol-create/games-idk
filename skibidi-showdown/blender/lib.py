"""Shared Blender helpers for the Skibidi Showdown model pipeline.

Every model is built from code into its own collection under a root empty.
Each mesh object carries three custom properties that the exporter reads:

    rbx_mat    palette key (see palette.json) -> Blender material + Roblox colour/material
    rbx_shape  Roblox primitive used for the in-game Part version:
               Block | Ball | Cylinder | Sphere (ellipsoid) | Wedge | Ring
    rbx_role   "both"  - real mesh (FBX) and a Part approximation (blueprint)
               "mesh"  - real mesh only (detail the Part version can't express)
               "proxy" - Part approximation only (hidden in renders, not exported)

Animated groups are parented to empties named J_<Joint>; their location is the
pivot the game rotates the group around (e.g. the toilet's neck).

Coordinates: Blender is Z-up with models facing -Y. Roblox is Y-up facing -Z.
The conversion (x, y, z) -> (-x, z, y) is a proper rotation, see to_rbx().
"""

import json
import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

import sdf as sdflib

HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, "palette.json")) as fh:
    PALETTE = {k: v for k, v in json.load(fh).items() if not k.startswith("_")}

# Blender -> Roblox axis change. Symmetric and orthogonal, so it is its own inverse.
C = Matrix(((-1, 0, 0), (0, 0, 1), (0, 1, 0)))
ROT_Z90 = Matrix(((0, -1, 0), (1, 0, 0), (0, 0, 1)))


def to_rbx(v):
    return C @ Vector(v)


# --------------------------------------------------------------------------------------
# Scene + materials
# --------------------------------------------------------------------------------------

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    return scene


def _srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def linear_rgba(key):
    return [_srgb_to_linear(v) for v in PALETTE[key]["rgb"]] + [1.0]


# Extra Principled settings for nicer renders (the game only uses colour + Enum.Material).
RENDER_LOOK = {
    "porcelain": {"Coat Weight": 0.8, "Coat Roughness": 0.03, "Roughness": 0.16},
    "porcelain_gray": {"Coat Weight": 0.8, "Coat Roughness": 0.03, "Roughness": 0.18},
    "porcelain_dirty": {"Coat Weight": 0.5, "Coat Roughness": 0.1, "Roughness": 0.3},
    "porcelain_shade": {"Coat Weight": 0.6, "Coat Roughness": 0.05},
    "camera_white": {"Coat Weight": 0.3, "Coat Roughness": 0.2},
    "skin": {"Subsurface Weight": 0.3, "Subsurface Scale": 0.05, "Roughness": 0.42,
             "Specular IOR Level": 0.45},
    "skin_shade": {"Subsurface Weight": 0.3, "Subsurface Scale": 0.05, "Roughness": 0.45},
    "eye_white": {"Coat Weight": 1.0, "Coat Roughness": 0.0, "Roughness": 0.25,
                  "Subsurface Weight": 0.2, "Subsurface Scale": 0.02},
    "pupil": {"Coat Weight": 1.0, "Coat Roughness": 0.0},
    "iris_brown": {"Coat Weight": 1.0, "Coat Roughness": 0.0},
    "iris_blue": {"Coat Weight": 1.0, "Coat Roughness": 0.0},
    "teeth": {"Coat Weight": 0.6, "Coat Roughness": 0.05, "Subsurface Weight": 0.2,
              "Subsurface Scale": 0.02},
    "tongue": {"Subsurface Weight": 0.4, "Subsurface Scale": 0.03, "Coat Weight": 0.6},
    "water": {"Transmission Weight": 0.7, "Roughness": 0.02, "IOR": 1.33},
    "screen": {"Coat Weight": 1.0, "Coat Roughness": 0.0, "Roughness": 0.1},
    "lens_glass": {"Coat Weight": 1.0, "Coat Roughness": 0.0, "Metallic": 0.4},
}


def get_material(key, vertex_colors=False):
    name = "M_" + key + ("_vc" if vertex_colors else "")
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    spec = PALETTE[key]
    mat = bpy.data.materials.new(name)
    if mat.node_tree is None:
        mat.use_nodes = True
    rgba = linear_rgba(key)
    nodes = mat.node_tree.nodes
    bsdf = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value = spec.get("roughness", 0.5)
    bsdf.inputs["Metallic"].default_value = spec.get("metallic", 0.0)
    if spec["material"] == "Neon":
        bsdf.inputs["Emission Color"].default_value = rgba
        bsdf.inputs["Emission Strength"].default_value = 4.0
    if spec["material"] == "Glass":
        bsdf.inputs["Coat Weight"].default_value = 1.0
        bsdf.inputs["Coat Roughness"].default_value = 0.02
    for inp, val in RENDER_LOOK.get(key, {}).items():
        bsdf.inputs[inp].default_value = val
    if "Subsurface Radius" in bsdf.inputs and key.startswith("skin"):
        bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
    if vertex_colors:
        attr = nodes.new("ShaderNodeVertexColor")
        attr.layer_name = "Col"
        mat.node_tree.links.new(attr.outputs["Color"], bsdf.inputs["Base Color"])
    mat.diffuse_color = rgba
    mat["rbx_key"] = key
    return mat


def _srgb_to_linear_np(c):
    c = np.asarray(c, np.float32) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def rgb_of(key_or_rgb):
    return np.asarray(PALETTE[key_or_rgb]["rgb"] if isinstance(key_or_rgb, str) else key_or_rgb,
                      np.float32)


def paint_layers(base, layers):
    """Vertex colour function: base colour, then (weight_fn(P) in 0..1, colour) layers on top."""
    def f(P):
        col = np.tile(rgb_of(base), (len(P), 1))
        for weight_fn, colour in layers:
            w = np.clip(weight_fn(P), 0, 1)[:, None]
            col = col * (1 - w) + rgb_of(colour) * w
        return col
    return f


# --------------------------------------------------------------------------------------
# bmesh primitives (all built headless, no operators)
# --------------------------------------------------------------------------------------

def _smooth(bm, sharp_angle):
    limit = math.radians(sharp_angle)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > limit:
            e.smooth = False


def bm_box(size, bevel=0.0, segments=3):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=segments,
                        profile=0.5, affect="EDGES", clamp_overlap=True)
    _smooth(bm, 40)
    return bm


def bm_cylinder(r1, r2, depth, segments=32):
    """Cone/cylinder along local Z, centred on the origin."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                          radius1=r1, radius2=r2, depth=depth)
    _smooth(bm, 40)
    return bm


def bm_sphere(size, u=32, v=16):
    """Ellipsoid with the given diameters."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=0.5)
    for vert in bm.verts:
        vert.co = Vector((vert.co.x * size[0], vert.co.y * size[1], vert.co.z * size[2]))
    _smooth(bm, 80)
    return bm


def bm_torus(major, minor, major_seg=40, minor_seg=12, sx=1.0, sy=1.0, minor_z=None):
    """Torus around local Z. sx/sy stretch the ring into an oval; minor_z flattens the tube."""
    minor_z = minor if minor_z is None else minor_z
    bm = bmesh.new()
    rings = []
    for i in range(major_seg):
        a = 2 * math.pi * i / major_seg
        ring = []
        for j in range(minor_seg):
            b = 2 * math.pi * j / minor_seg
            r = major + minor * math.cos(b)
            ring.append(bm.verts.new((r * math.cos(a) * sx, r * math.sin(a) * sy, minor_z * math.sin(b))))
        rings.append(ring)
    for i in range(major_seg):
        a, b = rings[i], rings[(i + 1) % major_seg]
        for j in range(minor_seg):
            k = (j + 1) % minor_seg
            bm.faces.new((a[j], b[j], b[k], a[k]))
    bm.normal_update()
    _smooth(bm, 80)
    return bm


def bm_lathe(profile, segments=40, sx=1.0, sy=1.0, close=True):
    """Revolve a list of (radius, z) points around Z. Points with radius 0 become poles."""
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        if r <= 1e-6:
            rings.append([bm.verts.new((0, 0, z))])
            continue
        ring = []
        for i in range(segments):
            a = 2 * math.pi * i / segments
            ring.append(bm.verts.new((r * math.cos(a) * sx, r * math.sin(a) * sy, z)))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        if len(a) == 1 and len(b) == 1:
            continue
        for i in range(segments):
            j = (i + 1) % segments
            if len(a) == 1:
                bm.faces.new((a[0], b[i], b[j]))
            elif len(b) == 1:
                bm.faces.new((a[i], b[0], a[j]))
            else:
                bm.faces.new((a[i], b[i], b[j], a[j]))
    if close and len(rings[0]) > 1:
        bm.faces.new(list(reversed(rings[0])))
    if close and len(rings[-1]) > 1:
        bm.faces.new(rings[-1])
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    _smooth(bm, 50)
    return bm


# --------------------------------------------------------------------------------------
# Model builder
# --------------------------------------------------------------------------------------

def _rot(deg):
    return tuple(math.radians(a) for a in deg)


class Model:
    """Collects the objects of one model under a root empty."""

    def __init__(self, name, mat_overrides=None, marker_up=4.0, marker_front=2.0):
        self.name = name
        self.mat_overrides = mat_overrides or {}
        self.marker_up = marker_up
        self.marker_front = marker_front
        self.collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(self.collection)
        self.root = self._empty(name + "_Root", (0, 0, 0), None)
        self.root["rbx_root"] = True
        self.joints = {"Root": self.root}
        self.parts = []

    # -- structure -------------------------------------------------------------------
    def _empty(self, name, loc, parent):
        e = bpy.data.objects.new(name, None)
        e.empty_display_type = "SPHERE"
        e.empty_display_size = 0.15
        e.location = loc
        self.collection.objects.link(e)
        if parent is not None:
            e.parent = parent
            e.matrix_parent_inverse = parent.matrix_world.inverted()
        bpy.context.view_layer.update()
        return e

    def joint(self, name, pivot, parent="Root"):
        e = self._empty("J_" + name, pivot, self.joints[parent])
        e.empty_display_type = "ARROWS"
        e.empty_display_size = 0.4
        self.joints[name] = e
        return name

    def _add(self, bm, name, mat, loc, rot, joint, shape, role, extra, vertex_colors=False):
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        obj = bpy.data.objects.new(name, me)
        me.materials.append(get_material(self.mat_overrides.get(mat, mat), vertex_colors))
        obj.location = loc
        obj.rotation_euler = _rot(rot)
        obj["rbx_mat"] = mat
        obj["rbx_shape"] = shape
        obj["rbx_role"] = role
        for k, v in (extra or {}).items():
            obj["rbx_" + k] = v
        self.collection.objects.link(obj)
        parent = self.joints[joint]
        bpy.context.view_layer.update()
        obj.parent = parent
        obj.matrix_parent_inverse = parent.matrix_world.inverted()
        if role == "proxy":
            obj.hide_render = True
            obj.display_type = "WIRE"
        self.parts.append(obj)
        return obj

    # -- primitives ------------------------------------------------------------------
    def box(self, name, size, loc, mat, rot=(0, 0, 0), joint="Root", bevel=0.0,
            shape="Block", role="both", **extra):
        return self._add(bm_box(size, bevel), name, mat, loc, rot, joint, shape, role, extra)

    def wedge(self, name, size, loc, mat, rot=(0, 0, 0), joint="Root", role="both", **extra):
        """Roblox WedgePart: slope rises towards local -Y (Roblox front, +Z back is tall)."""
        bm = bmesh.new()
        x, y, z = size[0] / 2, size[1] / 2, size[2] / 2
        # Roblox wedge: full height at the back (+Z roblox == +Y blender), zero at the front.
        v = [bm.verts.new(p) for p in (
            (-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z),   # bottom
            (-x, y, z), (x, y, z))]                                 # top back edge
        bm.faces.new((v[0], v[3], v[2], v[1]))
        bm.faces.new((v[2], v[3], v[4], v[5]))
        bm.faces.new((v[0], v[1], v[5], v[4]))
        bm.faces.new((v[1], v[2], v[5]))
        bm.faces.new((v[0], v[4], v[3]))
        bm.normal_update()
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        _smooth(bm, 30)
        return self._add(bm, name, mat, loc, rot, joint, "Wedge", role, extra)

    def cylinder(self, name, radius, depth, loc, mat, rot=(0, 0, 0), joint="Root",
                 radius_top=None, segments=32, shape="Cylinder", role="both", **extra):
        rt = radius if radius_top is None else radius_top
        return self._add(bm_cylinder(radius, rt, depth, segments), name, mat, loc, rot,
                         joint, shape, role, extra)

    def sphere(self, name, size, loc, mat, rot=(0, 0, 0), joint="Root", shape="Sphere",
               role="both", **extra):
        if isinstance(size, (int, float)):
            size = (size, size, size)
            shape = "Ball" if shape == "Sphere" else shape
        return self._add(bm_sphere(size), name, mat, loc, rot, joint, shape, role, extra)

    def torus(self, name, major, minor, loc, mat, rot=(0, 0, 0), joint="Root", sx=1.0, sy=1.0,
              minor_z=None, role="both", **extra):
        mz = minor if minor_z is None else minor_z
        extra.setdefault("ring_width", 2 * minor)
        return self._add(bm_torus(major, minor, sx=sx, sy=sy, minor_z=mz), name, mat, loc, rot,
                         joint, "Ring", role, extra)

    def tube(self, name, r_in, r_out, depth, loc, mat, rot=(0, 0, 0), joint="Root",
             segments=48, role="both", **extra):
        """Thick pipe (ring with a rectangular cross-section) around local Z."""
        h = depth / 2
        prof = [(r_in, -h), (r_out, -h), (r_out, h), (r_in, h), (r_in, -h)]
        bm = bm_lathe(prof, segments=segments, close=False)
        _smooth(bm, 30)
        extra.setdefault("ring_width", r_out - r_in)
        return self._add(bm, name, mat, loc, rot, joint, "Ring", role, extra)

    def lathe(self, name, profile, loc, mat, rot=(0, 0, 0), joint="Root", sx=1.0, sy=1.0,
              segments=40, shape="Sphere", role="mesh", close=True, **extra):
        return self._add(bm_lathe(profile, segments, sx, sy, close), name, mat, loc, rot,
                         joint, shape, role, extra)

    def sdf(self, name, node, bmin, bmax, mat, res=0.02, joint="Root", shape="Sphere",
            role="mesh", max_tris=9000, paint=None, **extra):
        """Mesh a signed distance field. `paint(P) -> (N,3) sRGB` adds vertex colours.

        Meshes above `max_tris` get a Decimate modifier that only applies to the viewport and
        exports (Roblox allows 20k triangles per MeshPart); renders keep the full detail.
        """
        verts, faces = sdflib.mesh_arrays(node, bmin, bmax, res)
        center = (verts.min(axis=0) + verts.max(axis=0)) / 2
        bm = bmesh.new()
        sdflib.to_bmesh(bm, verts - center, faces)
        for f in bm.faces:
            f.smooth = True
        obj = self._add(bm, name, mat, tuple(float(c) for c in center), (0, 0, 0), joint, shape,
                        role, extra, vertex_colors=paint is not None)
        me = obj.data
        if paint is not None:
            co = np.empty(len(me.vertices) * 3, np.float32)
            me.vertices.foreach_get("co", co)
            world = co.reshape(-1, 3) + center
            lin = _srgb_to_linear_np(np.clip(paint(world), 0, 255))
            rgba = np.concatenate([lin, np.ones((len(lin), 1), np.float32)], axis=1)
            attr = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
            attr.data.foreach_set("color", rgba.ravel())
        if len(me.polygons) > max_tris:
            dec = obj.modifiers.new("GameLOD", "DECIMATE")
            dec.ratio = max_tris / len(me.polygons)
            dec.show_render = False
        return obj

    def mirror(self, fn, name, *args, loc, rot=(0, 0, 0), **kw):
        """Build a part and its X-mirrored twin. Name gets L (+X, model's left) / R suffix."""
        *shape_args, mat = args          # the last positional argument is the palette key
        x, y, z = loc
        a = fn(name + "L", *shape_args, loc=(x, y, z), mat=mat, rot=rot, **kw)
        b = fn(name + "R", *shape_args, loc=(-x, y, z), mat=mat, rot=(rot[0], -rot[1], -rot[2]),
               **kw)
        return a, b

    def markers(self):
        """Tiny cubes the game uses to undo any axis/scale change made by the FBX importer."""
        for name, loc in (("_Root", (0, 0, 0)), ("_Up", (0, 0, self.marker_up)),
                          ("_Front", (0, -self.marker_front, 0))):
            obj = self.box(name, (0.3, 0.3, 0.3), loc, "marker", role="mesh")
            obj.hide_render = True
            obj["rbx_marker"] = True


# --------------------------------------------------------------------------------------
# Blueprint export (Part version used by the game when no imported meshes exist)
# --------------------------------------------------------------------------------------

def _fmt(x):
    s = f"{x:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _local_bounds(obj, depsgraph):
    ev = obj.evaluated_get(depsgraph)
    pts = [Vector(c) for c in ev.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return (mn + mx) / 2, mx - mn


def blueprint_data(model):
    """Convert the model to Roblox-space part records (relative to the root empty)."""
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    inv_root = model.root.matrix_world.inverted()

    joints = []
    for name, e in model.joints.items():
        if name == "Root":
            continue
        parent = e.parent.name[2:] if e.parent.name.startswith("J_") else "Root"
        pivot = to_rbx((inv_root @ e.matrix_world).translation)
        joints.append({"name": name, "parent": parent, "pivot": pivot})

    parts = []
    for obj in model.parts:
        if obj.get("rbx_marker"):
            continue
        center, dims = _local_bounds(obj, depsgraph)
        mw = inv_root @ obj.matrix_world
        loc, rot, scl = mw.decompose()
        dims = Vector((dims.x * scl.x, dims.y * scl.y, dims.z * scl.z))
        pos = to_rbx(mw @ center)
        R = C @ rot.to_matrix() @ C
        size = Vector((dims.x, dims.z, dims.y))
        shape = obj["rbx_shape"]
        if shape == "Cylinder":            # Roblox cylinders run along local X
            R = R @ ROT_Z90
            size = Vector((size.y, size.x, size.z))
        elif shape == "Ball":
            m = max(size)
            size = Vector((m, m, m))
        parent = obj.parent
        joint = parent.name[2:] if parent.name.startswith("J_") else "Root"
        rec = {"name": obj.name, "shape": shape, "mat": obj["rbx_mat"], "joint": joint,
               "role": obj["rbx_role"], "size": size, "pos": pos, "rot": R}
        if "rbx_ring_width" in obj:
            rec["ringWidth"] = float(obj["rbx_ring_width"])
        if obj.get("rbx_core"):
            rec["core"] = True
        parts.append(rec)
    return {"name": model.name, "joints": joints, "parts": parts,
            "markers": {"up": model.marker_up, "front": model.marker_front}}


def write_blueprint_luau(data, path, source):
    L = []
    L.append(f"-- AUTO-GENERATED by blender/build_models.py from {source}.")
    L.append("-- Edit the Blender model (or blender/models.py) and rebuild instead of editing this file.")
    L.append("-- Coordinates are studs, relative to the model origin (floor, centre), facing -Z.")
    L.append("return {")
    L.append(f'\tname = "{data["name"]}",')
    m = data["markers"]
    L.append(f"\tmarkers = {{ up = {_fmt(m['up'])}, front = {_fmt(m['front'])} }},")
    L.append("\tjoints = {")
    for j in data["joints"]:
        p = j["pivot"]
        L.append(f'\t\t{{ name = "{j["name"]}", parent = "{j["parent"]}", '
                 f"pivot = Vector3.new({_fmt(p.x)}, {_fmt(p.y)}, {_fmt(p.z)}) }},")
    L.append("\t},")
    L.append("\tparts = {")
    for p in data["parts"]:
        s, pos, R = p["size"], p["pos"], p["rot"]
        rot = ", ".join(_fmt(R[i][j]) for i in range(3) for j in range(3))
        extra = ""
        if p.get("ringWidth") is not None:
            extra += f", ringWidth = {_fmt(p['ringWidth'])}"
        if p.get("core"):
            extra += ", core = true"
        L.append(
            f'\t\t{{ name = "{p["name"]}", shape = "{p["shape"]}", mat = "{p["mat"]}", '
            f'joint = "{p["joint"]}", role = "{p["role"]}", '
            f"size = Vector3.new({_fmt(s.x)}, {_fmt(s.y)}, {_fmt(s.z)}), "
            f"cframe = CFrame.new({_fmt(pos.x)}, {_fmt(pos.y)}, {_fmt(pos.z)}, {rot}){extra} }},")
    L.append("\t},")
    L.append("}")
    with open(path, "w") as fh:
        fh.write("\n".join(L) + "\n")


def write_palette_luau(path):
    L = ["-- AUTO-GENERATED by blender/build_models.py from blender/palette.json.",
         "-- Colour + material for every palette key used by the Blender models.",
         "return {"]
    for key, spec in PALETTE.items():
        r, g, b = spec["rgb"]
        extra = ""
        if spec.get("reflectance"):
            extra += f", reflectance = {_fmt(spec['reflectance'])}"
        if spec.get("transparency"):
            extra += f", transparency = {_fmt(spec['transparency'])}"
        L.append(f"\t{key} = {{ color = Color3.fromRGB({r}, {g}, {b}), "
                 f"material = Enum.Material.{spec['material']}{extra} }},")
    L.append("}")
    with open(path, "w") as fh:
        fh.write("\n".join(L) + "\n")


# --------------------------------------------------------------------------------------
# Blueprint -> Blender (to preview exactly what the Part version looks like in game)
# --------------------------------------------------------------------------------------

def build_from_blueprint(data, offset=(0, 0, 0), yaw_deg=0.0, name_suffix="_parts"):
    """Recreate the Roblox Part approximation in Blender for a side-by-side render."""
    col = bpy.data.collections.new(data["name"] + name_suffix)
    bpy.context.scene.collection.children.link(col)
    place = Matrix.Translation(offset) @ Matrix.Rotation(math.radians(yaw_deg), 4, "Z")
    for p in data["parts"]:
        if p["role"] == "mesh":
            continue
        s, shape = p["size"], p["shape"]
        R_b = C @ p["rot"] @ C
        pos_b = C @ p["pos"]
        mats = []
        if shape in ("Block",):
            bm = bm_box((s.x, s.z, s.y))
        elif shape in ("Ball", "Sphere"):
            bm = bm_sphere((s.x, s.z, s.y), 24, 12)
        elif shape == "Cylinder":   # roblox local X axis
            bm = bm_cylinder(s.y / 2, s.y / 2, s.x, 24)
            mats.append(Matrix.Rotation(math.radians(90), 4, "Y"))
            # roblox X -> blender -X; after C the cylinder axis must be blender -X
        elif shape == "Wedge":
            bm = bmesh.new()
            x, y, z = s.x / 2, s.z / 2, s.y / 2
            v = [bm.verts.new(q) for q in ((-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z),
                                           (-x, y, z), (x, y, z))]
            for f in ((v[0], v[3], v[2], v[1]), (v[2], v[3], v[4], v[5]), (v[0], v[1], v[5], v[4]),
                      (v[1], v[2], v[5]), (v[0], v[4], v[3])):
                bm.faces.new(f)
            bm.normal_update()
        elif shape == "Ring":
            bm = _ring_segments(s, p.get("ringWidth", 0.2))
        else:
            continue
        me = bpy.data.meshes.new(p["name"] + name_suffix)
        bm.to_mesh(me)
        bm.free()
        obj = bpy.data.objects.new(me.name, me)
        me.materials.append(get_material(p["mat"]))
        local = Matrix.Identity(4)
        for m in mats:
            local = m @ local
        obj.matrix_world = place @ Matrix.Translation(pos_b) @ R_b.to_4x4() @ local
        col.objects.link(obj)
    return col


def _ring_segments(size, width, count=14):
    """Same construction as ModelFactory.luau: blocks around an ellipse in roblox local XZ."""
    bm = bmesh.new()
    rx = max(size.x / 2 - width / 2, 0.01)
    rz = max(size.z / 2 - width / 2, 0.01)
    pts = [(rx * math.cos(2 * math.pi * i / count), rz * math.sin(2 * math.pi * i / count))
           for i in range(count)]
    for i in range(count):
        (x0, z0), (x1, z1) = pts[i], pts[(i + 1) % count]
        mx, mz = (x0 + x1) / 2, (z0 + z1) / 2
        r = math.hypot(mx, mz)
        length = math.hypot(x1 - x0, z1 - z0) * (r + width / 2) / max(r, 1e-3) * 1.12
        ang = math.atan2(z1 - z0, x1 - x0)
        # roblox local (x, y, z) is blender local (-x, z, y); ring axis is roblox Y == blender Z
        mat = (Matrix.Translation((-mx, mz, 0)) @ Matrix.Rotation(-ang, 4, "Z")
               @ Matrix.Diagonal((length, width, size.y, 1.0)))
        bmesh.ops.create_cube(bm, size=1.0, matrix=mat)
    return bm


# --------------------------------------------------------------------------------------
# Export + render
# --------------------------------------------------------------------------------------

def select_only(objs):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    if objs:
        bpy.context.view_layer.objects.active = objs[0]


def export_meshes(model, fbx_path, glb_path=None):
    objs = [o for o in model.parts if o["rbx_role"] != "proxy"]
    select_only(objs)
    bpy.ops.export_scene.fbx(filepath=fbx_path, use_selection=True, object_types={"MESH"},
                             use_mesh_modifiers=True, mesh_smooth_type="FACE",
                             add_leaf_bones=False, bake_anim=False, axis_forward="-Z",
                             axis_up="Y", apply_scale_options="FBX_SCALE_UNITS")
    if glb_path:
        bpy.ops.export_scene.gltf(filepath=glb_path, export_format="GLB", use_selection=True,
                                  export_apply=True, export_animations=False)
    select_only([])


def setup_render(scene, res=(900, 900), samples=48):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    try:
        scene.cycles.denoiser = "OPENIMAGEDENOISE"
    except TypeError:
        pass
    scene.cycles.max_bounces = 6
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    try:
        scene.view_settings.view_transform = "AgX"
        scene.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        pass

    world = bpy.data.worlds.new("World")
    scene.world = world
    if world.node_tree is None:
        world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = (0.62, 0.68, 0.78, 1)
    bg.inputs["Strength"].default_value = 0.7
    hdri = os.path.join(bpy.utils.system_resource("DATAFILES"), "studiolights", "world",
                        "studio.exr")
    if os.path.exists(hdri):
        env = world.node_tree.nodes.new("ShaderNodeTexEnvironment")
        env.image = bpy.data.images.load(hdri)
        world.node_tree.links.new(env.outputs["Color"], bg.inputs["Color"])
        bg.inputs["Strength"].default_value = 0.6


def add_light(name, kind, loc, target, energy, size=4.0, color=(1, 1, 1)):
    light = bpy.data.lights.new(name, kind)
    light.energy = energy
    light.color = color
    if kind == "AREA":
        light.size = size
    obj = bpy.data.objects.new(name, light)
    obj.location = loc
    direction = Vector(target) - Vector(loc)
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(obj)
    return obj


def add_floor(color=(0.2, 0.085, 0.05, 1), size=80):
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=size / 2)
    me = bpy.data.meshes.new("Floor")
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new("Floor", me)
    mat = bpy.data.materials.new("M_Floor")
    if mat.node_tree is None:
        mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = 0.9
    me.materials.append(mat)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def frame_camera(center, radius, direction=(-0.55, -1.0, 0.38), lens=50, aspect=1.0, pad=1.15):
    cam_data = bpy.data.cameras.new("Camera")
    cam_data.lens = lens
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    fov = cam_data.angle if aspect >= 1 else 2 * math.atan(math.tan(cam_data.angle / 2) * aspect)
    if aspect > 1:
        fov = 2 * math.atan(math.tan(cam_data.angle / 2) / aspect)
    dist = radius * pad / math.sin(fov / 2)
    d = Vector(direction).normalized()
    cam.location = Vector(center) + d * dist
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    return cam


def studio_lights(center, radius):
    c = Vector(center)
    r = max(radius, 1.5)
    add_light("Key", "AREA", c + Vector((-2.2, -2.6, 2.8)) * r, c, 260 * r * r, size=2.2 * r)
    add_light("Fill", "AREA", c + Vector((2.8, -1.6, 1.2)) * r, c, 90 * r * r, size=3 * r,
              color=(0.85, 0.9, 1.0))
    add_light("Rim", "AREA", c + Vector((0.8, 3.0, 2.4)) * r, c, 200 * r * r, size=2 * r,
              color=(1.0, 0.95, 0.88))


def model_bounds(objs):
    bpy.context.view_layer.update()
    pts = []
    for o in objs:
        if o.type != "MESH" or o.hide_render:
            continue
        pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return mn, mx


def render(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
