import os
import re
import sys
import time
import threading
import webbrowser
import urllib.parse
import subprocess
import ctypes
from pathlib import Path
import psutil
import config

# ─── Constants ────────────────────────────────────────────────────────────────
CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]

# Only letters, digits, spaces, dots, dashes and underscores may reach taskkill
SAFE_PROCESS_NAME = re.compile(r"[a-z0-9 ._-]{1,64}")

VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP   = 0xAF

COMMON_WEBSITES = {
    "gemini": "https://gemini.google.com",
    "google gemini": "https://gemini.google.com",
    "temu": "https://www.temu.com",
    "chatgpt": "https://chatgpt.com",
    "gpt": "https://chatgpt.com",
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "github": "https://www.github.com",
    "facebook": "https://www.facebook.com",
    "instagram": "https://www.instagram.com",
    "twitter": "https://x.com",
    "x": "https://x.com",
    "tiktok": "https://www.tiktok.com",
    "amazon": "https://www.amazon.com",
    "netflix": "https://www.netflix.com",
    "gmail": "https://mail.google.com",
    "maps": "https://maps.google.com",
    "google maps": "https://maps.google.com",
    "reddit": "https://www.reddit.com",
    "wikipedia": "https://www.wikipedia.org",
    "canva": "https://www.canva.com",
    "spotify": "https://open.spotify.com",
    "linkedin": "https://www.linkedin.com",
    "whatsapp web": "https://web.whatsapp.com",
}

def _get_chrome_path() -> str | None:
    for p in CHROME_PATHS:
        if os.path.exists(p):
            return p
    return None

# ─── Browser / Search ─────────────────────────────────────────────────────────

def open_in_browser(url: str, force_chrome: bool = True):
    """Open URL in Chrome (if found) or default browser — fire-and-forget."""
    chrome = _get_chrome_path()
    def _run():
        if force_chrome and chrome:
            subprocess.Popen([chrome, url],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            webbrowser.open(url)
    threading.Thread(target=_run, daemon=True).start()

def search_google(query: str, in_chrome: bool = True) -> str:
    """Search Google for any topic in Chrome."""
    clean = query.strip()
    url = f"https://www.google.com/search?q={urllib.parse.quote(clean)}"
    open_in_browser(url, force_chrome=in_chrome)
    return f"Searching '{clean}' on Google, {config.USER_NAME}."

def open_chrome_and_search(query: str) -> str:
    """Open Chrome and immediately search for query."""
    clean = query.strip()
    chrome = _get_chrome_path()
    url = f"https://www.google.com/search?q={urllib.parse.quote(clean)}"
    def _run():
        if chrome:
            subprocess.Popen([chrome, url],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            webbrowser.open(url)
    threading.Thread(target=_run, daemon=True).start()
    return f"Opening Chrome and searching for '{clean}', {config.USER_NAME}."

# ─── YouTube ──────────────────────────────────────────────────────────────────

def play_youtube(query: str) -> str:
    """Search and play a video/song on YouTube (instant, non-blocking)."""
    clean = query.strip()
    def _play():
        try:
            import pywhatkit
            pywhatkit.playonyt(clean)
        except Exception:
            url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(clean)}"
            open_in_browser(url, force_chrome=True)
    threading.Thread(target=_play, daemon=True).start()
    return f"Playing '{clean}' on YouTube now, {config.USER_NAME}."

# ─── Volume Control ───────────────────────────────────────────────────────────

def control_volume(action: str) -> str:
    """Instantly control system volume via hardware VK codes."""
    act = action.lower()
    if any(k in act for k in ["up", "increase", "raise", "louder", "higher"]):
        for _ in range(5):
            ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, 2, 0)
        return f"Volume increased, {config.USER_NAME}."
    elif any(k in act for k in ["down", "decrease", "lower", "quieter", "reduce"]):
        for _ in range(5):
            ctypes.windll.user32.keybd_event(VK_VOLUME_DOWN, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_VOLUME_DOWN, 0, 2, 0)
        return f"Volume decreased, {config.USER_NAME}."
    elif any(k in act for k in ["mute", "unmute", "silent"]):
        ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 2, 0)
        return f"Volume muted/unmuted, {config.USER_NAME}."
    return "Unknown volume command."

# ─── Screenshot ───────────────────────────────────────────────────────────────

def take_screenshot() -> str:
    """Take screenshot using Win+PrtScn and save a PNG copy."""
    def _shot():
        # Win + PrtScn (saves to Pictures/Screenshots natively)
        ctypes.windll.user32.keybd_event(0x5B, 0, 0, 0)  # Win down
        ctypes.windll.user32.keybd_event(0x2C, 0, 0, 0)  # PrtScn down
        time.sleep(0.05)
        ctypes.windll.user32.keybd_event(0x2C, 0, 2, 0)  # PrtScn up
        ctypes.windll.user32.keybd_event(0x5B, 0, 2, 0)  # Win up
        # Also save timestamped PNG
        try:
            from PIL import ImageGrab
            folder = Path.home() / "Pictures" / "Screenshots"
            folder.mkdir(parents=True, exist_ok=True)
            fname = f"Screenshot_{time.strftime('%Y%m%d_%H%M%S')}.png"
            ImageGrab.grab().save(str(folder / fname))
        except Exception:
            pass
    threading.Thread(target=_shot, daemon=True).start()
    return f"Screenshot captured and saved to Pictures/Screenshots, {config.USER_NAME}."

# ─── Lock PC ──────────────────────────────────────────────────────────────────

def lock_pc() -> str:
    """Lock the Windows workstation immediately."""
    threading.Thread(target=ctypes.windll.user32.LockWorkStation, daemon=True).start()
    return f"Locking your computer now, {config.USER_NAME}."

# ─── Media Controls ───────────────────────────────────────────────────────────

def media_control(action: str) -> str:
    """Toggle play/pause or fullscreen for any media."""
    act = action.lower()
    if any(k in act for k in ["pause", "stop", "resume", "play"]):
        ctypes.windll.user32.keybd_event(0xB3, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0xB3, 0, 2, 0)
        return f"Toggled media playback, {config.USER_NAME}."
    elif "fullscreen" in act:
        # Send 'F' key for most players / YouTube
        ctypes.windll.user32.keybd_event(0x46, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0x46, 0, 2, 0)
        return f"Toggled fullscreen, {config.USER_NAME}."
    return "Media control executed."

# ─── WhatsApp ─────────────────────────────────────────────────────────────────

def send_whatsapp(contact: str, message: str) -> str:
    """Automate WhatsApp Desktop: search contact, open chat, send message."""
    try:
        import pyautogui
        import pyperclip
        pyautogui.FAILSAFE = False
    except ImportError:
        return "pyautogui or pyperclip is not installed."

    def _send():
        os.system("start whatsapp:")
        time.sleep(1.8)
        pyautogui.hotkey("ctrl", "f")
        time.sleep(0.4)
        pyautogui.hotkey("ctrl", "a")
        pyautogui.press("backspace")
        time.sleep(0.2)
        pyperclip.copy(contact.strip())
        pyautogui.hotkey("ctrl", "v")
        time.sleep(1.2)
        pyautogui.press("down")
        time.sleep(0.2)
        pyautogui.press("enter")
        time.sleep(0.8)
        pyperclip.copy(message.strip())
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.3)
        pyautogui.press("enter")

    threading.Thread(target=_send, daemon=True).start()
    return f"Sending message to {contact} on WhatsApp, {config.USER_NAME}."

# ─── Open Application ─────────────────────────────────────────────────────────

def open_application(app_name: str) -> str:
    """Open any desktop app, website, or fall back to Google search."""
    app = app_name.lower().strip()

    # ── Browsers ──────────────────────────────────────
    if app in ["chrome", "google chrome", "browser"]:
        def _open_chrome():
            chrome = _get_chrome_path()
            if chrome:
                subprocess.Popen([chrome], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                webbrowser.open("https://www.google.com")
        threading.Thread(target=_open_chrome, daemon=True).start()
        return f"Opening Google Chrome, {config.USER_NAME}."

    # ── Known websites ────────────────────────────────
    if app in COMMON_WEBSITES:
        open_in_browser(COMMON_WEBSITES[app], force_chrome=True)
        return f"Opening {app_name.title()} in Chrome, {config.USER_NAME}."

    # ── Direct URL ────────────────────────────────────
    if any(app.endswith(ext) for ext in [".com", ".org", ".net", ".io", ".lk", ".ai", ".co", ".app", ".edu"]):
        url = f"https://{app}" if not app.startswith("http") else app
        open_in_browser(url, force_chrome=True)
        return f"Opening {app} in Chrome, {config.USER_NAME}."

    # ── Desktop apps ──────────────────────────────────
    APP_CMDS = {
        ("notepad", "note"): ("notepad.exe", False),
        ("calculator", "calc"): ("calc.exe", False),
        ("vscode", "vs code", "code", "visual studio code"): ("code", True),
        ("cmd", "command prompt"): ("cmd.exe", True),
        ("terminal", "powershell"): ("powershell.exe", True),
        ("file explorer", "explorer", "this pc"): ("explorer.exe", False),
        ("settings", "windows settings"): ("ms-settings:", True),
        ("task manager", "taskmgr"): ("taskmgr.exe", False),
        ("paint"): ("mspaint.exe", False),
        ("word"): ("winword.exe", False),
        ("excel"): ("excel.exe", False),
        ("powerpoint"): ("powerpnt.exe", False),
        ("snipping tool", "snip"): ("snippingtool.exe", False),
        ("clock"): ("ms-clock:", True),
    }

    for keys, (cmd, use_shell) in APP_CMDS.items():
        if isinstance(keys, str):
            keys = (keys,)
        if app in keys:
            def _launch(c=cmd, s=use_shell):
                if s:
                    os.system(f"start {c}")
                else:
                    subprocess.Popen(c, shell=True,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            threading.Thread(target=_launch, daemon=True).start()
            return f"Opening {app_name.title()}, {config.USER_NAME}."

    if app in ["spotify", "music"]:
        def _spotify():
            os.system("start spotify:")
        threading.Thread(target=_spotify, daemon=True).start()
        return f"Opening Spotify, {config.USER_NAME}."

    if app in ["whatsapp", "whats app"]:
        threading.Thread(target=lambda: os.system("start whatsapp:"), daemon=True).start()
        return f"Opening WhatsApp, {config.USER_NAME}."

    # ── Fallback: Google search ────────────────────────
    return search_google(app_name, in_chrome=True)

# ─── Close Application ────────────────────────────────────────────────────────

def close_application(app_name: str) -> str:
    """Close any running application by name."""
    app = app_name.lower().strip()

    PROC_MAP = {
        "chrome":               ["chrome.exe"],
        "google chrome":        ["chrome.exe"],
        "notepad":              ["notepad.exe", "Notepad.exe"],
        "calculator":           ["CalculatorApp.exe", "Calculator.exe", "calc.exe"],
        "calc":                 ["CalculatorApp.exe", "Calculator.exe", "calc.exe"],
        "vscode":               ["Code.exe"],
        "vs code":              ["Code.exe"],
        "visual studio code":   ["Code.exe"],
        "spotify":              ["Spotify.exe"],
        "whatsapp":             ["WhatsApp.exe"],
        "cmd":                  ["cmd.exe"],
        "command prompt":       ["cmd.exe"],
        "powershell":           ["powershell.exe"],
        "terminal":             ["WindowsTerminal.exe"],
        "explorer":             ["explorer.exe"],
        "paint":                ["mspaint.exe"],
        "word":                 ["WINWORD.EXE"],
        "excel":                ["EXCEL.EXE"],
        "powerpoint":           ["POWERPNT.EXE"],
        "task manager":         ["Taskmgr.exe"],
        "vlc":                  ["vlc.exe"],
        "discord":              ["Discord.exe"],
        "telegram":             ["Telegram.exe"],
    }

    if app in PROC_MAP:
        targets = PROC_MAP[app]
    elif SAFE_PROCESS_NAME.fullmatch(app):
        targets = [f"{app}.exe"]
    else:
        return f"Sorry {config.USER_NAME}, '{app_name}' is not a valid application name."

    def _kill():
        for proc in targets:
            subprocess.run(["taskkill", "/f", "/im", proc, "/t"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    threading.Thread(target=_kill, daemon=True).start()
    return f"Closing {app_name.title()}, {config.USER_NAME}."

# ─── System Status ────────────────────────────────────────────────────────────

def get_system_status() -> str:
    """Return CPU, RAM, and battery info."""
    cpu = psutil.cpu_percent(interval=0.3)
    ram = psutil.virtual_memory().percent
    battery = psutil.sensors_battery()
    if battery:
        batt = f"{battery.percent:.0f}% ({'Charging' if battery.power_plugged else 'On Battery'})"
    else:
        batt = "No battery (Desktop PC)"
    return f"CPU {cpu}% | RAM {ram}% | Battery: {batt}."
