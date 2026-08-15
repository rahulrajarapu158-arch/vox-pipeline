import importlib.util, os
from manim import config

# Direct render with explicit resolution/fps (avoids the CLI xdg-open/preview bug)
spec = importlib.util.spec_from_file_location("mo", "manim_overlay.py")
mo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mo)

config.pixel_height = 720
config.pixel_width = 1280
config.frame_rate = 24
config.output_file = "manim_overlay"
config.media_dir = os.path.abspath("media")

scene = mo.VaultTitleCard()
scene.render()
print("RENDER DONE")
