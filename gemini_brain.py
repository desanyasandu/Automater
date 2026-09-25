import re
import threading
import requests
import google.generativeai as genai
import config
import actions

SYSTEM_INSTRUCTION = f"""
You are {config.ASSISTANT_NAME}, an ultra-fast, intelligent, and loyal AI desktop assistant inspired by J.A.R.V.I.S.
You assist the user ({config.USER_NAME}) by answering queries and having smart conversations.
Always address the user politely as '{config.USER_NAME}' unless instructed otherwise.
Be concise, smart, and direct in your responses (1-2 sentences max for voice clarity).
"""

CANDIDATE_GEMINI_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
    "gemini-3.5-flash",
    "gemini-flash-latest"
]

def fast_local_dispatch(text: str) -> str | None:
    """Instantly handles PC controls, YouTube, WhatsApp, and apps in 0.001s without API lag."""
    t = text.lower().strip()

    # 1. System / Battery / CPU status
    if any(k in t for k in ["pc status", "system status", "battery", "cpu", "ram usage", "check status", "system info"]):
        status = actions.get_system_status()
        return f"{config.USER_NAME}, {status}"

    # 2. YouTube Automation
    yt_patterns = [
        r"(?:open\s+youtube\s+and\s+)?play\s+(.*?)\s+(?:on|in)\s+youtube",
        r"(?:open\s+youtube\s+and\s+)?play\s+on\s+youtube\s+(.*)",
        r"play\s+(.*)\s+on\s+yt",
        r"youtube\s+(?:play\s+)?(.*)",
        r"^play\s+(.+)$"
    ]
    for pat in yt_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            song = m.group(1).strip()
            if song and song.lower() not in ["pc", "music"]:
                song = re.sub(r"\s+on\s+youtube$", "", song, flags=re.IGNORECASE).strip()
                actions.play_youtube(song)
                return f"Right away, {config.USER_NAME}. Playing '{song}' on YouTube now."

    # 3. WhatsApp Desktop Automation (Matches patterns like in demo video)
    # Pattern 1: "open whatsapp and send a reply to Bhagya IT saying kohomada eka"
    wa_reply = re.search(r"(?:open\s+whatsapp\s+and\s+)?send\s+(?:a\s+)?reply\s+to\s+(.*?)\s+saying\s+(.+)$", text, re.IGNORECASE)
    if wa_reply:
        contact, msg = wa_reply.group(1).strip(), wa_reply.group(2).strip()
        actions.send_whatsapp(contact, msg)
        return f"Sending reply to {contact} on WhatsApp for you, {config.USER_NAME}."

    # Pattern 2: "send a message to [contact] on whatsapp saying [msg]"
    wa_msg_saying = re.search(r"send\s+(?:a\s+)?message\s+(?:to\s+)?(.*?)\s+on\s+whatsapp\s+saying\s+(.+)$", text, re.IGNORECASE)
    if wa_msg_saying:
        contact, msg = wa_msg_saying.group(1).strip(), wa_msg_saying.group(2).strip()
        actions.send_whatsapp(contact, msg)
        return f"Sending that message to {contact} on WhatsApp for you, {config.USER_NAME}."

    # Pattern 3: "open whatsapp and send a message 'hi' to dad" or "send hi to dad on whatsapp"
    wa_match1 = re.search(r"send\s+(?:a\s+)?message\s+['\"]?([^'\"]+?)['\"]?\s+to\s+([a-zA-Z0-9_\s]+?)(?:\s+on\s+whatsapp)?$", text, re.IGNORECASE)
    wa_match2 = re.search(r"send\s+['\"]?([^'\"]+?)['\"]?\s+to\s+([a-zA-Z0-9_\s]+?)\s+on\s+whatsapp$", text, re.IGNORECASE)
    wa_match3 = re.search(r"tell\s+([a-zA-Z0-9_\s]+?)\s+['\"]?([^'\"]+?)['\"]?\s+on\s+whatsapp$", text, re.IGNORECASE)
    
    if wa_match1 or wa_match2:
        m = wa_match1 or wa_match2
        msg, contact = m.group(1).strip(), m.group(2).strip()
        actions.send_whatsapp(contact, msg)
        return f"Sending that message to {contact} on WhatsApp for you, {config.USER_NAME}."
    elif wa_match3:
        contact, msg = wa_match3.group(1).strip(), wa_match3.group(2).strip()
        actions.send_whatsapp(contact, msg)
        return f"Sending that message to {contact} on WhatsApp for you, {config.USER_NAME}."

    # 4. Screenshot & Lock PC
    if any(k in t for k in ["take a screenshot", "capture screen", "screenshot"]):
        return actions.take_screenshot()
    if any(k in t for k in ["lock pc", "lock the pc", "lock computer", "lock screen", "lock workstation"]):
        return actions.lock_pc()

    # 5. Media Playback Controls
    if any(k in t for k in ["pause video", "pause music", "pause playback", "resume video", "resume music", "fullscreen"]):
        return actions.media_control(t)

    # 6. Web Search & Open in Chrome
    # Pattern A: "open <site> in chrome" (e.g. "open gemini in chrome", "open temu in chrome")
    in_chrome_match = re.search(r"open\s+(.+?)\s+(?:in|on)\s+chrome$", t)
    if in_chrome_match:
        site = in_chrome_match.group(1).strip()
        return actions.open_application(site)

    # Pattern B: "open chrome and search <query>" or "search <query> in chrome/on google"
    b1_match = re.search(r"^open\s+chrome\s+and\s+search\s+(?:for\s+)?(.+)$", t)
    if b1_match and b1_match.group(1).strip():
        q = b1_match.group(1).strip()
        return actions.search_google(q, in_chrome=True)

    # Pattern C: "search for <query>", "search <query>", "google <query>"
    search_match2 = re.search(r"^(?:search\s+for|search|google)\s+(.+?)(?:\s+in\s+chrome|\s+on\s+google)?$", t)
    if search_match2 and search_match2.group(1).strip():
        q = search_match2.group(1).strip()
        if q not in ["status", "pc status"]:
            return actions.search_google(q, in_chrome=True)

    # 7. Volume Control
    if "volume up" in t or "increase volume" in t:
        return actions.control_volume("up")
    if "volume down" in t or "decrease volume" in t or "lower volume" in t:
        return actions.control_volume("down")
    if "mute" in t or "unmute" in t:
        return actions.control_volume("mute")

    # 8. Close Application
    close_match = re.search(r"^close\s+(.+)$", t)
    if close_match:
        target = close_match.group(1).strip()
        return actions.close_application(target)

    # 9. Open Apps & Websites
    open_match = re.search(r"^open\s+(.+)$", t)
    if open_match:
        target = open_match.group(1).strip()
        return actions.open_application(target)

    return None

class DYDBrain:
    def __init__(self):
        self.gemini_chat = None
        self.active_gemini_model = None
        self.lock = threading.Lock()
        self._init_gemini()

    def _init_gemini(self):
        key = config.get_api_key()
        if not key:
            return False

        genai.configure(api_key=key)

        for model_name in CANDIDATE_GEMINI_MODELS:
            try:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=SYSTEM_INSTRUCTION
                )
                self.gemini_chat = model.start_chat()
                self.active_gemini_model = model_name
                print(f"[DYD] Connected to Gemini model: {model_name}")
                return True
            except Exception as e:
                print(f"[DYD Warning] Could not init Gemini {model_name}: {e}")
                continue

        return False

    def query_ollama(self, prompt: str) -> str:
        """Queries local Ollama instance (e.g. Qwen 2.5 / 3.5 35B)."""
        ollama_url = config.get_ollama_url().rstrip("/")
        model = config.get_ollama_model()
        try:
            r = requests.post(
                f"{ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "system": SYSTEM_INSTRUCTION,
                    "stream": False
                },
                timeout=25
            )
            if r.status_code == 200:
                return r.json().get("response", "").strip()
            elif r.status_code == 404:
                return f"Model '{model}' is not pulled in Ollama. Run 'ollama run {model}' in terminal first."
            else:
                return f"Ollama returned error code {r.status_code}: {r.text[:100]}"
        except requests.exceptions.ConnectionError:
            return (
                f"Cannot connect to Ollama at {ollama_url}. "
                "Please make sure Ollama is running, or switch provider in Settings."
            )
        except Exception as e:
            return f"Ollama error: {str(e)}"

    def query_openai(self, prompt: str) -> str:
        """Queries OpenAI GPT API."""
        key = config.get_openai_key()
        if not key:
            return f"OpenAI API Key is missing, {config.USER_NAME}. Please set it in Settings."
        try:
            r = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o-mini",
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
            else:
                return f"OpenAI error {r.status_code}: {r.json().get('error', {}).get('message', r.text[:100])}"
        except Exception as e:
            return f"OpenAI error: {str(e)}"

    def query_claude(self, prompt: str) -> str:
        """Queries Anthropic Claude API."""
        key = config.get_claude_key()
        if not key:
            return f"Claude API Key is missing, {config.USER_NAME}. Please set it in Settings."
        try:
            r = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-3-5-sonnet-20241022",
                    "system": SYSTEM_INSTRUCTION,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 150
                },
                timeout=15
            )
            if r.status_code == 200:
                return r.json()["content"][0]["text"].strip()
            else:
                return f"Claude error {r.status_code}: {r.text[:100]}"
        except Exception as e:
            return f"Claude error: {str(e)}"

    def query_gemini(self, prompt: str) -> str:
        """Queries Google Gemini API."""
        if not self.gemini_chat:
            success = self._init_gemini()
            if not success:
                return f"Gemini API key is not configured, {config.USER_NAME}. Please set it in Settings."

        for attempt_model in [self.active_gemini_model] + [m for m in CANDIDATE_GEMINI_MODELS if m != self.active_gemini_model]:
            try:
                response = self.gemini_chat.send_message(prompt)
                return response.text.strip()
            except Exception as e:
                err_str = str(e)
                print(f"[DYD] Error with Gemini {attempt_model}: {err_str}")
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    return f"Google Gemini rate limit reached, {config.USER_NAME}. Please wait a moment."
                try:
                    alt_model = genai.GenerativeModel(
                        model_name=attempt_model,
                        system_instruction=SYSTEM_INSTRUCTION
                    )
                    self.gemini_chat = alt_model.start_chat()
                    self.active_gemini_model = attempt_model
                except Exception:
                    pass

        return f"Apologies {config.USER_NAME}, Gemini could not process that request right now."

    def process_command(self, user_text: str) -> str:
        """Processes user voice/text: Fast local actions first, then selected AI Provider."""
        clean_text = user_text.strip()
        for wake in ["hey dyd", "dyd", "hey jarvis", "jarvis"]:
            if clean_text.lower().startswith(wake):
                clean_text = clean_text[len(wake):].strip(" ,:.-")
                break

        if not clean_text:
            return f"Yes {config.USER_NAME}? How can DYD assist you?"

        # ⚡ Step 1: Ultra-fast local dispatch (0.001s for YouTube, PC, WhatsApp, Apps)
        fast_result = fast_local_dispatch(clean_text)
        if fast_result:
            return fast_result

        # 🧠 Step 2: Route to configured AI Provider
        provider = config.get_ai_provider()
        with self.lock:
            if provider == "OLLAMA":
                return self.query_ollama(clean_text)
            elif provider == "OPENAI":
                return self.query_openai(clean_text)
            elif provider == "CLAUDE":
                return self.query_claude(clean_text)
            else: # Default GEMINI
                return self.query_gemini(clean_text)
