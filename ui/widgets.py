"""Small building blocks: a button that mixes an icon glyph with text, and list rows."""
import customtkinter as ctk

from ui import theme


def _bind_all(widget, sequence, func):
    widget.bind(sequence, func)
    for child in widget.winfo_children():
        _bind_all(child, sequence, func)


class IconTextButton(ctk.CTkFrame):
    """Button with an icon-font glyph next to regular text (CTkButton can't mix fonts)."""

    def __init__(self, parent, glyph, text, command, height=44, fg=theme.ACCENT,
                 hover=theme.ACCENT_HOVER, text_color=theme.ON_ACCENT, font_size=13, radius=None):
        super().__init__(parent, fg_color=fg, corner_radius=radius if radius is not None else height // 2,
                         height=height, cursor="hand2")
        self.pack_propagate(False)
        self._fg, self._hover, self._command = fg, hover, command
        self._enabled = True
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")
        self.icon = ctk.CTkLabel(inner, text=glyph, font=theme.font(font_size + 2, kind="icons"),
                                 text_color=text_color, fg_color="transparent")
        self.icon.pack(side="left", padx=(0, 8))
        self.label = ctk.CTkLabel(inner, text=text, font=theme.font(font_size, "bold"),
                                  text_color=text_color, fg_color="transparent")
        self.label.pack(side="left")
        _bind_all(self, "<Enter>", lambda _e: self._enabled and self.configure(fg_color=self._hover))
        _bind_all(self, "<Leave>", lambda _e: self.configure(fg_color=self._fg))
        _bind_all(self, "<Button-1>", lambda _e: self._enabled and self._command())

    def set_style(self, glyph=None, text=None, fg=None, hover=None, text_color=None):
        if glyph is not None:
            self.icon.configure(text=glyph)
        if text is not None:
            self.label.configure(text=text)
        if fg is not None:
            self._fg = fg
            self.configure(fg_color=fg)
        if hover is not None:
            self._hover = hover
        if text_color is not None:
            self.icon.configure(text_color=text_color)
            self.label.configure(text_color=text_color)


class ActionRow(ctk.CTkFrame):
    """Clickable list row: icon tile, title and a muted description."""

    def __init__(self, parent, glyph, title, subtitle, command):
        super().__init__(parent, fg_color="transparent", corner_radius=theme.RADIUS_SM, cursor="hand2")
        tile = ctk.CTkFrame(self, width=32, height=32, corner_radius=8, fg_color=theme.SURFACE_2)
        tile.pack(side="left", padx=(8, 10), pady=4)
        tile.pack_propagate(False)
        ctk.CTkLabel(tile, text=glyph, font=theme.font(14, kind="icons"),
                     text_color=theme.ACCENT).place(relx=0.5, rely=0.5, anchor="center")
        texts = ctk.CTkFrame(self, fg_color="transparent")
        texts.pack(side="left", fill="x", expand=True, pady=4)
        ctk.CTkLabel(texts, text=title, font=theme.font(12, "bold"), text_color=theme.TEXT,
                     height=16, anchor="w").pack(fill="x")
        ctk.CTkLabel(texts, text=subtitle, font=theme.font(11), text_color=theme.TEXT_MUTED,
                     height=14, anchor="w").pack(fill="x")
        _bind_all(self, "<Enter>", lambda _e: self.configure(fg_color=theme.SURFACE_2))
        _bind_all(self, "<Leave>", lambda _e: self.configure(fg_color="transparent"))
        _bind_all(self, "<Button-1>", lambda _e: command())


class SectionLabel(ctk.CTkLabel):
    def __init__(self, parent, text):
        super().__init__(parent, text=text.upper(), font=theme.font(10, "bold"),
                         text_color=theme.TEXT_FAINT, anchor="w", height=16)
