import cv2, numpy as np

img = cv2.imread("vault_door.jpeg")
h, w = img.shape[:2]

# 1) Build red-outline mask
b, g, r = cv2.split(img)
red = (r > 140) & (g < 90) & (b < 90)
red_u8 = red.astype(np.uint8) * 255

# 2) Close the open bottom of the loop by connecting the two lowest red points
ys, xs = np.where(red)
if len(xs):
    # bottom-most red pixels on left and right halves
    left_mask = xs < w // 2
    right_mask = ~left_mask
    if left_mask.any() and right_mask.any():
        bl_y, bl_x = ys[left_mask].max(), xs[left_mask][ys[left_mask].argmax()]
        br_y, br_x = ys[right_mask].max(), xs[right_mask][ys[right_mask].argmax()]
        cv2.line(red_u8, (bl_x, bl_y), (br_x, br_y), 255, 3)

# 3) Dilate the outline a touch so flood-fill from inside reaches the boundary
kernel = np.ones((3, 3), np.uint8)
outline = cv2.dilate(red_u8, kernel, iterations=1)

# 4) Flood fill from a known interior point (center of red bbox)
ys2, xs2 = np.where(red)
cx, cy = int(xs2.mean()), int(ys2.mean())
fill = outline.copy()
cv2.floodFill(fill, None, (cx, cy), 255)
# keep only the filled interior (exclude the outline stroke itself)
interior = cv2.bitwise_and(fill, cv2.bitwise_not(outline))

# 5) Clean up with morphology, then make a soft alpha (feather)
interior = cv2.morphologyEx(interior, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
interior = cv2.dilate(interior, np.ones((2, 2), np.uint8), iterations=1)

alpha = interior.astype(np.float32) / 255.0
# feather edges
alpha = cv2.GaussianBlur(alpha, (11, 11), 0)
alpha = np.clip(alpha, 0, 1)

# 6) Write layers
# Foreground = original image * alpha
fg = (img.astype(np.float32) * alpha[..., None]).astype(np.uint8)
cv2.imwrite("layer_vault.png", fg)
# Background = original * (1-alpha)
bg = (img.astype(np.float32) * (1 - alpha[..., None])).astype(np.uint8)
cv2.imwrite("layer_bg.png", bg)
# Alpha matte
cv2.imwrite("layer_alpha.png", (alpha * 255).astype(np.uint8))

# stats
print("vault alpha coverage:", int((alpha > 0.5).sum()), "px of", w * h)
cv2.imwrite("dbg_fg_preview.png", fg)
print("wrote layers")
