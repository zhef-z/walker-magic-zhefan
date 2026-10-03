"""Clean Gemini-generated images into game-ready pixel sprites.

Steps per asset: green-screen key with tolerance + despill, palette mapping in
CIELAB, block-majority downscale (no interpolation, so no blended colours),
1 px outline, shared canvas per group. Writes transparent PNGs to
assets/sprites/, a 4x contact sheet per group, and an edit log.

Settings and landmark overrides live in tools/sprites.json.

Run with the ComfyUI venv (Pillow, NumPy, SciPy):
    E:/7270/tools/ComfyUI/.venv/Scripts/python.exe tools/clean_sprites.py [--debug DIR]
"""

import argparse
import colorsys
import datetime
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / "tools" / "sprites.json"
LOG_MD = REPO / "assets" / "sprites" / "EDIT-LOG.md"
LOG_JSON = REPO / "assets" / "sprites" / "edit-log.json"

# CHARACTER-SHEET.md palette: six key colours + outline.
SHEET_KEYS = {
    "hair": "E8E6F0", "red": "D62839", "indigo": "3A40A0",
    "gold": "D4A63A", "tunic": "6B5A4E", "skin": "F5DCCD",
}
OUTLINE = "1A1420"
SHEET_BG = (21, 23, 29)  # dark cave tone for contact sheets
SHEET_MID = (112, 116, 128)  # mid-gray row so the dark outline is visible


# ---------------------------------------------------------------- colour utils

def hex_rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_hex(c):
    return "".join(f"{int(v):02X}" for v in c)


def srgb_to_lab(rgb):
    c = np.asarray(rgb, dtype=np.float64) / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    m = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c @ m.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def rotate_hue(h, target, deg):
    d = ((target - h + 0.5) % 1.0) - 0.5
    step = deg / 360.0
    return (h + max(-step, min(step, d))) % 1.0


def ramp(hex_color):
    """Base colour plus one shade and one highlight step (shade cooler, highlight warmer)."""
    r, g, b = (v / 255 for v in hex_rgb(hex_color))
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    shade = colorsys.hsv_to_rgb(rotate_hue(h, 250 / 360, 8), min(1.0, s * 1.15 + 0.05), v * 0.72)
    light = colorsys.hsv_to_rgb(rotate_hue(h, 50 / 360, 8), s * 0.8, min(1.0, v * 1.18 + 0.04))
    to8 = lambda c: tuple(round(x * 255) for x in c)
    return [to8(shade), hex_rgb(hex_color), to8(light)]


def sheet_palette():
    names, cols = [], []
    for k, h in SHEET_KEYS.items():
        for step, c in zip(("shade", "base", "light"), ramp(h)):
            names.append(f"{k}-{step}")
            cols.append(c)
    names.append("outline")
    cols.append(hex_rgb(OUTLINE))
    return names, np.array(cols, dtype=np.uint8)


def extracted_palette(pixels, n, keep_accent=False):
    """Median-cut palette from opaque source pixels, plus the shared outline colour. With keep_accent,
    a small cluster of strongly saturated pixels (the wolf's cyan eyes) keeps its own entry, since
    median cut would otherwise merge it into the dominant grays."""
    sample = pixels[:: max(1, len(pixels) // 400000)]
    q = Image.fromarray(sample.reshape(-1, 1, 3)).quantize(n, method=Image.Quantize.MEDIANCUT)
    cols = np.array(q.getpalette()[: n * 3], dtype=np.uint8).reshape(n, 3)
    names = [f"c{i}" for i in range(n)]
    if keep_accent:
        hsv = np.asarray(Image.fromarray(pixels.reshape(-1, 1, 3)).convert("HSV")).reshape(-1, 3)
        acc = pixels[(hsv[:, 1] > 128) & (hsv[:, 2] > 128)]
        if len(acc) >= 50:
            cols = np.vstack([cols, np.median(acc, 0).astype(np.uint8)])
            names.append("accent")
    cols = np.vstack([cols, hex_rgb(OUTLINE)])
    return names + ["outline"], cols


def label_lut(palette):
    """32768-entry lookup: 5-bit-per-channel colour -> nearest palette index in CIELAB."""
    v = (np.arange(32) * 8 + 4).astype(np.float64)
    grid = np.stack(np.meshgrid(v, v, v, indexing="ij"), -1).reshape(-1, 3)
    d = ((srgb_to_lab(grid)[:, None, :] - srgb_to_lab(palette)[None, :, :]) ** 2).sum(-1)
    return d.argmin(1).astype(np.int16)


def to_labels(rgb, fg, lut):
    idx = (rgb[..., 0].astype(np.int32) >> 3) << 10 | (rgb[..., 1].astype(np.int32) >> 3) << 5 | (rgb[..., 2].astype(np.int32) >> 3)
    lab = lut[idx]
    lab[~fg] = -1
    return lab


# ----------------------------------------------------------------- keying

def key_green(a, k):
    """Return (despilled rgb, foreground mask, stats). Background colour is measured per image."""
    border = np.concatenate([a[:8].reshape(-1, 3), a[-8:].reshape(-1, 3), a[:, :8].reshape(-1, 3), a[:, -8:].reshape(-1, 3)])
    bg = np.median(border, 0)
    af = a.astype(np.int32)
    dist = np.sqrt(((af - bg) ** 2).sum(-1))
    gdom = af[..., 1] - np.maximum(af[..., 0], af[..., 2])
    bgmask = (dist < k["tolerance"]) | ((gdom > k["green_dominance"]) & (af[..., 1] > 120))
    fg = ~bgmask
    lab, n = ndimage.label(fg)
    sizes = ndimage.sum(fg, lab, range(1, n + 1))
    small = np.isin(lab, np.where(sizes < k["min_component_px"])[0] + 1)
    fg &= ~small
    # despill: within a band next to the background, clamp green to max(red, blue)
    band = fg & (ndimage.distance_transform_edt(fg) <= k["despill_band_px"])
    out = af.copy()
    lim = np.maximum(af[..., 0], af[..., 2])
    spill = band & (af[..., 1] > lim)
    out[..., 1] = np.where(spill, lim, af[..., 1])
    stats = {"bg_color": "#" + rgb_hex(bg), "keyed_px": int(bgmask.sum()), "speckle_px_removed": int(small.sum()),
             "despilled_px": int(spill.sum())}
    return out.astype(np.uint8), fg, stats


def remove_glow(rgb, fg):
    """Yellow-green crystal glow: hue 60-105 deg, saturated and bright."""
    hsv = np.asarray(Image.fromarray(rgb).convert("HSV")).astype(np.float64)
    h, s, v = hsv[..., 0] * 360 / 255, hsv[..., 1] / 255, hsv[..., 2] / 255
    glow = fg & (h >= 60) & (h <= 105) & (s > 0.35) & (v > 0.5)
    lab, n = ndimage.label(glow)
    if n:
        sizes = ndimage.sum(glow, lab, range(1, n + 1))
        glow = np.isin(lab, np.where(sizes >= 200)[0] + 1)
        glow = ndimage.binary_dilation(glow, iterations=2) & fg
    return fg & ~glow, int(glow.sum())


# ---------------------------------------------------------------- downscale

def block_majority(labels, y_edges, x_edges, n_labels):
    """Each output pixel takes the most common label in its source block; transparent if >50% of the block is."""
    H, W = labels.shape
    out = np.full((len(y_edges) - 1, len(x_edges) - 1), -1, dtype=np.int16)
    for i in range(len(y_edges) - 1):
        y0, y1 = max(0, int(round(y_edges[i]))), min(H, int(round(y_edges[i + 1])))
        if y1 <= y0:
            continue
        row = labels[y0:y1]
        for j in range(len(x_edges) - 1):
            x0, x1 = max(0, int(round(x_edges[j]))), min(W, int(round(x_edges[j + 1])))
            if x1 <= x0:
                continue
            blk = row[:, x0:x1].ravel()
            full = (int(round(y_edges[i + 1])) - int(round(y_edges[i]))) * (int(round(x_edges[j + 1])) - int(round(x_edges[j])))
            counts = np.bincount(blk + 1, minlength=n_labels + 1)
            transparent = counts[0] + (full - blk.size)  # outside the image counts as transparent
            if transparent * 2 >= full:
                continue
            out[i, j] = counts[1:].argmax()
    return out


def add_outline(lab, outline_idx, open_edges=("top", "bottom", "left", "right")):
    """Recolour opaque pixels that touch transparency (4-neighbour) in place. Image borders listed in
    open_edges count as transparent; the others (tile seams) do not."""
    op = lab >= 0
    pad = np.pad(op, 1, constant_values=False)
    if "top" not in open_edges:
        pad[0, 1:-1] = op[0]
    if "bottom" not in open_edges:
        pad[-1, 1:-1] = op[-1]
    if "left" not in open_edges:
        pad[1:-1, 0] = op[:, 0]
    if "right" not in open_edges:
        pad[1:-1, -1] = op[:, -1]
    edge = op & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    # Only outline where the shape keeps a fill pixel behind the outline: 1-2 px features
    # (staff shaft, hair tips) would otherwise turn entirely into outline and vanish on dark ground.
    interior = op & ~edge
    ip = np.pad(interior, 1, constant_values=False)
    backed = ip[:-2, 1:-1] | ip[2:, 1:-1] | ip[1:-1, :-2] | ip[1:-1, 2:]
    edge &= backed
    out = lab.copy()
    out[edge] = outline_idx
    return out, int(edge.sum())


def render(lab, palette):
    h, w = lab.shape
    img = np.zeros((h, w, 4), dtype=np.uint8)
    op = lab >= 0
    img[op, :3] = palette[lab[op]]
    img[op, 3] = 255
    return Image.fromarray(img, "RGBA")


def render_anchored(labels, f, anchor, canvas, anchor_out, n_labels):
    """Downscale so that source point `anchor` lands on output pixel boundary `anchor_out`."""
    W, H = canvas
    ax, ay = anchor
    aox, aoy = anchor_out
    x_edges = ax + (np.arange(W + 1) - aox) * f
    y_edges = ay + (np.arange(H + 1) - aoy) * f
    return block_majority(labels, y_edges, x_edges, n_labels)


# ---------------------------------------------------------------- helpers

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return np.asarray(Image.open(path).convert("RGB"))


def bbox(mask):
    ys, xs = np.where(mask)
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def save_png(img, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, optimize=True)
    return {"file": str(path.relative_to(REPO)).replace("\\", "/"), "size": list(img.size), "sha256": sha256(path)}


def check_output(img, palette):
    a = np.asarray(img)
    alpha_ok = bool(np.isin(a[..., 3], (0, 255)).all())
    pal = {tuple(c) for c in palette.tolist()}
    opaque = a[a[..., 3] == 255][:, :3]
    off = sum(1 for c in map(tuple, opaque.tolist()) if c not in pal)
    used = sorted({rgb_hex(c) for c in map(tuple, opaque.tolist())})
    return {"binary_alpha": alpha_ok, "off_palette_px": off, "colors_used": len(used)}


def contact_sheet(items, path, scale=4, gap=6, marker=None):
    """items: list of (label, RGBA image, ground_row or None). Two rows: mid-gray (to check outlines)
    and the dark cave tone (to check readability in game). Draws ground lines, a height marker and labels."""
    w = sum(im.width * scale for _, im, _ in items) + gap * (len(items) + 1) + (40 if marker else 0)
    row_h = max(im.height for _, im, _ in items) * scale + 2 * gap
    sheet = Image.new("RGB", (w, 2 * row_h + 22), SHEET_BG)
    d = ImageDraw.Draw(sheet)
    d.rectangle([0, 0, w, row_h], fill=SHEET_MID)
    for top in (gap, row_h + gap):
        x = gap + (40 if marker else 0)
        if marker:
            base = top + items[0][1].height * scale
            if items[0][2] is not None:
                base = top + items[0][2] * scale
            d.line([(16, base - marker * scale), (16, base - 1)], fill=(230, 80, 200), width=3)
            d.text((4, base - marker * scale - 12), f"{marker}px", fill=(230, 80, 200))
        for label, im, ground in items:
            big = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
            if ground is not None:
                gy = top + ground * scale
                d.line([(x - 2, gy), (x + big.width + 1, gy)], fill=(150, 150, 170), width=1)
            sheet.paste(big, (x, top), big)
            if top > row_h:
                d.text((x, 2 * row_h + 6), label, fill=(200, 200, 210))
            x += big.width + gap
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path, optimize=True)
    return str(path.relative_to(REPO)).replace("\\", "/")


def debug_overlay(a, fg, marks, path, scale=0.25):
    """Source image with background dimmed and landmark lines; saved outside the repo."""
    img = Image.fromarray(np.where(fg[..., None], a, (a * 0.25).astype(np.uint8)))
    img = img.resize((int(img.width * scale), int(img.height * scale)), Image.NEAREST)
    d = ImageDraw.Draw(img)
    for kind, v, color in marks:
        if kind == "h":
            d.line([(0, v * scale), (img.width, v * scale)], fill=color, width=1)
        elif kind == "v":
            d.line([(v * scale, 0), (v * scale, img.height)], fill=color, width=1)
        elif kind == "box":
            d.rectangle([c * scale for c in v], outline=color, width=1)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


# ---------------------------------------------------------------- groups

def lowest_in_band(fg, x0, x1):
    cols = fg[:, max(0, x0):x1]
    rows = np.where(cols.any(1))[0]
    return int(rows.max())


def process_mage(cfg, k, debug, log):
    names, pal = sheet_palette()
    lut = label_lut(pal)
    src_dir = REPO / cfg["dir"]
    frames = {}
    for name, fc in cfg["frames"].items():
        path = src_dir / fc["src"]
        a = load(path)
        rgb, fg, stats = key_green(a, k)
        glow_px = 0
        if name == "cast":
            fg, glow_px = remove_glow(rgb, fg)
        lab = to_labels(rgb, fg, lut)
        x0, y0, x1, y1 = bbox(fg)
        fig_h = y1 - y0 + 1
        skin = np.isin(lab, [names.index(f"skin-{s}") for s in ("shade", "base", "light")])
        sl, n = ndimage.label(skin)
        best, face = 0, None
        for i, sl_obj in enumerate(ndimage.find_objects(sl), 1):
            ys, xs = sl_obj
            area = int((sl[sl_obj] == i).sum())
            if (ys.start + ys.stop) / 2 < y0 + 0.45 * fig_h and area > best:
                best, face = area, (xs.start, ys.start, xs.stop - 1, ys.stop - 1)
        # Head size is measured as face width: the face's top edge moves with hair and hat brim
        # (cast/hurt/fail differ by ~20%), while the width stays within 1% across frames of equal scale.
        face_w = face[2] - face[0] + 1
        face_h = face[3] - face[1] + 1
        face_cx = (face[0] + face[2]) / 2
        ov = fc.get("override", {})
        band = (int(face_cx - 0.30 * fig_h), int(face_cx + 0.22 * fig_h))
        ground = ov.get("ground_y", lowest_in_band(fg, *band))
        cx = ov.get("center_x", face_cx)
        frames[name] = dict(path=path, a=a, fg=fg, lab=lab, stats=stats, glow_px=glow_px, bbox=(x0, y0, x1, y1),
                            face=face, face_w=face_w, face_h=face_h, ground=ground, cx=cx, band=band, ov=ov, src=fc["src"])

    idle = frames["idle"]
    f_idle = (idle["ground"] - idle["bbox"][1] + 1) / cfg["idle_height_px"]
    face_target = idle["face_w"] / f_idle
    for fr in frames.values():
        fr["f"] = fr["face_w"] / face_target
    # shared canvas: union of every frame's extent around its anchor (cx, ground)
    left = max((fr["cx"] - fr["bbox"][0]) / fr["f"] for fr in frames.values())
    right = max((fr["bbox"][2] + 1 - fr["cx"]) / fr["f"] for fr in frames.values())
    up = max((fr["ground"] + 1 - fr["bbox"][1]) / fr["f"] for fr in frames.values())
    down = max((fr["bbox"][3] - fr["ground"]) / fr["f"] for fr in frames.values())
    pad = cfg["pad_px"]
    half = int(np.ceil(max(left, right))) + pad
    W = 2 * half
    aoy = int(np.ceil(up)) + pad
    H = aoy + int(np.ceil(max(down, 0))) + pad

    outdir = REPO / cfg["out"]
    sheet_items = []
    for name, fr in frames.items():
        out = render_anchored(fr["lab"], fr["f"], (fr["cx"], fr["ground"] + 1), (W, H), (half, aoy), len(pal))
        out, outline_px = add_outline(out, names.index("outline"))
        img = render(out, pal)
        info = save_png(img, outdir / f"mage_{name}.png")
        op = np.asarray(img)[..., 3] > 0
        ys = np.where(op.any(1))[0]
        info.update(check_output(img, pal))
        log.append({
            "group": "mage", "asset": name, "source": f"{cfg['dir']}/{fr['src']}", "source_sha256": sha256(fr["path"]),
            "source_size": [fr["a"].shape[1], fr["a"].shape[0]], **fr["stats"], "glow_px_removed": fr["glow_px"],
            "figure_bbox_src": list(fr["bbox"]), "face_bbox_src": list(map(int, fr["face"])), "face_w_src": fr["face_w"], "face_h_src": fr["face_h"],
            "ground_y_src": fr["ground"], "ground_mode": cfg["frames"][name].get("ground", "feet"),
            "center_x_src": round(float(fr["cx"]), 1), "overrides": fr["ov"],
            "scale_src_px_per_px": round(fr["f"], 3), "face_w_out": round(fr["face_w"] / fr["f"], 2),
            "face_h_out": round(fr["face_h"] / fr["f"], 2),
            "out_height_px": int(ys.max() - ys.min() + 1), "outline_px": outline_px, "canvas": [W, H],
            "anchor_out": [half, aoy], **info,
        })
        sheet_items.append((name, img, aoy))
        if debug:
            debug_overlay(fr["a"], fr["fg"], [
                ("box", fr["bbox"], (255, 255, 0)), ("box", fr["face"], (255, 0, 255)),
                ("h", fr["ground"], (255, 0, 0)), ("v", fr["cx"], (0, 200, 255)),
                ("v", fr["band"][0], (255, 140, 0)), ("v", fr["band"][1], (255, 140, 0)),
            ], debug / f"mage_{name}.png")
    sheet = contact_sheet(sheet_items, outdir / "mage-contact-sheet-4x.png", marker=cfg["idle_height_px"])
    return {"palette": dict(zip(names, ("#" + rgb_hex(c) for c in pal))), "f_idle": round(f_idle, 3),
            "face_width_target_px": round(face_target, 2), "canvas": [W, H], "contact_sheet": sheet}


def process_wolf(cfg, k, debug, log):
    src_dir = REPO / cfg["dir"]
    frames = {}
    for name, fc in cfg["frames"].items():
        path = src_dir / fc["src"]
        a = load(path)
        rgb, fg, stats = key_green(a, k)
        frames[name] = dict(path=path, a=a, rgb=rgb, fg=fg, stats=stats, bbox=bbox(fg), src=fc["src"], ov=fc.get("override", {}))
    names, pal = extracted_palette(np.concatenate([fr["rgb"][fr["fg"]] for fr in frames.values()]), cfg["colors"],
                                   keep_accent=cfg.get("keep_accent", False))
    lut = label_lut(pal)
    ref = frames[cfg["scale_from"]]
    f = (ref["bbox"][3] - ref["bbox"][1] + 1) / cfg["height_px"]
    for fr in frames.values():
        fr["lab"] = to_labels(fr["rgb"], fr["fg"], lut)
        fr["ground"] = fr["ov"].get("ground_y", fr["bbox"][3])
        fr["cx"] = fr["ov"].get("center_x", (fr["bbox"][0] + fr["bbox"][2]) / 2)
    half = int(np.ceil(max(max(fr["cx"] - fr["bbox"][0], fr["bbox"][2] + 1 - fr["cx"]) / f for fr in frames.values()))) + cfg["pad_px"]
    aoy = int(np.ceil(max((fr["ground"] + 1 - fr["bbox"][1]) / f for fr in frames.values()))) + cfg["pad_px"]
    W, H = 2 * half, aoy + cfg["pad_px"]
    outdir = REPO / cfg["out"]
    items = []
    for name, fr in frames.items():
        out = render_anchored(fr["lab"], f, (fr["cx"], fr["ground"] + 1), (W, H), (half, aoy), len(pal))
        out, outline_px = add_outline(out, names.index("outline"))
        img = render(out, pal)
        info = save_png(img, outdir / f"wolf_{name}.png")
        info.update(check_output(img, pal))
        op = np.asarray(img)[..., 3] > 0
        ys = np.where(op.any(1))[0]
        log.append({"group": "wolf", "asset": name, "source": f"{cfg['dir']}/{fr['src']}", "source_sha256": sha256(fr["path"]),
                    **fr["stats"], "figure_bbox_src": list(fr["bbox"]), "ground_y_src": fr["ground"],
                    "center_x_src": round(float(fr["cx"]), 1), "overrides": fr["ov"], "scale_src_px_per_px": round(f, 3),
                    "out_height_px": int(ys.max() - ys.min() + 1), "outline_px": outline_px, "canvas": [W, H], **info})
        items.append((name, img, aoy))
        if debug:
            debug_overlay(fr["a"], fr["fg"], [("box", fr["bbox"], (255, 255, 0)), ("h", fr["ground"], (255, 0, 0)),
                                              ("v", fr["cx"], (0, 200, 255))], debug / f"wolf_{name}.png")
    sheet = contact_sheet(items, outdir / "wolf-contact-sheet-4x.png", marker=cfg["height_px"])
    return {"palette": dict(zip(names, ("#" + rgb_hex(c) for c in pal))), "scale": round(f, 3), "canvas": [W, H], "contact_sheet": sheet}


def process_fx(cfg, k, debug, log):
    path = REPO / cfg["dir"] / cfg["src"]
    a = load(path)
    crops = {}
    for name, sc in cfg["sprites"].items():
        x0, y0, x1, y1 = sc["crop"]
        rgb, fg, stats = key_green(a[y0:y1, x0:x1], k)
        lab_cc, n = ndimage.label(fg)
        sizes = ndimage.sum(fg, lab_cc, range(1, n + 1))
        main = int(sizes.argmax()) + 1
        mx0, my0, mx1, my1 = bbox(lab_cc == main)
        m = int(0.02 * max(mx1 - mx0, my1 - my0))
        keep = [main]
        for i, sl in enumerate(ndimage.find_objects(lab_cc), 1):  # keep pieces inside the main shape's box (flame wisps)
            if i != main and sl[0].start >= my0 - m and sl[0].stop <= my1 + m and sl[1].start >= mx0 - m and sl[1].stop <= mx1 + m:
                keep.append(i)
        kept = np.isin(lab_cc, keep)
        stats["discarded_px"] = int((fg & ~kept).sum())
        crops[name] = dict(rgb=rgb, fg=kept, stats=stats, crop=sc["crop"], h=sc["height_px"])
    names, pal = extracted_palette(np.concatenate([c["rgb"][c["fg"]] for c in crops.values()]), cfg["colors"])
    lut = label_lut(pal)
    outdir = REPO / cfg["out"]
    items = []
    for name, c in crops.items():
        lab = to_labels(c["rgb"], c["fg"], lut)
        bx0, by0, bx1, by1 = bbox(c["fg"])
        f = (by1 - by0 + 1) / c["h"]
        p = cfg["pad_px"]
        W = int(np.ceil((bx1 - bx0 + 1) / f)) + 2 * p
        H = c["h"] + 2 * p
        out = render_anchored(lab, f, ((bx0 + bx1 + 1) / 2, by1 + 1), (W, H), (W / 2, H - p), len(pal))
        out, outline_px = add_outline(out, names.index("outline"))
        img = render(out, pal)
        info = save_png(img, outdir / f"fx_{name}.png")
        info.update(check_output(img, pal))
        log.append({"group": "fx", "asset": name, "source": f"{cfg['dir']}/{cfg['src']}", "source_sha256": sha256(path),
                    "crop_src": c["crop"], **c["stats"], "shape_bbox_in_crop": [bx0, by0, bx1, by1],
                    "scale_src_px_per_px": round(f, 3), "target_height_px": c["h"], "outline_px": outline_px, **info})
        items.append((name, img, None))
        if debug:
            debug_overlay(c["rgb"], c["fg"], [("box", (bx0, by0, bx1, by1), (255, 255, 0))], debug / f"fx_{name}.png", 0.5)
    sheet = contact_sheet(items, outdir / "fx-contact-sheet-4x.png")
    return {"palette": dict(zip(names, ("#" + rgb_hex(c) for c in pal))), "contact_sheet": sheet}


def process_tiles(cfg, k, f_idle, debug, log):
    path = REPO / cfg["dir"] / cfg["src"]
    a = load(path)
    rgb, fg, stats = key_green(a, k)
    names, pal = extracted_palette(rgb[fg], cfg["colors"])
    lut = label_lut(pal)
    lab = to_labels(rgb, fg, lut)
    f = f_idle  # same source-to-game pixel ratio as the mage
    tx0, ty0, tx1, ty1 = cfg["tile_crop"]
    th = int(round((ty1 - ty0) / f))
    tw = int(round((tx1 - tx0) / f))
    snapped = [tx0, ty0, round(tx0 + tw * f, 1), round(ty0 + th * f, 1)]

    def piece(x0, w_px, open_edges):
        out = block_majority(lab, ty0 + np.arange(th + 1) * f, x0 + np.arange(w_px + 1) * f, len(pal))
        return add_outline(out, names.index("outline"), open_edges)

    tile, t_out = piece(tx0, tw, ("top",))
    outputs = {}
    # end caps: trim the join side to the first mostly-opaque column so no outline appears at the seam
    rx0, _, rx1, _ = cfg["cap_right_crop"]
    col = fg[ty0:ty1, rx0:rx1].mean(0)
    rx0 = rx0 + int(np.argmax(col > 0.9 * col.max()))
    rw = int(round((rx1 - rx0) / f))
    cap_r, _ = piece(rx0, rw, ("top", "right"))
    lx0, _, lx1, _ = cfg["cap_left_crop"]
    col = fg[ty0:ty1, lx0:lx1].mean(0)
    lx1 = lx0 + len(col) - int(np.argmax(col[::-1] > 0.9 * col.max()))
    lw = int(round((lx1 - lx0) / f))
    cap_l, _ = piece(lx1 - lw * f, lw, ("top", "left"))
    outdir = REPO / cfg["out"]
    for nm, arr, crop in (("cave_ground_tile", tile, snapped),
                          ("cave_ground_cap_left", cap_l, [round(lx1 - lw * f, 1), ty0, lx1, round(ty0 + th * f, 1)]),
                          ("cave_ground_cap_right", cap_r, [rx0, ty0, round(rx0 + rw * f, 1), round(ty0 + th * f, 1)])):
        img = render(arr, pal)
        info = save_png(img, outdir / f"{nm}.png")
        info.update(check_output(img, pal))
        outputs[nm] = img
        log.append({"group": "tiles", "asset": nm, "source": f"{cfg['dir']}/{cfg['src']}", "source_sha256": sha256(path),
                    **stats, "crop_requested_src": cfg["tile_crop"] if nm == "cave_ground_tile" else None,
                    "crop_used_src": crop, "crop_note": cfg["tile_crop_note"] if nm == "cave_ground_tile" else "join side trimmed to first >90% opaque column",
                    "scale_src_px_per_px": round(f, 3), **info})
    # seam preview: left cap + N tiles + right cap, 4x, seams marked above the art
    seq = [outputs["cave_ground_cap_left"]] + [outputs["cave_ground_tile"]] * cfg["preview_tiles"] + [outputs["cave_ground_cap_right"]]
    strip = Image.new("RGBA", (sum(i.width for i in seq), th), (0, 0, 0, 0))
    x, seams = 0, []
    for i in seq:
        strip.paste(i, (x, 0))
        x += i.width
        seams.append(x)
    s = 4
    prev = Image.new("RGB", (strip.width * s, strip.height * s + 12), SHEET_BG)
    big = strip.resize((strip.width * s, strip.height * s), Image.NEAREST)
    prev.paste(big, (0, 12), big)
    d = ImageDraw.Draw(prev)
    for sx in seams[:-1]:
        d.line([(sx * s, 0), (sx * s, 9)], fill=(230, 80, 200), width=2)
    pp = outdir / "tiles-seam-preview-4x.png"
    prev.save(pp, optimize=True)
    if debug:
        debug_overlay(a, fg, [("box", snapped, (255, 0, 255)), ("box", (rx0, ty0, rx0 + rw * f, ty0 + th * f), (0, 200, 255)),
                              ("box", (lx1 - lw * f, ty0, lx1, ty0 + th * f), (0, 200, 255))], debug / "tiles.png")
    return {"palette": dict(zip(names, ("#" + rgb_hex(c) for c in pal))), "tile_size": [tw, th],
            "seam_preview": str(pp.relative_to(REPO)).replace("\\", "/")}


def process_background(cfg, log):
    path = REPO / cfg["dir"] / cfg["src"]
    a = load(path)
    H, W = a.shape[:2]
    ow, oh = cfg["size"]
    cw = int(round(H * ow / oh))
    x0 = (W - cw) // 2
    xs = (x0 + (np.arange(ow) + 0.5) * cw / ow).astype(int)
    ys = ((np.arange(oh) + 0.5) * H / oh).astype(int)
    img = Image.fromarray(a[ys][:, xs])
    info = save_png(img, REPO / cfg["out"] / "cave_bg.png")
    log.append({"group": "background", "asset": "cave_bg", "source": f"{cfg['dir']}/{cfg['src']}", "source_sha256": sha256(path),
                "crop_src": [x0, 0, x0 + cw, H], "method": "center crop to 16:9, nearest-neighbour sample at block centres, no quantize",
                "scale_src_px_per_px": round(cw / ow, 3), **info})


# ---------------------------------------------------------------- log

def write_log(log, groups):
    LOG_JSON.parent.mkdir(parents=True, exist_ok=True)
    LOG_JSON.write_text(json.dumps({"generated": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
                                    "groups": groups, "assets": log}, indent=2), encoding="utf-8")
    L = ["# Sprite edit log", "",
         f"Generated by `tools/clean_sprites.py` with settings from `tools/sprites.json` on "
         f"{datetime.datetime.now().astimezone().isoformat(timespec='seconds')}. Full data: `edit-log.json`.", "",
         "Every asset: green key (tolerance + despill), palette mapping in CIELAB, block-majority downscale (no interpolation), "
         "1 px outline `#" + OUTLINE + "` recoloured in place. Source pixels per output pixel = scale.", ""]
    for g, meta in groups.items():
        L.append(f"## {g}")
        L.append("")
        for kk, v in meta.items():
            if kk != "palette":
                L.append(f"- {kk}: `{v}`")
        if "palette" in meta:
            L.append("- palette: " + " ".join(f"`{n} {c}`" for n, c in meta["palette"].items()))
        L.append("")
        rows = [e for e in log if e["group"] == g]
        if not rows:
            continue
        cols = [c for c in ("asset", "source", "crop_used_src", "crop_src", "bg_color", "despilled_px", "glow_px_removed",
                            "discarded_px", "face_w_src", "face_w_out", "face_h_out", "ground_y_src", "ground_mode", "scale_src_px_per_px",
                            "out_height_px", "size", "colors_used", "off_palette_px", "binary_alpha", "file")
                if any(c in e and e[c] is not None for e in rows)]
        L.append("| " + " | ".join(cols) + " |")
        L.append("|" + "---|" * len(cols))
        for e in rows:
            L.append("| " + " | ".join(f"`{e.get(c)}`" if c in ("source", "file") else str(e.get(c, "")) for c in cols) + " |")
        L.append("")
    LOG_MD.write_text("\n".join(L), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--debug", type=Path, help="write landmark overlays to this directory (keep it outside the repo)")
    ap.add_argument("--only", nargs="*", choices=["mage", "wolf", "fx", "tiles", "background"])
    args = ap.parse_args()
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    k = cfg["key"]
    only = set(args.only or ["mage", "wolf", "fx", "tiles", "background"])
    log, groups = [], {}
    mage = process_mage(cfg["mage"], k, args.debug, log)  # always run: tiles reuse its scale
    if "mage" in only:
        groups["mage"] = mage
    else:
        log.clear()
    if "wolf" in only:
        groups["wolf"] = process_wolf(cfg["wolf"], k, args.debug, log)
    if "fx" in only:
        groups["fx"] = process_fx(cfg["fx"], k, args.debug, log)
    if "tiles" in only:
        groups["tiles"] = process_tiles(cfg["tiles"], k, mage["f_idle"], args.debug, log)
    if "background" in only:
        process_background(cfg["background"], log)
        groups["background"] = {}
    write_log(log, groups)
    for e in log:
        print(f"{e['group']:10s} {e['asset']:22s} {str(e.get('size')):10s} h={e.get('out_height_px', '-')!s:3s} "
              f"scale={e.get('scale_src_px_per_px')} off_palette={e.get('off_palette_px', '-')} alpha_ok={e.get('binary_alpha', '-')}")


if __name__ == "__main__":
    main()
