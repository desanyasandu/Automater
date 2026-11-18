"""Scrollable conversation view with chat bubbles."""
import time
import customtkinter as ctk

from ui import theme

BUBBLE_WIDTH_RATIO = 0.72


class ChatView(ctk.CTkScrollableFrame):
    def __init__(self, parent, assistant_name: str = "DYD", user_name: str = "You", **kw):
        super().__init__(parent, fg_color=theme.SURFACE, corner_radius=0,
                         scrollbar_button_color=theme.SURFACE_2,
                         scrollbar_button_hover_color=theme.SURFACE_3, **kw)
        self.assistant_name = assistant_name
        self.user_name = user_name
        self._labels: list[ctk.CTkLabel] = []
        self._wrap = 480
        self.bind("<Configure>", self._on_resize)

    # ── Public API ─────────────────────────────────────────────────────────────

    def add_message(self, sender: str, text: str):
        """sender is 'user' or 'assistant'."""
        is_user = sender == "user"
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=theme.SPACE_XL, pady=(theme.SPACE_MD, 0))

        side = "e" if is_user else "w"
        meta = ctk.CTkLabel(
            row,
            text=f"{self.user_name if is_user else self.assistant_name}  ·  {time.strftime('%H:%M')}",
            font=theme.font(11), text_color=theme.TEXT_FAINT, height=16,
        )
        meta.pack(anchor=side, padx=4, pady=(0, 3))

        bubble = ctk.CTkFrame(
            row, corner_radius=theme.RADIUS_LG,
            fg_color=theme.USER_BUBBLE if is_user else theme.ASSISTANT_BUBBLE,
            border_width=0 if is_user else 1, border_color=theme.BORDER_SOFT,
        )
        bubble.pack(anchor=side)
        label = ctk.CTkLabel(
            bubble, text=text, font=theme.font(13), text_color=theme.TEXT,
            justify="left", anchor="w", wraplength=self._wrap,
        )
        label.pack(padx=14, pady=9)
        self._labels.append(label)
        self.scroll_to_bottom()
        return row

    def clear(self):
        for child in self.winfo_children():
            child.destroy()
        self._labels.clear()

    def scroll_to_bottom(self):
        self.after(10, lambda: (self.update_idletasks(), self._parent_canvas.yview_moveto(1.0)))

    # ── Internals ──────────────────────────────────────────────────────────────

    def _on_resize(self, event):
        scale = ctk.ScalingTracker.get_widget_scaling(self)
        wrap = max(240, int(event.width / scale * BUBBLE_WIDTH_RATIO))
        if abs(wrap - self._wrap) > 8:
            self._wrap = wrap
            for label in self._labels:
                if label.winfo_exists():
                    label.configure(wraplength=wrap)
