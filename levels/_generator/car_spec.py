"""Shared car geometry + atlas mapping (used by build_street.py and paint_textures.py).
Car space: +x = front, +y = left, z up, origin on the ground under the car centre. 1 unit = 1 m.
Generic 1970s boxy sedan / wagon proportions (not a copy of a specific model)."""
import math

W = 1.62                      # body width
HW = W / 2
AX_F, AX_R, WR = 1.30, -1.12, 0.29     # axles, wheel radius
ARCH_R = 0.36
SILL = 0.26

def profile(kind):
    """side outline of the lower body (x, z), counter-clockwise seen from -y"""
    top = [(2.02, 0.28), (2.05, 0.55), (2.04, 0.80), (0.70, 0.89)]
    if kind == 'wagon': top += [(-1.98, 0.91)]
    else: top += [(-0.95, 0.91), (-1.99, 0.87)]
    back = [(-2.05, 0.62), (-2.03, 0.30)]
    return top + back + [(-1.50, SILL)] + _arch_sorted(AX_R) + _arch_sorted(AX_F) + [(1.70, SILL + .01)]

def _arch_sorted(cx):
    """arch points ordered rear -> front (x increasing), going over the wheel"""
    pts = []
    for a in (185, 155, 125, 90, 55, 25, -5):
        r = math.radians(a); pts.append((cx + ARCH_R * math.cos(r), 0.29 + ARCH_R * math.sin(r)))
    return pts

def greenhouse(kind):
    """(bottom-front x, z), (bottom-rear x, z), (top-front x), (top-rear x), roof z, bottom half-width, top half-width"""
    if kind == 'wagon': return dict(bf=(0.70, 0.88), br=(-1.97, 0.89), tf=0.05, tr=-1.90, roof=1.42, bw=0.72, tw=0.63)
    return dict(bf=(0.70, 0.88), br=(-0.95, 0.90), tf=0.05, tr=-0.60, roof=1.40, bw=0.72, tw=0.62)

# ---------------- atlas (256 x 256), v = 1 at the top row
def px_side(x, z):  return ((2.1 - x) / 4.2 * 256.0, (1.45 - z) / 1.30 * 96.0)            # rows 0..96
def px_top(x, y):   return ((2.1 - x) / 4.2 * 256.0, 96.0 + (y + 0.85) / 1.7 * 80.0)      # rows 96..176
def px_front(y, z): return ((y + 0.85) / 1.7 * 128.0, 176.0 + (1.45 - z) / 1.30 * 80.0)   # rows 176..256, cols 0..128
def px_back(y, z):  return (128.0 + (0.85 - y) / 1.7 * 128.0, 176.0 + (1.45 - z) / 1.30 * 80.0)
DARK_PX = (252.0, 253.0)      # a black pixel for wheel wells and the underside

def uv(px): return (px[0] / 256.0, 1.0 - px[1] / 256.0)

# pillars and door lines (x positions, car space)
DOORS = dict(front_door=(0.72, -0.13), rear_door=(-0.15, -0.80))
B_PILLAR = (-0.12, -0.18)     # bottom x, top x
HEADLIGHTS = [(0.67, 0.665), (0.47, 0.665)]   # (|y|, z) twin round lamps, radius .085
TAIL = (0.44, 0.79, 0.60, 0.78)               # |y| from..to, z from..to
