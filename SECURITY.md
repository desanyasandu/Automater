# Security Policy

## Reporting a vulnerability

Please **do not open a public issue** for security problems. Instead, report them privately through
GitHub's [private vulnerability reporting](https://github.com/desanyasandu/Automater/security/advisories/new).
I'll reply as soon as I can.

## API keys

- This repository never contains API keys. Every user must create and use their own.
- Keys are stored only in your local `.env` file, which is listed in `.gitignore`.
- Never commit `.env`, paste your key into an issue, or show it in a screenshot or video.
- If you think your key has leaked, revoke it with your provider immediately and create a new one.

## What the assistant can do on your PC

DYD controls your computer on your behalf, so be aware that it can:

- open and close applications (`close <app>` force-closes matching processes),
- open websites and run Google/YouTube searches,
- type and send WhatsApp messages by controlling the mouse and keyboard,
- take screenshots (saved to `Pictures/Screenshots`),
- lock your PC and change the volume.

Commands are matched locally with fixed patterns; replies from the AI provider are only displayed and
spoken, never executed. During WhatsApp automation you can move the mouse to a screen corner to abort.

## Privacy

Text sent to Gemini, OpenAI or Claude is handled under that provider's terms. Use Ollama if you want
everything to stay on your machine.
