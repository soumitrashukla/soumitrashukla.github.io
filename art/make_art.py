"""Hand-drawn style generative art for the website (light + dark variants).

    python3 art/make_art.py art

talks-*       : lecture hall from the back row — screen with a chart, lectern, speaker, listeners
media-*       : folded newspapers and a microphone
discussions-* : annotated paper pages with margin notes and a pencil
mentors-*     : a branching tree
rafa-*        : tennis ball, stick and paw prints
corner-*      : faint topographic contours for the top-right corner of every page
Each sketch gets its own watercolour hue (see HUES); ink is the same everywhere.
"""
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
rng = np.random.default_rng(12)

INK = {"light": (40, 37, 32), "dark": (236, 230, 220)}
WASH = {"light": (184, 98, 62), "dark": (214, 146, 104)}


# ---------------------------------------------------------------- drawing helpers

def draw_strokes(size, strokes, color, ss=2):
    """Pencil strokes: each stroke is (points, alpha, width). Overlaps build up like graphite."""
    W, H = size
    acc = np.zeros((H * ss, W * ss), dtype=np.float32)
    groups = {}
    for pts, alpha, width in strokes:
        groups.setdefault((round(alpha, 3), width), []).append(pts)
    for (alpha, width), paths in groups.items():
        for i in range(0, len(paths), 80):
            m = Image.new("L", (W * ss, H * ss), 0)
            dm = ImageDraw.Draw(m)
            for pts in paths[i:i + 80]:
                dm.line([(x * ss, y * ss) for x, y in pts], fill=255, width=max(1, int(width * ss)), joint="curve")
            acc += np.asarray(m, dtype=np.float32) / 255.0 * alpha
    a = 0.85 * (1 - np.exp(-acc / 0.85))
    grain = gaussian_filter(rng.normal(size=a.shape).astype(np.float32), 0.7)
    a *= np.clip(1 + 0.25 * grain / (grain.std() + 1e-6), 0.55, 1.3)   # paper tooth
    rgba = np.zeros((H * ss, W * ss, 4), dtype=np.float32)
    rgba[..., 0], rgba[..., 1], rgba[..., 2] = color
    rgba[..., 3] = np.clip(a, 0, 1) * 255
    return Image.fromarray(rgba.astype(np.uint8), "RGBA").resize((W, H), Image.LANCZOS)


def sketchy(pts, wobble=1.2, passes=2, alpha=0.35, width=1.0, overshoot=6):
    """Re-stroke a path a few times with small offsets and overshoot, like a quick pencil line."""
    pts = np.asarray(pts, dtype=np.float32)
    out = []
    n = len(pts)
    for k in range(passes):
        t = np.linspace(0, 1, n)
        drift = gaussian_filter(rng.normal(0, wobble, size=(n, 2)).astype(np.float32), (max(2, n // 12), 0))
        p = pts + drift * 3 + rng.normal(0, wobble * 0.6, size=2)
        # overshoot / undershoot at the ends
        if n > 2 and overshoot:
            d0 = p[0] - p[1]
            d1 = p[-1] - p[-2]
            p = np.vstack([p[0] + d0 / (np.linalg.norm(d0) + 1e-6) * rng.uniform(0, overshoot), p,
                           p[-1] + d1 / (np.linalg.norm(d1) + 1e-6) * rng.uniform(0, overshoot)])
        out.append((list(map(tuple, p)), alpha * (1.0 if k == 0 else rng.uniform(0.35, 0.7)), width))
    return out


def wash(size, center, radius, color, strength, stretch=(1.0, 1.0), seed=1):
    """Soft watercolour patch."""
    W, H = size
    r = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = center
    a = np.zeros((H, W), dtype=np.float32)
    for _ in range(10):
        bx = cx + r.normal(0, radius * 0.45 * stretch[0])
        by = cy + r.normal(0, radius * 0.3 * stretch[1])
        rx = radius * r.uniform(0.4, 0.8) * stretch[0]
        ry = radius * r.uniform(0.35, 0.7) * stretch[1]
        a += r.uniform(0.4, 0.8) * np.exp(-(((xx - bx) / rx) ** 2 + ((yy - by) / ry) ** 2))
    low = gaussian_filter(r.normal(size=(H, W)).astype(np.float32), radius * 0.3)
    a *= np.clip(1 + 0.4 * low / (low.std() + 1e-6), 0.3, 1.7)
    a = 1 - np.exp(-1.4 * a)
    rim = gaussian_filter(np.abs(np.gradient(a)[0]) + np.abs(np.gradient(a)[1]), 1.2)
    a = np.clip((a + 5 * rim) * strength, 0, 0.6)
    rgba = np.zeros((H, W, 4), dtype=np.float32)
    rgba[..., 0], rgba[..., 1], rgba[..., 2] = color
    rgba[..., 3] = a * 255
    return Image.fromarray(rgba.astype(np.uint8), "RGBA")


def fade(img, left=0.0, right=0.0, top=0.0, bottom=0.0):
    W, H = img.size
    x = np.linspace(0, 1, W)[None, :]
    y = np.linspace(0, 1, H)[:, None]
    m = np.ones((H, W), dtype=np.float32)
    if left:
        m *= np.clip(x / left, 0, 1) ** 1.4
    if right:
        m *= np.clip((1 - x) / right, 0, 1) ** 1.4
    if top:
        m *= np.clip(y / top, 0, 1) ** 1.4
    if bottom:
        m *= np.clip((1 - y) / bottom, 0, 1) ** 1.4
    arr = np.asarray(img).astype(np.float32)
    arr[..., 3] *= m
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def save(img, name):
    img.save(f"{OUT}/{name}.webp", "WEBP", quality=88, method=6)


# ---------------------------------------------------------------- small sketch primitives

def circle(cx, cy, r, alpha=0.45, width=1.0, turns=1.15, wobble=0.35, ry=None):
    t = np.linspace(0, 2 * np.pi * turns, max(24, int(r * 3))) + rng.uniform(0, 6.28)
    ry = r if ry is None else ry
    return sketchy(list(zip(cx + r * np.cos(t), cy + ry * np.sin(t))), wobble=wobble, passes=1,
                   alpha=alpha, width=width, overshoot=0)


def line(p0, p1, alpha=0.4, width=1.0, passes=2, wobble=0.5, n=12, overshoot=4):
    x = np.linspace(p0[0], p1[0], n)
    y = np.linspace(p0[1], p1[1], n)
    return sketchy(list(zip(x, y)), wobble=wobble, passes=passes, alpha=alpha, width=width, overshoot=overshoot)


def rect(x, y, w, h, angle=0.0, alpha=0.45, width=1.1, passes=2):
    c, s_ = np.cos(angle), np.sin(angle)
    pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    rot = [(x + (px - x) * c - (py - y) * s_, y + (px - x) * s_ + (py - y) * c) for px, py in pts]
    out = []
    for i in range(4):
        out += line(rot[i], rot[(i + 1) % 4], alpha=alpha, width=width, passes=passes)
    return out, (lambda px, py: (x + (px - x) * c - (py - y) * s_, y + (px - x) * s_ + (py - y) * c))


def text_lines(to_page, x, y, w, rows, gap=11, alpha=0.22, width=0.9, ragged=True):
    out = []
    for i in range(rows):
        ww = w * (rng.uniform(0.55, 0.95) if (ragged and i % 5 == 4) else rng.uniform(0.88, 1.0))
        out += line(to_page(x, y + i * gap), to_page(x + ww, y + i * gap), alpha=alpha, width=width,
                    passes=1, wobble=0.3, n=8, overshoot=0)
    return out


def scribble(x, y, w, h=4, alpha=0.5, width=1.2, loops=None):
    loops = loops or max(3, int(w / 9))
    t = np.linspace(0, 1, loops * 10)
    xs = x + w * t + 3 * np.sin(t * loops * 2 * np.pi)
    ys = y + h * np.sin(t * loops * 2 * np.pi * 1.07) + rng.normal(0, 0.3, t.size)
    return sketchy(list(zip(xs, ys)), wobble=0.2, passes=1, alpha=alpha, width=width, overshoot=0)


# ---------------------------------------------------------------- talks: hall seen from the back

def lecture_hall(W, H):
    cx, cy = W * 0.5, H * 0.34            # stage, far away
    squash = 0.36
    strokes = []

    def pos(r, a):
        return cx + r * np.cos(a), cy + r * np.sin(a) * squash

    a0, a1 = np.radians(14), np.radians(166)
    aisle = np.radians(90)
    radii = np.linspace(170, 1250, 11)
    for i, r in enumerate(radii):
        near = 0.55 + 0.9 * (r - radii[0]) / (radii[-1] - radii[0])   # nearer rows are drawn bigger
        for lo, hi in ((a0, aisle - 0.045), (aisle + 0.045, a1)):
            ang = np.linspace(lo, hi, 140)
            x, y = pos(r, ang)
            strokes += sketchy(list(zip(x, y)), wobble=0.8, passes=2, alpha=0.26, width=1.0)
            n = int((hi - lo) * r / (24 * near))
            for a in np.linspace(lo + 0.01, hi - 0.01, max(n, 2)):
                x0, y0 = pos(r, a)
                hgt = 13 * near
                strokes += line((x0, y0), (x0 + rng.normal(0, 0.6), y0 - hgt), alpha=0.18, width=0.9,
                                passes=1, wobble=0.2, n=4, overshoot=1)
                if rng.random() < 0.2:                                    # a listener, from behind
                    s = 6.2 * near
                    hx, hy = x0 + rng.normal(0, 1), y0 - hgt - s * 1.2
                    strokes += circle(hx, hy, s, alpha=0.40, width=1.0)
                    t = np.linspace(np.pi * 1.0, np.pi * 2.0, 18)
                    strokes += sketchy(list(zip(hx + s * 2.0 * np.cos(t), hy + s * 2.3 + s * 1.3 * np.sin(t))),
                                       wobble=0.3, passes=1, alpha=0.32, width=1.0, overshoot=0)

    # projection screen with a hand-drawn chart
    sw, sh = 330, 176
    sx, sy = cx - sw / 2, cy - sh - 62
    r_out, _ = rect(sx, sy, sw, sh, alpha=0.5, width=1.2)
    strokes += r_out
    strokes += line((sx + 30, sy + 22), (sx + 30, sy + sh - 26), alpha=0.35)            # y axis
    strokes += line((sx + 30, sy + sh - 26), (sx + sw - 26, sy + sh - 26), alpha=0.35)  # x axis
    xs = np.linspace(sx + 38, sx + sw - 34, 60)
    u = (xs - xs[0]) / (xs[-1] - xs[0])
    ys = sy + sh - 36 - 95 * (u ** 1.6) - 7 * np.sin(u * 11)
    strokes += sketchy(list(zip(xs, ys)), wobble=0.4, passes=2, alpha=0.55, width=1.4, overshoot=0)
    for k, bx in enumerate(np.linspace(sx + 44, sx + sw - 60, 6)):
        bh = 18 + 9 * k + rng.normal(0, 3)
        for hx in np.arange(bx, bx + 14, 3.2):
            strokes += line((hx, sy + sh - 27), (hx, sy + sh - 27 - bh), alpha=0.13, width=0.9, passes=1,
                            wobble=0.2, n=4, overshoot=0)
    strokes += scribble(sx + 34, sy + 12, 120, h=2.5, alpha=0.35, width=1.0)            # slide title
    for side in (-1, 1):                                                                 # stand legs
        strokes += line((cx + side * sw * 0.42, sy + sh), (cx + side * sw * 0.46, cy - 8), alpha=0.25)

    # stage edge + lectern + speaker
    ang = np.linspace(a0 - 0.05, a1 + 0.05, 120)
    x, y = pos(110, ang)
    strokes += sketchy(list(zip(x, y)), wobble=0.8, passes=3, alpha=0.42, width=1.2)
    lx, ly = cx + 70, cy - 30
    for p0, p1 in (((lx - 14, ly), (lx + 14, ly)), ((lx - 11, ly), (lx - 8, ly + 30)),
                   ((lx + 11, ly), (lx + 8, ly + 30)), ((lx - 12, ly + 30), (lx + 12, ly + 30)),
                   ((lx + 8, ly), (lx + 16, ly - 16))):                                  # last one: microphone
        strokes += line(p0, p1, alpha=0.55, width=1.2, passes=2, wobble=0.3, overshoot=2)
    strokes += circle(lx + 17, ly - 18, 2.4, alpha=0.6)
    px, py = lx - 34, cy - 58                                                           # speaker, gesturing
    strokes += circle(px, py, 7.5, alpha=0.6, width=1.2)
    strokes += line((px, py + 8), (px + 1, py + 40), alpha=0.55, width=1.2)
    strokes += line((px, py + 16), (px - 20, py + 4), alpha=0.5, width=1.1)            # raised arm to the screen
    strokes += line((px, py + 16), (px + 13, py + 30), alpha=0.5, width=1.1)
    strokes += line((px + 1, py + 40), (px - 7, py + 62), alpha=0.5, width=1.1)
    strokes += line((px + 1, py + 40), (px + 9, py + 62), alpha=0.5, width=1.1)
    return strokes, (cx, sy + sh * 0.55)


# ---------------------------------------------------------------- media: newspapers + microphone

def media_sketch(W, H):
    strokes = []
    # back paper, folded
    ow, _ = rect(W * 0.30, H * 0.20, 430, 330, angle=-0.10, alpha=0.30)
    strokes += ow
    # front paper
    x0, y0, w, h = W * 0.36, H * 0.26, 470, 350
    fr, to = rect(x0, y0, w, h, angle=0.05, alpha=0.5, width=1.2)
    strokes += fr
    strokes += scribble(*to(x0 + 30, y0 + 30), w=w - 60, h=6, alpha=0.6, width=2.0, loops=22)   # masthead
    strokes += line(to(x0 + 20, y0 + 52), to(x0 + w - 20, y0 + 52), alpha=0.4, passes=1)
    strokes += line(to(x0 + 20, y0 + 56), to(x0 + w - 20, y0 + 56), alpha=0.25, passes=1)
    strokes += scribble(*to(x0 + 24, y0 + 80), w=260, h=4.5, alpha=0.55, width=1.6)             # headline
    strokes += scribble(*to(x0 + 24, y0 + 98), w=190, h=4.5, alpha=0.55, width=1.6)
    pr, _ = rect(*to(x0 + 300, y0 + 74), 146, 96, angle=0.05, alpha=0.4)                        # photo box
    strokes += pr
    for k in range(18):
        a0 = to(x0 + 304 + k * 8, y0 + 168)
        strokes += line(a0, (a0[0] + 30, a0[1] - 86), alpha=0.12, passes=1, wobble=0.2, n=6, overshoot=0)
    for col in range(3):
        strokes += text_lines(to, x0 + 24 + col * 92, y0 + 128 + (0 if col else 0), 80, 16, gap=12)
    strokes += text_lines(to, x0 + 300, y0 + 186, 146, 12, gap=12)
    # microphone at right
    mx, my = W * 0.74, H * 0.36
    strokes += circle(mx, my, 34, alpha=0.55, width=1.3, ry=40)
    for k in range(-3, 4):
        strokes += line((mx - 30, my + k * 9), (mx + 30, my + k * 9), alpha=0.15, passes=1, n=8, overshoot=0)
        strokes += line((mx + k * 9, my - 36), (mx + k * 9, my + 36), alpha=0.15, passes=1, n=8, overshoot=0)
    strokes += line((mx - 30, my + 44), (mx + 30, my + 44), alpha=0.5, width=1.2)
    strokes += line((mx - 12, my + 48), (mx - 10, my + 170), alpha=0.5, width=1.2)
    strokes += line((mx + 12, my + 48), (mx + 10, my + 170), alpha=0.5, width=1.2)
    t = np.linspace(0, 1, 50)
    strokes += sketchy(list(zip(mx + 70 * t + 40 * t ** 2, my + 170 + 60 * np.sin(t * 3) + 40 * t)),
                       wobble=0.5, passes=1, alpha=0.35, width=1.1, overshoot=0)
    for k in range(3):                                                                         # sound arcs
        t = np.linspace(-0.7, 0.7, 20)
        rr = 60 + k * 22
        strokes += sketchy(list(zip(mx + rr * np.cos(t) + 10, my + rr * np.sin(t))), wobble=0.3, passes=1,
                           alpha=0.3, width=1.0, overshoot=0)
    return strokes, to(x0 + 150, y0 + 90)


# ---------------------------------------------------------------- discussions: annotated pages

def discussion_sketch(W, H):
    strokes = []
    marks = []
    for k, (px, ang) in enumerate(((W * 0.28, -0.04), (W * 0.52, 0.03))):
        w, h = 300, 390
        py = H * 0.12
        fr, to = rect(px, py, w, h, angle=ang, alpha=0.45, width=1.1)
        strokes += fr
        strokes += scribble(*to(px + 34, py + 36), w=170, h=3, alpha=0.45, width=1.4)
        strokes += text_lines(to, px + 34, py + 62, 200, 24, gap=12)
        # margin notes
        for j in range(3):
            yy = py + 90 + j * 100 + rng.uniform(-10, 10)
            strokes += scribble(*to(px + w - 52, yy), w=38, h=2.5, alpha=0.45, width=1.0)
            strokes += scribble(*to(px + w - 52, yy + 10), w=28, h=2.5, alpha=0.45, width=1.0)
        # circle a phrase and draw an arrow to the margin
        cy_ = py + 62 + 12 * (6 + 8 * k)
        c = to(px + 90, cy_)
        strokes += circle(c[0], c[1], 42, alpha=0.5, width=1.2, ry=10)
        t = np.linspace(0, 1, 30)
        a0, a1 = to(px + 134, cy_ - 4), to(px + w - 56, py + 90 + (1 + k) * 100 - 8)
        xs = a0[0] + (a1[0] - a0[0]) * t
        ys = a0[1] + (a1[1] - a0[1]) * t - 30 * np.sin(np.pi * t)
        strokes += sketchy(list(zip(xs, ys)), wobble=0.3, passes=1, alpha=0.45, width=1.1, overshoot=0)
        strokes += line((xs[-1], ys[-1]), (xs[-1] - 9, ys[-1] - 5), alpha=0.45, passes=1, overshoot=0)
        strokes += line((xs[-1], ys[-1]), (xs[-1] - 4, ys[-1] - 10), alpha=0.45, passes=1, overshoot=0)
        marks.append(to(px + 34 + 100, py + 62 + 12 * 14))
        # question mark in the margin
        q = to(px + 16, py + 62 + 12 * 18)
        t = np.linspace(np.pi * 1.1, np.pi * 2.6, 20)
        strokes += sketchy(list(zip(q[0] + 6 * np.cos(t), q[1] + 7 * np.sin(t))), wobble=0.2, passes=1,
                           alpha=0.5, width=1.2, overshoot=0)
        strokes += line((q[0], q[1] + 7), (q[0], q[1] + 13), alpha=0.5, passes=1, overshoot=0)
        strokes += circle(q[0], q[1] + 19, 1.3, alpha=0.6)
    # pencil lying across
    bx, by = W * 0.70, H * 0.80
    ang = -0.42
    c, s_ = np.cos(ang), np.sin(ang)
    L, R = 300, 8
    for off in (-R, R):
        strokes += line((bx - s_ * off, by + c * off), (bx + c * L - s_ * off, by + s_ * L + c * off), alpha=0.5)
    tip = (bx + c * (L + 40), by + s_ * (L + 40))
    for off in (-R, R):
        strokes += line((bx + c * L - s_ * off, by + s_ * L + c * off), tip, alpha=0.5, passes=1)
    strokes += line((bx - s_ * -R, by + c * -R), (bx - s_ * R, by + c * R), alpha=0.5)
    return strokes, marks


# ---------------------------------------------------------------- mentors: a branching tree

def mentor_tree(W, H):
    strokes = []
    tips = []

    def branch(x, y, ang, length, depth, width):
        x2 = x + length * np.cos(ang)
        y2 = y - length * np.sin(ang)
        t = np.linspace(0, 1, 14)
        bend = rng.normal(0, 0.12) * length
        xs = x + (x2 - x) * t + bend * np.sin(np.pi * t) * np.sin(ang)
        ys = y + (y2 - y) * t + bend * np.sin(np.pi * t) * np.cos(ang)
        for off in np.linspace(-width / 2, width / 2, max(1, int(width / 2.5))):
            strokes.extend(sketchy(list(zip(xs + off * np.sin(ang), ys + off * np.cos(ang))), wobble=0.4,
                                   passes=1, alpha=0.35 if depth < 3 else 0.28, width=1.0, overshoot=0))
        if depth == 0 or length < 14:
            tips.append((x2, y2))
            for _ in range(3):
                strokes.extend(circle(x2 + rng.normal(0, 6), y2 + rng.normal(0, 6), rng.uniform(4, 8),
                                      alpha=0.3, width=1.0, ry=rng.uniform(2.5, 5)))
            return
        for d in (-1, 1):
            branch(x2, y2, ang + d * rng.uniform(0.28, 0.55), length * rng.uniform(0.68, 0.8), depth - 1,
                   max(1.0, width * 0.66))
        if rng.random() < 0.35:
            branch(x2, y2, ang + rng.normal(0, 0.15), length * 0.6, depth - 2, max(1.0, width * 0.5))

    branch(W * 0.5, H * 0.97, np.pi / 2, 135, 9, 16)
    # roots
    for d in (-1, 1):
        for k in range(3):
            t = np.linspace(0, 1, 12)
            strokes += sketchy(list(zip(W * 0.5 + d * (10 + 60 * t * (k + 1) / 2), H * 0.97 + 6 * t * (k + 1))),
                               wobble=0.3, passes=1, alpha=0.3, width=1.0, overshoot=0)
    strokes += line((W * 0.25, H * 0.975), (W * 0.75, H * 0.975), alpha=0.3, passes=2)
    xs = [p[0] for p in tips]
    ys = [p[1] for p in tips]
    return strokes, (np.mean(xs), np.mean(ys))


# ---------------------------------------------------------------- rafa: tennis ball, stick, paw prints

def rafa_sketch(W, H):
    strokes = []
    bx, by, r = W * 0.28, H * 0.50, 100
    strokes += circle(bx, by, r, alpha=0.55, width=1.4, turns=1.2)
    for side in (-1, 1):                                      # seam
        t = np.linspace(-1.1, 1.1, 40)
        strokes += sketchy(list(zip(bx + side * (r * 0.55 - 26 * np.cos(t * 1.4)), by + r * 0.92 * np.sin(t))),
                           wobble=0.3, passes=2, alpha=0.45, width=1.2, overshoot=0)
    for k in range(40):                                       # fuzz shading on one side
        a = rng.uniform(0.2, 1.4)
        rr = rng.uniform(0.35, 0.95) * r
        x0, y0 = bx + rr * np.cos(a), by + rr * np.sin(a)
        strokes += line((x0, y0), (x0 + 9, y0 - 7), alpha=0.12, passes=1, wobble=0.2, n=4, overshoot=0)
    # stick
    t = np.linspace(0, 1, 40)
    xs = W * 0.36 + 470 * t
    ys = H * 0.82 - 60 * t + 8 * np.sin(t * 9)
    for off in (-7, 7):
        strokes += sketchy(list(zip(xs, ys + off * (1 - 0.4 * t))), wobble=0.5, passes=1, alpha=0.5, width=1.3)
    for k in range(30):
        j = rng.integers(2, 38)
        strokes += line((xs[j], ys[j] - 4), (xs[j] + 14, ys[j] + 3), alpha=0.18, passes=1, wobble=0.2, n=4, overshoot=0)
    strokes += line((xs[18], ys[18] - 4), (xs[18] + 26, ys[18] - 34), alpha=0.4, passes=1)
    strokes += circle(xs[28], ys[28], 3, alpha=0.3, ry=2)
    # paw prints walking off to the right
    for k in range(7):
        px = W * 0.47 + k * 128
        py = H * 0.40 + (22 if k % 2 else -22) - k * 10
        strokes += circle(px, py, 21, alpha=0.5, width=1.3, ry=17)
        for dx, dy in ((-24, -26), (-8, -37), (9, -37), (25, -26)):
            strokes += circle(px + dx, py + dy, 7, alpha=0.5, width=1.2, ry=8.5)
    # grass tufts
    for k in range(26):
        gx = W * 0.12 + k * 55 + rng.normal(0, 6)
        gy = H * 0.94
        for j in range(3):
            strokes += line((gx + j * 4, gy), (gx + j * 4 + rng.normal(0, 5), gy - rng.uniform(10, 22)),
                            alpha=0.25, passes=1, wobble=0.3, n=5, overshoot=0)
    return strokes, (bx, by)


# ---------------------------------------------------------------- contour corner

def contour_strokes(W, H):
    yy, xx = np.mgrid[0:H:4, 0:W:4].astype(np.float32)
    f = np.zeros_like(xx)
    for _ in range(7):
        bx, by = rng.uniform(0.35, 1.1) * W, rng.uniform(-0.1, 0.7) * H
        s = rng.uniform(0.12, 0.32) * W
        f += rng.uniform(0.5, 1.2) * np.exp(-((xx - bx) ** 2 + (yy - by) ** 2) / (2 * s * s))
    f += 0.15 * gaussian_filter(rng.normal(size=f.shape).astype(np.float32), 18)
    fig = plt.figure()
    cs = plt.contour(xx, yy, f, levels=26)
    strokes = []
    for level_segs in cs.allsegs:
        for seg in level_segs:
            if len(seg) < 12:
                continue
            seg = seg[:: max(1, len(seg) // 220)]
            strokes += sketchy(seg, wobble=0.7, passes=2, alpha=0.26, width=1.0, overshoot=0)
    plt.close(fig)
    return strokes


# ---------------------------------------------------------------- build

HUES = {  # (light, dark) wash colours for each page's sketch
    "talks":       ((184, 98, 62),  (214, 146, 104)),   # terracotta
    "media":       ((76, 108, 140), (140, 172, 204)),   # slate blue
    "discussions": ((166, 92, 112), (206, 150, 166)),   # dusty rose
    "mentors":     ((104, 132, 84), (160, 190, 138)),   # sage
    "rafa":        ((196, 140, 58), (226, 178, 102)),   # golden retriever
}


def build(name, size, strokes, washes, fades):
    W, H = size
    for i, theme in enumerate(("light", "dark")):
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        for center, radius, stretch, strength in washes:
            img = Image.alpha_composite(img, wash(size, center, radius, HUES[name][i], strength, stretch,
                                                 seed=int(center[0]) % 97))
        img = Image.alpha_composite(img, draw_strokes(size, strokes, INK[theme]))
        save(fade(img, **fades), f"{name}-{theme}")


S = (1800, 720)
hall, screen = lecture_hall(*S)
build("talks", S, hall, [((screen[0], screen[1] + 150), 60, (2.6, 0.7), 0.55)], dict(left=0.06, right=0.06, bottom=0.12))

S = (1800, 600)
media, headline = media_sketch(*S)
build("media", S, media, [(headline, 34, (2.6, 0.55), 0.6)], dict(left=0.05, right=0.05))

disc, marks = discussion_sketch(*S)
build("discussions", S, disc, [(m, 22, (2.8, 0.3), 0.9) for m in marks], dict(left=0.05, right=0.05))

tree, canopy = mentor_tree(*S)
build("mentors", S, tree, [(canopy, 95, (1.8, 0.8), 0.4)], dict(left=0.05, right=0.05, top=0.04))

rafa, ball = rafa_sketch(*S)
build("rafa", S, rafa, [(ball, 88, (1.1, 1.1), 0.8)], dict(left=0.05, right=0.05))

W, H = 1200, 900
cs = contour_strokes(W, H)
for theme in ("light", "dark"):
    img = draw_strokes((W, H), cs, INK[theme])
    arr = np.asarray(img).astype(np.float32)
    arr[..., 3] *= 0.28                                  # keep it a whisper behind the text
    img = fade(Image.fromarray(arr.astype(np.uint8), "RGBA"), left=0.8, bottom=0.7)
    save(img, f"corner-{theme}")

print("done")
