============================================================
VOX-STYLE VAULT CLIP — WORKFLOW (Rahul / Hermes)
============================================================
Architecture (as agreed):
  [Cloud: Google Colab, GPU]  -> SVD image-to-video clip
  [Local: Manim, CPU]         -> minimalist title-card overlay
  [Local: 4GB PC, FFmpeg]     -> stitches final video

FILES (all in /home/rahul/Downloads/vox/):
  SVD_Colab_Notebook.py   - run in Colab (GPU) to make svd_vault.mp4
  manim_overlay.py        - the Vox title-card scene
  run_manim.py            - renders manim_overlay.py at 1280x720/24
  stitch.sh               - SVD clip + Manim overlay + room tone -> final
  localbin/xdg-open       - dummy no-op so Manim doesn't crash on preview

------------------------------------------------------------
STEP 1 — COLAB: generate the SVD clip (real AI video)
------------------------------------------------------------
1. Open https://colab.research.google.com
2. Upload SVD_Colab_Notebook.py and vault_door.jpeg
3. Runtime -> Change runtime type -> GPU (T4+)
4. Run all cells. Downloads: svd_vault.mp4
   (model: stabilityai/stable-video-diffusion-img2vid-xt,
    motion_bucket_id=190 = slow zoom/pan, 25 frames @12fps -> 24fps)
5. Copy svd_vault.mp4 to /home/rahul/Downloads/vox/

------------------------------------------------------------
STEP 2 — LOCAL: render the Manim title overlay (already done)
------------------------------------------------------------
  cd /home/rahul/Downloads/vox
  . .venv/bin/activate
  export PATH="$PWD/localbin:$PATH"
  python run_manim.py
  -> media/videos/720p24/manim_overlay.mp4
  (rendered on solid #0b0b10 key color; stitch.sh chroma-keys it out)

------------------------------------------------------------
STEP 3 — LOCAL: stitch everything (already tested)
------------------------------------------------------------
  cd /home/rahul/Downloads/vox
  bash stitch.sh svd_vault.mp4 media/videos/720p24/manim_overlay.mp4 vault_final.mp4

Result: vault_final.mp4  (1280x720, 10s, title over SVD footage + room tone)
Copy to Windows: cp vault_final.mp4 /mnt/c/Users/Acer/Downloads/

------------------------------------------------------------
NOTES / GOTCHAS FIXED
------------------------------------------------------------
- Manim CLI `manim render` crashes (xdg-open missing) -> use run_manim.py.
- Manim --transparent fails ("24 is not in script") -> render opaque on
  #0b0b10 and chroma-key in FFmpeg instead.
- ffmpeg aloop=loop=-1 stalls -> generate room tone at exact duration.
- This WSL box has NO GPU, so SVD MUST run in Colab (Step 1).

To re-theme the title, edit the Text() lines in manim_overlay.py.
