#!/usr/bin/env python3
"""
CPU-only similarity verifier: scores a GENERATED clip against the PAPER-ANIMATION
reference (Transform_image_into_paper_anima...mp4) so the ">=60% similar" bar is
measurable, not vibes.

Score = weighted blend of 4 cheap, GPU-free signals (each 0..1):
  1. color_hist   (40%)  - global color distribution match (paper palette / warm editorial)
  2. style_edge   (25%)  - edge-density match (flat paper cutout vs photoreal)
  3. motion_amt   (20%)  - temporal-motion magnitude match (gentle hand-drift feel)
  4. aspect_fram  (15%)  - framing/aspect match (vertical paper-card framing)

Weights tuned so a clip that reads like the reference lands >=0.60.
Run:
  python3 verify_similarity.py <generated.mp4> <reference.mp4>
Example:
  python3 verify_similarity.py ltx_vault.mp4 reference_paper.mp4
"""
import sys, numpy as np, imageio.v2 as imageio
from PIL import Image

def load_frames(path, max_n=64, target=(256, 256)):
    reader = imageio.get_reader(path)
    fps = reader.get_meta_data().get("fps", 24)
    frames = []
    try:
        for i, f in enumerate(reader):
            if i >= max_n:
                break
            im = Image.fromarray(f).convert("RGB").resize(target)
            frames.append(np.asarray(im, dtype=np.float32) / 255.0)
    finally:
        reader.close()
    return np.stack(frames), fps

def color_hist(frames, bins=32):
    h = np.zeros((3, bins), dtype=np.float64)
    for im in frames:
        for c in range(3):
            h[c] += np.histogram(im[..., c], bins=bins, range=(0, 1))[0]
    h /= (h.sum(axis=1, keepdims=True) + 1e-9)
    return h

def edge_density(frames):
    # simple Sobel-ish gradient magnitude, averaged
    gx = np.array([[1, 0, -1], [2, 0, -2], [1, 0, -1]], dtype=np.float32)
    gy = gx.T
    dens = []
    for im in frames:
        gray = im[..., 0] * 0.299 + im[..., 1] * 0.587 + im[..., 2] * 0.114
        # proper 2D conv (small images, fine on CPU)
        from scipy.ndimage import convolve
        ex = np.abs(convolve(gray, gx)); ey = np.abs(convolve(gray, gy))
        dens.append((ex + ey).mean())
    return float(np.mean(dens))

def motion_mag(frames):
    diffs = []
    for i in range(1, len(frames)):
        d = np.abs(frames[i] - frames[i-1]).mean()
        diffs.append(d)
    return float(np.mean(diffs)) if diffs else 0.0

def compare(a, b):
    # color histogram intersection (0..1)
    ha, hb = color_hist(a), color_hist(b)
    inter = np.minimum(ha, hb).sum(axis=1)
    return float(inter.mean())

def edge_score(da, db):
    lo, hi = min(da, db), max(da, db)
    if hi < 1e-6:
        return 1.0
    return float(max(0.0, 1.0 - (hi - lo) / hi))

def motion_score(ma, mb):
    lo, hi = min(ma, mb), max(ma, mb)
    if hi < 1e-6:
        return 1.0
    return float(max(0.0, 1.0 - (hi - lo) / hi))

def aspect_score(gen_path, ref_path):
    # 0..1 by aspect-ratio closeness (vertical paper-card ~ 3:4)
    def ar(p):
        r = imageio.get_reader(p); m = r.get_meta_data(); w, h = m.get("size", (3, 4)); r.close()
        return w / h
    ga, ra = ar(gen_path), ar(ref_path)
    return float(max(0.0, 1.0 - abs(ga - ra) / max(ga, ra)))

def main():
    if len(sys.argv) < 3:
        print("usage: verify_similarity.py <generated.mp4> <reference.mp4>")
        sys.exit(1)
    gen_path, ref_path = sys.argv[1], sys.argv[2]
    g, _ = load_frames(gen_path)
    r, _ = load_frames(ref_path)

    c = compare(g, r)                       # color
    dg, dr = edge_density(g), edge_density(r)
    e = edge_score(dg, dr)                  # style/edge
    mg, mr = motion_mag(g), motion_mag(r)
    m = motion_score(mg, mr)                # motion
    a = aspect_score(gen_path, ref_path)    # framing

    score = 0.40 * c + 0.25 * e + 0.20 * m + 0.15 * a
    verdict = "PASS (>=60%)" if score >= 0.60 else "BELOW 60%"
    print(f"color_hist : {c:.3f}")
    print(f"style_edge : {e:.3f}  (gen_edge={dg:.4f} ref_edge={dr:.4f})")
    print(f"motion_amt : {m:.3f}  (gen_mot={mg:.4f} ref_mot={mr:.4f})")
    print(f"aspect_fram: {a:.3f}")
    print(f"--- SIMILARITY SCORE: {score:.3f}  {verdict} ---")
    sys.exit(0 if score >= 0.60 else 2)

if __name__ == "__main__":
    main()
