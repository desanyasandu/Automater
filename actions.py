import os
import sys
import threading
import webbrowser
import urllib.parse
import subprocess
import psutil
import pyautogui
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

def open_in_browser(url: str, force_chrome: bool = True):
    """Opens a URL in Google Chrome (if available) or default browser."""
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

def send_whatsapp(contact_or_number: str, message: str) -> str:
    """Send a WhatsApp message to a specific contact or phone number."""
    contact_clean = contact_or_number.strip()
    phone = config.get_whatsapp_contact(contact_clean)
    
    if not phone:
        digits_only = "".join(filter(str.isdigit, contact_clean))
        if len(digits_only) >= 9:
            phone = digits_only

    if not phone:
        return (
            f"Could not find phone number for '{contact_or_number}'. "
            f"Please save their number first in settings."
        )

    if phone.startswith("0"):
        phone = "94" + phone[1:]

    def _do_send():
        try:
            import pywhatkit
            pywhatkit.sendwhatmsg_instantly(
                phone_no=f"+{phone}",
                message=message,
                wait_time=10,
                tab_close=False
            )
        except Exception:
            encoded_msg = urllib.parse.quote(message)
            url = f"https://web.whatsapp.com/send?phone={phone}&text={encoded_msg}"
            open_in_browser(url, force_chrome=True)

    threading.Thread(target=_do_send, daemon=True).start()
    return f"Sending message '{message}' to {contact_or_number} on WhatsApp."

def open_application(app_name: str) -> str:
    """Open desktop apps, websites, or search Google intelligently."""
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

    # Local desktop software
    local_apps = {
        "whatsapp": "whatsapp:",
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "calc": "calc.exe",
        "vscode": "code",
        "vs code": "code",
        "visual studio code": "code",
        "cmd": "start cmd",
        "command prompt": "start cmd",
        "terminal": "start wt",
        "powershell": "start powershell",
        "file explorer": "explorer.exe",
        "explorer": "explorer.exe",
        "settings": "start ms-settings:",
        "spotify": "start spotify:",
        "task manager": "taskmgr.exe"
    }

    if app_clean in local_apps:
        target = local_apps[app_clean]
        os.system(target)
        return f"Opening {app_name}, {config.USER_NAME}."

    # Safe fallback: Search on Google in Chrome instead of Windows 'file not found' error
    return search_google(app_name, in_chrome=True)

def control_volume(action: str) -> str:
    """Control system volume: 'up', 'down', 'mute'."""
    action = action.lower()
    if "up" in action:
        for _ in range(5):
            pyautogui.press("volumeup")
        return "Increased system volume."
    elif "down" in action:
        for _ in range(5):
            pyautogui.press("volumedown")
        return "Decreased system volume."
    elif "mute" in action:
        pyautogui.press("volumemute")
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
