"""Tiny signed-distance-field modelling kit (numpy) + marching cubes -> Blender mesh.

Organic and cast shapes (porcelain bowls, heads, rounded housings) are modelled as smooth
blends of primitives, the way a sculptor or a CAD fillet would round them, then meshed.

Every node is a callable taking an (N, 3) float32 array of points and returning (N,)
signed distances (negative inside). Formulas follow Inigo Quilez's distance functions.
"""

import math

import numpy as np

try:
    from skimage.measure import marching_cubes
except ImportError:  # pragma: no cover - explained at runtime
    marching_cubes = None


def rot_matrix(deg):
    """XYZ Euler (degrees) -> 3x3 matrix, same convention as Blender's rotation_euler."""
    x, y, z = (math.radians(a) for a in deg)
    cx, sx, cy, sy, cz, sz = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return (rz @ ry @ rx).astype(np.float32)


def _local(P, c, rot):
    q = P - np.asarray(c, np.float32)
    if rot is not None:
        q = q @ rot_matrix(rot)        # row vectors: R^T (p - c)
    return q


def _len(q):
    return np.sqrt(np.sum(q * q, axis=1))


# --------------------------------------------------------------------------- primitives

def sphere(c, r):
    return lambda P: _len(P - np.asarray(c, np.float32)) - r


def ellipsoid(c, radii, rot=None):
    r = np.asarray(radii, np.float32)

    def f(P):
        q = _local(P, c, rot)
        k0 = _len(q / r)
        k1 = _len(q / (r * r))
        return k0 * (k0 - 1.0) / np.maximum(k1, 1e-6)
    return f


def round_box(c, half, radius, rot=None):
    h = np.asarray(half, np.float32) - radius

    def f(P):
        q = np.abs(_local(P, c, rot)) - h
        return _len(np.maximum(q, 0)) + np.minimum(q.max(axis=1), 0) - radius
    return f


def capsule(a, b, ra, rb=None):
    """Round cone between a and b (radius ra at a, rb at b)."""
    rb = ra if rb is None else rb
    a = np.asarray(a, np.float32)
    b = np.asarray(b, np.float32)
    ba = b - a
    l2 = float(ba @ ba)

    def f(P):
        pa = P - a
        t = np.clip((pa @ ba) / l2, 0, 1)
        r = ra + (rb - ra) * t
        return _len(pa - t[:, None] * ba) - r
    return f


def tube_path(points, radii):
    """Smoothly joined round cones through a polyline."""
    segs = [capsule(points[i], points[i + 1], radii[i], radii[i + 1]) for i in range(len(points) - 1)]
    return union(*segs, k=min(radii) * 0.5)


def torus(c, major, minor, rot=None, sx=1.0, sy=1.0):
    """Torus around local Z; sx/sy stretch the ring into an oval (approximate distance)."""
    def f(P):
        q = _local(P, c, rot)
        qx, qy = q[:, 0] / sx, q[:, 1] / sy
        ring = np.sqrt(qx * qx + qy * qy) - major
        return np.sqrt(ring * ring * min(sx, sy) ** 2 + q[:, 2] ** 2) - minor
    return f


def cylinder(c, radius, half_h, rot=None, round_r=0.0, sx=1.0, sy=1.0):
    """Capped cylinder along local Z, optionally oval and with rounded rims."""
    def f(P):
        q = _local(P, c, rot)
        rr = np.sqrt((q[:, 0] / sx) ** 2 + (q[:, 1] / sy) ** 2) * min(sx, sy)
        d0 = rr - (radius - round_r)
        d1 = np.abs(q[:, 2]) - (half_h - round_r)
        out = np.sqrt(np.maximum(d0, 0) ** 2 + np.maximum(d1, 0) ** 2)
        return out + np.minimum(np.maximum(d0, d1), 0) - round_r
    return f


def half_space(point, normal):
    """Inside where (p - point) . normal < 0."""
    n = np.asarray(normal, np.float32)
    n = n / np.linalg.norm(n)
    p0 = np.asarray(point, np.float32)
    return lambda P: (P - p0) @ n


def oval_ring(c, rx, ry, width, height, rot=None, round_r=0.03):
    """Flat elliptic ring (toilet seat): band of the given width around an ellipse."""
    def f(P):
        q = _local(P, c, rot)
        # distance to the ellipse, approximated by scaling to the mean radius
        k = math.sqrt(rx * ry)
        e = np.sqrt((q[:, 0] * k / rx) ** 2 + (q[:, 1] * k / ry) ** 2) - k
        d0 = np.abs(e) - (width / 2 - round_r)
        d1 = np.abs(q[:, 2]) - (height / 2 - round_r)
        out = np.sqrt(np.maximum(d0, 0) ** 2 + np.maximum(d1, 0) ** 2)
        return out + np.minimum(np.maximum(d0, d1), 0) - round_r
    return f


# --------------------------------------------------------------------------- operations

def _smin(a, b, k):
    if k <= 0:
        return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b + (a - b) * h - k * h * (1 - h)


def union(*nodes, k=0.0):
    def f(P):
        d = nodes[0](P)
        for n in nodes[1:]:
            d = _smin(d, n(P), k)
        return d
    return f


def subtract(a, b, k=0.0):
    """a minus b."""
    return lambda P: -_smin(-a(P), b(P), k)


def intersect(a, b, k=0.0):
    return lambda P: -_smin(-a(P), -b(P), k)


def shell(a, thickness):
    return lambda P: np.abs(a(P)) - thickness / 2


def offset(a, amount):
    return lambda P: a(P) - amount


def mirror_x(node_fn):
    """Evaluate node_fn on |x| so a feature built on +X appears on both sides."""
    def f(P):
        Q = P.copy()
        Q[:, 0] = np.abs(Q[:, 0])
        return node_fn(Q)
    return f


def displace(a, fn):
    """Add a small analytic offset field (e.g. wrinkles) to a distance."""
    return lambda P: a(P) + fn(P)


# --------------------------------------------------------------------------- weights

def falloff(node, width):
    """1 inside/at the surface of `node`, fading to 0 at `width` outside it."""
    return lambda P: np.clip(1.0 - node(P) / width, 0, 1)


# --------------------------------------------------------------------------- meshing

def mesh_arrays(node, bmin, bmax, res):
    """Marching cubes over the box [bmin, bmax] at `res` spacing. Returns verts, faces."""
    if marching_cubes is None:
        raise RuntimeError("scikit-image is required: pip install scikit-image")
    bmin = np.asarray(bmin, np.float32) - res * 2
    bmax = np.asarray(bmax, np.float32) + res * 2
    n = np.ceil((bmax - bmin) / res).astype(int) + 1
    xs = bmin[0] + np.arange(n[0], dtype=np.float32) * res
    ys = bmin[1] + np.arange(n[1], dtype=np.float32) * res
    zs = bmin[2] + np.arange(n[2], dtype=np.float32) * res
    vol = np.empty((n[0], n[1], n[2]), np.float32)
    yy, zz = np.meshgrid(ys, zs, indexing="ij")
    yz = np.stack([yy.ravel(), zz.ravel()], axis=1)
    for i, x in enumerate(xs):
        P = np.empty((yz.shape[0], 3), np.float32)
        P[:, 0] = x
        P[:, 1:] = yz
        vol[i] = node(P).reshape(n[1], n[2])
    # close the surface wherever the shape touches the sampling box
    vol[0, :, :] = vol[-1, :, :] = res
    vol[:, 0, :] = vol[:, -1, :] = res
    vol[:, :, 0] = vol[:, :, -1] = res
    verts, faces, _normals, _ = marching_cubes(vol, 0.0, spacing=(res, res, res),
                                               gradient_direction="ascent")
    verts = verts.astype(np.float32) + bmin
    return verts, faces


def to_bmesh(bm, verts, faces):
    vs = [bm.verts.new(v) for v in verts.tolist()]
    for a, b, c in faces.tolist():
        try:
            bm.faces.new((vs[a], vs[b], vs[c]))
        except ValueError:      # duplicate face from a degenerate cell
            pass
    bm.normal_update()
    return bm
