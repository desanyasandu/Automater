# ⚡ DYD - AI Desktop Assistant (Multi-Provider: Ollama & Cloud APIs)

DYD is an ultra-fast voice & text desktop assistant inspired by J.A.R.V.I.S. It supports both **Local Offline LLMs (via Ollama)** and **Cloud APIs (Gemini, OpenAI GPT, Claude)** with instant hardware automation.

---

## 🚀 Key Features

### 1. 🦙 Multi-Provider AI Brain (Local & Cloud)
Select your desired AI in **⚙ Settings & AI Models**:
- **Local Ollama** (100% Free, Offline, Unlimited Speed): Run `qwen2.5:32b`, `qwen3.5:35b`, `llama3.2`, etc.
- **Google Gemini**: High-speed multimodal AI (`gemini-3.5-flash-lite`, `gemini-3.8-flash`).
- **OpenAI**: `gpt-4o-mini`, `gpt-4o`.
- **Anthropic Claude**: `claude-3-5-sonnet`.

### 2. ⚡ 0.001s Instant Local Execution
Commands for desktop automation are executed locally without waiting for cloud roundtrips:
- **YouTube**: *"Play Night Changes on YouTube"*, *"Play Shape of You on YouTube"*
- **WhatsApp**: *"Send message 'hi' to Dad on WhatsApp"*
- **PC Metrics**: *"Check the PC status right now"* (Instant CPU, RAM, Battery)
- **Windows Apps**: *"Open Chrome"*, *"Open Notepad"*, *"Open VS Code"*, *"Open Calculator"*
- **Volume Controls**: *"Volume up"*, *"Volume down"*, *"Mute"*

### 3. 🎙️ Fixed & Enhanced Voice Recognition
- **Auto-detected Hardware Digital Mic Array** (`Intel Smart Sound Technology`).
- **Multi-accent Speech Recognition** (`en-US` with `en-IN` fallback for South Asian phonetics).
- **Auto Wake-Word Switch**: Toggle `Auto Wake-Word (Hey DYD)` to listen in the background continuously without clicking buttons!
- **Microphone Test Diagnostic**: Test and verify your microphone in Settings with real-time transcription.

---

## 🏃 Quick Start

Double-click `run.bat` or run:
```bash
python main.py
```
