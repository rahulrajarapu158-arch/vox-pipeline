from manim import *

class VaultTitleCard(Scene):
    def construct(self):
        self.camera.background_color = "#0b0b10"
        anchor_y = -2.0

        # Red accent bar that wipes in from left. Build at full width, hide by scaling x to 0.
        bar = Rectangle(width=3.0, height=0.07, fill_color="#e23b3b",
                        fill_opacity=1, stroke_width=0)
        bar.move_to(UP * (anchor_y + 0.55))
        bar.save_state()
        bar.stretch(0.0, dim=0, about_edge=LEFT)  # start at zero width (left edge)

        kicker = Text("ARCHIVE FILE 1948", font_size=20, color="#b8b2a6", weight=LIGHT)
        kicker.move_to(UP * (anchor_y + 0.85))

        title = Text("THE UNTOUCHED VAULT", font_size=54, color="#f4f1ea", weight=BOLD)
        title.move_to(UP * anchor_y)

        sub = Text("A sealed bank vault, never opened since 1947.", font_size=22, color="#cfc9bc")
        sub.move_to(UP * (anchor_y - 0.55))

        # start hidden
        bar.set_opacity(0)
        kicker.set_opacity(0)
        title.set_opacity(0).scale(0.92)
        sub.set_opacity(0)

        self.play(bar.animate.set_opacity(1).restore(), run_time=0.7,
                  rate_func=rate_functions.ease_out_expo)
        self.play(kicker.animate.set_opacity(1),
                  title.animate.set_opacity(1).scale(1.0),
                  run_time=0.6, rate_func=rate_functions.ease_out_quint)
        self.play(sub.animate.set_opacity(1), run_time=0.5)
        self.wait(7.0)
        self.play(FadeOut(kicker), FadeOut(title), FadeOut(sub), FadeOut(bar), run_time=0.8)
