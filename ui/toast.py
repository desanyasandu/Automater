"""Small transient notification shown at the bottom-right of a window."""
import customtkinter as ctk

from ui import theme, icons

_KIND = {
    "success": (icons.CHECK, theme.SUCCESS),
    "info":    (icons.INFO, theme.ACCENT),
    "error":   (icons.ERROR, theme.DANGER),
}


class Toast:
    def __init__(self, window):
        self.window = window
        self._frame = None
        self._hide_job = None

    def show(self, message: str, kind: str = "success", duration_ms: int = 2600):
        self.hide()
        glyph, color = _KIND.get(kind, _KIND["info"])
        frame = ctk.CTkFrame(self.window, fg_color=theme.SURFACE_2, corner_radius=theme.RADIUS_MD,
                             border_width=1, border_color=theme.BORDER)
        ctk.CTkLabel(frame, text=glyph, font=theme.font(14, kind="icons"),
                     text_color=color, width=18).pack(side="left", padx=(14, 8), pady=10)
        ctk.CTkLabel(frame, text=message, font=theme.font(12),
                     text_color=theme.TEXT).pack(side="left", padx=(0, 16), pady=10)
        frame.place(relx=1.0, rely=1.0, x=-24, y=-52, anchor="se")
        frame.lift()
        self._frame = frame
        self._hide_job = self.window.after(duration_ms, self.hide)

    def hide(self):
        if self._hide_job:
            self.window.after_cancel(self._hide_job)
            self._hide_job = None
        if self._frame is not None and self._frame.winfo_exists():
            self._frame.destroy()
        self._frame = None
