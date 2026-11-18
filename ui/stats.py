"""Live CPU / memory / battery card."""
import customtkinter as ctk
import psutil

from ui import theme

REFRESH_MS = 2000


class SystemStats(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=theme.SURFACE_2, corner_radius=theme.RADIUS_MD,
                         border_width=1, border_color=theme.BORDER_SOFT)
        ctk.CTkLabel(self, text="SYSTEM", font=theme.font(10, "bold"),
                     text_color=theme.TEXT_FAINT).pack(anchor="w", padx=14, pady=(10, 2))
        self._rows = {name: self._make_row(name) for name in ("CPU", "Memory", "Battery")}
        psutil.cpu_percent(interval=None)  # prime the counter so the first read isn't 0
        self.after(300, self._refresh)

    def _make_row(self, name):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=(4, 0))
        top = ctk.CTkFrame(row, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(top, text=name, font=theme.font(11), text_color=theme.TEXT_MUTED,
                     height=16).pack(side="left")
        value = ctk.CTkLabel(top, text="—", font=theme.font(11, kind="mono"),
                             text_color=theme.TEXT, height=16)
        value.pack(side="right")
        bar = ctk.CTkProgressBar(row, height=4, corner_radius=2, fg_color=theme.SURFACE_3,
                                 progress_color=theme.ACCENT)
        bar.set(0)
        bar.pack(fill="x", pady=(4, 6))
        return value, bar

    def _set(self, name, pct, text):
        value, bar = self._rows[name]
        value.configure(text=text)
        bar.set(max(0, min(1, pct / 100)))
        color = theme.DANGER if pct >= 90 else theme.WARNING if pct >= 75 else theme.ACCENT
        if name == "Battery":
            color = theme.DANGER if pct <= 15 else theme.SUCCESS
        bar.configure(progress_color=color)

    def _refresh(self):
        if not self.winfo_exists():
            return
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().percent
        self._set("CPU", cpu, f"{cpu:.0f}%")
        self._set("Memory", mem, f"{mem:.0f}%")
        battery = psutil.sensors_battery()
        if battery:
            plug = " · charging" if battery.power_plugged else ""
            self._set("Battery", battery.percent, f"{battery.percent:.0f}%{plug}")
        else:
            self._set("Battery", 100, "AC power")
        self.after(REFRESH_MS, self._refresh)
