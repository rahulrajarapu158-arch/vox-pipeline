import cv2, numpy as np, math

W, H = 1280, 720
FPS = 24
DUR = 10
N = FPS * DUR

img = cv2.imread("vault_door.jpeg")
ah, aw = img.shape[:2]
bg_layer = cv2.imread("layer_bg.png").astype(np.float32)
fg_layer = cv2.imread("layer_vault.png").astype(np.float32)
alpha = cv2.imread("layer_alpha.png").astype(np.float32) / 255.0
bga = cv2.cvtColor(bg_layer, cv2.COLOR_BGR2BGRA)
# alpha is HxWx3 (grayscale replicated). Make 4-channel for RGBA multiply.
if alpha.ndim == 3:
    alpha1 = alpha[:, :, 0:1]
else:
    alpha1 = alpha[:, :, None]
a4 = np.concatenate([alpha1, alpha1, alpha1, alpha1], axis=2)
bga = bga * (1.0 - a4 / 255.0)  # bg with holes where vault is (inverted mask)

# We'll render at source res then scale to 1280x720 at the end for crisp look.
# Work in source coordinate space; transforms applied via affine warps.

def warp_layer(layer, scale, dx, dy, rot_deg, pivot):
    """scale about pivot, rotate about pivot, translate dx,dy. layer is HxWxC float32."""
    h, w = layer.shape[:2]
    M = np.eye(2)
    # scale
    M = np.diag([scale, scale]) @ M
    # rotate
    a = math.radians(rot_deg)
    R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    M = R @ M
    # full affine: t = M*(p-pivot) + pivot + (dx,dy)
    T = np.array([[M[0,0], M[0,1], pivot[0] - M[0,0]*pivot[0] - M[0,1]*pivot[1] + dx],
                  [M[1,0], M[1,1], pivot[1] - M[1,0]*pivot[0] - M[1,1]*pivot[1] + dy]],
                 dtype=np.float32)
    return cv2.warpAffine(layer, T, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)

# pivot = center of vault bbox
ys, xs = np.where((alpha[:,:,0] if alpha.ndim==3 else alpha) > 0.1)
pivot = (int(xs.mean()), int(ys.mean()))

out = cv2.VideoWriter("layered_raw.mp4", cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))

for f in range(N):
    t = f / FPS
    # Background paper: slow gentle drift + tiny rotate (opposite phase to vault)
    bg_dx = 14 * math.sin(t * 0.35)
    bg_dy = 8 * math.sin(t * 0.27 + 1.0)
    bg_rot = 0.25 * math.sin(t * 0.22)
    bg_scale = 1.0 + 0.004 * math.sin(t * 0.3)
    bg_w = warp_layer(bga, bg_scale, bg_dx, bg_dy, bg_rot, (aw//2, ah//2)).astype(np.float32)

    # Vault foreground: floats opposite to bg + slight scale "breathing"
    fg_dx = -10 * math.sin(t * 0.35)
    fg_dy = -6 * math.sin(t * 0.27 + 1.0) + 3*math.sin(t*0.5)
    fg_rot = -0.3 * math.sin(t * 0.22) + 0.6*math.sin(t*0.4)
    fg_scale = 1.0 + 0.012 * math.sin(t * 0.5)
    fg_w = warp_layer(fg_layer, fg_scale, fg_dx, fg_dy, fg_rot, pivot).astype(np.float32)
    al_w = warp_layer(alpha, fg_scale, fg_dx, fg_dy, fg_rot, pivot)

    # Composite: start with bg, then overlay fg using fg alpha
    comp = bg_w[..., :3].copy()
    a3 = np.clip(al_w[..., 0:1], 0, 1) if al_w.ndim == 3 else np.clip(al_w, 0, 1)
    comp = comp * (1 - a3) + fg_w[..., :3] * a3

    # scale to output
    frame = cv2.resize(comp.astype(np.uint8), (W, H), interpolation=cv2.INTER_LINEAR)
    # gentle vintage grade
    frame = cv2.convertScaleAbs(frame, alpha=1.04, beta=-3)
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    a = cv2.add(a, -3); b = cv2.add(b, -3)  # pull saturation toward vintage
    lab = cv2.merge([l, a, b])
    frame = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    out.write(frame)

out.release()
print("rendered", N, "frames -> layered_raw.mp4")
