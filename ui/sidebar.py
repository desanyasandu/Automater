"""Left panel: assistant orb, voice controls, quick actions and system stats."""
import customtkinter as ctk

import config
from ui import theme, icons
from ui.orb import AssistantOrb
from ui.stats import SystemStats
from ui.widgets import IconTextButton, ActionRow, SectionLabel

STATE_COPY = {
    "idle":       ("Ready when you are", "Tap the mic or type a command"),
    "listening":  ("Listening…", "Speak now, I'm all ears"),
    "processing": ("Thinking…", "Working on your request"),
    "speaking":   ("Speaking", "Here's what I found"),
    "error":      ("Didn't catch that", "Check your mic and try again"),
}


class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, on_voice, on_wake_toggle, on_run, on_prefill):
        super().__init__(parent, fg_color=theme.SURFACE, corner_radius=theme.RADIUS_LG, width=300,
                         border_width=1, border_color=theme.BORDER_SOFT)
        self.pack_propagate(False)
        pad = theme.SPACE_LG

        # Packed first so it keeps its space when the window is short
        self.stats = SystemStats(self)
        self.stats.pack(side="bottom", fill="x", padx=pad, pady=pad)

        self.orb = AssistantOrb(self, size=148)
        self.orb.pack(pady=(theme.SPACE_LG, theme.SPACE_XS))

        self.state_title = ctk.CTkLabel(self, text="", font=theme.font(16, "bold", "display"),
                                        text_color=theme.TEXT, height=22)
        self.state_title.pack()
        self.state_hint = ctk.CTkLabel(self, text="", font=theme.font(12), text_color=theme.TEXT_MUTED,
                                       height=18)
        self.state_hint.pack(pady=(2, theme.SPACE_MD))

        self.voice_btn = IconTextButton(self, icons.MIC, "Tap to speak", on_voice, height=46)
        self.voice_btn.pack(fill="x", padx=pad)

        self.wake_switch = ctk.CTkSwitch(
            self, text=f"Always listening (“Hey {config.ASSISTANT_NAME}”)", font=theme.font(12),
            text_color=theme.TEXT_MUTED, progress_color=theme.ACCENT, button_color=theme.TEXT,
            button_hover_color="#ffffff", fg_color=theme.SURFACE_3, command=on_wake_toggle,
        )
        self.wake_switch.pack(anchor="w", padx=pad + 2, pady=(theme.SPACE_MD, theme.SPACE_MD))

        ctk.CTkFrame(self, height=1, fg_color=theme.BORDER_SOFT).pack(fill="x", padx=pad)

        SectionLabel(self, "Quick actions").pack(fill="x", padx=pad + 2, pady=(theme.SPACE_MD, 2))
        actions = [
            (icons.PC, "System status", "CPU, memory and battery", lambda: on_run("check the pc status")),
            (icons.CAMERA, "Take a screenshot", "Saved to Pictures", lambda: on_run("take a screenshot")),
            (icons.MUSIC, "Play on YouTube", "Type a song or video", lambda: on_prefill("play ", " on youtube")),
            (icons.CHAT, "Send a WhatsApp", "Message a saved contact",
             lambda: on_prefill("send message to ", " on whatsapp saying ")),
        ]
        for glyph, title, sub, cmd in actions:
            ActionRow(self, glyph, title, sub, cmd).pack(fill="x", padx=pad - 8, pady=0)

        self.set_state("idle")

    def set_state(self, state: str, title: str | None = None, hint: str | None = None):
        default_title, default_hint = STATE_COPY.get(state, STATE_COPY["idle"])
        self.state_title.configure(text=title or default_title)
        self.state_hint.configure(text=hint or default_hint)
        self.orb.set_state(state)

    def set_listening(self, listening: bool):
        if listening:
            self.voice_btn.set_style(glyph=icons.STOP, text="Listening…", fg=theme.DANGER,
                                     hover=theme.DANGER_HOVER, text_color="#ffffff")
        else:
            self.voice_btn.set_style(glyph=icons.MIC, text="Tap to speak", fg=theme.ACCENT,
                                     hover=theme.ACCENT_HOVER, text_color=theme.ON_ACCENT)
