import os
import sys
import time
import threading
import webbrowser
import urllib.parse
import subprocess
import ctypes
from pathlib import Path
import psutil
import pyautogui
pyautogui.FAILSAFE = False
import pyperclip
import config

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

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
    "linkedin": "https://www.linkedin.com"
}

# Windows Virtual-Key Codes for Volume
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF

def open_in_browser(url: str, force_chrome: bool = True):
    """Opens a URL in Google Chrome (if available) or default browser non-blocking."""
    def _run():
        if force_chrome and os.path.exists(CHROME_PATH):
            subprocess.Popen([CHROME_PATH, url])
        else:
            try:
                if os.path.exists(CHROME_PATH):
                    subprocess.Popen([CHROME_PATH, url])
                else:
                    webbrowser.open(url)
            except Exception:
                webbrowser.open(url)
    threading.Thread(target=_run, daemon=True).start()

def search_google(query: str, in_chrome: bool = True) -> str:
    """Search Google for any topic or question in Chrome."""
    clean_query = query.strip()
    encoded = urllib.parse.quote(clean_query)
    url = f"https://www.google.com/search?q={encoded}"
    open_in_browser(url, force_chrome=in_chrome)
    return f"Searching '{clean_query}' on Google, {config.USER_NAME}."

def play_youtube(query: str) -> str:
    """Search and play a video or song on YouTube."""
    clean_query = query.strip()
    
    def _do_play():
        try:
            import pywhatkit
            pywhatkit.playonyt(clean_query)
        except Exception:
            encoded = urllib.parse.quote(clean_query)
            url = f"https://www.youtube.com/results?search_query={encoded}"
            open_in_browser(url, force_chrome=True)

    threading.Thread(target=_do_play, daemon=True).start()
    return f"Playing '{clean_query}' on YouTube now."

def media_control(action: str) -> str:
    """Pause, resume, or toggle fullscreen for media."""
    act = action.lower()
    if any(k in act for k in ["pause", "stop", "resume", "play"]):
        ctypes.windll.user32.keybd_event(0xB3, 0, 0, 0) # VK_MEDIA_PLAY_PAUSE
        time.sleep(0.02)
        ctypes.windll.user32.keybd_event(0xB3, 0, 2, 0)
        return f"Toggled media playback, {config.USER_NAME}."
    elif "fullscreen" in act:
        pyautogui.press("f")
        return f"Toggled fullscreen, {config.USER_NAME}."
    return "Media control executed."

def send_whatsapp(contact_or_number: str, message: str) -> str:
    """
    Automates WhatsApp Desktop directly by contact name (or number)
    just like in the demo video.
    """
    contact_clean = contact_or_number.strip()
    clean_msg = message.strip()

    def _do_send():
        # 1. Bring WhatsApp Desktop to front
        os.system("start whatsapp:")
        time.sleep(1.8)

        # 2. Focus search bar (Ctrl + F)
        pyautogui.hotkey("ctrl", "f")
        time.sleep(0.4)

        # Clear previous search
        pyautogui.hotkey("ctrl", "a")
        pyautogui.press("backspace")
        time.sleep(0.2)

        # 3. Paste contact name via clipboard
        pyperclip.copy(contact_clean)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(1.2)

        # 4. Select the first matched contact
        pyautogui.press("down")
        time.sleep(0.2)
        pyautogui.press("enter")
        time.sleep(0.8)

        # 5. Type and send message
        pyperclip.copy(clean_msg)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.4)
        pyautogui.press("enter")

    threading.Thread(target=_do_send, daemon=True).start()
    return f"Sending reply to {contact_clean} on WhatsApp, {config.USER_NAME}."

def open_application(app_name: str) -> str:
    """Open desktop apps, websites, or search Google non-blocking."""
    app_clean = app_name.lower().strip()

    # Browser launch
    if app_clean in ["chrome", "google chrome", "browser"]:
        open_in_browser("https://www.google.com", force_chrome=True)
        return f"Opening Google Chrome, {config.USER_NAME}."

    # Known websites
    if app_clean in COMMON_WEBSITES:
        url = COMMON_WEBSITES[app_clean]
        open_in_browser(url, force_chrome=True)
        return f"Opening {app_name.title()} in Chrome, {config.USER_NAME}."

    # Direct URL with domain
    if any(app_clean.endswith(ext) for ext in [".com", ".org", ".net", ".io", ".lk", ".ai", ".co", ".app"]):
        url = f"https://{app_clean}" if not app_clean.startswith("http") else app_clean
        open_in_browser(url, force_chrome=True)
        return f"Opening {app_clean} in Chrome, {config.USER_NAME}."

    # Non-blocking Local Desktop Software
    if app_clean in ["notepad", "note"]:
        subprocess.Popen("notepad.exe", shell=True)
        return f"Opening Notepad, {config.USER_NAME}."

    if app_clean in ["calculator", "calc"]:
        subprocess.Popen("calc.exe", shell=True)
        return f"Opening Calculator, {config.USER_NAME}."

    if app_clean in ["vscode", "vs code", "code", "visual studio code"]:
        subprocess.Popen("code", shell=True)
        return f"Opening Visual Studio Code, {config.USER_NAME}."

    if app_clean in ["spotify", "music"]:
        def _launch_spotify():
            try:
                os.system("start spotify:")
            except Exception:
                open_in_browser("https://open.spotify.com", force_chrome=True)
        threading.Thread(target=_launch_spotify, daemon=True).start()
        return f"Opening Spotify, {config.USER_NAME}."

    if app_clean in ["whatsapp"]:
        os.system("start whatsapp:")
        return f"Opening WhatsApp, {config.USER_NAME}."

    if app_clean in ["cmd", "command prompt"]:
        subprocess.Popen("start cmd", shell=True)
        return f"Opening Command Prompt, {config.USER_NAME}."

    if app_clean in ["terminal", "powershell"]:
        subprocess.Popen("start powershell", shell=True)
        return f"Opening PowerShell, {config.USER_NAME}."

    if app_clean in ["file explorer", "explorer"]:
        subprocess.Popen("explorer.exe", shell=True)
        return f"Opening File Explorer, {config.USER_NAME}."

    if app_clean in ["settings", "windows settings"]:
        subprocess.Popen("start ms-settings:", shell=True)
        return f"Opening Windows Settings, {config.USER_NAME}."

    if app_clean in ["task manager", "taskmgr"]:
        subprocess.Popen("taskmgr.exe", shell=True)
        return f"Opening Task Manager, {config.USER_NAME}."

    # Safe fallback: Search on Google in Chrome instead of Windows error
    return search_google(app_name, in_chrome=True)

def close_application(app_name: str) -> str:
    """Closes running desktop applications cleanly."""
    app_clean = app_name.lower().strip()
    proc_map = {
        "chrome": ["chrome.exe"],
        "google chrome": ["chrome.exe"],
        "notepad": ["Notepad.exe", "notepad.exe"],
        "calculator": ["CalculatorApp.exe", "Calculator.exe", "calc.exe"],
        "calc": ["CalculatorApp.exe", "Calculator.exe", "calc.exe"],
        "vscode": ["Code.exe"],
        "vs code": ["Code.exe"],
        "visual studio code": ["Code.exe"],
        "spotify": ["Spotify.exe"],
        "whatsapp": ["WhatsApp.exe"],
        "cmd": ["cmd.exe"],
        "powershell": ["powershell.exe"]
    }

    targets = proc_map.get(app_clean, [f"{app_clean}.exe"])
    def _do_kill():
        for t in targets:
            os.system(f"taskkill /f /im {t} /t >nul 2>&1")
    threading.Thread(target=_do_kill, daemon=True).start()
    return f"Closed {app_name}, {config.USER_NAME}."

def take_screenshot() -> str:
    """Takes a screenshot and saves it to user's Pictures/Screenshots folder."""
    def _do_shot():
        # 1. Native Windows Win + PrtScn hardware event
        ctypes.windll.user32.keybd_event(0x5B, 0, 0, 0) # Win down
        ctypes.windll.user32.keybd_event(0x2C, 0, 0, 0) # PrtScn down
        time.sleep(0.05)
        ctypes.windll.user32.keybd_event(0x2C, 0, 2, 0) # PrtScn up
        ctypes.windll.user32.keybd_event(0x5B, 0, 2, 0) # Win up
        
        # 2. Also save timestamped PNG file
        try:
            from PIL import ImageGrab
            user_pictures = Path.home() / "Pictures" / "Screenshots"
            user_pictures.mkdir(parents=True, exist_ok=True)
            filename = f"Screenshot_{time.strftime('%Y%m%d_%H%M%S')}.png"
            filepath = user_pictures / filename
            img = ImageGrab.grab()
            img.save(str(filepath))
        except Exception:
            pass

    threading.Thread(target=_do_shot, daemon=True).start()
    return f"Screenshot captured and saved to Pictures/Screenshots, {config.USER_NAME}."

def lock_pc() -> str:
    """Locks the Windows computer."""
    def _do_lock():
        time.sleep(0.3)
        ctypes.windll.user32.LockWorkStation()
    threading.Thread(target=_do_lock, daemon=True).start()
    return f"Locking computer workstation now, {config.USER_NAME}."

def control_volume(action: str) -> str:
    """Control system volume: 'up', 'down', 'mute' via hardware keystrokes."""
    act = action.lower()
    if "up" in act or "increase" in act or "raise" in act or "louder" in act:
        for _ in range(6):
            ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, 0, 0)
            time.sleep(0.01)
            ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, 2, 0)
            time.sleep(0.01)
        return "Increased system volume."
    elif "down" in act or "decrease" in act or "lower" in act or "quieter" in act:
        for _ in range(6):
            ctypes.windll.user32.keybd_event(VK_VOLUME_DOWN, 0, 0, 0)
            time.sleep(0.01)
            ctypes.windll.user32.keybd_event(VK_VOLUME_DOWN, 0, 2, 0)
            time.sleep(0.01)
        return "Decreased system volume."
    elif "mute" in act or "unmute" in act:
        ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 0, 0)
        time.sleep(0.01)
        ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 2, 0)
        return "Toggled system mute."
    return "Unknown volume command."

def get_system_status() -> str:
    """Get PC battery, CPU, and RAM metrics."""
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory().percent
    
    battery_info = "No battery detected (Desktop PC)"
    battery = psutil.sensors_battery()
    if battery:
        percent = battery.percent
        plugged = "Plugged in" if battery.power_plugged else "Running on battery"
        battery_info = f"{percent}% ({plugged})"

    return f"System Status: CPU usage is {cpu}%, RAM usage is {ram}%, Battery is {battery_info}."
