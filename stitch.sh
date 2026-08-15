#!/usr/bin/env bash
# ============================================================
#  Final stitch:  [SVD clip] + [Manim overlay] + [room tone]
#                 -> finished Vox-style clip (FFmpeg, CPU)
#  Local 4GB PC stage. No GPU needed.
# ------------------------------------------------------------
#  Usage:
#    ./stitch.sh SVD_CLIP.mp4 MANIM_CLIP.mp4 OUT.mp4
#  Assumes a room-tone file roomtone.aac in this dir (or makes one).
# ============================================================
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

SVD="${1:?pass SVD clip as arg1}"
MANIM="${2:?pass Manim clip as arg2}"
OUT="${3:-vault_final.mp4}"

# normalize both to 1280x720 24fps yuv420p for clean overlay
ffmpeg -y -i "$SVD"  -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=24" -c:v libx264 -pix_fmt yuv420p -crf 18 svd_n.mp4
ffmpeg -y -i "$MANIM" -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=24,format=yuva420p" -c:v libx264 -pix_fmt yuv420p -crf 18 manim_n.mp4

# overlay manim on top of svd, chroma-keying out the key color (#0b0b10)
ffmpeg -y -i svd_n.mp4 -i manim_n.mp4 -filter_complex \
  "[1:v]colorkey=0x0b0b10:similarity=0.08:blend=0.05[ov];[0:v][ov]overlay=shortest=1[v]" \
  -map "[v]" -c:v libx264 -pix_fmt yuv420p -crf 18 svd_plus_manim.mp4

# room tone (generate if missing) — match video duration exactly (avoid aloop stall)
if [ ! -f roomtone.aac ]; then
  DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 svd_plus_manim.mp4)
  ffmpeg -y -f lavfi -i "anoisesrc=d=${DUR}:r=48000:a=0.005:c=brown,highpass=f=120,lowpass=f=900" \
         -f lavfi -i "sine=frequency=60:duration=${DUR}" \
         -filter_complex "[1:a]volume=0.004[a1];[0:a][a1]amix=inputs=2:duration=longest" \
         -t "$DUR" -c:a aac roomtone.aac
fi

# final mux (audio already matches duration; copy both streams)
ffmpeg -y -i svd_plus_manim.mp4 -i roomtone.aac \
  -map 0:v -map 1:a -c:v copy -c:a copy "$OUT"
echo "WROTE $OUT"
