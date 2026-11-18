import os
import re
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "DYD")
USER_NAME = os.getenv("USER_NAME", "Sir")

def get_setting(key: str, default: str = "") -> str:
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    return os.getenv(key, default)

def save_setting(key: str, value: str):
    """Saves or updates a key-value pair in .env file."""
    # Strip line breaks so a pasted value can't inject extra lines/settings into .env
    key = re.sub(r"[^A-Za-z0-9_]", "", key)
    value = value.replace("\r", "").replace("\n", "")
    lines = []
    found = False
    if ENV_PATH.exists():
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
    new_lines = []
    for line in lines:
        if line.strip().startswith(f"{key}="):
            new_lines.append(f"{key}={value.strip()}\n")
            found = True
        else:
            new_lines.append(line)
            
    if not found:
        new_lines.append(f"{key}={value.strip()}\n")
        
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
        
    load_dotenv(dotenv_path=ENV_PATH, override=True)

# Provider getters and setters
def get_ai_provider() -> str:
    return get_setting("AI_PROVIDER", "GEMINI").upper()

def set_ai_provider(provider: str):
    save_setting("AI_PROVIDER", provider.upper())

def get_api_key() -> str:
    return get_setting("GEMINI_API_KEY", "")

def save_api_key(new_key: str):
    save_setting("GEMINI_API_KEY", new_key)

def get_gemini_model() -> str:
    return get_setting("GEMINI_MODEL", "gemini-2.5-flash")

def get_openai_key() -> str:
    return get_setting("OPENAI_API_KEY", "")

def save_openai_key(key: str):
    save_setting("OPENAI_API_KEY", key)

def get_openai_model() -> str:
    return get_setting("OPENAI_MODEL", "gpt-4o-mini")

def get_claude_key() -> str:
    return get_setting("CLAUDE_API_KEY", "")

def save_claude_key(key: str):
    save_setting("CLAUDE_API_KEY", key)

def get_claude_model() -> str:
    return get_setting("CLAUDE_MODEL", "claude-haiku-5-5")

DEFAULT_OLLAMA_URL = "http://localhost:11434"

def get_ollama_url() -> str:
    url = get_setting("OLLAMA_URL", DEFAULT_OLLAMA_URL).strip()
    # Only plain http(s) endpoints - never file:// or other schemes
    if not re.match(r"^https?://[^\s/]+", url, re.IGNORECASE):
        return DEFAULT_OLLAMA_URL
    return url

def save_ollama_url(url: str):
    save_setting("OLLAMA_URL", url)

def get_ollama_model() -> str:
    return get_setting("OLLAMA_MODEL", "qwen2.5:32b")

def save_ollama_model(model: str):
    save_setting("OLLAMA_MODEL", model)

# WhatsApp contact management
def get_whatsapp_contact(name: str):
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    key = name.strip().upper().replace(" ", "_")
    return os.getenv(key, "")

def save_whatsapp_contact(name: str, phone: str):
    key = name.strip().upper().replace(" ", "_")
    clean_phone = phone.replace("+", "").replace(" ", "").replace("-", "").strip()
    save_setting(key, clean_phone)
