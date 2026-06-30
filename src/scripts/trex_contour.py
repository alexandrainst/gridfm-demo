#!/usr/bin/env python3
"""Extract the T-Rex outline + eye from the source image.

Foreground = non-white pixels (the green body + outline + features).
Outer contour traced via matplotlib; eye = compact dark blob in the head.
Run directly to write a debug overlay so the trace can be eyeballed.
"""
import os
import numpy as np
from PIL import Image
from scipy import ndimage
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

IMG = "/home/bourdeet/Pictures/Screenshots/Screenshot from 2026-06-29 16-49-46.png"
TARGET_W = 120.0          # scale longest extent to ~120 km


def extract(path=IMG, n_points=199):
    rgb = np.asarray(Image.open(path).convert("RGB")).astype(int)
    R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    H, W = R.shape

    white = (R > 235) & (G > 235) & (B > 235)
    fg = ndimage.binary_fill_holes(~white)
    lbl, n = ndimage.label(fg)
    sizes = ndimage.sum(np.ones_like(lbl), lbl, range(1, n + 1))
    fg = lbl == (np.argmax(sizes) + 1)               # largest blob = the dino

    # outer contour (longest iso-0.5 path); matplotlib gives (x=col, y=row)
    cs = plt.contour(fg.astype(float), levels=[0.5])
    plt.close()
    segs = [s for col in cs.allsegs for s in col]
    seg = max(segs, key=len)

    # resample by arc length
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(seg, axis=0).T))]
    s = np.linspace(0, d[-1], n_points, endpoint=False)
    cx = np.interp(s, d, seg[:, 0])
    cy = np.interp(s, d, seg[:, 1])
    contour_px = np.column_stack([cx, cy])           # (col, row)

    # eye = compact dark blob in upper-left head region
    dark = (R < 80) & (G < 80) & (B < 80)
    dl, dn = ndimage.label(dark)
    eye_px, best = None, -1
    for i in range(1, dn + 1):
        ys, xs = np.where(dl == i)
        area = xs.size
        if area < 50:
            continue
        bbox = (xs.max() - xs.min() + 1) * (ys.max() - ys.min() + 1)
        compact = area / bbox
        in_head = xs.mean() < 0.45 * W and ys.mean() < 0.5 * H
        if in_head and compact > 0.35 and area > best:
            best, eye_px = area, (xs.mean(), ys.mean())
    if eye_px is None:                               # fallback: head centroid
        eye_px = (0.32 * W, 0.22 * H)

    # to model coords: y up, scaled
    scale = TARGET_W / max(W, H)
    to_xy = lambda px: np.column_stack([px[..., 0], H - px[..., 1]]) * scale
    contour = to_xy(contour_px)
    eye = (to_xy(np.array([eye_px]))[0])
    return contour, eye, (rgb, H, W, scale)


def debug_overlay(out):
    contour, eye, (rgb, H, W, scale) = extract()
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.imshow(rgb)
    # back to pixel space for overlay
    ax.plot(contour[:, 0] / scale, H - contour[:, 1] / scale, ".-",
            color="red", ms=4, lw=0.8)
    ax.plot(eye[0] / scale, H - eye[1] / scale, "X", color="blue", ms=16,
            markeredgecolor="white")
    ax.set_title("traced contour (%d pts) + detected eye" % len(contour))
    ax.axis("off")
    fig.savefig(out, dpi=110, bbox_inches="tight")
    print("wrote", out, "| eye(px)=", (eye / scale))


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    debug_overlay(os.path.join(here, "..", "..", "trex_trace_debug.png"))
