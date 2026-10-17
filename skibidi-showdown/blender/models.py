"""Model definitions. Each builder fills a lib.Model; units are studs (1 Blender unit = 1 stud).

Blender axes: Z up, models face -Y, the model's own left is +X.

Organic/cast shapes are sculpted as signed distance fields (sdf.py / sculpts.py); hard-surface
details are bevelled primitives. Every part that the in-game Part version can't express gets a
"proxy" Part next to it (see lib.py).
"""

import math

import numpy as np

import sculpts
import sdf as S

# ======================================================================================
# Skibidi toilets
# ======================================================================================

HEAD_C = 3.78     # head centre height
HEAD_S = 2.0      # head size (chin to crown) in studs

TANK_Y = 1.75     # tank centre (front face at TANK_Y - 0.42)


def toilet(m, variant="basic"):
    porcelain = {"tank": "porcelain_gray", "laser": "porcelain_gray"}.get(variant, "porcelain")
    trim = "gold" if variant == "boss" else porcelain
    metal = "gold" if variant == "boss" else "chrome"
    m.joint("Body", (0, 0, 0))

    # --- cast porcelain body (bowl, pedestal, trapway, deck) ------------------------------
    body_field = sculpts.toilet_body_field()
    m.sdf("Bowl", body_field, (-1.3, -1.7, 0), (1.3, 1.9, 2.16), porcelain, res=0.02,
          joint="Body", max_tris=12000)
    m.sphere("BowlUpper", (2.26, 2.84, 1.1), (0, -0.1, 1.55), porcelain, joint="Body",
             role="proxy")
    m.sphere("BowlRim", (2.36, 2.96, 0.3), (0, -0.1, 1.97), porcelain, joint="Body", role="proxy")
    m.cylinder("Pedestal", 0.56, 1.2, (0, 0.18, 0.62), porcelain, joint="Body", role="proxy")
    m.sphere("Foot", (1.56, 2.06, 0.3), (0, 0.18, 0.12), porcelain, joint="Body", role="proxy")
    m.box("Deck", (1.4, 0.9, 0.7), (0, 1.32, 1.7), porcelain, joint="Body", role="proxy")

    rx, ry = sculpts.water_level_radii(1.8)
    m.sphere("Water", (2 * rx, 2 * ry, 0.03), (0, -0.14, 1.8), "water", joint="Body", role="mesh")
    m.sphere("WaterTop", (1.86, 2.36, 0.04), (0, -0.12, 2.1), "water", joint="Body", role="proxy")

    seat = S.oval_ring((0, -0.12, 2.13), 1.0, 1.28, 0.34, 0.075, round_r=0.03)
    m.sdf("Seat", seat, (-1.25, -1.5, 2.05), (1.25, 1.3, 2.2), trim, res=0.012, joint="Body",
          shape="Ring", role="both", ring_width=0.34, max_tris=6000)
    m.mirror(m.box, "Hinge", (0.18, 0.22, 0.1), metal, loc=(0.42, 1.12, 2.16), joint="Body",
             bevel=0.03)

    # --- tank -------------------------------------------------------------------------------
    m.sdf("Tank", S.round_box((0, TANK_Y, 2.92), (1.12, 0.42, 0.74), 0.12),
          (-1.2, TANK_Y - 0.5, 2.1), (1.2, TANK_Y + 0.5, 3.74), porcelain, res=0.02, joint="Body",
          shape="Block", role="both", max_tris=5000)
    m.sdf("TankLid", S.round_box((0, TANK_Y, 3.72), (1.18, 0.47, 0.07), 0.05),
          (-1.25, TANK_Y - 0.55, 3.6), (1.25, TANK_Y + 0.55, 3.84), trim, res=0.012,
          joint="Body", shape="Block", role="both", max_tris=4000)
    m.cylinder("LeverPlate", 0.11, 0.04, (-0.78, TANK_Y - 0.43, 3.3), metal, rot=(90, 0, 0),
               joint="Body")
    m.sdf("Lever", S.capsule((-0.78, TANK_Y - 0.47, 3.3), (-0.47, TANK_Y - 0.49, 3.26), 0.035),
          (-0.85, TANK_Y - 0.56, 3.2), (-0.4, TANK_Y - 0.4, 3.36), metal, res=0.008, joint="Body",
          shape="Cylinder", role="both", max_tris=1500)
    m.cylinder("FlushButton", 0.15, 0.04, (0, TANK_Y, 3.8), metal, joint="Body")
    m.cylinder("FlushButtonTop", 0.11, 0.03, (0, TANK_Y, 3.83), "porcelain_shade"
               if variant != "boss" else "gold", joint="Body")

    # --- lid, standing open in front of the tank ------------------------------------------
    m.joint("Lid", (0, 1.12, 2.2), parent="Body")
    lid_tilt = 85
    a = math.radians(lid_tilt)
    lid_c = (0, 1.12 + 1.24 * math.cos(a), 2.2 + 1.24 * math.sin(a))
    lid = S.cylinder(lid_c, 1.0, 0.045, rot=(lid_tilt, 0, 0), sy=1.24, round_r=0.04)
    m.sdf("Lid", lid, (-1.1, lid_c[1] - 0.35, 2.05), (1.1, lid_c[1] + 0.35, 4.75), trim,
          res=0.012, joint="Lid", shape="Sphere", role="both", max_tris=5000)

    # --- head on its long neck ---------------------------------------------------------------
    m.joint("Head", (0, 0, 1.7), parent="Body")
    expression = {"boss": "smug", "tank": "angry", "speedy": "angry"}.get(variant, "manic")
    eyes = {"laser": "laser_red", "boss": "boss_eye"}.get(variant, "normal")
    iris = "iris_blue" if variant == "speedy" else "iris_brown"
    H = sculpts.head(m, (0, -0.02, HEAD_C), HEAD_S, expression=expression, eyes=eyes, iris=iris)
    e = sculpts.EXPRESSIONS[expression]
    field = sculpts.head_field(e)

    def layer(name, region, mat, thickness, lift=0.0, res=0.006, shape="Sphere", role="mesh",
              bmin=(-0.42, -0.62, -0.7), bmax=(0.42, 0.55, 0.62), max_tris=6000):
        """A shell of `thickness` lying on the skin, clipped to `region` (normalised space)."""
        node = lambda P: np.maximum(np.abs(field(P) - lift - thickness / 2) - thickness / 2,
                                    region(P))
        m.sdf(name, H.node(node), *H.bounds(bmin, bmax), mat, res=res * HEAD_S, joint="Head",
              shape=shape, role=role, max_tris=max_tris)

    if variant == "speedy":
        layer("Headband", lambda P: np.abs(P[:, 2] - 0.26) - 0.04, "stripe_red", 0.02)
        for side, sx in (("L", 1), ("R", -1)):
            c = H.point((sx * 0.115, -0.395, 0.27))
            m.cylinder("Goggle" + side, H.size(0.06), H.size(0.05), c, "camera_black",
                       rot=(75, 0, sx * 18), joint="Head")
            lc = H.point((sx * 0.12, -0.425, 0.278))
            m.cylinder("GoggleLens" + side, H.size(0.048), H.size(0.012), lc, "lens_glass",
                       rot=(75, 0, sx * 18), joint="Head")
        m.box("GoggleBridge", H.size((0.07, 0.03, 0.02)), H.point((0, -0.41, 0.27)),
              "camera_black", joint="Head")
        m.mirror(m.box, "Stripe", (0.24, 0.03, 1.46), "stripe_red",
                 loc=(0.36, TANK_Y - 0.43, 2.92), joint="Body")
        m.mirror(m.box, "LidStripe", (0.2, 0.03, 2.3), "stripe_red",
                 loc=(0.3, lid_c[1] - 0.05, lid_c[2]), rot=(lid_tilt - 90, 0, 0), joint="Lid")
    elif variant == "laser":
        layer("Implant", lambda P: np.maximum.reduce([P[:, 0] + 0.04, -0.32 - P[:, 0],
                                                      np.abs(P[:, 2] - 0.06) - 0.15,
                                                      P[:, 1] + 0.12]),
              "chrome", 0.022, res=0.005, shape="Block", role="both")
        for i, (x, z) in enumerate(((-0.27, 0.17), (-0.27, -0.05), (-0.08, 0.19))):
            m.sphere(f"Rivet{i}", H.size(0.022), H.point((x, -0.37 + 0.25 * (x + 0.08), z)),
                     "metal_dark", joint="Head")
        m.cylinder("Antenna", H.size(0.018), H.size(0.5), H.point((0.12, 0.05, 0.68)), "chrome",
                   rot=(0, -10, 0), joint="Head")
        m.sphere("AntennaTip", H.size(0.06), H.point((0.165, 0.05, 0.93)), "laser_red",
                 joint="Head")
        m.mirror(m.cylinder, "Emitter", 0.16, 0.36, "chrome", loc=(1.22, TANK_Y, 3.0),
                 rot=(0, 90, 0), joint="Body")
        m.mirror(m.sphere, "EmitterGlow", 0.2, "laser_red", loc=(1.42, TANK_Y, 3.0),
                 joint="Body")
    elif variant == "tank":
        layer("Helmet", lambda P: np.maximum(0.12 - P[:, 2] - 0.12 * (P[:, 1] > 0.2), -1e3),
              "armor", 0.065, lift=0.01, shape="Sphere", role="both")
        layer("HelmetBrim", lambda P: np.maximum(np.abs(P[:, 2] - 0.13) - 0.025,
                                                 P[:, 1] + 0.05 * 0 - 0.6),
              "armor", 0.03, lift=0.07)
        layer("ChinStrap", lambda P: np.maximum(np.abs(P[:, 1] - 0.02) - 0.022,
                                                np.maximum(P[:, 2] - 0.14, -0.47 - P[:, 2])),
              "camera_black", 0.012)
        armor = lambda P: np.maximum.reduce([np.abs(body_field(P) - 0.05) - 0.035,
                                              P[:, 1] + 0.75, np.abs(P[:, 2] - 1.5) - 0.42])
        m.sdf("BowlArmor", armor, (-1.3, -1.75, 0.95), (1.3, -0.4, 2.05), "armor", res=0.018,
              joint="Body", shape="Block", role="mesh", max_tris=5000)
        m.box("BowlArmorProxy", (1.7, 0.2, 0.84), (0, -1.5, 1.5), "armor", rot=(-12, 0, 0),
              joint="Body", role="proxy")
        for i, (x, z) in enumerate(((-0.75, 1.82), (0.75, 1.82), (-0.6, 1.2), (0.6, 1.2))):
            m.sphere(f"Bolt{i}", 0.12, (x, -1.56 + abs(x) * 0.42 + (1.82 - z) * 0.2, z), "chrome",
                     joint="Body")
        m.box("TankArmor", (2.4, 0.1, 0.62), (0, TANK_Y - 0.47, 3.0), "armor", joint="Body",
              bevel=0.03)
    elif variant == "boss":
        hair_region = lambda P: np.maximum(0.2 - P[:, 2] - 0.32 * np.clip(P[:, 1] + 0.1, 0, 1),
                                           np.abs(P[:, 0]) - 0.3)
        m.sdf("Hair", H.node(lambda P: np.maximum(
                  np.abs(field(P) - 0.035 - 0.004 * np.sin(P[:, 0] * 120)) - 0.035,
                  hair_region(P))),
              *H.bounds((-0.4, -0.5, -0.2), (0.4, 0.5, 0.6)), "hair", res=0.006 * HEAD_S,
              joint="Head", shape="Sphere", role="mesh", max_tris=8000)
        m.sphere("HairProxy", H.size((0.66, 0.86, 0.6)), H.point((0, 0.04, 0.24)), "hair",
                 joint="Head", role="proxy")
        layer("Collar", lambda P: np.abs(P[:, 2] + 0.62) - 0.06, "collar_white", 0.03)
        m.torus("CollarProxy", H.size(0.18), H.size(0.04), H.point((0, 0.07, -0.62)),
                "collar_white", sy=1.08, joint="Head", role="proxy")
        m.box("TieKnot", H.size((0.09, 0.05, 0.08)), H.point((0, -0.13, -0.6)), "tie_red",
              joint="Head", bevel=0.02)
        m.box("Tie", H.size((0.12, 0.03, 0.3)), H.point((0, -0.14, -0.8)), "tie_red",
              rot=(-6, 0, 0), joint="Head", bevel=0.01)
        m.torus("RimTrim", 1.13, 0.05, (0, -0.1, 2.0), "gold", joint="Body", sy=1.26)


# ======================================================================================
# Alliance heads (origin = top of the R6 torso, the neck)
# ======================================================================================

def neck(m, radius=0.24):
    m.cylinder("NeckJoint", radius, 0.44, (0, 0, 0.2), "camera_black")


def camera_head(m):
    """White CCTV security camera with sun shield, dark front glass and a side flashlight."""
    neck(m)
    m.box("MountBase", (0.42, 0.42, 0.14), (0, 0.1, 0.47), "camera_black", bevel=0.05)
    m.sphere("Swivel", 0.28, (0, 0.12, 0.62), "camera_black")
    housing = S.round_box((0, 0.12, 1.2), (0.66, 0.92, 0.45), 0.2)
    seam = S.intersect(S.round_box((0, 0.75, 1.2), (0.8, 0.012, 0.6), 0.005),
                       S.shell(housing, 0.03))
    m.sdf("Housing", S.subtract(housing, seam, k=0.004), (-0.7, -0.84, 0.72), (0.7, 1.08, 1.68),
          "camera_white", res=0.012, shape="Block", role="both", max_tris=8000)
    shield_core = S.round_box((0, 0.0, 1.2), (0.66, 1.05, 0.45), 0.2)
    shield = lambda P: np.maximum.reduce([np.abs(shield_core(P) - 0.075) - 0.025,
                                          1.25 - P[:, 2], P[:, 1] - 0.95,
                                          -1.07 - P[:, 1] + 0.25 * np.clip(P[:, 2] - 1.6, 0, 1)])
    m.sdf("SunShield", shield, (-0.8, -1.1, 1.2), (0.8, 1.0, 1.8), "camera_white", res=0.01,
          shape="Block", role="mesh", max_tris=6000)
    m.box("ShieldProxy", (1.5, 2.0, 0.08), (0, -0.07, 1.74), "camera_white", role="proxy")
    for i, (x, y) in enumerate(((0.74, -0.5), (-0.74, -0.5), (0.74, 0.5), (-0.74, 0.5))):
        m.sphere(f"ShieldScrew{i}", 0.07, (x, y, 1.42), "chrome")
    bezel = S.subtract(S.round_box((0, -0.8, 1.2), (0.58, 0.05, 0.38), 0.12),
                       S.round_box((0, -0.86, 1.2), (0.5, 0.05, 0.3), 0.1), k=0.01)
    m.sdf("Bezel", bezel, (-0.62, -0.88, 0.78), (0.62, -0.72, 1.62), "camera_black", res=0.008,
          shape="Block", role="both", max_tris=4000)
    m.box("FrontGlass", (1.0, 0.03, 0.6), (0, -0.8, 1.2), "screen", bevel=0.08)
    m.cylinder("LensBarrel", 0.21, 0.14, (0.0, -0.86, 1.2), "camera_black", rot=(90, 0, 0))
    m.torus("LensRing", 0.18, 0.025, (0.0, -0.93, 1.2), "chrome", rot=(90, 0, 0))
    m.cylinder("Lens", 0.16, 0.02, (0.0, -0.93, 1.2), "lens_glass", rot=(90, 0, 0))
    m.sphere("LensGlint", 0.05, (-0.06, -0.945, 1.26), "eye_white")
    for i in range(10):
        a = 2 * math.pi * i / 10
        m.sphere(f"IRLed{i}", 0.045, (0.3 * math.cos(a), -0.83, 1.2 + 0.24 * math.sin(a)),
                 "led_red", role="mesh")
    m.sphere("RecLight", 0.08, (0.48, -0.74, 1.6), "rec_red")
    # flashlight clamped under the camera's right side (the round light in the reference)
    m.box("Clamp", (0.16, 0.3, 0.32), (-0.58, -0.25, 0.82), "camera_black", bevel=0.04)
    m.cylinder("FlashBody", 0.15, 0.8, (-0.72, -0.35, 0.68), "camera_black", rot=(90, 0, 0))
    m.cylinder("FlashHead", 0.2, 0.22, (-0.72, -0.8, 0.68), "camera_black", rot=(90, 0, 0),
               radius_top=0.2)
    m.torus("FlashRing", 0.17, 0.03, (-0.72, -0.915, 0.68), "chrome", rot=(90, 0, 0))
    m.cylinder("FlashLens", 0.16, 0.02, (-0.72, -0.915, 0.68), "flash_lens", rot=(90, 0, 0))
    for i in range(3):
        m.torus(f"Grip{i}", 0.15, 0.022, (-0.72, -0.1 - 0.12 * i, 0.68), "metal_dark",
                rot=(90, 0, 0), role="mesh")
    m.cylinder("CableGland", 0.1, 0.18, (0, 1.1, 1.0), "camera_black", rot=(90, 0, 0))
    cable = S.tube_path([(0, 1.18, 1.0), (0, 1.4, 0.75), (0, 1.15, 0.3), (0, 0.55, 0.12)],
                        [0.05, 0.05, 0.05, 0.05])
    m.sdf("Cable", cable, (-0.1, 0.45, 0.02), (0.1, 1.5, 1.1), "cable", res=0.012,
          shape="Cylinder", role="mesh", max_tris=2000)


def _cone_profile(r_out, r_in, depth, steps=10):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        r = r_out + (r_in - r_out) * t
        pts.append((r, -depth * (t ** 0.8)))
    return pts


def speaker_head(m):
    """Grey speaker cabinet: big exposed woofer, horn tweeter, bass port, side handles."""
    neck(m)
    cab = S.round_box((0, 0.05, 1.47), (0.8, 0.62, 1.03), 0.1)
    recess = S.round_box((0, -0.66, 1.47), (0.71, 0.08, 0.95), 0.07)
    port = S.round_box((0, -0.6, 0.62), (0.4, 0.2, 0.06), 0.05)
    handle = S.mirror_x(S.round_box((0.82, 0.05, 2.0), (0.06, 0.32, 0.1), 0.04))
    shell = S.subtract(S.subtract(S.subtract(cab, recess, k=0.02), port, k=0.01), handle, k=0.02)
    m.sdf("Cabinet", shell, (-0.85, -0.6, 0.42), (0.85, 0.7, 2.52), "speaker_gray", res=0.014,
          shape="Block", role="both", max_tris=8000)
    m.box("Baffle", (1.4, 0.04, 1.88), (0, -0.565, 1.47), "speaker_black", bevel=0.05)
    m.mirror(m.box, "HandleBar", (0.05, 0.5, 0.06), "chrome", loc=(0.8, 0.05, 2.0), bevel=0.02)

    # woofer: rubber surround, paper cone, dust cap, chrome frame + screws
    wc = (0, -0.6, 1.08)
    m.joint("Woofer", wc)
    m.lathe("WooferCone", _cone_profile(0.5, 0.14, 0.22), wc, "speaker_cone", rot=(90, 0, 0),
            joint="Woofer", shape="Cylinder", role="mesh", close=False, segments=56)
    m.cylinder("WooferFace", 0.5, 0.04, (wc[0], wc[1] + 0.06, wc[2]), "speaker_cone",
               rot=(90, 0, 0), joint="Woofer", role="proxy")
    m.sphere("DustCap", (0.32, 0.14, 0.32), (wc[0], wc[1] + 0.16, wc[2]), "speaker_rubber",
             joint="Woofer")
    m.torus("Surround", 0.54, 0.055, (wc[0], wc[1] - 0.01, wc[2]), "speaker_rubber",
            rot=(90, 0, 0), joint="Woofer")
    m.torus("WooferFrame", 0.63, 0.04, (wc[0], wc[1] - 0.02, wc[2]), "chrome", rot=(90, 0, 0))
    for i in range(8):
        a = 2 * math.pi * (i + 0.5) / 8
        m.sphere(f"Screw{i}", 0.06, (0.63 * math.cos(a), wc[1] - 0.05, wc[2] + 0.63 * math.sin(a)),
                 "chrome", role="mesh")

    # horn tweeter
    tc = (0, -0.6, 2.06)
    m.joint("Tweeter", tc)
    horn = S.subtract(S.round_box((0, -0.62, 2.06), (0.42, 0.07, 0.2), 0.05),
                      lambda P: S.round_box((0, -0.7, 2.06), (0.36, 0.1, 0.14), 0.05)(P)
                      + np.clip(P[:, 1] + 0.62, 0, 1) * 0.6, k=0.02)
    m.sdf("Horn", horn, (-0.46, -0.72, 1.82), (0.46, -0.52, 2.3), "speaker_black", res=0.008,
          joint="Tweeter", shape="Block", role="both", max_tris=4000)
    m.sphere("TweeterDome", (0.16, 0.08, 0.16), (0, -0.6, 2.06), "chrome", joint="Tweeter")
    m.box("Badge", (0.36, 0.02, 0.08), (0.42, -0.58, 0.5), "chrome", bevel=0.01)


def tv_head(m):
    """CRT television: bulging glowing screen, control strip, rabbit-ear antennas."""
    neck(m)
    front = S.round_box((0, -0.02, 1.25), (1.0, 0.5, 0.8), 0.14)
    back = S.round_box((0, 0.72, 1.2), (0.68, 0.45, 0.55), 0.24)
    case = S.union(front, back, k=0.25)
    recess = S.round_box((0, -0.58, 1.38), (0.8, 0.12, 0.56), 0.16)
    slots = lambda P: np.maximum.reduce([
        np.abs(((P[:, 0] + 0.6) % 0.1) - 0.05) - 0.018, np.abs(P[:, 0] + 0.38) - 0.32,
        np.abs(P[:, 2] - 0.62) - 0.08, -0.5 - P[:, 1] + 0.0, P[:, 1] + 0.47])
    case = S.subtract(S.subtract(case, recess, k=0.03), slots, k=0.005)
    vents = lambda P: np.maximum.reduce([
        np.abs(((P[:, 2] - 0.8) % 0.12) - 0.06) - 0.02, np.abs(P[:, 2] - 1.2) - 0.4,
        np.abs(np.abs(P[:, 0]) - 0.66) - 0.04, np.abs(P[:, 1] - 0.72) - 0.3])
    case = S.subtract(case, vents, k=0.005)
    m.sdf("Case", case, (-1.05, -0.56, 0.42), (1.05, 1.2, 2.08), "tv_body", res=0.014,
          shape="Block", role="mesh", max_tris=9000)
    m.box("CaseProxy", (2.0, 1.0, 1.6), (0, -0.02, 1.25), "tv_body", role="proxy")
    m.box("BackProxy", (1.36, 0.9, 1.1), (0, 0.72, 1.2), "tv_body", role="proxy")
    screen = S.intersect(S.ellipsoid((0, -0.3, 1.38), (0.8, 0.3, 0.58)),
                         S.round_box((0, -0.5, 1.38), (0.74, 0.2, 0.52), 0.15), k=0.01)
    m.sdf("Screen", screen, (-0.8, -0.62, 0.84), (0.8, -0.3, 1.92), "tv_screen", res=0.01,
          shape="Block", role="both", max_tris=4000)
    m.mirror(m.box, "ScreenEye", (0.16, 0.02, 0.26), "tv_bezel", loc=(0.26, -0.6, 1.48),
             bevel=0.05)
    m.box("ScreenMouth", (0.5, 0.02, 0.06), (0, -0.6, 1.16), "tv_bezel", bevel=0.025)
    for i, x in enumerate((0.5, 0.75)):
        m.cylinder(f"Knob{i}", 0.08, 0.1, (x, -0.55, 0.62), "chrome", rot=(90, 0, 0))
    m.box("PowerLed", (0.06, 0.02, 0.04), (0.34, -0.53, 0.62), "rec_red")
    m.sphere("AntennaBase", (0.46, 0.46, 0.26), (0, 0.35, 2.02), "tv_bezel")
    m.joint("Antenna", (0, 0.35, 2.05))
    for side, sgn in (("L", 1), ("R", -1)):
        ang = math.radians(30 * sgn)
        d = np.array([math.sin(ang), 0.15, math.cos(ang)])
        d /= np.linalg.norm(d)
        base = np.array((0, 0.35, 2.05))
        segs = [(0.0, 0.55, 0.04), (0.55, 1.05, 0.03), (1.05, 1.5, 0.022)]
        for k, (t0, t1, r) in enumerate(segs):
            c = base + d * (t0 + t1) / 2
            m.cylinder(f"Antenna{side}{k}", r, t1 - t0, tuple(c), "chrome",
                       rot=(-math.degrees(math.asin(d[1])), 30 * sgn, 0), joint="Antenna")
        m.sphere("AntennaTip" + side, 0.11, tuple(base + d * 1.52), "chrome", joint="Antenna")


# ======================================================================================
# Agent suit: an R6 mannequin plus the clothes and gear from the reference screenshot
# ======================================================================================

def agent_suit(m):
    # Core R6 parts (exact R6 sizes and rest positions; the game rebuilds them as the rig).
    m.joint("Torso", (0, 0, 3))
    m.joint("RightArm", (-1.5, 0, 3.5))
    m.joint("LeftArm", (1.5, 0, 3.5))
    m.joint("RightLeg", (-0.5, 0, 2))
    m.joint("LeftLeg", (0.5, 0, 2))
    m.box("Torso", (2, 1, 2), (0, 0, 3), "shirt", joint="Torso", core=True, bevel=0.03)
    m.box("RightArm", (1, 1, 2), (-1.5, 0, 3), "limb", joint="RightArm", core=True, bevel=0.04)
    m.box("LeftArm", (1, 1, 2), (1.5, 0, 3), "limb", joint="LeftArm", core=True, bevel=0.04)
    m.box("RightLeg", (1, 1, 2), (-0.5, 0, 1), "trousers", joint="RightLeg", core=True,
          bevel=0.03)
    m.box("LeftLeg", (1, 1, 2), (0.5, 0, 1), "trousers", joint="LeftLeg", core=True, bevel=0.03)

    # Coat body (open at the front so the white shirt and tie show).
    m.box("CoatBack", (2.14, 0.1, 2.04), (0, 0.55, 3.0), "coat", joint="Torso", bevel=0.03)
    m.mirror(m.box, "CoatFront", (0.6, 0.1, 2.04), "coat", loc=(0.77, -0.55, 3.0),
             joint="Torso", bevel=0.03)
    m.mirror(m.box, "CoatSide", (0.1, 1.2, 2.04), "coat", loc=(1.06, 0, 3.0), joint="Torso",
             bevel=0.03)
    m.mirror(m.box, "Epaulette", (0.5, 1.12, 0.06), "coat", loc=(0.8, 0, 4.03), joint="Torso",
             bevel=0.02)
    m.mirror(m.wedge, "Lapel", (0.36, 0.06, 1.0), "coat_lapel", loc=(0.33, -0.62, 3.45),
             rot=(0, 0, 0), joint="Torso")
    m.mirror(m.box, "CollarPoint", (0.2, 0.06, 0.16), "shirt", loc=(0.12, -0.56, 3.9),
             rot=(0, -35, 0), joint="Torso", bevel=0.02)
    m.box("TieKnot", (0.22, 0.1, 0.2), (0, -0.58, 3.84), "tie", joint="Torso", bevel=0.04)
    m.box("Tie", (0.26, 0.05, 1.12), (0, -0.565, 3.15), "tie", joint="Torso", bevel=0.02)
    m.box("TieTip", (0.19, 0.05, 0.19), (0, -0.565, 2.58), "tie", rot=(0, 45, 0), joint="Torso")
    for i, z in enumerate((3.55, 3.2, 2.85)):
        m.cylinder(f"ShirtButton{i}", 0.035, 0.02, (0.18, -0.51, z), "button", rot=(90, 0, 0),
                   role="mesh")
    for side, sx in (("L", 1), ("R", -1)):
        for i, z in enumerate((2.95, 2.55)):
            m.cylinder(f"CoatButton{side}{i}", 0.07, 0.03, (sx * 0.58, -0.62, z), "button",
                       rot=(90, 0, 0))
        m.box("PocketFlap" + side, (0.5, 0.06, 0.12), (sx * 0.78, -0.63, 2.4), "coat_lapel",
              joint="Torso", bevel=0.02)
    m.box("PocketSquare", (0.22, 0.04, 0.1), (0.72, -0.62, 3.62), "shirt", joint="Torso",
          bevel=0.015)
    m.box("Belt", (2.06, 1.1, 0.18), (0, 0, 2.1), "belt", joint="Torso")
    m.box("Buckle", (0.32, 0.06, 0.22), (0, -0.57, 2.1), "chrome", joint="Torso", bevel=0.02)

    # Coat tails hang from the waist and swing with the legs (CoatTailL/R joints).
    for side, sgn in (("L", 1), ("R", -1)):
        j = m.joint("CoatTail" + side, (0.5 * sgn, 0, 2.05), parent="Torso")
        m.box("TailBack" + side, (1.03, 0.1, 1.45), (0.535 * sgn, 0.56, 1.3), "coat", joint=j,
              bevel=0.03)
        m.box("TailSide" + side, (0.1, 1.2, 1.45), (1.07 * sgn, 0.0, 1.3), "coat", joint=j,
              bevel=0.03)
        m.box("TailFront" + side, (0.3, 0.1, 1.45), (0.93 * sgn, -0.56, 1.3), "coat", joint=j,
              bevel=0.03)

    # Gloves, shirt cuffs, shoulders, trousers creases, shoes.
    for side, sgn in (("L", 1), ("R", -1)):
        arm = "LeftArm" if sgn > 0 else "RightArm"
        legj = "LeftLeg" if sgn > 0 else "RightLeg"
        m.box("Glove" + side, (1.05, 1.05, 0.62), (1.5 * sgn, 0, 2.3), "glove", joint=arm,
              bevel=0.05)
        m.box("Thumb" + side, (0.22, 0.34, 0.36), (1.5 * sgn - 0.4 * sgn, -0.5, 2.3), "glove",
              joint=arm, bevel=0.06)
        m.box("Cuff" + side, (1.07, 1.07, 0.12), (1.5 * sgn, 0, 2.66), "cuff", joint=arm,
              bevel=0.02)
        m.box("Shoulder" + side, (1.08, 1.08, 0.55), (1.5 * sgn, 0, 3.76), "coat", joint=arm,
              bevel=0.05)
        m.box("Crease" + side, (0.04, 0.02, 1.5), (0.5 * sgn, -0.51, 1.05), "coat_lapel",
              joint=legj)
        m.box("Shoe" + side, (1.04, 1.24, 0.34), (0.5 * sgn, -0.12, 0.24), "shoe", joint=legj,
              bevel=0.1)
        m.box("Sole" + side, (1.08, 1.3, 0.1), (0.5 * sgn, -0.13, 0.05), "sole", joint=legj,
              bevel=0.03)

    # Gear: baton across the back, handcuffs on the right hip.
    m.cylinder("Baton", 0.11, 2.7, (0.25, 0.72, 3.55), "gear_black", rot=(0, 38, 0),
               joint="Torso")
    m.cylinder("BatonGrip", 0.14, 0.6, (-0.52, 0.72, 4.55), "gear_black", rot=(0, 38, 0),
               joint="Torso")
    for i in range(3):
        m.torus(f"BatonRing{i}", 0.14, 0.025, (-0.38 - 0.13 * i, 0.72, 4.37 + 0.17 * i), "chrome",
                rot=(0, 38, 0), joint="Torso", role="mesh")
    m.torus("CuffRing1", 0.22, 0.05, (-1.14, -0.22, 1.85), "cuffs_white", rot=(0, 90, 0),
            joint="Torso")
    m.torus("CuffRing2", 0.22, 0.05, (-1.16, -0.32, 1.42), "cuffs_white", rot=(0, 90, 20),
            joint="Torso")
    for i in range(3):
        m.torus(f"Link{i}", 0.04, 0.012, (-1.15, -0.25 - 0.025 * i, 1.7 - 0.07 * i), "chrome",
                rot=(0, 90 * (i % 2), 0), joint="Torso", role="mesh")


# ======================================================================================
# Toilet portal: a sewer pipe sticking out of the arena wall (enemy spawner)
# ======================================================================================

def toilet_portal(m):
    cz = 4.6
    m.tube("Pipe", 3.6, 4.2, 3.2, (0, 0.6, cz), "metal_light", rot=(90, 0, 0))
    m.tube("Flange", 3.9, 4.8, 0.5, (0, -1.0, cz), "metal_dark", rot=(90, 0, 0))
    m.tube("BackFlange", 4.0, 4.6, 0.4, (0, 2.0, cz), "metal_dark", rot=(90, 0, 0))
    for i in range(16):
        a = 2 * math.pi * i / 16
        m.cylinder(f"Bolt{i}", 0.16, 0.2, (math.cos(a) * 4.35, -1.3, cz + math.sin(a) * 4.35),
                   "chrome", rot=(90, 0, 0), segments=12)
    m.cylinder("Back", 3.65, 0.3, (0, 2.0, cz), "portal_dark", rot=(90, 0, 0))
    m.joint("Swirl", (0, 1.6, cz))
    spiral = []
    for i in range(60):
        t = i / 59
        a = t * 4 * math.pi
        r = 3.2 * (1 - t) + 0.25
        spiral.append((r * math.cos(a), 1.75 - 0.6 * t, cz + r * math.sin(a)))
    sp = S.tube_path(spiral, [0.32 * (1 - 0.7 * i / 59) for i in range(60)])
    m.sdf("Vortex", sp, (-3.6, 0.9, cz - 3.6), (3.6, 2.1, cz + 3.6), "portal_glow", res=0.05,
          joint="Swirl", shape="Ring", role="mesh", max_tris=8000)
    m.torus("SwirlOuter", 2.9, 0.22, (0, 1.6, cz), "portal_glow", rot=(90, 0, 0), joint="Swirl",
            role="proxy")
    m.torus("SwirlInner", 1.7, 0.18, (0, 1.65, cz), "portal_glow", rot=(90, 0, 0), joint="Swirl",
            role="proxy")
    m.sphere("SwirlCore", (1.2, 0.2, 1.2), (0, 1.7, cz), "portal_glow", joint="Swirl")
    drip = S.union(S.round_box((0, -0.5, cz - 3.62), (1.5, 0.12, 0.12), 0.1),
                   S.capsule((-0.6, -0.55, cz - 3.62), (-0.6, -0.6, cz - 4.2), 0.1, 0.06),
                   S.capsule((0.5, -0.55, cz - 3.62), (0.5, -0.6, cz - 4.4), 0.12, 0.07), k=0.1)
    m.sdf("Drip", drip, (-1.7, -0.8, 0.1), (1.7, -0.3, cz - 3.4), "slime", res=0.03,
          shape="Block", role="both", max_tris=3000)
    m.sphere("Puddle", (5.5, 4.0, 0.12), (0, -2.6, 0.06), "slime")
    m.mirror(m.box, "Strut", (0.8, 2.6, 0.6), "metal_dark", loc=(2.6, 0.6, 0.3), bevel=0.06)


MODELS = {
    "SkibidiToilet": dict(build=lambda m: toilet(m, "basic")),
    "SpeedyToilet": dict(build=lambda m: toilet(m, "speedy")),
    "LaserToilet": dict(build=lambda m: toilet(m, "laser")),
    "TankToilet": dict(build=lambda m: toilet(m, "tank")),
    "GToilet": dict(build=lambda m: toilet(m, "boss")),
    "CameraHead": dict(build=camera_head, up=2.0, front=1.0),
    "SpeakerHead": dict(build=speaker_head, up=2.0, front=1.0),
    "TVHead": dict(build=tv_head, up=2.0, front=1.0),
    "AgentSuit": dict(build=agent_suit),
    "ToiletPortal": dict(build=toilet_portal, up=8.0, front=4.0),
}

# Class colour swaps used by the poster render (the game applies the same swaps,
# see Config.Classes[...].suit).
SUITS = {
    "Cameraman": {},
    "Speakerman": {"coat": "coat_speaker", "shirt": "shirt_speaker", "tie": "tie_speaker"},
    "TVMan": {"coat": "coat_tv", "shirt": "shirt_tv", "tie": "tie_tv"},
}
