import cv2, numpy as np

img = cv2.imread("vault_door.jpeg")
print("shape", img.shape)
h,w = img.shape[:2]

# Look at the red outline around the vault. In RGB-ish (BGR here).
# Red is high R, low G, low B.
b,g,r = cv2.split(img)
red_mask = (r > 140) & (g < 90) & (b < 90)
cnt = red_mask.sum()
print("red-ish pixels:", cnt)
# bounding box of strong red
ys,xs = np.where(red_mask)
if len(xs):
    print("red bbox x", xs.min(), xs.max(), "y", ys.min(), ys.max())

# Also: how much near-white paper background (the base)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
print("gray range", gray.min(), gray.max())
# Save a quick red mask preview
cv2.imwrite("dbg_redmask.png", (red_mask.astype(np.uint8))*255)
print("wrote dbg_redmask.png")
