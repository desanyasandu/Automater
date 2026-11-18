import re
import threading
import requests
from google import genai
from google.genai import types
import config
import actions

# ─── System prompt ────────────────────────────────────────────────────────────
SYSTEM_INSTRUCTION = (
    f"You are {config.ASSISTANT_NAME}, an ultra-fast, intelligent, and loyal AI desktop assistant "
    f"inspired by J.A.R.V.I.S. You assist {config.USER_NAME}. "
    "Always be concise (1-2 sentences max). Never include markdown or emojis in spoken responses."
)

# ─── Secret redaction ─────────────────────────────────────────────────────────
KEY_PATTERN = re.compile(r"(sk-[A-Za-z0-9_-]{8,}|AIza[0-9A-Za-z_-]{20,}|AQ\.[0-9A-Za-z_.-]{20,})")

def redact_secrets(text: str) -> str:
    """Remove API keys from text before it is shown, spoken or logged."""
    for key in (config.get_api_key(), config.get_openai_key(), config.get_claude_key()):
        if key:
            text = text.replace(key, "[hidden]")
    return KEY_PATTERN.sub("[hidden]", text)

# ─── Fast local dispatcher (0-1ms, no API call) ───────────────────────────────

def fast_local_dispatch(text: str) -> str | None:
    """
    Instantly handles all PC control commands without any API call.
    Returns a response string if handled, or None to fall through to AI.
    """
    t = text.lower().strip()

    # ── Volume ────────────────────────────────────────────────────────────────
    if any(t == phrase for phrase in ["volume up", "turn up", "louder"]):
        return actions.control_volume("up")
    if any(t == phrase for phrase in ["volume down", "turn down", "quieter"]):
        return actions.control_volume("down")
    if "volume up" in t or "increase volume" in t or "turn up the volume" in t or "raise volume" in t:
        return actions.control_volume("up")
    if "volume down" in t or "decrease volume" in t or "lower volume" in t or "turn down the volume" in t:
        return actions.control_volume("down")
    if ("mute" in t and "unmute" not in t) or t == "silence":
        return actions.control_volume("mute")
    if "unmute" in t:
        return actions.control_volume("mute")

    # ── Screenshot ────────────────────────────────────────────────────────────
    if any(k in t for k in ["take a screenshot", "take screenshot", "capture screen", "screenshot", "screen capture"]):
        return actions.take_screenshot()

    # ── Lock PC ───────────────────────────────────────────────────────────────
    if any(k in t for k in ["lock pc", "lock the pc", "lock computer", "lock the computer",
                              "lock screen", "lock workstation", "lock my pc"]):
        return actions.lock_pc()

    # ── System Status ─────────────────────────────────────────────────────────
    if any(k in t for k in ["pc status", "system status", "battery", "cpu usage", "ram usage",
                              "check status", "system info", "check pc", "how is my pc"]):
        return f"{config.USER_NAME}, {actions.get_system_status()}"

    # ── Media Controls ────────────────────────────────────────────────────────
    if any(k in t for k in ["pause video", "pause music", "pause playback", "pause",
                              "resume video", "resume music", "resume playback"]):
        return actions.media_control(t)
    if "fullscreen" in t or "full screen" in t:
        return actions.media_control("fullscreen")

    # ── YouTube ───────────────────────────────────────────────────────────────
    # Patterns: "play X", "play X on youtube", "open youtube and play X", "youtube play X"
    yt_patterns = [
        r"(?:open\s+youtube\s+and\s+)?play\s+(.+?)\s+(?:on|in)\s+(?:youtube|yt)\b",
        r"(?:open\s+youtube\s+and\s+)?play\s+on\s+(?:youtube|yt)\s+(.+)",
        r"(?:youtube|yt)\s+(?:play\s+)?(.+)",
        r"^play\s+(.+)$",
    ]
    for pat in yt_patterns:
        m = re.search(pat, t, re.IGNORECASE)
        if m:
            song = m.group(1).strip()
            # Filter out false positives
            if song and song not in ["music", "a song", "something", "video"]:
                song = re.sub(r"\s+on\s+(?:youtube|yt)$", "", song, flags=re.IGNORECASE).strip()
                return actions.play_youtube(song)

    # ── WhatsApp ──────────────────────────────────────────────────────────────
    # Pattern 1: "send a reply to X saying Y"
    m = re.search(r"send\s+(?:a\s+)?reply\s+to\s+(.+?)\s+saying\s+(.+)$", t, re.IGNORECASE)
    if m:
        return actions.send_whatsapp(m.group(1).strip(), m.group(2).strip())

    # Pattern 2: "send a message to X on whatsapp saying Y"
    m = re.search(r"send\s+(?:a\s+)?message\s+to\s+(.+?)\s+on\s+whatsapp\s+saying\s+(.+)$", t, re.IGNORECASE)
    if m:
        return actions.send_whatsapp(m.group(1).strip(), m.group(2).strip())

    # Pattern 3: "send 'Y' to X on whatsapp" or "send Y to X on whatsapp"
    m = re.search(r"send\s+[\"']?(.+?)[\"']?\s+to\s+(.+?)\s+on\s+whatsapp$", t, re.IGNORECASE)
    if m:
        return actions.send_whatsapp(m.group(2).strip(), m.group(1).strip())

    # Pattern 4: "open whatsapp and send X to Y"
    m = re.search(r"open\s+whatsapp\s+and\s+send\s+[\"']?(.+?)[\"']?\s+to\s+(.+)$", t, re.IGNORECASE)
    if m:
        return actions.send_whatsapp(m.group(2).strip(), m.group(1).strip())

    # Pattern 5: "tell X Y on whatsapp"
    m = re.search(r"tell\s+(.+?)\s+[\"']?(.+?)[\"']?\s+on\s+whatsapp$", t, re.IGNORECASE)
    if m:
        return actions.send_whatsapp(m.group(1).strip(), m.group(2).strip())

    # ── Open Chrome + Search ─────────────────────────────────────────────────
    # "open chrome and search for X" / "open chrome and search X"
    m = re.search(r"^open\s+chrome\s+and\s+search\s+(?:for\s+)?(.+)$", t)
    if m and m.group(1).strip():
        return actions.open_chrome_and_search(m.group(1).strip())

    # "search X in chrome" / "search for X in chrome"
    m = re.search(r"^search\s+(?:for\s+)?(.+?)\s+(?:in|on)\s+chrome$", t)
    if m and m.group(1).strip():
        return actions.open_chrome_and_search(m.group(1).strip())

    # ── Open in Chrome ────────────────────────────────────────────────────────
    # "open X in chrome"
    m = re.search(r"^open\s+(.+?)\s+(?:in|on)\s+chrome$", t)
    if m:
        return actions.open_application(m.group(1).strip())

    # ── Google Search ─────────────────────────────────────────────────────────
    # "search for X", "google X", "search X"
    m = re.search(r"^(?:search\s+for|google|search)\s+(.+?)(?:\s+on\s+google)?$", t)
    if m and m.group(1).strip() not in ["status", "pc status"]:
        return actions.search_google(m.group(1).strip())

    # ── Close App ─────────────────────────────────────────────────────────────
    m = re.search(r"^close\s+(.+)$", t)
    if m:
        return actions.close_application(m.group(1).strip())

    # ── Open App / Website ────────────────────────────────────────────────────
    m = re.search(r"^open\s+(.+)$", t)
    if m:
        return actions.open_application(m.group(1).strip())

    return None  # Let the AI handle it


# ─── AI Brain ─────────────────────────────────────────────────────────────────

class DYDBrain:
    def __init__(self):
        self._genai_client = None
        self.active_gemini_model = None
        self._chat_history = []
        self.lock = threading.Lock()
        self._init_gemini()

    def _init_gemini(self) -> bool:
        key = config.get_api_key()
        if not key:
            return False
        try:
            self._genai_client = genai.Client(api_key=key)
            self.active_gemini_model = config.get_gemini_model()
            print(f"[DYD] Using Gemini model: {self.active_gemini_model}")
            self._chat_history = []
            return True
        except Exception as e:
            print(f"[DYD] Gemini init error: {redact_secrets(str(e))}")
            return False

    # ── Cloud AI Queries ───────────────────────────────────────────────────────

    def query_gemini(self, prompt: str) -> str:
        if not self._genai_client:
            if not self._init_gemini():
                return f"Gemini API key is not set, {config.USER_NAME}. Please open Settings."
        try:
            contents = []
            # Include recent history (last 6 messages for context)
            for h in self._chat_history[-6:]:
                contents.append(h)
            contents.append(types.Content(
                role="user",
                parts=[types.Part(text=prompt)]
            ))
            response = self._genai_client.models.generate_content(
                model=self.active_gemini_model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    max_output_tokens=200,
                    temperature=0.7,
                )
            )
            reply = (response.text or "").strip()
            if not reply:
                return f"I don't have an answer for that, {config.USER_NAME}."
            # Save to history
            self._chat_history.append(types.Content(role="user", parts=[types.Part(text=prompt)]))
            self._chat_history.append(types.Content(role="model", parts=[types.Part(text=reply)]))
            return reply
        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                return f"Gemini rate limit reached. Please wait a moment, {config.USER_NAME}."
            self._genai_client = None
            return f"Gemini error: {err[:120]}"

    def query_ollama(self, prompt: str) -> str:
        url = config.get_ollama_url().rstrip("/")
        model = config.get_ollama_model()
        try:
            r = requests.post(
                f"{url}/api/generate",
                json={"model": model, "prompt": prompt,
                      "system": SYSTEM_INSTRUCTION, "stream": False},
                timeout=20
            )
            if r.status_code == 200:
                return r.json().get("response", "").strip()
            elif r.status_code == 404:
                return f"Model '{model}' not found in Ollama. Run 'ollama run {model}' first."
            return f"Ollama error {r.status_code}: {r.text[:100]}"
        except requests.exceptions.ConnectionError:
            return f"Cannot connect to Ollama at {url}. Make sure Ollama is running."
        except Exception as e:
            return f"Ollama error: {e}"

    def query_openai(self, prompt: str) -> str:
        key = config.get_openai_key()
        if not key:
            return f"OpenAI API key is missing, {config.USER_NAME}. Please set it in Settings."
        try:
            r = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": config.get_openai_model(),
                    "messages": [
                        {"role": "system", "content": SYSTEM_INSTRUCTION},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 150
                },
                timeout=15
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
            try:
                detail = r.json().get("error", {}).get("message", "")
            except ValueError:
                detail = r.text[:100]
            return f"OpenAI error {r.status_code}: {detail}"
        except Exception as e:
            return f"OpenAI error: {e}"

    def query_claude(self, prompt: str) -> str:
        key = config.get_claude_key()
        if not key:
            return f"Claude API key is missing, {config.USER_NAME}. Please set it in Settings."
        try:
            r = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": config.get_claude_model(),
                    "system": SYSTEM_INSTRUCTION,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 150
                },
                timeout=15
            )
            if r.status_code == 200:
                return r.json()["content"][0]["text"].strip()
            return f"Claude error {r.status_code}: {r.text[:100]}"
        except Exception as e:
            return f"Claude error: {e}"

    # ── Main Entry ─────────────────────────────────────────────────────────────

    def process_command(self, user_text: str) -> str:
        """
        Process voice/text command:
          1. Strip wake words
          2. Try instant local dispatch (0-1ms)
          3. Fall through to selected AI provider
        """
        clean = user_text.strip()

        # Strip wake words
        for wake in ["hey dyd", "dyd,", "hey dyd,", "dyd", "hey jarvis,", "hey jarvis", "jarvis,", "jarvis"]:
            if clean.lower().startswith(wake):
                clean = clean[len(wake):].strip(" ,:.-")
                break

        if not clean:
            return f"Yes {config.USER_NAME}? How can DYD assist you?"

        # ⚡ Step 1: Instant local dispatch
        fast = fast_local_dispatch(clean)
        if fast is not None:
            return fast

        # 🧠 Step 2: AI Provider
        provider = config.get_ai_provider()
        with self.lock:
            if provider == "OLLAMA":
                reply = self.query_ollama(clean)
            elif provider == "OPENAI":
                reply = self.query_openai(clean)
            elif provider == "CLAUDE":
                reply = self.query_claude(clean)
            else:
                reply = self.query_gemini(clean)
        return redact_secrets(reply)
