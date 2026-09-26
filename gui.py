import math
import time
import queue
import threading
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import speech_recognition as sr

import config
from gemini_brain import DYDBrain
from speech_engine import SpeechEngine, get_best_microphone_index
import actions

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

CYAN = "#00f0ff"
NEON_BLUE = "#0088ff"
DARK_BG = "#0b0f19"
PANEL_BG = "#111827"
ACCENT_BG = "#1f293d"
TEXT_COLOR = "#e2e8f0"
MUTED_TEXT = "#64748b"

class ArcReactorCanvas(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, highlightthickness=0, bg=PANEL_BG, **kwargs)
        self.angle = 0
        self.pulse = 0
        self.pulse_dir = 1
        self.active_color = CYAN
        self.is_animating = True
        self._animate()

    def set_state(self, state: str):
        if state == "listening":
            self.active_color = "#38bdf8"
        elif state == "processing":
            self.active_color = "#f59e0b"
        elif state == "speaking":
            self.active_color = "#10b981"
        else:
            self.active_color = CYAN

    def _animate(self):
        if not self.winfo_exists():
            return
        
        self.delete("all")
        w = self.winfo_width() or 180
        h = self.winfo_height() or 180
        cx, cy = w // 2, h // 2
        r = min(cx, cy) - 15

        if r > 20:
            self.create_oval(cx - r, cy - r, cx + r, cy + r, outline="#1e293b", width=2)
            for i in range(0, 360, 45):
                start_angle = (i + self.angle) % 360
                self.create_arc(
                    cx - r, cy - r, cx + r, cy + r,
                    start=start_angle, extent=25,
                    style="arc", outline=self.active_color, width=3
                )
            r2 = r - 16
            self.create_oval(cx - r2, cy - r2, cx + r2, cy + r2, outline="#162e4a", width=1)
            for i in range(0, 360, 60):
                start_angle = (360 - (i + self.angle * 1.5)) % 360
                self.create_arc(
                    cx - r2, cy - r2, cx + r2, cy + r2,
                    start=start_angle, extent=35,
                    style="arc", outline=NEON_BLUE, width=2
                )
            core_r = max(8, 14 + int(self.pulse))
            self.create_oval(
                cx - core_r, cy - core_r, cx + core_r, cy + core_r,
                fill=self.active_color, outline="#ffffff", width=1
            )

        self.angle = (self.angle + 3) % 360
        self.pulse += 0.4 * self.pulse_dir
        if self.pulse > 6 or self.pulse < -2:
            self.pulse_dir *= -1

        if self.is_animating:
            self.after(40, self._animate)

class DYDApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("DYD // AI Desktop Assistant (Ollama & Gemini / GPT / Claude)")
        self.geometry("980x700")
        self.minsize(820, 580)
        self.configure(fg_color=DARK_BG)

        # Initialize engines
        self.brain = DYDBrain()
        self.speech = SpeechEngine()
        self.is_listening = False
        self.auto_listen_active = False
        self.cmd_queue = queue.Queue()

        self._build_ui()
        self._check_initial_keys()

        # Dedicated sequential command worker
        self.worker_thread = threading.Thread(target=self._command_worker, daemon=True)
        self.worker_thread.start()

    def _build_ui(self):
        # 1. Header Frame
        header = ctk.CTkFrame(self, fg_color=PANEL_BG, corner_radius=0, height=60)
        header.pack(fill="x", side="top", padx=0, pady=0)

        title_label = ctk.CTkLabel(
            header,
            text="⚡ DYD // PROTOCOL",
            font=ctk.CTkFont(family="Consolas", size=20, weight="bold"),
            text_color=CYAN
        )
        title_label.pack(side="left", padx=20, pady=12)

        self.provider_badge = ctk.CTkLabel(
            header,
            text=f"[{config.get_ai_provider()}]",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color="#38bdf8"
        )
        self.provider_badge.pack(side="left", padx=5)

        self.status_badge = ctk.CTkLabel(
            header,
            text="● ONLINE",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            text_color="#10b981"
        )
        self.status_badge.pack(side="left", padx=5)

        settings_btn = ctk.CTkButton(
            header,
            text="⚙ Settings & AI Models",
            width=180,
            height=32,
            fg_color=ACCENT_BG,
            hover_color="#2d3748",
            border_width=1,
            border_color="#334155",
            command=self.open_settings_window
        )
        settings_btn.pack(side="right", padx=20, pady=12)

        # 2. Main Content Container
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=15)

        # Left Column: Reactor & Controls
        left_panel = ctk.CTkFrame(main_container, fg_color=PANEL_BG, corner_radius=12, width=290)
        left_panel.pack(side="left", fill="y", padx=(0, 15), pady=0)
        left_panel.pack_propagate(False)

        reactor_title = ctk.CTkLabel(
            left_panel,
            text="AI CORE STATUS",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color=MUTED_TEXT
        )
        reactor_title.pack(pady=(12, 5))

        self.reactor = ArcReactorCanvas(left_panel, width=170, height=170)
        self.reactor.pack(pady=5)

        self.state_label = ctk.CTkLabel(
            left_panel,
            text="SYSTEM READY",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            text_color=CYAN
        )
        self.state_label.pack(pady=4)

        # Voice Button
        self.voice_btn = ctk.CTkButton(
            left_panel,
            text="🎙️  CLICK TO SPEAK",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=46,
            fg_color="#0284c7",
            hover_color="#0369a1",
            corner_radius=8,
            command=self.toggle_voice_listen
        )
        self.voice_btn.pack(fill="x", padx=15, pady=(12, 6))

        # Continuous listening switch
        self.auto_listen_switch = ctk.CTkSwitch(
            left_panel,
            text="Auto Wake-Word (Hey DYD)",
            font=ctk.CTkFont(size=11),
            command=self.toggle_continuous_listen
        )
        self.auto_listen_switch.pack(padx=18, pady=(4, 10), anchor="w")

        # Quick Actions
        quick_label = ctk.CTkLabel(
            left_panel,
            text="QUICK COMMANDS",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color=MUTED_TEXT
        )
        quick_label.pack(anchor="w", padx=18, pady=(8, 4))

        quick_yt = ctk.CTkButton(
            left_panel, text="🎵 Play Night Changes",
            height=28, fg_color=ACCENT_BG, hover_color="#2d3748", anchor="w",
            command=lambda: self.execute_prompt("play night changes on youtube")
        )
        quick_yt.pack(fill="x", padx=15, pady=3)

        quick_wa = ctk.CTkButton(
            left_panel, text="💬 WhatsApp 'Hi' to Dad",
            height=28, fg_color=ACCENT_BG, hover_color="#2d3748", anchor="w",
            command=lambda: self.execute_prompt("open whatsapp and send hi to dad")
        )
        quick_wa.pack(fill="x", padx=15, pady=3)

        quick_pc = ctk.CTkButton(
            left_panel, text="💻 Check PC Stats",
            height=28, fg_color=ACCENT_BG, hover_color="#2d3748", anchor="w",
            command=lambda: self.execute_prompt("check the PC status right now")
        )
        quick_pc.pack(fill="x", padx=15, pady=3)

        # Right Column: Chat History & Input
        right_panel = ctk.CTkFrame(main_container, fg_color=PANEL_BG, corner_radius=12)
        right_panel.pack(side="right", fill="both", expand=True)

        chat_header = ctk.CTkFrame(right_panel, fg_color="transparent", height=30)
        chat_header.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkLabel(
            chat_header,
            text="ACTIVITY FEED & TELEMETRY",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color=MUTED_TEXT
        ).pack(side="left")

        clear_btn = ctk.CTkButton(
            chat_header, text="Clear", width=50, height=24,
            fg_color="transparent", text_color=MUTED_TEXT, hover_color=ACCENT_BG,
            command=self.clear_chat
        )
        clear_btn.pack(side="right")

        # Scrollable Chat
        self.chat_box = ctk.CTkTextbox(
            right_panel,
            fg_color="#0d131f",
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            corner_radius=8,
            wrap="word"
        )
        self.chat_box.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        self.chat_box.configure(state="disabled")

        # Bottom Input Bar
        input_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        input_frame.pack(fill="x", padx=15, pady=(0, 15))

        self.input_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Enter command or question (e.g. 'play night changes', 'check pc status')...",
            font=ctk.CTkFont(size=13),
            height=42,
            fg_color="#1e293b",
            border_color="#334155",
            corner_radius=8
        )
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.input_entry.bind("<Return>", lambda event: self.send_text_command())

        send_btn = ctk.CTkButton(
            input_frame,
            text="Execute ⚡",
            font=ctk.CTkFont(size=13, weight="bold"),
            width=100,
            height=42,
            fg_color="#0284c7",
            hover_color="#0369a1",
            corner_radius=8,
            command=self.send_text_command
        )
        send_btn.pack(side="right")

        # Welcome message
        self.append_chat("DYD", f"Systems online, {config.USER_NAME}. Ready for your voice or text commands.")

    def _check_initial_keys(self):
        provider = config.get_ai_provider()
        if provider == "GEMINI" and not config.get_api_key():
            self.after(500, self.open_settings_window)

    def append_chat(self, sender: str, message: str):
        self.chat_box.configure(state="normal")
        timestamp = time.strftime("%H:%M:%S")
        if sender == "USER":
            prefix = f"\n[{timestamp}] YOU:\n"
            self.chat_box.insert("end", prefix, "user_tag")
            self.chat_box.insert("end", f"  {message}\n")
        else:
            prefix = f"\n[{timestamp}] DYD:\n"
            self.chat_box.insert("end", prefix, "dyd_tag")
            self.chat_box.insert("end", f"  {message}\n")
        self.chat_box.see("end")
        self.chat_box.configure(state="disabled")

    def clear_chat(self):
        self.chat_box.configure(state="normal")
        self.chat_box.delete("1.0", "end")
        self.chat_box.configure(state="disabled")
        self.append_chat("DYD", "Activity feed cleared.")

    def update_state(self, state_text: str, state_type: str = "normal"):
        self.state_label.configure(text=state_text)
        self.reactor.set_state(state_type)

    def send_text_command(self):
        cmd = self.input_entry.get().strip()
        if not cmd:
            return
        self.input_entry.delete(0, "end")
        self.execute_prompt(cmd)

    def execute_prompt(self, user_text: str):
        self.append_chat("USER", user_text)
        self.cmd_queue.put(user_text)

    def _command_worker(self):
        while True:
            prompt = self.cmd_queue.get()
            if prompt is None:
                break

            self.after(0, lambda: self.update_state("PROCESSING...", "processing"))
            try:
                response = self.brain.process_command(prompt)
            except Exception as e:
                response = f"System error: {str(e)}"

            self.after(0, lambda r=response: self._on_response_ready(r))
            self.cmd_queue.task_done()

    def _on_response_ready(self, response: str):
        self.append_chat("DYD", response)
        self.update_state("SPEAKING...", "speaking")
        self.speech.speak(response)
        # Reset state label after a short delay
        self.after(2000, lambda: self.update_state("SYSTEM READY", "normal"))

    def toggle_voice_listen(self):
        if self.is_listening:
            return

        self.is_listening = True
        self.voice_btn.configure(text="🔴 LISTENING NOW...", fg_color="#ef4444")
        self.update_state("LISTENING TO MIC...", "listening")

        def listen_task():
            text = self.speech.listen()
            self.after(0, lambda: self._on_speech_captured(text))

        threading.Thread(target=listen_task, daemon=True).start()

    def _on_speech_captured(self, text: str):
        self.is_listening = False
        self.voice_btn.configure(text="🎙️  CLICK TO SPEAK", fg_color="#0284c7")
        if text:
            self.execute_prompt(text)
        else:
            self.update_state("NO AUDIO DETECTED", "normal")
            self.after(1500, lambda: self.update_state("SYSTEM READY", "normal"))

    def toggle_continuous_listen(self):
        self.auto_listen_active = self.auto_listen_switch.get() == 1
        if self.auto_listen_active:
            self.append_chat("DYD", "Auto-listen enabled. Just speak anytime — no wake word needed!")
            threading.Thread(target=self._continuous_listen_loop, daemon=True).start()
        else:
            self.append_chat("DYD", "Auto-listen disabled.")

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

    def open_settings_window(self):
        win = ctk.CTkToplevel(self)
        win.title("DYD Configuration & AI Models")
        win.geometry("620x680")
        win.resizable(False, True)
        win.attributes("-topmost", True)
        win.configure(fg_color=PANEL_BG)

        scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=15)

        ctk.CTkLabel(
            scroll,
            text="⚙ DYD ASSISTANT CONFIGURATION",
            font=ctk.CTkFont(family="Consolas", size=16, weight="bold"),
            text_color=CYAN
        ).pack(pady=(5, 15))

        # 1. AI Provider Selection
        prov_frame = ctk.CTkFrame(scroll, fg_color=DARK_BG, corner_radius=8)
        prov_frame.pack(fill="x", pady=8)

        ctk.CTkLabel(
            prov_frame,
            text="Select AI Intelligence Provider:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 4))

        provider_var = ctk.StringVar(value=config.get_ai_provider())
        provider_menu = ctk.CTkSegmentedButton(
            prov_frame,
            values=["GEMINI", "OLLAMA", "OPENAI", "CLAUDE"],
            variable=provider_var
        )
        provider_menu.pack(fill="x", padx=15, pady=(4, 12))

        # Ollama Details Frame
        ollama_frame = ctk.CTkFrame(scroll, fg_color=DARK_BG, corner_radius=8)
        ollama_frame.pack(fill="x", pady=6)
        ctk.CTkLabel(ollama_frame, text="🦙 Local Ollama (Offline, 100% Free):", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=15, pady=(8, 2))
        
        ol_url_box = ctk.CTkFrame(ollama_frame, fg_color="transparent")
        ol_url_box.pack(fill="x", padx=15, pady=3)
        ctk.CTkLabel(ol_url_box, text="URL: ", width=60, anchor="w").pack(side="left")
        ollama_url_entry = ctk.CTkEntry(ol_url_box)
        ollama_url_entry.insert(0, config.get_ollama_url())
        ollama_url_entry.pack(side="right", fill="x", expand=True)

        ol_mod_box = ctk.CTkFrame(ollama_frame, fg_color="transparent")
        ol_mod_box.pack(fill="x", padx=15, pady=3)
        ctk.CTkLabel(ol_mod_box, text="Model: ", width=60, anchor="w").pack(side="left")
        ollama_mod_entry = ctk.CTkEntry(ol_mod_box, placeholder_text="e.g. qwen2.5:32b, qwen3.5:35b, llama3.2")
        ollama_mod_entry.insert(0, config.get_ollama_model())
        ollama_mod_entry.pack(side="right", fill="x", expand=True)

        # Cloud API Keys Frame
        keys_frame = ctk.CTkFrame(scroll, fg_color=DARK_BG, corner_radius=8)
        keys_frame.pack(fill="x", pady=6)
        ctk.CTkLabel(keys_frame, text="🔑 Cloud API Keys:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=15, pady=(8, 4))

        gemini_box = ctk.CTkFrame(keys_frame, fg_color="transparent")
        gemini_box.pack(fill="x", padx=15, pady=3)
        ctk.CTkLabel(gemini_box, text="Gemini: ", width=65, anchor="w").pack(side="left")
        gemini_entry = ctk.CTkEntry(gemini_box, placeholder_text="Gemini API Key (AIza...)", show="●")
        gemini_entry.insert(0, config.get_api_key())
        gemini_entry.pack(side="right", fill="x", expand=True)

        openai_box = ctk.CTkFrame(keys_frame, fg_color="transparent")
        openai_box.pack(fill="x", padx=15, pady=3)
        ctk.CTkLabel(openai_box, text="OpenAI: ", width=65, anchor="w").pack(side="left")
        openai_entry = ctk.CTkEntry(openai_box, placeholder_text="OpenAI Key (sk-...)", show="●")
        openai_entry.insert(0, config.get_openai_key())
        openai_entry.pack(side="right", fill="x", expand=True)

        claude_box = ctk.CTkFrame(keys_frame, fg_color="transparent")
        claude_box.pack(fill="x", padx=15, pady=(3, 10))
        ctk.CTkLabel(claude_box, text="Claude: ", width=65, anchor="w").pack(side="left")
        claude_entry = ctk.CTkEntry(claude_box, placeholder_text="Anthropic Key (sk-ant-...)", show="●")
        claude_entry.insert(0, config.get_claude_key())
        claude_entry.pack(side="right", fill="x", expand=True)

        # Microphone Diagnostics
        mic_frame = ctk.CTkFrame(scroll, fg_color=DARK_BG, corner_radius=8)
        mic_frame.pack(fill="x", pady=6)
        ctk.CTkLabel(mic_frame, text="🎙️ Microphone Hardware Detection:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=15, pady=(8, 2))
        
        detected_mic_idx = get_best_microphone_index()
        mic_status_lbl = ctk.CTkLabel(
            mic_frame,
            text=f"Active Mic: Device Index #{detected_mic_idx} (Hardware Digital Array)",
            font=ctk.CTkFont(size=11),
            text_color="#38bdf8"
        )
        mic_status_lbl.pack(anchor="w", padx=15, pady=2)

        mic_test_result = ctk.CTkLabel(mic_frame, text="", font=ctk.CTkFont(size=11), text_color="#10b981")
        mic_test_result.pack(anchor="w", padx=15, pady=2)

        def run_mic_test():
            mic_test_result.configure(text="Listening for 3 seconds... say 'hello'", text_color="#f59e0b")
            def _t():
                txt = self.speech.listen(timeout=4, phrase_time_limit=4)
                if txt:
                    mic_test_result.configure(text=f"✓ Heard: '{txt}'", text_color="#10b981")
                else:
                    mic_test_result.configure(text="✗ No audio heard. Check Windows mic mute switch.", text_color="#ef4444")
            threading.Thread(target=_t, daemon=True).start()

        mic_test_btn = ctk.CTkButton(
            mic_frame, text="🎤 Test Microphone Now", height=28, width=170,
            fg_color=ACCENT_BG, hover_color="#2d3748", command=run_mic_test
        )
        mic_test_btn.pack(anchor="w", padx=15, pady=(4, 10))

        # WhatsApp Contacts Section
        contacts_frame = ctk.CTkFrame(scroll, fg_color=DARK_BG, corner_radius=8)
        contacts_frame.pack(fill="x", pady=6)

        ctk.CTkLabel(contacts_frame, text="📱 WhatsApp Quick Contacts:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=15, pady=(8, 2))
        dad_box = ctk.CTkFrame(contacts_frame, fg_color="transparent")
        dad_box.pack(fill="x", padx=15, pady=3)
        ctk.CTkLabel(dad_box, text="DAD: ", width=60, anchor="w").pack(side="left")
        dad_entry = ctk.CTkEntry(dad_box, placeholder_text="e.g. 94771234567")
        dad_entry.insert(0, config.get_whatsapp_contact("DAD"))
        dad_entry.pack(side="right", fill="x", expand=True)

        mom_box = ctk.CTkFrame(contacts_frame, fg_color="transparent")
        mom_box.pack(fill="x", padx=15, pady=(3, 10))
        ctk.CTkLabel(mom_box, text="MOM: ", width=60, anchor="w").pack(side="left")
        mom_entry = ctk.CTkEntry(mom_box, placeholder_text="e.g. 94777654321")
        mom_entry.insert(0, config.get_whatsapp_contact("MOM"))
        mom_entry.pack(side="right", fill="x", expand=True)

        def save_and_close():
            sel_provider = provider_var.get()
            config.set_ai_provider(sel_provider)
            self.provider_badge.configure(text=f"[{sel_provider}]")

            if ollama_url_entry.get().strip():
                config.save_ollama_url(ollama_url_entry.get().strip())
            if ollama_mod_entry.get().strip():
                config.save_ollama_model(ollama_mod_entry.get().strip())

            if gemini_entry.get().strip():
                config.save_api_key(gemini_entry.get().strip())
                self.brain._init_gemini()
            if openai_entry.get().strip():
                config.save_openai_key(openai_entry.get().strip())
            if claude_entry.get().strip():
                config.save_claude_key(claude_entry.get().strip())

            if dad_entry.get().strip():
                config.save_whatsapp_contact("DAD", dad_entry.get().strip())
            if mom_entry.get().strip():
                config.save_whatsapp_contact("MOM", mom_entry.get().strip())

            self.append_chat("DYD", f"Settings saved! Active provider: {sel_provider}")
            win.destroy()

        save_btn = ctk.CTkButton(
            scroll,
            text="Save Settings & Initialize",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#10b981",
            hover_color="#059669",
            height=40,
            command=save_and_close
        )
        save_btn.pack(pady=15)

if __name__ == "__main__":
    app = DYDApp()
    app.mainloop()
