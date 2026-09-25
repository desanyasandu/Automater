import os
import sys
import threading
import webbrowser
import urllib.parse
import subprocess
import psutil
import pyautogui
import config

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
            webbrowser.open(url)

    # Run in background so Gemini does not wait 15 seconds to reply
    threading.Thread(target=_do_play, daemon=True).start()
    return f"Playing '{clean_query}' on YouTube now."

def send_whatsapp(contact_or_number: str, message: str) -> str:
    """Send a WhatsApp message to a specific contact or phone number."""
    contact_clean = contact_or_number.strip()
    phone = config.get_whatsapp_contact(contact_clean)
    
    # If not mapped by name, check if it's already a numeric phone number
    if not phone:
        digits_only = "".join(filter(str.isdigit, contact_clean))
        if len(digits_only) >= 9:
            phone = digits_only

    if not phone:
        return (
            f"Could not find phone number for '{contact_or_number}'. "
            f"Please save their number first in settings or say 'Save contact [Name] as [Number]'."
        )

    # Clean country code: ensure it has standard international format without '+'
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
            webbrowser.open(url)

    threading.Thread(target=_do_send, daemon=True).start()
    return f"Sending message '{message}' to {contact_or_number} on WhatsApp."

def open_application(app_name: str) -> str:
    """Open a desktop application, website, or system tool."""
    app_lower = app_name.lower().strip()

    # Pre-mapped common apps
    app_map = {
        "chrome": "start chrome",
        "google chrome": "start chrome",
        "youtube": "https://www.youtube.com",
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

    if app_lower in app_map:
        target = app_map[app_lower]
        if target.startswith("http"):
            webbrowser.open(target)
            return f"Opened {app_name} in your browser."
        else:
            os.system(target)
            return f"Opened {app_name}."

    # General launch attempt
    try:
        os.system(f"start {app_lower}")
        return f"Attempting to launch {app_name}."
    except Exception as e:
        return f"Failed to open {app_name}: {str(e)}"

def search_google(query: str) -> str:
    """Search Google for information."""
    encoded = urllib.parse.quote(query)
    webbrowser.open(f"https://www.google.com/search?q={encoded}")
    return f"Searched Google for '{query}'."

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
