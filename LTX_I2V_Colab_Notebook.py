# LTX-Video 2B (Distilled) — Image-to-Video on Colab free GPU
# Goal: animate Vault_door_paper_collage.jpeg into a Vox/paper-animation-style clip.
# Model: Lightricks/LTX-Video-2B-0.9.6-Distilled-04-25  (FREE, image-to-video, ~6-8GB VRAM -> fits Colab T4 15GB)
# Reference style target: Transform_image_into_paper_anima...mp4 (paper-cutout / hand-animated explainer look)
#
# HOW TO RUN:
#   1. Open https://colab.research.google.com  (log in with YOUR Google account)
#   2. File > Upload notebook  -> select THIS file
#   3. Runtime > Change runtime type > GPU  (T4 is fine)  > Save
#   4. Runtime > Run all
#   5. The final clip downloads to your Colab session; right-click -> Download,
#      then drop it at /home/rahul/Downloads/vox/ltx_vault.mp4 on this PC
#      (or /mnt/c/Users/Acer/Downloads/ if coming from Windows side).
#   6. Tell Hermes to score it against the reference with the verifier (verify_similarity.py).

# ---------- Cell 1: install ----------
# !pip install -q "diffusers>=0.33" transformers accelerate imageio imageio-ffmpeg decord

# ---------- Cell 2: imports + device ----------
import torch
from diffusers import LTXImageToVideoPipeline
from PIL import Image
import imageio.v2 as imageio
import os, math

device = "cuda" if torch.cuda.is_available() else "cpu"
print("device:", device, "| cuda:", torch.cuda.is_available())

# ---------- Cell 3: load model (2B distilled, FREE) ----------
MODEL_ID = "Lightricks/LTX-Video-2B-0.9.6-Distilled-04-25"
pipe = LTXImageToVideoPipeline.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.bfloat16,
    low_cpu_mem_usage=True,
).to(device)
# distilled variant = fewer steps, no CFG/STG needed (per LTX README)
pipe.transformer = pipe.transformer.to(device)

# ---------- Cell 4: inputs ----------
# Upload vault_door.jpeg to Colab (left panel) OR mount Drive.
# Simplest: drag vault_door.jpeg into the Colab file browser, then set path:
IMAGE_PATH = "/content/vault_door.jpeg"   # CHANGE if you named it differently
assert os.path.exists(IMAGE_PATH), f"Upload {IMAGE_PATH} first (left sidebar -> upload)"

img = Image.open(IMAGE_PATH).convert("RGB")
# LTX expects the FIRST frame as the conditioning image; match REFERENCE aspect (vertical paper card).
# Reference clip = 720x1280 (AR 0.562). Use 704x1280 (both 32-divisible for LTX, AR 0.55 ~ matching).
W, H = 704, 1280   # vertical portrait, matches the reference paper-collage explainer framing
img = img.resize((W, H))

# ---------- Cell 5: prompt (steer toward the PAPER-ANIMATION reference look) ----------
# The reference clip = flat paper cutout, gentle hand-animated drift, editorial explainer feel.
prompt = (
    "Paper-collage animation style, flat illustrated vault door made of cut paper layers, "
    "the paper pieces shift and lift slightly with a gentle hand-made stop-motion drift, "
    "soft paper shadows, warm editorial color palette, Vox-style explainer motion, "
    "subtle slow camera push-in, no 3D, no photorealism"
)
negative_prompt = "photorealistic, 3d render, CGI, jitter, flicker, distorted, blurry"

# ---------- Cell 6: generate ----------
# distilled: ~25-50 steps is plenty; ~5s clip @ 24fps (121 frames)
frames = pipe(
    image=img,
    prompt=prompt,
    negative_prompt=negative_prompt,
    height=H, width=W,
    num_frames=121,            # ~5s at 24fps
    num_inference_steps=30,    # distilled -> low step count, fast
    generator=torch.Generator(device=device).manual_seed(42),
).frames[0]

# ---------- Cell 7: save + download ----------
OUT = "/content/ltx_vault.mp4"
writer = imageio.get_writer(OUT, fps=24, codec="libx264", macro_block_size=None)
for f in frames:
    writer.append_data(f)
writer.close()
print("saved", OUT, "frames:", len(frames))

from google.colab import files
files.download(OUT)
print("Download triggered. Move it to ~/Downloads/vox/ltx_vault.mp4 and ask Hermes to verify.")
