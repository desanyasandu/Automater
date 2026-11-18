"""Tabbed settings dialog: AI provider, API keys, voice and contacts."""
import threading
import webbrowser
import customtkinter as ctk
import speech_recognition as sr

import config
from ui import theme, icons
from ui.widgets import SectionLabel
from speech_engine import get_best_microphone_index

# Muted accent so white segment text stays readable
SELECTED = theme.blend(theme.ACCENT_SOFT, theme.ACCENT, 0.45)

PROVIDERS = ["GEMINI", "OPENAI", "CLAUDE", "OLLAMA"]
PROVIDER_INFO = {
    "GEMINI": "Google's fast multimodal models. Free tier available with your own key.",
    "OPENAI": "GPT models from OpenAI. Requires your own OpenAI API key.",
    "CLAUDE": "Claude models from Anthropic. Requires your own Anthropic API key.",
    "OLLAMA": "Runs a model locally on this PC. Free, private and works offline.",
}


def _entry(parent, value="", placeholder="", secret=False):
    e = ctk.CTkEntry(parent, height=38, corner_radius=theme.RADIUS_SM, font=theme.font(13),
                     fg_color=theme.SURFACE_2, border_color=theme.BORDER, border_width=1,
                     text_color=theme.TEXT, placeholder_text=placeholder,
                     placeholder_text_color=theme.TEXT_FAINT, show="•" if secret else "")
    if value:
        e.insert(0, value)
    return e


def _field(parent, label, value="", placeholder="", secret=False, help_text=None, link=None):
    box = ctk.CTkFrame(parent, fg_color="transparent")
    box.pack(fill="x", pady=(0, theme.SPACE_MD))
    top = ctk.CTkFrame(box, fg_color="transparent")
    top.pack(fill="x", pady=(0, 6))
    ctk.CTkLabel(top, text=label, font=theme.font(12, "bold"), text_color=theme.TEXT,
                 anchor="w", height=18).pack(side="left")
    if link:
        get_key = ctk.CTkLabel(top, text="Get a key ↗", font=theme.font(12), text_color=theme.ACCENT,
                               height=18, cursor="hand2")
        get_key.pack(side="right")
        get_key.bind("<Button-1>", lambda _e: webbrowser.open(link))

    row = ctk.CTkFrame(box, fg_color="transparent")
    row.pack(fill="x")
    entry = _entry(row, value, placeholder, secret)
    entry.pack(side="left", fill="x", expand=True)
    if secret:
        def toggle():
            hidden = entry.cget("show") != ""
            entry.configure(show="" if hidden else "•")
            eye.configure(text=icons.HIDE if hidden else icons.VIEW)
        eye = ctk.CTkButton(row, text=icons.VIEW, font=theme.font(14, kind="icons"), width=38, height=38,
                            corner_radius=theme.RADIUS_SM, fg_color=theme.SURFACE_2,
                            hover_color=theme.SURFACE_3, border_width=1, border_color=theme.BORDER,
                            text_color=theme.TEXT_MUTED, command=toggle)
        eye.pack(side="right", padx=(6, 0))
    if help_text:
        ctk.CTkLabel(box, text=help_text, font=theme.font(11), text_color=theme.TEXT_FAINT,
                     anchor="w", height=16).pack(fill="x", pady=(4, 0))
    return entry, box


class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, speech, on_saved):
        super().__init__(parent)
        self.speech = speech
        self.on_saved = on_saved
        self.title("Settings")
        self.configure(fg_color=theme.BG)
        self.geometry("620x640")
        self.minsize(560, 560)
        self.transient(parent)

        self._build()
        self.after(120, self._make_modal)

    def _make_modal(self):
        self.lift()
        self.focus_force()
        try:
            self.grab_set()
        except Exception:
            pass

    # ── Layout ─────────────────────────────────────────────────────────────────

    def _build(self):
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=theme.SPACE_XL, pady=(theme.SPACE_XL, theme.SPACE_SM))
        ctk.CTkLabel(head, text="Settings", font=theme.font(20, "bold", "display"),
                     text_color=theme.TEXT, anchor="w").pack(fill="x")
        ctk.CTkLabel(head, text="Choose your AI, add your own API keys and set up voice.",
                     font=theme.font(12), text_color=theme.TEXT_MUTED, anchor="w").pack(fill="x")

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=theme.SPACE_XL, pady=theme.SPACE_LG)
        ctk.CTkButton(footer, text="Save changes", width=130, height=38, corner_radius=theme.RADIUS_SM,
                      font=theme.font(13, "bold"), fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
                      text_color=theme.ON_ACCENT, command=self._save).pack(side="right")
        ctk.CTkButton(footer, text="Cancel", width=90, height=38, corner_radius=theme.RADIUS_SM,
                      font=theme.font(13), fg_color="transparent", hover_color=theme.SURFACE_2,
                      border_width=1, border_color=theme.BORDER, text_color=theme.TEXT,
                      command=self.destroy).pack(side="right", padx=(0, theme.SPACE_SM))

        tabs = ctk.CTkTabview(
            self, fg_color=theme.SURFACE, corner_radius=theme.RADIUS_LG, border_width=1,
            border_color=theme.BORDER_SOFT, segmented_button_fg_color=theme.SURFACE_2,
            segmented_button_selected_color=theme.SURFACE_3,
            segmented_button_selected_hover_color=theme.SURFACE_3,
            segmented_button_unselected_color=theme.SURFACE_2,
            segmented_button_unselected_hover_color=theme.SURFACE_3, text_color=theme.TEXT,
        )
        tabs.pack(fill="both", expand=True, padx=theme.SPACE_XL)
        self._tabs = tabs
        for name in ("AI model", "API keys", "Voice", "Contacts"):
            tabs.add(name)
        self._build_ai(tabs.tab("AI model"))
        self._build_keys(tabs.tab("API keys"))
        self._build_voice(tabs.tab("Voice"))
        self._build_contacts(tabs.tab("Contacts"))

    def _page(self, tab):
        page = ctk.CTkScrollableFrame(tab, fg_color="transparent", scrollbar_button_color=theme.SURFACE,
                                      scrollbar_button_hover_color=theme.SURFACE_3)
        page.pack(fill="both", expand=True, padx=theme.SPACE_SM, pady=theme.SPACE_SM)
        return page

    def _build_ai(self, tab):
        page = self._page(tab)
        SectionLabel(page, "Provider").pack(fill="x", pady=(0, 6))
        names = [config.PROVIDER_NAMES[p] for p in PROVIDERS]
        current = config.PROVIDER_NAMES.get(config.get_ai_provider(), "Gemini")
        self.provider_var = ctk.StringVar(value=current)
        ctk.CTkSegmentedButton(
            page, values=names, variable=self.provider_var, height=36, font=theme.font(12, "bold"),
            fg_color=theme.SURFACE_2, selected_color=SELECTED, selected_hover_color=SELECTED,
            unselected_color=theme.SURFACE_2, unselected_hover_color=theme.SURFACE_3,
            text_color=theme.TEXT, command=lambda _v: self._show_provider(),
        ).pack(fill="x")
        self.provider_desc = ctk.CTkLabel(page, text="", font=theme.font(12), text_color=theme.TEXT_MUTED,
                                          anchor="w", justify="left", wraplength=500)
        self.provider_desc.pack(fill="x", pady=(theme.SPACE_SM, theme.SPACE_LG))

        self._provider_boxes = {}
        holder = ctk.CTkFrame(page, fg_color="transparent")
        holder.pack(fill="x")
        for p in PROVIDERS:
            self._provider_boxes[p] = ctk.CTkFrame(holder, fg_color="transparent")
        self.gemini_model, _ = _field(self._provider_boxes["GEMINI"], "Model", config.get_gemini_model(),
                                      "gemini-2.5-flash")
        self.openai_model, _ = _field(self._provider_boxes["OPENAI"], "Model", config.get_openai_model(),
                                      "gpt-4o-mini")
        self.claude_model, _ = _field(self._provider_boxes["CLAUDE"], "Model", config.get_claude_model(),
                                      "claude-haiku-5-5")
        self.ollama_url, _ = _field(self._provider_boxes["OLLAMA"], "Server URL", config.get_ollama_url(),
                                    "http://localhost:11434")
        self.ollama_model, _ = _field(self._provider_boxes["OLLAMA"], "Model", config.get_ollama_model(),
                                      "llama3.2", help_text="Pull it first with: ollama pull <model>")
        self._show_provider()

    def _selected_provider(self) -> str:
        name = self.provider_var.get()
        return next((p for p, n in config.PROVIDER_NAMES.items() if n == name), "GEMINI")

    def _show_provider(self):
        selected = self._selected_provider()
        self.provider_desc.configure(text=PROVIDER_INFO[selected])
        for p, box in self._provider_boxes.items():
            if p == selected:
                box.pack(fill="x")
            else:
                box.pack_forget()

    def _build_keys(self, tab):
        page = self._page(tab)
        note = ctk.CTkFrame(page, fg_color=theme.ACCENT_SOFT, corner_radius=theme.RADIUS_SM)
        note.pack(fill="x", pady=(0, theme.SPACE_LG))
        ctk.CTkLabel(note, text=icons.KEY, font=theme.font(14, kind="icons"),
                     text_color=theme.ACCENT).pack(side="left", padx=(12, 8), pady=10)
        ctk.CTkLabel(note, text="Use your own keys. They're saved only on this PC, in the .env file.",
                     font=theme.font(12), text_color=theme.TEXT, anchor="w").pack(side="left", pady=10)

        self.gemini_key, _ = _field(page, "Gemini API key", config.get_api_key(), "Paste your Gemini key",
                                    secret=True, link="https://aistudio.google.com/apikey")
        self.openai_key, _ = _field(page, "OpenAI API key", config.get_openai_key(), "sk-…", secret=True,
                                    link="https://platform.openai.com/api-keys")
        self.claude_key, _ = _field(page, "Anthropic API key", config.get_claude_key(), "sk-ant-…",
                                    secret=True, link="https://console.anthropic.com/settings/keys")

    def _build_voice(self, tab):
        page = self._page(tab)
        SectionLabel(page, "Microphone").pack(fill="x", pady=(0, 6))
        idx = get_best_microphone_index()
        try:
            mic_name = sr.Microphone.list_microphone_names()[idx] if idx is not None else "System default"
        except Exception:
            mic_name = "System default"
        card = ctk.CTkFrame(page, fg_color=theme.SURFACE_2, corner_radius=theme.RADIUS_SM)
        card.pack(fill="x")
        ctk.CTkLabel(card, text=icons.MIC, font=theme.font(16, kind="icons"),
                     text_color=theme.ACCENT).pack(side="left", padx=(14, 10), pady=12)
        ctk.CTkLabel(card, text=mic_name, font=theme.font(13), text_color=theme.TEXT,
                     anchor="w").pack(side="left", fill="x", expand=True)

        self.mic_result = ctk.CTkLabel(page, text="Say something after pressing Test to check recognition.",
                                       font=theme.font(12), text_color=theme.TEXT_MUTED, anchor="w")
        self.mic_result.pack(fill="x", pady=(theme.SPACE_MD, theme.SPACE_SM))
        ctk.CTkButton(page, text="Test microphone", width=150, height=36, corner_radius=theme.RADIUS_SM,
                      font=theme.font(12, "bold"), fg_color=theme.SURFACE_2, hover_color=theme.SURFACE_3,
                      border_width=1, border_color=theme.BORDER, text_color=theme.TEXT,
                      command=self._test_mic).pack(anchor="w")

    def _build_contacts(self, tab):
        page = self._page(tab)
        ctk.CTkLabel(page, text="Saved contacts can be messaged by name, e.g. “send hi to Dad on WhatsApp”.",
                     font=theme.font(12), text_color=theme.TEXT_MUTED, anchor="w",
                     wraplength=500, justify="left").pack(fill="x", pady=(0, theme.SPACE_LG))
        self.dad_entry, _ = _field(page, "Dad", config.get_whatsapp_contact("DAD"), "94771234567",
                                   help_text="Country code and number, no + or spaces")
        self.mom_entry, _ = _field(page, "Mom", config.get_whatsapp_contact("MOM"), "94771234567")

    # ── Actions ────────────────────────────────────────────────────────────────

    def _test_mic(self):
        self.mic_result.configure(text="Listening… say “hello”", text_color=theme.WARNING)

        def run():
            heard = self.speech.listen(timeout=4, phrase_time_limit=4)
            if not self.winfo_exists():
                return
            if heard:
                self.after(0, lambda: self.mic_result.configure(text=f"Heard: “{heard}”",
                                                                text_color=theme.SUCCESS))
            else:
                self.after(0, lambda: self.mic_result.configure(
                    text="Nothing heard. Check that your mic isn't muted in Windows.", text_color=theme.DANGER))
        threading.Thread(target=run, daemon=True).start()

    def _save(self):
        provider = self._selected_provider()
        config.set_ai_provider(provider)
        savers = [
            (self.gemini_model, config.save_gemini_model),
            (self.openai_model, config.save_openai_model),
            (self.claude_model, config.save_claude_model),
            (self.ollama_url, config.save_ollama_url),
            (self.ollama_model, config.save_ollama_model),
            (self.gemini_key, config.save_api_key),
            (self.openai_key, config.save_openai_key),
            (self.claude_key, config.save_claude_key),
        ]
        for entry, save in savers:
            value = entry.get().strip()
            if value:
                save(value)
        for entry, name in ((self.dad_entry, "DAD"), (self.mom_entry, "MOM")):
            if entry.get().strip():
                config.save_whatsapp_contact(name, entry.get().strip())
        self.on_saved(provider)
        self.destroy()
