"""Design tokens for the DYD interface: colors, typography and spacing.

Every widget pulls its look from here so the whole app stays consistent.
"""
import tkinter.font as tkfont

# ─── Colors ───────────────────────────────────────────────────────────────────
BG          = "#0A0C10"   # window background
SURFACE     = "#11141A"   # cards and panels
SURFACE_2   = "#171B23"   # raised elements inside panels (inputs, rows)
SURFACE_3   = "#1E232D"   # hover state for SURFACE_2
BORDER      = "#232937"
BORDER_SOFT = "#1A1F29"

TEXT        = "#E6E9EF"
TEXT_MUTED  = "#8A93A6"
TEXT_FAINT  = "#5B6375"

ACCENT       = "#22D3EE"
ACCENT_HOVER = "#06B6D4"
ACCENT_SOFT  = "#0E2A33"   # tinted background behind accent content
ON_ACCENT    = "#04141A"   # text placed on ACCENT

SUCCESS = "#34D399"
WARNING = "#F5B544"
DANGER  = "#F87171"
DANGER_HOVER = "#EF4444"

USER_BUBBLE      = "#16333D"
ASSISTANT_BUBBLE = SURFACE_2

# Assistant state → color used by the orb, status pill and labels
STATE_COLORS = {
    "idle":       ACCENT,
    "listening":  ACCENT,
    "processing": WARNING,
    "speaking":   SUCCESS,
    "error":      DANGER,
}

# ─── Spacing & shape ──────────────────────────────────────────────────────────
SPACE_XS = 4
SPACE_SM = 8
SPACE_MD = 12
SPACE_LG = 16
SPACE_XL = 24

RADIUS_SM = 8
RADIUS_MD = 12
RADIUS_LG = 16

# ─── Typography ───────────────────────────────────────────────────────────────
_FALLBACKS = {
    "display": ["Segoe UI Variable Display", "Segoe UI", "Helvetica"],
    "text":    ["Segoe UI Variable Text", "Segoe UI", "Helvetica"],
    "mono":    ["Cascadia Mono", "Consolas", "Courier New"],
    "icons":   ["Segoe Fluent Icons", "Segoe MDL2 Assets"],
}
_resolved: dict[str, str] = {}


def family(kind: str) -> str:
    """Return the first installed font family for a role (display/text/mono/icons)."""
    if kind not in _resolved:
        installed = set(tkfont.families())
        options = _FALLBACKS[kind]
        _resolved[kind] = next((f for f in options if f in installed), options[-1])
    return _resolved[kind]


def font(size: int = 13, weight: str = "normal", kind: str = "text"):
    """CustomTkinter font tuple for the given role."""
    import customtkinter as ctk
    return ctk.CTkFont(family=family(kind), size=size, weight=weight)


def blend(color_a: str, color_b: str, t: float) -> str:
    """Mix two hex colors; t=0 gives color_a, t=1 gives color_b."""
    t = max(0.0, min(1.0, t))
    a = [int(color_a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(color_b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))
