"""Live CPU / memory / battery card."""
import customtkinter as ctk
import psutil

from ui import theme

REFRESH_MS = 2000


class SystemStats(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=theme.SURFACE_2, corner_radius=theme.RADIUS_MD,
                         border_width=1, border_color=theme.BORDER_SOFT)
        self._rows = {}
        for col, name in enumerate(("CPU", "Memory", "Battery")):
            self.grid_columnconfigure(col, weight=1, uniform="stat")
            self._rows[name] = self._make_cell(col, name)
        psutil.cpu_percent(interval=None)  # prime the counter so the first read isn't 0
        self.after(300, self._refresh)

    def _make_cell(self, col, name):
        cell = ctk.CTkFrame(self, fg_color="transparent")
        cell.grid(row=0, column=col, sticky="ew", padx=(12 if col == 0 else 6, 12 if col == 2 else 6), pady=10)
        ctk.CTkLabel(cell, text=name.upper(), font=theme.font(9, "bold"), text_color=theme.TEXT_FAINT,
                     height=12, anchor="w").pack(fill="x")
        value = ctk.CTkLabel(cell, text="—", font=theme.font(15, "bold", "display"),
                             text_color=theme.TEXT, height=22, anchor="w")
        value.pack(fill="x")
        bar = ctk.CTkProgressBar(cell, height=3, corner_radius=2, fg_color=theme.SURFACE_3,
                                 progress_color=theme.ACCENT)
        bar.set(0)
        bar.pack(fill="x", pady=(4, 0))
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
            self._set("Battery", battery.percent, f"{battery.percent:.0f}%{'⚡' if battery.power_plugged else ''}")
        else:
            self._set("Battery", 100, "AC")
        self.after(REFRESH_MS, self._refresh)
