"""Top bar: brand, live status, active model and settings."""
import customtkinter as ctk

import config
from ui import theme, icons

STATUS_TEXT = {
    "idle":       "Ready",
    "listening":  "Listening",
    "processing": "Thinking",
    "speaking":   "Speaking",
    "error":      "Error",
}


class Pill(ctk.CTkFrame):
    """Rounded label with an optional leading dot or icon."""

    def __init__(self, parent, text="", dot_color=None, glyph=None):
        super().__init__(parent, fg_color=theme.SURFACE_2, corner_radius=14, height=28,
                         border_width=1, border_color=theme.BORDER_SOFT)
        self.lead = None
        if dot_color:
            self.lead = ctk.CTkLabel(self, text="●", font=theme.font(10), text_color=dot_color, width=10)
        elif glyph:
            self.lead = ctk.CTkLabel(self, text=glyph, font=theme.font(12, kind="icons"),
                                     text_color=theme.TEXT_MUTED, width=14)
        if self.lead:
            self.lead.pack(side="left", padx=(12, 6), pady=4)
        self.label = ctk.CTkLabel(self, text=text, font=theme.font(12), text_color=theme.TEXT, height=20)
        self.label.pack(side="left", padx=(0 if self.lead else 12, 12), pady=4)


class Header(ctk.CTkFrame):
    def __init__(self, parent, on_settings):
        super().__init__(parent, fg_color=theme.BG, corner_radius=0, height=64)
        self.pack_propagate(False)

        brand = ctk.CTkFrame(self, fg_color="transparent")
        brand.pack(side="left", padx=theme.SPACE_XL)
        mark = ctk.CTkFrame(brand, width=34, height=34, corner_radius=10, fg_color=theme.ACCENT_SOFT,
                            border_width=1, border_color=theme.blend(theme.ACCENT_SOFT, theme.ACCENT, 0.35))
        mark.pack(side="left")
        mark.pack_propagate(False)
        ctk.CTkLabel(mark, text=config.ASSISTANT_NAME[:1].upper(), font=theme.font(16, "bold", "display"),
                     text_color=theme.ACCENT).place(relx=0.5, rely=0.5, anchor="center")

        names = ctk.CTkFrame(brand, fg_color="transparent")
        names.pack(side="left", padx=(12, 0))
        ctk.CTkLabel(names, text=config.ASSISTANT_NAME, font=theme.font(16, "bold", "display"),
                     text_color=theme.TEXT, height=20).pack(anchor="w")
        ctk.CTkLabel(names, text="Desktop Assistant", font=theme.font(11),
                     text_color=theme.TEXT_MUTED, height=14).pack(anchor="w")

        self.settings_btn = ctk.CTkButton(
            self, text=icons.SETTINGS, font=theme.font(16, kind="icons"), width=38, height=38,
            corner_radius=10, fg_color="transparent", hover_color=theme.SURFACE_2,
            text_color=theme.TEXT_MUTED, command=on_settings,
        )
        self.settings_btn.pack(side="right", padx=(8, theme.SPACE_XL))

        self.model_pill = Pill(self, glyph=icons.CLOUD)
        self.model_pill.pack(side="right", padx=4)
        self.status_pill = Pill(self, text="Ready", dot_color=theme.SUCCESS)
        self.status_pill.pack(side="right", padx=4)
        self.refresh_model()

        ctk.CTkFrame(self, height=1, fg_color=theme.BORDER_SOFT, corner_radius=0).place(
            relx=0, rely=1.0, relwidth=1.0, anchor="sw")

    def set_status(self, state: str):
        color = theme.SUCCESS if state == "idle" else theme.STATE_COLORS.get(state, theme.ACCENT)
        self.status_pill.lead.configure(text_color=color)
        self.status_pill.label.configure(text=STATUS_TEXT.get(state, state.title()))

    def refresh_model(self):
        provider = config.get_ai_provider()
        name = config.PROVIDER_NAMES.get(provider, provider.title())
        glyph = icons.PC if provider == "OLLAMA" else icons.CLOUD
        self.model_pill.lead.configure(text=glyph)
        self.model_pill.label.configure(text=f"{name}  ·  {config.get_active_model(provider)}")
