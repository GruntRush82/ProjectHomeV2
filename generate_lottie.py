#!/usr/bin/env python3
"""
Generate real Lottie animation JSON for all 30 L5-L10 icons.

Each animation uses colored animated shapes — no external assets needed.
Run from project-home/:  python generate_lottie.py
"""

import json, math
from pathlib import Path

LOTTIE_DIR = Path(__file__).parent / "app/static/lottie"
FPS = 30
DUR = 90   # 3-second loop at 30fps

# ── Primitive helpers ──────────────────────────────────────────────────────

def s(v):
    """Static value."""
    return {"a": 0, "k": v if isinstance(v, list) else [v]}

def ease(x=0.42, y=1.0):
    return {"x": [x], "y": [y]}

def kf(t, v, ei=None, eo=None):
    """Keyframe. v must be a list."""
    k = {"t": t, "s": v}
    k["i"] = ei or ease()
    k["o"] = eo or ease(0.58, 0)
    return k

def kf_linear(t, v):
    return {"t": t, "s": v,
            "i": {"x": [0.5], "y": [0.5]},
            "o": {"x": [0.5], "y": [0.5]}}

def anim(*kfs):
    return {"a": 1, "k": list(kfs)}

# ── Shapes ─────────────────────────────────────────────────────────────────

def el(w, h=None):
    return {"ty": "el", "p": s([0, 0]), "s": s([w, h or w]), "nm": "E"}

def star(pts, outer, inner=None):
    inner = inner or outer * 0.42
    return {"ty": "sr", "sy": 1, "d": 1,
            "pt": s(pts), "p": s([0, 0]), "r": s(0),
            "ir": s(inner), "is": s(0),
            "or": s(outer), "os": s(0), "nm": "S"}

def fl(r, g, b, a=1):
    return {"ty": "fl", "c": s([r, g, b, a]), "o": s(100), "r": 1, "nm": "F"}

def fl_anim(color_kfs):
    return {"ty": "fl", "c": {"a": 1, "k": color_kfs}, "o": s(100), "r": 1, "nm": "F"}

def st(r, g, b, w=3, a=1):
    return {"ty": "st", "c": s([r, g, b, a]), "o": s(100),
            "lc": 2, "lj": 2, "w": s(w), "nm": "St"}

def tr(px=0, py=0, sx=100, sy=100, r=0, o=100):
    return {"ty": "tr",
            "p": s([px, py]), "a": s([0, 0]),
            "s": s([sx, sy]), "r": s(r), "o": s(o)}

def grp(*shapes, px=0, py=0, sx=100, sy=100, r=0, o=100):
    return {"ty": "gr", "nm": "G",
            "it": list(shapes) + [tr(px, py, sx, sy, r, o)]}

# ── Animation builders ─────────────────────────────────────────────────────

def pulse_scale(lo=92, hi=108, dur=DUR):
    h = dur // 2
    return anim(kf(0, [lo, lo, 100]), kf(h, [hi, hi, 100]), kf(dur, [lo, lo, 100]))

def spin_rot(dur=DUR, deg=360):
    return {"a": 1, "k": [
        {"t": 0,   "s": [0],   "i": {"x": [0.83], "y": [0.83]}, "o": {"x": [0.17], "y": [0.17]}},
        {"t": dur, "s": [deg]},
    ]}

def op_pulse(lo=60, hi=100, dur=DUR):
    h = dur // 2
    return anim(kf(0, [hi]), kf(h, [lo]), kf(dur, [hi]))

def flash_op(dur=DUR):
    t = dur // 4
    return anim(kf(0, [100]), kf(t, [30]), kf(t*2, [100]),
                kf(t*3, [30]), kf(dur, [100]))

# ── Layer builder ──────────────────────────────────────────────────────────

def layer(ind, nm, shapes, px=50, py=50, sc=None, ro=None, op=None):
    return {
        "ddd": 0, "ind": ind, "ty": 4, "nm": nm, "sr": 1,
        "ks": {
            "o": op or s(100),
            "r": ro or s(0),
            "p": s([px, py, 0]),
            "a": s([0, 0, 0]),
            "s": sc or s([100, 100, 100]),
        },
        "ao": 0, "shapes": list(shapes), "ip": 0, "op": DUR, "st": 0, "bm": 0
    }

def orbit_layer(ind, nm, radius, dot_size, color_fl, period=DUR, start_angle=0):
    """Dot that orbits the center by spinning the whole layer with an offset dot."""
    return {
        "ddd": 0, "ind": ind, "ty": 4, "nm": nm, "sr": 1,
        "ks": {
            "o": s(100),
            "r": spin_rot(period),
            "p": s([50, 50, 0]),
            "a": s([0, 0, 0]),
            "s": s([100, 100, 100]),
        },
        "ao": 0,
        "shapes": [grp(el(dot_size), color_fl, px=radius, py=0)],
        "ip": 0, "op": DUR, "st": start_angle, "bm": 0
    }

def wrap(nm, layers_list):
    return {"v": "5.7.4", "fr": FPS, "ip": 0, "op": DUR,
            "w": 100, "h": 100, "nm": nm, "ddd": 0,
            "assets": [], "layers": list(layers_list)}

def save(nm, data):
    p = LOTTIE_DIR / f"icon_{nm}.json"
    txt = json.dumps(data, separators=(",", ":"))
    p.write_text(txt)
    print(f"  {p.name:40s}  {len(txt):>6,} bytes")

# ─────────────────────────────────────────────────────────────────────────────
# ICON DEFINITIONS
# Colors: Lottie uses 0-1 float RGB
# ─────────────────────────────────────────────────────────────────────────────

GREEN      = fl(0.18, 0.80, 0.44)   # #2ecc71
DARK_GREEN = fl(0.15, 0.68, 0.38)   # #27ae60
ORANGE     = fl(0.93, 0.50, 0.18)   # #ee8030
DEEP_ORG   = fl(0.93, 0.44, 0.10)   # #ee7018
PURPLE     = fl(0.61, 0.35, 0.71)   # #9b59b6
VIOLET     = fl(0.44, 0.13, 0.49)   # #70207e
YELLOW     = fl(0.95, 0.77, 0.06)   # #f2c40f
GOLD       = fl(1.00, 0.84, 0.00)   # #ffd700
BRIGHT_GOLD= fl(1.00, 0.90, 0.20)   # #ffe533
CYAN       = fl(0.00, 0.83, 1.00)   # #00d4ff
CYAN2      = fl(0.00, 1.00, 0.94)   # #00fff0
BLUE       = fl(0.20, 0.60, 0.86)   # #3399db
RED        = fl(0.75, 0.22, 0.17)   # #c0382c
FIRE_RED   = fl(1.00, 0.27, 0.00)   # #ff4500
FIRE_ORG   = fl(1.00, 0.42, 0.00)   # #ff6b00
MAGENTA    = fl(1.00, 0.00, 0.43)   # #ff006e
WHITE      = fl(1.00, 1.00, 1.00)   # #ffffff
NEAR_BLK   = fl(0.04, 0.01, 0.16)   # #0a0329
VOID_DARK  = fl(0.02, 0.00, 0.10)   # #050019
COSMIC_PUR = fl(0.42, 0.20, 0.51)   # #6b3382
SPACE_BLUE = fl(0.13, 0.45, 0.81)   # #2173ce
ICE        = fl(0.56, 0.94, 1.00)   # #8ef0ff
EMBER_RED  = fl(0.90, 0.16, 0.08)   # #e62815
FIREFLY    = fl(0.65, 1.00, 0.24)   # #a6ff3d
ELEC_BLUE  = fl(0.67, 0.87, 1.00)   # #abdeff

# ─────────────────────────────────────────────────────────────────────────────
# L5 — Champion  (gentle pulse, 3s cycle)
# ─────────────────────────────────────────────────────────────────────────────

def make_dragon_face():
    """Green pulsing dragon circle with eyes."""
    return wrap("dragon_face", [
        layer(1, "body",  [el(64), GREEN], sc=pulse_scale(92, 108)),
        layer(2, "eye_l", [el(10), fl(0,0,0)], px=36, py=43),
        layer(3, "eye_r", [el(10), fl(0,0,0)], px=64, py=43),
        layer(4, "pupil_l",[el(5), fl(1,1,1)], px=38, py=43),
        layer(5, "pupil_r",[el(5), fl(1,1,1)], px=66, py=43),
    ])

def make_phoenix():
    """Orange 6-pointed star pulsing like a flame."""
    return wrap("phoenix", [
        layer(1, "glow",  [el(70), fl(0.93, 0.40, 0.0, 0.35)], sc=pulse_scale(88, 112, 75)),
        layer(2, "body",  [star(6, 32), ORANGE], sc=pulse_scale(92, 108)),
    ])

def make_wizard():
    """Purple 8-pointed star rotating slowly — magical spin."""
    return wrap("wizard", [
        layer(1, "outer", [star(8, 34, 14), fl(0.44, 0.19, 0.61, 0.6)], ro=spin_rot(180)),
        layer(2, "inner", [star(8, 24, 10), PURPLE], ro=spin_rot(120, -360)),
        layer(3, "core",  [el(18), fl(0.78, 0.60, 0.90)]),
    ])

def make_lightning_charged():
    """Yellow 4-pointed star with electric flash."""
    return wrap("lightning_charged", [
        layer(1, "halo",  [el(72), fl(0.95, 0.77, 0.06, 0.25)], op=flash_op()),
        layer(2, "bolt",  [star(4, 32, 8), YELLOW], op=flash_op(DUR)),
        layer(3, "bolt2", [star(4, 20, 5), fl(1,1,0.6)], ro=spin_rot(45), op=flash_op()),
    ])

def make_gem_glowing():
    """Cyan diamond (4-point star) rotating with glow."""
    return wrap("gem_glowing", [
        layer(1, "glow",  [el(68), fl(0.0, 0.83, 1.0, 0.30)], sc=pulse_scale(90, 110, 60)),
        layer(2, "gem",   [star(4, 30, 12), CYAN], ro=spin_rot(DUR, 90)),
        layer(3, "shine", [star(4, 16, 4), fl(1, 1, 1, 0.9)], ro=spin_rot(DUR, -90)),
    ])

# ─────────────────────────────────────────────────────────────────────────────
# L6 — Hero  (shimmer / opacity effects, ~2.5s cycle)
# ─────────────────────────────────────────────────────────────────────────────

def make_knight_hero():
    """Blue pulsing shield-circle with white core."""
    return wrap("knight_hero", [
        layer(1, "ring",  [el(70), fl(0.20, 0.60, 0.86, 0.30)], sc=pulse_scale(88, 112, 60)),
        layer(2, "shield",[el(60), BLUE], sc=pulse_scale(94, 106, 60)),
        layer(3, "cross_h",[{"ty":"rc","p":s([0,0]),"s":s([36,7]),"r":s(0),"nm":"R"},
                             fl(1,1,1,0.9)]),
        layer(4, "cross_v",[{"ty":"rc","p":s([0,0]),"s":s([7,36]),"r":s(0),"nm":"R"},
                             fl(1,1,1,0.9)]),
    ])

def make_samurai():
    """Red circle with spinning outer ring — disciplined rotation."""
    return wrap("samurai", [
        layer(1, "ring", [el(66), st(0.75, 0.22, 0.17, 4)], ro=spin_rot(60)),
        layer(2, "body", [el(54), RED], sc=pulse_scale(95, 105, 75)),
        layer(3, "mark", [star(3, 14, 6), fl(1, 1, 1, 0.95)]),
    ])

def make_thunder_storm():
    """Yellow-orange lightning triangle flashing."""
    return wrap("thunder_storm", [
        layer(1, "halo", [star(3, 40, 20), fl(0.95, 0.62, 0.0, 0.28)], op=flash_op(75)),
        layer(2, "tri",  [star(3, 30, 15), YELLOW], op=flash_op()),
        layer(3, "core", [el(14), fl(1, 1, 0.7)], op=flash_op()),
    ])

def make_fire_hero():
    """Orange-red 5-point star blazing."""
    return wrap("fire_hero", [
        layer(1, "aura", [el(72), fl(1.0, 0.27, 0.0, 0.25)], sc=pulse_scale(85, 115, 50)),
        layer(2, "star", [star(5, 32), FIRE_ORG],              sc=pulse_scale(90, 110, 65)),
        layer(3, "core", [el(20), YELLOW],                     sc=pulse_scale(88, 108, 60)),
    ])

def make_fire_wolf():
    """Magenta circle with inner shimmer."""
    return wrap("fire_wolf", [
        layer(1, "outer",[el(68), fl(1.0, 0.0, 0.43, 0.28)], op=op_pulse(50, 100, 60)),
        layer(2, "body", [el(58), MAGENTA],                    sc=pulse_scale(92, 108, 60)),
        layer(3, "eyes", [star(2, 16, 2), fl(1,1,1,0.8)],    ro=spin_rot(90, 180)),
    ])

# ─────────────────────────────────────────────────────────────────────────────
# L7 — Legend  (rotation focus, slow spin)
# ─────────────────────────────────────────────────────────────────────────────

def make_dragon_full():
    """Large green circle with orbiting red fire dot."""
    return wrap("dragon_full", [
        layer(1, "body",  [el(62), DARK_GREEN], sc=pulse_scale(95, 105, 90)),
        layer(2, "ring",  [el(68), st(0.15, 0.68, 0.38, 2)], ro=spin_rot(120)),
        orbit_layer(3, "fire", 36, 12, fl(1.0, 0.42, 0.0), period=60),
    ])

def make_flame_premium():
    """Tall flame ellipse breathing — orange fire."""
    h = DUR // 2
    breathe_v = anim(kf(0, [90, 110, 100]), kf(h, [110, 90, 100]), kf(DUR, [90, 110, 100]))
    return wrap("flame_premium", [
        layer(1, "glow",  [el(50, 70), fl(1.0, 0.42, 0.0, 0.25)], sc=breathe_v),
        layer(2, "flame", [el(38, 58), FIRE_ORG], sc=breathe_v),
        layer(3, "core",  [el(22, 30), YELLOW]),
    ])

def make_constellation():
    """White 8-pointed star rotating slowly — cosmic."""
    return wrap("constellation", [
        layer(1, "outer", [star(8, 36, 15), fl(1,1,1,0.25)], ro=spin_rot(180)),
        layer(2, "star",  [star(8, 28, 11), WHITE],           ro=spin_rot(240, -360)),
        layer(3, "core",  [el(12), fl(0.8, 0.9, 1.0)],        sc=pulse_scale(85, 115, 75)),
    ])

def make_thunderbolt():
    """Gold 4-point star flashing."""
    return wrap("thunderbolt", [
        layer(1, "halo",  [el(72), fl(1, 0.84, 0, 0.25)],  op=flash_op()),
        layer(2, "outer", [star(4, 34, 10), GOLD],           op=flash_op()),
        layer(3, "inner", [star(4, 18, 6), BRIGHT_GOLD],     ro=spin_rot(45), op=flash_op()),
    ])

def make_vortex():
    """Cyan spiral — fast spinning rings."""
    return wrap("vortex", [
        layer(1, "ring3", [el(70), st(0.0, 0.83, 1.0, 3, 0.4)], ro=spin_rot(30, -360)),
        layer(2, "ring2", [el(52), st(0.0, 0.83, 1.0, 3, 0.7)], ro=spin_rot(25)),
        layer(3, "core",  [el(36), CYAN],                          ro=spin_rot(20, -360)),
        layer(4, "dot",   [el(12), fl(1, 1, 1)],                   sc=pulse_scale(90, 110, 45)),
    ])

# ─────────────────────────────────────────────────────────────────────────────
# L8 — Master  (intense effects)
# ─────────────────────────────────────────────────────────────────────────────

def make_firefly_swarm():
    """4 green-yellow dots blinking at staggered offsets."""
    dots = []
    positions = [(30,35), (65,38), (42,65), (72,60)]
    delays = [0, 22, 11, 33]
    for i, ((px, py), d) in enumerate(zip(positions, delays)):
        blink = anim(kf(0, [80]), kf(15, [15]), kf(30, [90]), kf(DUR, [60]))
        dots.append(layer(i+1, f"fly{i}", [el(9), FIREFLY], px=px, py=py,
                          op={"a":1,"k":[kf(0,[80 if d==0 else 15]),
                                         kf(15+d,[15 if d==0 else 80]),
                                         kf(30+d,[90]),
                                         kf(DUR,[80 if d==0 else 15])]}))
    return wrap("firefly_swarm", dots)

def make_black_hole():
    """Dark circle with spinning gold accretion ring."""
    return wrap("black_hole", [
        layer(1, "disk",  [el(64), NEAR_BLK]),
        layer(2, "ring1", [el(78), st(1.0, 0.84, 0.0, 4, 0.9)], ro=spin_rot(45, -360)),
        layer(3, "ring2", [el(72), st(0.6, 0.20, 0.9, 2, 0.5)], ro=spin_rot(30)),
        layer(4, "core",  [el(16), fl(1, 0.7, 0)],               sc=pulse_scale(85, 115, 45)),
    ])

def make_meteor():
    """Orange-white ellipse blazing — strong pulse."""
    return wrap("meteor", [
        layer(1, "trail", [el(70, 40), fl(1.0, 0.27, 0.0, 0.30)],
              sc=pulse_scale(80, 120, 45), op=op_pulse(40, 100, 45)),
        layer(2, "body",  [el(54, 30), FIRE_RED],    sc=pulse_scale(88, 112, 45)),
        layer(3, "core",  [el(30, 18), fl(1,0.9,0.6)]),
    ])

def make_phoenix_master():
    """Two 6-point stars counter-rotating — fire bird."""
    return wrap("phoenix_master", [
        layer(1, "outer", [star(6, 34), fl(1.0, 0.27, 0.0, 0.8)], ro=spin_rot(60)),
        layer(2, "inner", [star(6, 22), fl(1.0, 0.65, 0.0)],       ro=spin_rot(45, -360)),
        layer(3, "core",  [el(14), YELLOW],                          sc=pulse_scale(85, 115, 40)),
    ])

def make_electric_storm():
    """White-blue 8-pointed star with electric flash."""
    return wrap("electric_storm", [
        layer(1, "halo",  [el(76), fl(0.67, 0.87, 1.0, 0.22)], op=flash_op(60)),
        layer(2, "outer", [star(8, 34, 12), ELEC_BLUE],          ro=spin_rot(60), op=flash_op(45)),
        layer(3, "inner", [star(8, 20, 7), fl(1,1,1,0.9)],       ro=spin_rot(45, -360)),
    ])

# ─────────────────────────────────────────────────────────────────────────────
# L9 — Titan  (complex multi-layer)
# ─────────────────────────────────────────────────────────────────────────────

def make_dragon_ember():
    """Red dragon circle with two orbiting ember dots."""
    return wrap("dragon_ember", [
        layer(1, "body",  [el(60), EMBER_RED],   sc=pulse_scale(93, 107, 60)),
        layer(2, "ring",  [el(66), st(0.90, 0.16, 0.08, 2)], ro=spin_rot(90)),
        orbit_layer(3, "ember1", 34, 10, fl(1.0, 0.55, 0.0), period=50),
        orbit_layer(4, "ember2", 34, 10, fl(1.0, 0.80, 0.0), period=50, start_angle=45),
    ])

def make_spaceship():
    """Blue ellipse with trailing star-field dots."""
    return wrap("spaceship", [
        layer(1, "aura",  [el(66, 48), fl(0.13, 0.45, 0.81, 0.25)], sc=pulse_scale(88, 112, 55)),
        layer(2, "hull",  [el(52, 36), SPACE_BLUE],                   sc=pulse_scale(93, 107, 55)),
        layer(3, "window",[el(20, 16), fl(0.6, 0.9, 1.0)]),
        orbit_layer(4, "star1", 38, 7, fl(1,1,1,0.8), period=40),
        orbit_layer(5, "star2", 38, 7, fl(1,1,0.6,0.7), period=40, start_angle=60),
    ])

def make_cosmic_wolf():
    """Purple circle with 3 orbiting cosmic dots."""
    return wrap("cosmic_wolf", [
        layer(1, "body",  [el(60), COSMIC_PUR], sc=pulse_scale(94, 106, 75)),
        layer(2, "ring",  [el(68), st(0.42, 0.20, 0.51, 2)], ro=spin_rot(90, -360)),
        orbit_layer(3, "dot1", 36, 9, fl(0.8, 0.5, 1.0), period=60),
        orbit_layer(4, "dot2", 36, 9, fl(0.5, 0.8, 1.0), period=60, start_angle=30),
        orbit_layer(5, "dot3", 36, 9, fl(1.0, 0.5, 0.8), period=60, start_angle=60),
    ])

def make_supernova():
    """Gold 8-point star expanding burst — intense pulse."""
    return wrap("supernova", [
        layer(1, "burst", [el(80), fl(1.0, 0.84, 0.0, 0.15)], sc=pulse_scale(70, 120, 40),
              op=op_pulse(0, 60, 40)),
        layer(2, "outer", [star(8, 36, 13), GOLD],              sc=pulse_scale(86, 114, 45)),
        layer(3, "inner", [star(8, 22, 8), BRIGHT_GOLD],        ro=spin_rot(45, -360),
              sc=pulse_scale(90, 110, 45)),
        layer(4, "core",  [el(12), fl(1,1,1)],                  sc=pulse_scale(80, 120, 40)),
    ])

def make_ice_titan():
    """Cyan 6-pointed snowflake rotating slowly."""
    return wrap("ice_titan", [
        layer(1, "glow",  [el(72), fl(0.56, 0.94, 1.0, 0.20)], sc=pulse_scale(90, 110, 90)),
        layer(2, "outer", [star(6, 34, 8), ICE],                 ro=spin_rot(180)),
        layer(3, "inner", [star(6, 22, 5), CYAN2],               ro=spin_rot(120, -360)),
        layer(4, "core",  [el(14), fl(1, 1, 1)]),
    ])

# ─────────────────────────────────────────────────────────────────────────────
# L10 — Ultimate  (maximum drama, fastest animations)
# ─────────────────────────────────────────────────────────────────────────────

def make_galaxy():
    """Purple circle with 3 orbiting dots at different radii/speeds."""
    return wrap("galaxy", [
        layer(1, "nebula",[el(76), fl(0.24, 0.05, 0.50, 0.25)], sc=pulse_scale(88, 112, 75)),
        layer(2, "core",  [el(56), fl(0.31, 0.08, 0.65)],        ro=spin_rot(90, -360)),
        layer(3, "center",[el(20), fl(0.6, 0.3, 0.9)],           sc=pulse_scale(90, 110, 60)),
        orbit_layer(4, "star1", 38, 8, fl(1.0, 0.9, 0.4), period=40),
        orbit_layer(5, "star2", 28, 6, fl(0.8, 0.6, 1.0), period=35, start_angle=30),
        orbit_layer(6, "star3", 18, 5, fl(0.6, 0.9, 1.0), period=30, start_angle=60),
    ])

def make_infinity_ultimate():
    """Gold 8-point star spinning fast + counter-rotating ring."""
    return wrap("infinity_ultimate", [
        layer(1, "halo",  [el(78), fl(1.0, 0.84, 0.0, 0.22)], sc=pulse_scale(85, 115, 40)),
        layer(2, "outer", [star(8, 36, 14), GOLD],              ro=spin_rot(35)),
        layer(3, "inner", [star(8, 24, 9), BRIGHT_GOLD],        ro=spin_rot(25, -360)),
        layer(4, "core",  [el(14), fl(1,1,1)],                  sc=pulse_scale(80, 120, 35)),
    ])

def make_titan_god():
    """Gold 6-point star blazing with intense pulse."""
    return wrap("titan_god", [
        layer(1, "aura",  [el(80), fl(1.0, 0.84, 0.0, 0.20)], sc=pulse_scale(75, 125, 35),
              op=op_pulse(30, 80, 35)),
        layer(2, "outer", [star(6, 36, 15), GOLD],              sc=pulse_scale(85, 115, 35)),
        layer(3, "inner", [star(6, 22, 9), BRIGHT_GOLD],        ro=spin_rot(70, -360),
              sc=pulse_scale(88, 112, 35)),
        layer(4, "core",  [el(12), fl(1, 1, 0.8)],              sc=pulse_scale(78, 122, 30)),
    ])

def make_void_dragon():
    """Near-black void circle with gold orbiting ring."""
    return wrap("void_dragon", [
        layer(1, "void",   [el(64), VOID_DARK]),
        layer(2, "ring1",  [el(72), st(1.0, 0.84, 0.0, 3)], ro=spin_rot(40)),
        layer(3, "ring2",  [el(78), st(0.5, 0.0, 0.9, 2, 0.5)], ro=spin_rot(30, -360)),
        orbit_layer(4, "pulse1", 38, 9, fl(1.0, 0.84, 0.0), period=35),
        orbit_layer(5, "pulse2", 38, 9, fl(0.6, 0.0, 1.0), period=35, start_angle=45),
        layer(6, "core",   [el(10), fl(1, 0.9, 0.2)],       sc=pulse_scale(80, 120, 30)),
    ])

def make_omega():
    """White + gold stars counter-rotating at max speed — light speed."""
    return wrap("omega", [
        layer(1, "halo",  [el(80), fl(1.0, 1.0, 1.0, 0.15)], sc=pulse_scale(80, 120, 30)),
        layer(2, "outer", [star(4, 36, 10), WHITE],             ro=spin_rot(30)),
        layer(3, "mid",   [star(4, 28, 8), GOLD],               ro=spin_rot(25, -360)),
        layer(4, "inner", [star(4, 18, 5), BRIGHT_GOLD],        ro=spin_rot(20)),
        layer(5, "core",  [el(12), fl(1, 1, 1)],                sc=pulse_scale(78, 122, 25)),
    ])

# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

MAKERS = {
    # L5
    "dragon_face":       make_dragon_face,
    "phoenix":           make_phoenix,
    "wizard":            make_wizard,
    "lightning_charged": make_lightning_charged,
    "gem_glowing":       make_gem_glowing,
    # L6
    "knight_hero":       make_knight_hero,
    "samurai":           make_samurai,
    "thunder_storm":     make_thunder_storm,
    "fire_hero":         make_fire_hero,
    "fire_wolf":         make_fire_wolf,
    # L7
    "dragon_full":       make_dragon_full,
    "flame_premium":     make_flame_premium,
    "constellation":     make_constellation,
    "thunderbolt":       make_thunderbolt,
    "vortex":            make_vortex,
    # L8
    "firefly_swarm":     make_firefly_swarm,
    "black_hole":        make_black_hole,
    "meteor":            make_meteor,
    "phoenix_master":    make_phoenix_master,
    "electric_storm":    make_electric_storm,
    # L9
    "dragon_ember":      make_dragon_ember,
    "spaceship":         make_spaceship,
    "cosmic_wolf":       make_cosmic_wolf,
    "supernova":         make_supernova,
    "ice_titan":         make_ice_titan,
    # L10
    "galaxy":            make_galaxy,
    "infinity_ultimate": make_infinity_ultimate,
    "titan_god":         make_titan_god,
    "void_dragon":       make_void_dragon,
    "omega":             make_omega,
}

if __name__ == "__main__":
    print(f"Generating {len(MAKERS)} Lottie animation files → {LOTTIE_DIR}/\n")
    for name, fn in MAKERS.items():
        data = fn()
        save(name, data)
    print(f"\n✅ Done — {len(MAKERS)} files generated.")
