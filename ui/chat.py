"""Scrollable conversation view with chat bubbles."""
import time
import customtkinter as ctk

from ui import theme

BUBBLE_WIDTH_RATIO = 0.72


class ChatView(ctk.CTkScrollableFrame):
    def __init__(self, parent, assistant_name: str = "DYD", user_name: str = "You", **kw):
        super().__init__(parent, fg_color=theme.SURFACE, corner_radius=0,
                         scrollbar_button_color=theme.SURFACE,
                         scrollbar_button_hover_color=theme.SURFACE_3, **kw)
        self.assistant_name = assistant_name
        self.user_name = user_name
        self._labels: list[ctk.CTkLabel] = []
        self._wrap = 480
        self._typing = None
        self._empty = None
        self.on_copy = None
        self.bind("<Configure>", self._on_resize)

    # ── Public API ─────────────────────────────────────────────────────────────

    def add_message(self, sender: str, text: str):
        """sender is 'user' or 'assistant'."""
        is_user = sender == "user"
        self._hide_empty()
        if not is_user:
            self.hide_typing()
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
        for w in (bubble, label):
            w.bind("<Button-3>", lambda _e, t=text: self._copy(t))
        self._labels.append(label)
        self.scroll_to_bottom()
        return row

    def show_empty_state(self, title: str, subtitle: str, suggestions: list[str], on_pick):
        """Welcome screen with clickable example commands, shown when there are no messages."""
        self._hide_empty()
        box = ctk.CTkFrame(self, fg_color="transparent")
        box.pack(fill="x", pady=(90, 0))
        ctk.CTkLabel(box, text=title, font=theme.font(24, "bold", "display"),
                     text_color=theme.TEXT).pack()
        ctk.CTkLabel(box, text=subtitle, font=theme.font(13), text_color=theme.TEXT_MUTED).pack(pady=(6, 24))
        grid = ctk.CTkFrame(box, fg_color="transparent")
        grid.pack()
        for i, text in enumerate(suggestions):
            chip = ctk.CTkButton(
                grid, text=text, font=theme.font(12), height=40, width=240, corner_radius=theme.RADIUS_MD,
                fg_color=theme.SURFACE_2, hover_color=theme.SURFACE_3, border_width=1,
                border_color=theme.BORDER_SOFT, text_color=theme.TEXT, anchor="w",
                command=lambda t=text: on_pick(t),
            )
            chip.grid(row=i // 2, column=i % 2, padx=5, pady=5)
        self._empty = box

    def _hide_empty(self):
        if self._empty is not None and self._empty.winfo_exists():
            self._empty.destroy()
        self._empty = None

    def show_typing(self):
        """Animated three-dot bubble shown while the assistant is thinking."""
        if self._typing is not None:
            return
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=theme.SPACE_XL, pady=(theme.SPACE_MD, 0))
        bubble = ctk.CTkFrame(row, corner_radius=theme.RADIUS_LG, fg_color=theme.ASSISTANT_BUBBLE,
                              border_width=1, border_color=theme.BORDER_SOFT)
        bubble.pack(anchor="w")
        dots = []
        for i in range(3):
            d = ctk.CTkLabel(bubble, text="●", font=theme.font(10), text_color=theme.TEXT_FAINT, width=10)
            d.pack(side="left", padx=(16 if i == 0 else 3, 16 if i == 2 else 3), pady=12)
            dots.append(d)
        self._typing = row
        self._animate_typing(dots, 0)
        self.scroll_to_bottom()

    def hide_typing(self):
        if self._typing is not None and self._typing.winfo_exists():
            self._typing.destroy()
        self._typing = None

    def _animate_typing(self, dots, step):
        if self._typing is None or not dots[0].winfo_exists():
            return
        for i, d in enumerate(dots):
            d.configure(text_color=theme.TEXT_MUTED if i == step % 3 else theme.TEXT_FAINT)
        self.after(280, lambda: self._animate_typing(dots, step + 1))

    def clear(self):
        self.hide_typing()
        self._empty = None
        for child in self.winfo_children():
            child.destroy()
        self._labels.clear()

    def scroll_to_bottom(self):
        self.after(10, lambda: (self.update_idletasks(), self._parent_canvas.yview_moveto(1.0)))

    # ── Internals ──────────────────────────────────────────────────────────────

    def _copy(self, text: str):
        self.clipboard_clear()
        self.clipboard_append(text)
        if self.on_copy:
            self.on_copy()

    def _on_resize(self, event):
        scale = ctk.ScalingTracker.get_widget_scaling(self)
        wrap = max(240, int(event.width / scale * BUBBLE_WIDTH_RATIO))
        if abs(wrap - self._wrap) > 8:
            self._wrap = wrap
            for label in self._labels:
                if label.winfo_exists():
                    label.configure(wraplength=wrap)
