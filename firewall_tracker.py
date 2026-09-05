import customtkinter as ctk
import time
import os
import sys
import json
from typing import List
from roblox_console import RobloxConsoleStreamer

# --- Load Settings ---
SETTINGS_FILE = "firewall_settings.json"
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"theme": "Default (Blue)"}

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f)

app_settings = load_settings()

ctk.set_default_color_theme("blue")
if app_settings["theme"] == "Catppuccin":
    theme = ctk.ThemeManager.theme
    theme["CTk"]["fg_color"] = ["#EFF1F5", "#1E1E2E"]
    theme["CTkToplevel"]["fg_color"] = ["#EFF1F5", "#1E1E2E"]
    theme["CTkFrame"]["fg_color"] = ["#E6E9EF", "#181825"]
    theme["CTkFrame"]["top_fg_color"] = ["#DCE0E8", "#11111B"]
    theme["CTkFrame"]["border_color"] = ["#CCD0DA", "#313244"]
    theme["CTkButton"]["fg_color"] = ["#8839EF", "#CBA6F7"]
    theme["CTkButton"]["hover_color"] = ["#7287FD", "#89B4FA"]
    theme["CTkButton"]["text_color"] = ["#EFF1F5", "#11111B"]
    theme["CTkLabel"]["text_color"] = ["#4C4F69", "#CDD6F4"]
    theme["CTkOptionMenu"]["fg_color"] = ["#8839EF", "#CBA6F7"]
    theme["CTkOptionMenu"]["button_color"] = ["#7287FD", "#89B4FA"]
    theme["CTkOptionMenu"]["button_hover_color"] = ["#1E66F5", "#B4BEFE"]
    theme["CTkOptionMenu"]["text_color"] = ["#EFF1F5", "#11111B"]
elif app_settings["theme"] == "Custom Firewall":
    theme = ctk.ThemeManager.theme
    theme["CTk"]["fg_color"] = ["#F2F2F2", "#1A0F0D"]
    theme["CTkToplevel"]["fg_color"] = ["#F2F2F2", "#1A0F0D"]
    theme["CTkFrame"]["fg_color"] = ["#E5E5E5", "#261311"]
    theme["CTkFrame"]["top_fg_color"] = ["#DBDBDB", "#331613"]
    theme["CTkFrame"]["border_color"] = ["#CCCCCC", "#4A1D18"]
    theme["CTkButton"]["fg_color"] = ["#FF5D00", "#E63900"]
    theme["CTkButton"]["hover_color"] = ["#D94F00", "#FF7326"]
    theme["CTkButton"]["text_color"] = ["#FFFFFF", "#FFFFFF"]
    theme["CTkLabel"]["text_color"] = ["#11111B", "#FAD8D4"]
    theme["CTkOptionMenu"]["fg_color"] = ["#FF5D00", "#E63900"]
    theme["CTkOptionMenu"]["button_color"] = ["#D94F00", "#CC3300"]
    theme["CTkOptionMenu"]["button_hover_color"] = ["#B34100", "#4D79FF"]
    theme["CTkOptionMenu"]["text_color"] = ["#FFFFFF", "#FFFFFF"]

ctk.set_appearance_mode("dark")

import math
from typing import List

class Run:
    def __init__(self, t: float):
        self.time = t
        self.penalty = None  # None or "DNF"

    @property
    def value(self):
        return float('inf') if self.penalty == "DNF" else self.time

class StatsManager:
    def __init__(self):
        self.runs: List[Run] = []

    def add_time(self, t: float):
        self.runs.append(Run(t))

    def get_best_single(self):
        valid = [r.time for r in self.runs if r.penalty != "DNF"]
        if not valid:
            return None
        return min(valid)

    def get_session_mean(self):
        valid = [r.time for r in self.runs if r.penalty != "DNF"]
        if not valid:
            return None
        return sum(valid) / len(valid)

    def calculate_ao(self, n: int):
        if len(self.runs) < n:
            return None
        recent = [r.value for r in self.runs[-n:]]
        recent.sort()
        drop_count = math.ceil(n * 0.05)
        kept = recent[drop_count : -drop_count] if drop_count > 0 else recent
        if not kept:
            return None
        if float('inf') in kept:
            return float('inf')
        return sum(kept) / len(kept)

    def calculate_mo(self, n: int):
        if len(self.runs) < n:
            return None
        recent = [r.value for r in self.runs[-n:]]
        if float('inf') in recent:
            return float('inf')
        return sum(recent) / len(recent)

def format_time(t) -> str:
    if t is None:
        return "--.---"
    if t == float('inf'):
        return "DNF"
    if t < 60:
        return f"{t:.3f}"
    else:
        minutes = int(t // 60)
        seconds = t % 60
        return f"{minutes}:{seconds:06.3f}"


class TimerWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Timer")
        saved = app_settings.get("geometries", {}).get("timer")
        self.geometry(saved if saved else "500x200")
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.time_label = ctk.CTkLabel(self, text="0.000", font=("Consolas", 120, "bold"))
        self.time_label.pack(expand=True, fill="both")
        self.attributes("-topmost", True)
        self.bind("<Configure>", self.on_resize)

    def on_closing(self):
        app_settings.setdefault("geometries", {})["timer"] = self.geometry()
        save_settings(app_settings)
        self.destroy()

    def on_resize(self, event):
        if event.widget == self:
            h_size = int(event.height * 0.6)
            w_size = int(event.width * 0.24)
            new_size = max(10, min(h_size, w_size))
            self.time_label.configure(font=("Consolas", new_size, "bold"))


class DebugWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Debug Console")
        saved = app_settings.get("geometries", {}).get("debug")
        self.geometry(saved if saved else "600x400")
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.textbox = ctk.CTkTextbox(self, state="disabled", font=("Consolas", 12))
        self.textbox.pack(expand=True, fill="both", padx=10, pady=10)

        # Pull existing logs
        self.log_message("Debug window opened.\n")
        for log in parent.debug_logs:
            self.log_message(log)

    def on_closing(self):
        app_settings.setdefault("geometries", {})["debug"] = self.geometry()
        save_settings(app_settings)
        self.destroy()

    def log_message(self, msg):
        self.textbox.configure(state="normal")
        self.textbox.insert("end", msg + "\n")
        self.textbox.see("end")
        self.textbox.configure(state="disabled")


class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Settings")
        saved = app_settings.get("geometries", {}).get("settings")
        self.geometry(saved if saved else "300x250")
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Theme:", font=("Arial", 14)).grid(row=0, column=0, padx=10, pady=20, sticky="e")
        
        self.theme_menu = ctk.CTkOptionMenu(self, values=["Default (Blue)", "Catppuccin", "Custom Firewall"], command=self.change_theme)
        self.theme_menu.grid(row=0, column=1, padx=10, pady=20, sticky="w")
        self.theme_menu.set(app_settings["theme"])

        self.restart_lbl = ctk.CTkLabel(self, text="", text_color="red", font=("Arial", 12))
        self.restart_lbl.grid(row=1, column=0, columnspan=2)

        self.debug_btn = ctk.CTkButton(self, text="Open Debug Console", command=self.open_debug, fg_color="gray", hover_color="darkgray")
        self.debug_btn.grid(row=2, column=0, columnspan=2, pady=20)

    def on_closing(self):
        app_settings.setdefault("geometries", {})["settings"] = self.geometry()
        save_settings(app_settings)
        self.destroy()

    def change_theme(self, choice):
        app_settings["theme"] = choice
        save_settings(app_settings)
        
        if hasattr(self, 'restart_lbl'):
            self.restart_lbl.configure(text="Please close and reopen the app to apply the theme!")
            
        import tkinter.messagebox
        tkinter.messagebox.showinfo("Restart Required", "Theme saved!\n\nPlease close and reopen Firewall Tracker to apply the new theme.")

    def open_debug(self):
        self.parent.open_debug_window()


class FirewallTrackerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Firewall Tracker")
        saved = app_settings.get("geometries", {}).get("main")
        self.geometry(saved if saved else "800x250")

        self.stats = StatsManager()
        self.debug_logs = []
        self.debug_window = None
        self.timer_window = None

        self.timer_state = "STOPPED"
        self.start_time = 0.0
        self.elapsed_time = 0.0 
        
        self.stats_visible = False

        self.setup_ui()
        self.setup_streamer()

        self.bind("<space>", self.manual_trigger)
        self.update_timer_loop()

    def log_debug(self, msg):
        self.debug_logs.append(msg)
        if len(self.debug_logs) > 100:
            self.debug_logs.pop(0)
        if self.debug_window and self.debug_window.winfo_exists():
            self.debug_window.log_message(msg)

    def open_debug_window(self):
        if self.debug_window is None or not self.debug_window.winfo_exists():
            self.debug_window = DebugWindow(self)
        else:
            self.debug_window.focus()

    def open_timer_window(self):
        if self.timer_window is None or not self.timer_window.winfo_exists():
            self.timer_window = TimerWindow(self)
        else:
            self.timer_window.focus()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1) 
        self.grid_rowconfigure(1, weight=0) # Toggle button row
        self.grid_rowconfigure(2, weight=3) # Stats

        # --- Top Section ---
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.top_frame.bind("<Configure>", self.on_top_frame_resize)

        self.settings_btn = ctk.CTkButton(self.top_frame, text="⚙", width=36, height=36, font=("Arial", 20), command=self.open_settings)
        self.settings_btn.place(relx=1.0, rely=0.0, anchor="ne")

        self.popout_btn = ctk.CTkButton(self.top_frame, text="↗️ Popout", width=36, height=36, font=("Arial", 14, "bold"), command=self.open_timer_window)
        self.popout_btn.place(relx=0.0, rely=0.0, anchor="nw")

        self.time_label = ctk.CTkLabel(self.top_frame, text="0.000", font=("Consolas", 80, "bold"))
        self.time_label.pack(expand=True, pady=(20, 0))

        self.ao5_label = ctk.CTkLabel(self.top_frame, text="AO5: --.---", font=("Consolas", 24, "underline"))
        self.ao5_label.pack()

        # --- Actions Row ---
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.grid(row=1, column=0, pady=(0, 10))

        self.btn_ok = ctk.CTkButton(self.action_frame, text="✔ OK", width=60, height=35, font=("Arial", 14, "bold"), fg_color="green", hover_color="darkgreen", command=self.set_ok)
        self.btn_ok.pack(side="left", padx=5)

        self.btn_dnf = ctk.CTkButton(self.action_frame, text="🚫 DNF", width=60, height=35, font=("Arial", 14, "bold"), fg_color="red", hover_color="darkred", command=self.set_dnf)
        self.btn_dnf.pack(side="left", padx=5)

        self.btn_del = ctk.CTkButton(self.action_frame, text="🗑️ DEL", width=60, height=35, font=("Arial", 14, "bold"), fg_color="gray", hover_color="darkgray", command=self.delete_last)
        self.btn_del.pack(side="left", padx=5)

        self.stats_toggle_btn = ctk.CTkButton(self.action_frame, text="Stats ▼", width=120, height=35, font=("Arial", 16, "bold"), fg_color=("gray75", "gray25"), hover_color=("gray70", "gray30"), command=self.toggle_stats)
        self.stats_toggle_btn.pack(side="left", padx=5)

        # --- Stats Section ---
        self.stats_frame = ctk.CTkFrame(self)
        # We don't grid it initially, so it is hidden
        
        self.stats_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.stats_frame.grid_rowconfigure((0, 1), weight=1)

        # 1. Current Stats
        self.current_stats_frame = ctk.CTkFrame(self.stats_frame)
        self.current_stats_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(self.current_stats_frame, text="Current Stats", font=("Arial", 16, "bold")).pack(anchor="w", padx=5, pady=5)
        self.lbl_curr_mo3 = ctk.CTkLabel(self.current_stats_frame, text="MO3: --.---", font=("Consolas", 14))
        self.lbl_curr_mo3.pack(anchor="w", padx=10)
        self.lbl_curr_ao5 = ctk.CTkLabel(self.current_stats_frame, text="AO5: --.---", font=("Consolas", 14))
        self.lbl_curr_ao5.pack(anchor="w", padx=10)
        self.lbl_curr_ao12 = ctk.CTkLabel(self.current_stats_frame, text="AO12: --.---", font=("Consolas", 14))
        self.lbl_curr_ao12.pack(anchor="w", padx=10)
        self.lbl_curr_ao100 = ctk.CTkLabel(self.current_stats_frame, text="AO100: --.---", font=("Consolas", 14))
        self.lbl_curr_ao100.pack(anchor="w", padx=10)

        # 2. Firewall Count
        self.count_frame = ctk.CTkFrame(self.stats_frame)
        self.count_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(self.count_frame, text="Firewall Count", font=("Arial", 16, "bold")).pack(anchor="w", padx=5, pady=5)
        self.lbl_count = ctk.CTkLabel(self.count_frame, text="0", font=("Consolas", 32))
        self.lbl_count.pack(expand=True)

        # 3. Session Mean
        self.mean_frame = ctk.CTkFrame(self.stats_frame)
        self.mean_frame.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(self.mean_frame, text="Session Mean", font=("Arial", 16, "bold")).pack(anchor="w", padx=5, pady=5)
        self.lbl_mean = ctk.CTkLabel(self.mean_frame, text="--.---", font=("Consolas", 32))
        self.lbl_mean.pack(expand=True)

        # 4. Best Single
        self.best_single_frame = ctk.CTkFrame(self.stats_frame)
        self.best_single_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(self.best_single_frame, text="Best Single", font=("Arial", 16, "bold")).pack(anchor="w", padx=5, pady=5)
        self.lbl_best_single = ctk.CTkLabel(self.best_single_frame, text="--.---", font=("Consolas", 32))
        self.lbl_best_single.pack(expand=True)

    def on_top_frame_resize(self, event):
        if event.widget == self.top_frame:
            h_size = int(event.height * 0.45)
            w_size = int(event.width * 0.12)
            new_size = max(10, min(h_size, w_size))
            self.time_label.configure(font=("Consolas", new_size, "bold"))

    def toggle_stats(self):
        current_width = self.winfo_width()
        pos_x = self.winfo_x()
        pos_y = self.winfo_y()
        if self.stats_visible:
            self.stats_frame.grid_forget()
            self.stats_toggle_btn.configure(text="Stats ▼")
            self.geometry(f"{current_width}x250+{pos_x}+{pos_y}")
            self.stats_visible = False
        else:
            self.stats_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
            self.stats_toggle_btn.configure(text="Stats ▲")
            self.geometry(f"{current_width}x600+{pos_x}+{pos_y}")
            self.stats_visible = True

    def open_settings(self):
        SettingsWindow(self)

    def setup_streamer(self):
        self.streamer = RobloxConsoleStreamer(self.on_roblox_log)
        self.streamer.start()

    def set_ok(self):
        if self.stats.runs and self.timer_state == "STOPPED":
            self.stats.runs[-1].penalty = None
            self.update_stats_ui()

    def set_dnf(self):
        if self.stats.runs and self.timer_state == "STOPPED":
            self.stats.runs[-1].penalty = "DNF"
            self.update_stats_ui()

    def delete_last(self):
        if self.stats.runs and self.timer_state == "STOPPED":
            self.stats.runs.pop()
            self.update_stats_ui()

    def on_roblox_log(self, time_str: str, level: str, message: str):
        msg_lower = message.lower().strip()
        self.log_debug(f"[{time_str}] {message}")
        
        # Teleport / New Server / Lobby
        if "joingame" in msg_lower or "connecting to server" in msg_lower:
            self.after(0, self.clear_console)
            self.log_debug("-> TRIGGER: NEW SERVER (CLEARED)")
            return

        # Reset Conditions
        if "requesting admin command: kill with args" in msg_lower or \
           "room name: start" in msg_lower or \
           "portalcomponent" in msg_lower or \
           "started portal component" in msg_lower:
            self.after(0, self.reset_timer)
            self.log_debug("-> TRIGGER: RESET")
            return

        # Start Condition
        if "warning: nil" in msg_lower and "room name:" not in msg_lower: 
            self.after(0, self.start_timer)
            self.log_debug("-> TRIGGER: START")
            
        # Pause Condition
        elif "fired" in msg_lower:
            self.after(0, self.pause_timer)
            self.log_debug("-> TRIGGER: PAUSE")
            
        # Resume Condition
        elif "can equip changed false" in msg_lower:
            self.after(0, self.resume_timer)
            self.log_debug("-> TRIGGER: RESUME")
            
        # Stop Condition
        elif "setting jump power to 0" in msg_lower:
            self.after(0, self.stop_timer)
            self.log_debug("-> TRIGGER: STOP")

    def clear_console(self):
        self.debug_logs.clear()
        if self.debug_window and self.debug_window.winfo_exists():
            self.debug_window.textbox.configure(state="normal")
            self.debug_window.textbox.delete("1.0", "end")
            self.debug_window.textbox.configure(state="disabled")
            self.debug_window.log_message("Console cleared (New server/teleport detected).\n")

    def manual_trigger(self, event=None):
        if self.timer_state == "STOPPED":
            self.start_timer()
        elif self.timer_state in ("RUNNING", "PAUSED"):
            self.stop_timer()

    def set_time_color(self, color):
        self.time_label.configure(text_color=color)
        if self.timer_window and self.timer_window.winfo_exists():
            self.timer_window.time_label.configure(text_color=color)

    def set_time_text(self, text):
        self.time_label.configure(text=text)
        if self.timer_window and self.timer_window.winfo_exists():
            self.timer_window.time_label.configure(text=text)

    def reset_timer(self):
        self.timer_state = "STOPPED"
        self.start_time = 0.0
        self.elapsed_time = 0.0
        self.set_time_text("0.000")
        self.set_time_color("white")

    def start_timer(self):
        if self.timer_state == "STOPPED":
            self.start_time = time.perf_counter()
            self.elapsed_time = 0.0
            self.timer_state = "RUNNING"
            self.set_time_color("white")

    def pause_timer(self):
        if self.timer_state == "RUNNING":
            self.elapsed_time += time.perf_counter() - self.start_time
            self.timer_state = "PAUSED"
            self.set_time_color("orange")

    def resume_timer(self):
        if self.timer_state == "PAUSED":
            self.start_time = time.perf_counter()
            self.timer_state = "RUNNING"
            self.set_time_color("white")

    def stop_timer(self):
        if self.timer_state == "RUNNING" or self.timer_state == "PAUSED":
            if self.timer_state == "RUNNING":
                self.elapsed_time += time.perf_counter() - self.start_time
            self.timer_state = "STOPPED"
            
            final_time = self.elapsed_time
            self.stats.add_time(final_time)
            self.update_stats_ui()
            self.set_time_color("green")

    def update_timer_loop(self):
        if self.timer_state == "RUNNING":
            current = self.elapsed_time + (time.perf_counter() - self.start_time)
            self.set_time_text(format_time(current))
        elif self.timer_state == "PAUSED":
            self.set_time_text(format_time(self.elapsed_time))
            
        self.after(10, self.update_timer_loop)

    def update_stats_ui(self):
        if self.stats.runs and self.timer_state == "STOPPED":
            latest = self.stats.runs[-1]
            self.set_time_text(format_time(latest.value))
            if latest.penalty == "DNF":
                self.set_time_color("red")
            else:
                self.set_time_color("green")
        elif not self.stats.runs and self.timer_state == "STOPPED":
            self.set_time_text("0.000")
            self.set_time_color("white")
        
        mo3 = self.stats.calculate_mo(3)
        ao5 = self.stats.calculate_ao(5)
        ao12 = self.stats.calculate_ao(12)
        ao100 = self.stats.calculate_ao(100)
        
        self.ao5_label.configure(text=f"AO5: {format_time(ao5)}")
        self.lbl_curr_mo3.configure(text=f"MO3: {format_time(mo3)}")
        self.lbl_curr_ao5.configure(text=f"AO5: {format_time(ao5)}")
        self.lbl_curr_ao12.configure(text=f"AO12: {format_time(ao12)}")
        self.lbl_curr_ao100.configure(text=f"AO100: {format_time(ao100)}")
        
        self.lbl_count.configure(text=str(len(self.stats.runs)))
        self.lbl_mean.configure(text=format_time(self.stats.get_session_mean()))
        self.lbl_best_single.configure(text=format_time(self.stats.get_best_single()))

    def destroy(self):
        app_settings.setdefault("geometries", {})["main"] = self.geometry()
        if self.timer_window and self.timer_window.winfo_exists():
            app_settings["geometries"]["timer"] = self.timer_window.geometry()
        if self.debug_window and self.debug_window.winfo_exists():
            app_settings["geometries"]["debug"] = self.debug_window.geometry()
        save_settings(app_settings)
        self.streamer.stop()
        super().destroy()


if __name__ == "__main__":
    app = FirewallTrackerApp()
    app.mainloop()
