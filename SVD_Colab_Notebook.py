# ============================================================
#  ComfyUI-style SVD image-to-video, run on Google Colab GPU
#  Pipeline target (from Rahul / Hermes):
#    [Static vault image] -> [SVD] -> [Slow Zoom/Pan MP4]
#  This notebook uses the official stabilityai/stable-video-diffusion
#  image-to-video checkpoint directly via diffusers (no ComfyUI GUI
#  needed; same model ComfyUI's SVD node uses).
# ------------------------------------------------------------
#  HOW TO USE:
#   1. Open in Google Colab: https://colab.research.google.com
#   2. Menu -> Runtime -> Change runtime type -> GPU (T4 or better)
#   3. Upload your vault image (vault_door.jpeg) to the session
#      (use the left file panel, or run the upload cell).
#   4. Run cells top to bottom.
#   5. Download svd_vault.mp4 (the generated slow zoom/pan clip).
# ============================================================

# ---------- Cell 1: install deps ----------
# !pip install -q diffusers transformers accelerate imageio imageio-ffmpeg torch

# ---------- Cell 2: imports ----------
import torch
from diffusers import StableVideoDiffusionPipeline
from diffusers.utils import load_image, export_to_video
import imageio

print("CUDA available:", torch.cuda.is_available())
assert torch.cuda.is_available(), "Set runtime to GPU first (Runtime -> Change runtime type -> GPU)"

# ---------- Cell 3: load model (SVD img2vid, 576x1024) ----------
pipe = StableVideoDiffusionPipeline.from_pretrained(
    "stabilityai/stable-video-diffusion-img2vid-xt",
    torch_dtype=torch.float16,
    variant="fp16",
)
pipe.enable_model_cpu_offload()
pipe.unet.enable_forward_chunking()

# ---------- Cell 4: load + condition image ----------
# Upload your image file to the Colab session, then set the path.
IMAGE_PATH = "vault_door.jpeg"   # <-- change if your filename differs
image = load_image(IMAGE_PATH).resize((1024, 576))  # SVD expects portrait-ish; we use 1024x576 landscape
image.save("vault_resized.png")

# ---------- Cell 5: generate slow zoom/pan ----------
# motion_bucket_id high (~180-200) => more camera motion (slow zoom/pan)
# noise_aug_strength low (~0.02) => stays faithful to the input image
generator = torch.manual_seed(42)
frames = pipe(
    image,
    num_frames=25,
    num_inference_steps=30,
    motion_bucket_id=190,
    noise_aug_strength=0.02,
    decode_chunk_size=8,
    generator=generator,
).frames[0]

# ---------- Cell 6: export + optional slow-motion via ffmpeg ----------
export_to_video(frames, "svd_vault_raw.mp4", fps=12)

# Upscale to 24fps smooth slow-mo and 720p for the final stitch
# (imageio-ffmpeg is bundled; this uses it)
import subprocess, imageio_ffmpeg
ff = imageio_ffmpeg.get_ffmpeg_exe()
out = "svd_vault.mp4"
cmd = [ff, "-y", "-i", "svd_vault_raw.mp4",
       "-vf", "scale=1280:720:flags=lanczos,fps=24",
       "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", out]
subprocess.run(cmd, check=True)
print("Wrote", out)

# ---------- Cell 7: download ----------
# Files panel -> right-click svd_vault.mp4 -> Download
# (or mount Google Drive and copy it there)
