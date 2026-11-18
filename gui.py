import time
import queue
import threading
import customtkinter as ctk

import config
from gemini_brain import DYDBrain
from speech_engine import SpeechEngine
from ui import theme, icons
from ui.chat import ChatView
from ui.header import Header
from ui.settings import SettingsDialog
from ui.sidebar import Sidebar
from ui.toast import Toast
from ui.widgets import center_window

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class DYDApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"{config.ASSISTANT_NAME} — Desktop Assistant")
        center_window(self, 1120, 740)
        self.minsize(920, 620)
        self.configure(fg_color=theme.BG)

        # Initialize engines
        self.brain = DYDBrain()
        self.speech = SpeechEngine()
        self.is_listening = False
        self.auto_listen_active = False
        self.cmd_queue = queue.Queue()
        self._history: list[str] = []
        self._history_pos = 0

        self._build_ui()
        self.toast = Toast(self)
        self._check_initial_keys()

        # Dedicated sequential command worker
        self.worker_thread = threading.Thread(target=self._command_worker, daemon=True)
        self.worker_thread.start()

    # ── Layout ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.header = Header(self, on_settings=self.open_settings_window)
        self.header.pack(fill="x", side="top")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=theme.SPACE_XL, pady=theme.SPACE_LG)

        self.sidebar = Sidebar(
            body,
            on_voice=self.toggle_voice_listen,
            on_wake_toggle=self.toggle_continuous_listen,
            on_run=self.execute_prompt,
            on_prefill=self.prefill_input,
        )
        self.sidebar.pack(side="left", fill="y", padx=(0, theme.SPACE_LG))

        panel = ctk.CTkFrame(body, fg_color=theme.SURFACE, corner_radius=theme.RADIUS_LG,
                             border_width=1, border_color=theme.BORDER_SOFT)
        panel.pack(side="right", fill="both", expand=True)

        bar = ctk.CTkFrame(panel, fg_color="transparent", height=52)
        bar.pack(fill="x", padx=theme.SPACE_XL, pady=(theme.SPACE_SM, 0))
        bar.pack_propagate(False)
        ctk.CTkLabel(bar, text="Conversation", font=theme.font(14, "bold", "display"),
                     text_color=theme.TEXT).pack(side="left")
        ctk.CTkButton(bar, text=icons.DELETE, font=theme.font(14, kind="icons"), width=34, height=34,
                      corner_radius=theme.RADIUS_SM, fg_color="transparent", hover_color=theme.SURFACE_2,
                      text_color=theme.TEXT_MUTED, command=self.clear_chat).pack(side="right")
        ctk.CTkFrame(panel, height=1, fg_color=theme.BORDER_SOFT).pack(fill="x")

        composer = ctk.CTkFrame(panel, fg_color="transparent")
        composer.pack(side="bottom", fill="x", padx=theme.SPACE_XL, pady=theme.SPACE_LG)
        box = ctk.CTkFrame(composer, fg_color=theme.SURFACE_2, corner_radius=theme.RADIUS_MD,
                           border_width=1, border_color=theme.BORDER)
        box.pack(fill="x")
        self.input_entry = ctk.CTkEntry(
            box, height=48, border_width=0, fg_color="transparent", font=theme.font(14),
            text_color=theme.TEXT, placeholder_text=f"Ask {config.ASSISTANT_NAME} anything, or type a command…",
            placeholder_text_color=theme.TEXT_FAINT,
        )
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(theme.SPACE_MD, 0))
        self.input_entry.bind("<Return>", lambda _e: self.send_text_command())
        self.input_entry.bind("<Up>", lambda _e: self._recall_history(-1))
        self.input_entry.bind("<Down>", lambda _e: self._recall_history(1))
        self.input_entry.bind("<FocusIn>", lambda _e: box.configure(border_color=theme.ACCENT))
        self.input_entry.bind("<FocusOut>", lambda _e: box.configure(border_color=theme.BORDER))
        ctk.CTkButton(box, text=icons.SEND, font=theme.font(15, kind="icons"), width=40, height=40,
                      corner_radius=10, fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
                      text_color=theme.ON_ACCENT, command=self.send_text_command).pack(side="right", padx=6, pady=6)

        self.chat = ChatView(panel, assistant_name=config.ASSISTANT_NAME)
        self.chat.pack(fill="both", expand=True, padx=2)

        self._show_welcome()

    def _show_welcome(self):
        hour = time.localtime().tm_hour
        part = "morning" if hour < 12 else "afternoon" if hour < 18 else "evening"
        self.chat.show_empty_state(
            f"Good {part}, {config.USER_NAME}",
            "Speak or type a command. Here are a few ideas:",
            ["Check the PC status", "Play lo-fi beats on YouTube",
             "Search for the weather today", "Open notepad"],
            on_pick=self.execute_prompt,
        )

    def _check_initial_keys(self):
        provider = config.get_ai_provider()
        if provider == "GEMINI" and not config.get_api_key():
            self.after(500, self.open_settings_window)

    # ── Chat ───────────────────────────────────────────────────────────────────

    def append_chat(self, sender: str, message: str):
        self.chat.add_message("user" if sender == "USER" else "assistant", message)

    def clear_chat(self):
        self.chat.clear()
        self._show_welcome()
        self.toast.show("Conversation cleared", "info")

    def update_state(self, state: str):
        self.sidebar.set_state(state)
        self.header.set_status(state)

    def prefill_input(self, before: str, after: str = ""):
        self.input_entry.delete(0, "end")
        self.input_entry.insert(0, before + after)
        self.input_entry.focus_set()
        self.input_entry.icursor(len(before))

    def send_text_command(self):
        cmd = self.input_entry.get().strip()
        if not cmd:
            return
        self.input_entry.delete(0, "end")
        if not self._history or self._history[-1] != cmd:
            self._history.append(cmd)
        self._history_pos = len(self._history)
        self.execute_prompt(cmd)

    def _recall_history(self, step: int):
        """Up/Down in the command box cycles through previously typed commands."""
        if not self._history:
            return "break"
        self._history_pos = max(0, min(len(self._history), self._history_pos + step))
        text = self._history[self._history_pos] if self._history_pos < len(self._history) else ""
        self.input_entry.delete(0, "end")
        self.input_entry.insert(0, text)
        return "break"

    def execute_prompt(self, user_text: str):
        self.append_chat("USER", user_text)
        self.cmd_queue.put(user_text)

    def _command_worker(self):
        while True:
            prompt = self.cmd_queue.get()
            if prompt is None:
                break

            self.after(0, lambda: (self.update_state("processing"), self.chat.show_typing()))
            try:
                response = self.brain.process_command(prompt)
            except Exception as e:
                response = f"System error: {str(e)}"

            self.after(0, lambda r=response: self._on_response_ready(r))
            self.cmd_queue.task_done()

    def _on_response_ready(self, response: str):
        self.append_chat("DYD", response)
        self.update_state("speaking")
        self.speech.speak(response)
        self.after(600, self._return_to_idle_when_quiet)

    def _return_to_idle_when_quiet(self):
        if self.speech.is_speaking or not self.speech.tts_queue.empty():
            self.after(300, self._return_to_idle_when_quiet)
        elif not self.is_listening:
            self.update_state("idle")

    # ── Voice ──────────────────────────────────────────────────────────────────

    def toggle_voice_listen(self):
        if self.is_listening:
            return

        self.is_listening = True
        self.sidebar.set_listening(True)
        self.update_state("listening")

        def listen_task():
            text = self.speech.listen()
            self.after(0, lambda: self._on_speech_captured(text))

        threading.Thread(target=listen_task, daemon=True).start()

    def _on_speech_captured(self, text: str):
        self.is_listening = False
        self.sidebar.set_listening(False)
        if text:
            self.execute_prompt(text)
        else:
            self.update_state("error")
            self.after(1800, lambda: self.update_state("idle"))

    def toggle_continuous_listen(self):
        self.auto_listen_active = self.sidebar.wake_switch.get() == 1
        if self.auto_listen_active:
            self.toast.show("Always listening is on", "info")
            threading.Thread(target=self._continuous_listen_loop, daemon=True).start()
        else:
            self.toast.show("Always listening is off", "info")

    def _continuous_listen_loop(self):
        """Background thread: always listening, no strict wake-word guard."""
        while self.auto_listen_active:
            if self.is_listening or self.speech.is_speaking or not self.cmd_queue.empty():
                time.sleep(0.3)
                continue
            text = self.speech.listen(timeout=5, phrase_time_limit=10)
            if text and self.auto_listen_active:
                self.after(0, lambda t=text: self.execute_prompt(t))
            time.sleep(0.1)

    # ── Settings ───────────────────────────────────────────────────────────────

    def open_settings_window(self):
        existing = getattr(self, "_settings", None)
        if existing is not None and existing.winfo_exists():
            existing.lift()
            existing.focus_force()
            return
        self._settings = SettingsDialog(self, self.speech, on_saved=self._on_settings_saved)

    def _on_settings_saved(self, provider: str):
        self.brain._init_gemini()
        self.header.refresh_model()
        self.toast.show(f"Settings saved · using {config.PROVIDER_NAMES.get(provider, provider)}")


if __name__ == "__main__":
    app = DYDApp()
    app.mainloop()
