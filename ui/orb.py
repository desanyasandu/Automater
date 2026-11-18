"""Animated orb that shows what the assistant is doing.

idle        slow breathing glow
listening   ripples moving outward
processing  fast spinning arcs
speaking    quick pulsing core
"""
import math
import tkinter as tk
import customtkinter as ctk

from ui import theme

FRAME_MS = 33  # ~30 fps


class AssistantOrb(tk.Canvas):
    def __init__(self, parent, size: int = 200, bg: str = theme.SURFACE):
        scale = ctk.ScalingTracker.get_widget_scaling(parent)
        self._size = int(size * scale)
        super().__init__(parent, width=self._size, height=self._size,
                         bg=bg, highlightthickness=0, bd=0)
        self._bg = bg
        self._state = "idle"
        self._color = theme.STATE_COLORS["idle"]
        self._t = 0.0
        self._spin = 0.0
        self._running = True
        self.bind("<Destroy>", lambda _e: setattr(self, "_running", False))
        self._tick()

    def set_state(self, state: str):
        self._state = state if state in theme.STATE_COLORS else "idle"

    # ── Animation ──────────────────────────────────────────────────────────────

    def _tick(self):
        if not self._running:
            return
        target = theme.STATE_COLORS[self._state]
        # Ease the color toward the new state instead of snapping
        self._color = theme.blend(self._color, target, 0.18)

        speed = {"idle": 0.6, "listening": 1.0, "processing": 4.5, "speaking": 1.6}.get(self._state, 1)
        self._t += FRAME_MS / 1000
        self._spin = (self._spin + speed * 2.2) % 360
        self._draw()
        self.after(FRAME_MS, self._tick)

    def _circle(self, cx, cy, r, **kw):
        self.create_oval(cx - r, cy - r, cx + r, cy + r, **kw)

    def _draw(self):
        self.delete("all")
        s = self._size
        cx = cy = s / 2
        ring_r = s * 0.40
        core_r = s * 0.17
        c, bg, t = self._color, self._bg, self._t

        # Soft outer glow (Tk has no alpha, so blend rings toward the background)
        breathe = (math.sin(t * (5 if self._state == "speaking" else 1.6)) + 1) / 2
        glow_strength = 0.10 + 0.08 * breathe
        for i in range(8):
            frac = i / 8
            r = ring_r * (1.12 - frac * 0.55)
            self._circle(cx, cy, r, fill=theme.blend(bg, c, glow_strength * (0.25 + frac)), outline="")

        # Listening: ripples travelling outward
        if self._state == "listening":
            for k in range(3):
                p = ((t * 0.9) + k / 3) % 1
                r = core_r + (ring_r * 1.15 - core_r) * p
                self._circle(cx, cy, r, outline=theme.blend(c, bg, p), width=2)

        # Track ring
        self._circle(cx, cy, ring_r, outline=theme.blend(bg, c, 0.22), width=1)

        # Rotating arcs (processing makes them sweep in and out)
        sweep = 70 + (40 * math.sin(t * 6) if self._state == "processing" else 0)
        box = (cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r)
        self.create_arc(*box, start=self._spin, extent=sweep, style="arc", outline=c, width=3)
        self.create_arc(*box, start=self._spin + 180, extent=sweep * 0.45, style="arc",
                        outline=theme.blend(c, bg, 0.35), width=3)
        inner = ring_r * 0.82
        self.create_arc(cx - inner, cy - inner, cx + inner, cy + inner,
                        start=-self._spin * 0.7, extent=40, style="arc",
                        outline=theme.blend(c, bg, 0.55), width=2)

        # Core: stacked circles give a soft radial gradient
        pulse = {"speaking": 0.10, "processing": 0.04}.get(self._state, 0.05)
        r_core = core_r * (1 + pulse * math.sin(t * (9 if self._state == "speaking" else 2.4)))
        for i in range(6):
            frac = i / 5
            self._circle(cx, cy, r_core * (1 - frac * 0.75),
                         fill=theme.blend(theme.blend(bg, c, 0.55), "#ffffff", frac * 0.55), outline="")
