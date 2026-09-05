import customtkinter as ctk
import time
import os
import sys
import json
import threading
import urllib.request
import shutil
from typing import List
from roblox_console import RobloxConsoleStreamer

CURRENT_VERSION = "v1.0.2"
GITHUB_API_URL = "https://api.github.com/repos/Dylan2228/firewall-tracker/releases/latest"

# --- App Data Paths ---
APP_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "FirewallTracker")
os.makedirs(APP_DIR, exist_ok=True)

SETTINGS_FILE = os.path.join(APP_DIR, "firewall_settings.json")

# --- Load Settings ---
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {
        "theme": "Default (Blue)",
        "keybind_ok": "<Control-1>",
        "keybind_dnf": "<Control-2>",
        "keybind_delete": "<Control-3>"
    }

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

STATS_FILE = os.path.join(APP_DIR, "firewall_stats.json")

def load_runs() -> List[Run]:
    runs = []
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r") as f:
                data = json.load(f)
                for item in data:
                    r = Run(item["time"])
                    r.penalty = item.get("penalty")
                    runs.append(r)
        except Exception:
            pass
    return runs

def save_runs(runs: List[Run]):
    data = [{"time": r.time, "penalty": r.penalty} for r in runs]
    try:
        with open(STATS_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass

class StatsManager:
    def __init__(self):
        self.runs: List[Run] = load_runs()

    def add_time(self, t: float):
        self.runs.append(Run(t))
        save_runs(self.runs)

    def get_best_single(self):
        valid = [r.time for r in self.runs if r.penalty != "DNF"]
        if not valid:
            return None
        return min(valid)

    def get_best_ao_details(self, n: int):
        best = None
        best_details = None
        for i in range(n, len(self.runs) + 1):
            subset = self.runs[i-n:i]
            recent = [(r.value, idx) for idx, r in enumerate(subset)]
            sorted_recent = sorted(recent, key=lambda x: x[0])
            
            drop_count = math.ceil(n * 0.05)
            worst_indices = [x[1] for x in sorted_recent[-drop_count:]] if drop_count > 0 else []
            best_indices = [x[1] for x in sorted_recent[:drop_count]] if drop_count > 0 else []
            dropped_indices = set(worst_indices + best_indices)
            
            kept = [x[0] for x in sorted_recent[drop_count:-drop_count]] if drop_count > 0 else [x[0] for x in sorted_recent]
            
            if float('inf') not in kept:
                avg = sum(kept) / len(kept)
                if best is None or avg < best:
                    best = avg
                    
                    if n == 5:
                        details = []
                        for idx, r in enumerate(subset):
                            t_str = "DNF" if r.value == float('inf') else f"{r.time:.3f}"
                            if idx in dropped_indices:
                                details.append(f"({t_str})")
                            else:
                                details.append(t_str)
                        best_details = "\n".join(details)
                    else:
                        best_details = None
                        
        return best, best_details

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
        self.geometry(saved if saved else "350x300")
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Theme:", font=("Arial", 14)).grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.theme_menu = ctk.CTkOptionMenu(self, values=["Default (Blue)", "Catppuccin", "Custom Firewall"], command=self.change_theme)
        self.theme_menu.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        self.theme_menu.set(app_settings["theme"])

        self.restart_lbl = ctk.CTkLabel(self, text="", text_color="red", font=("Arial", 12))
        self.restart_lbl.grid(row=1, column=0, columnspan=2)

        # Keybinds
        ctk.CTkLabel(self, text="OK Keybind:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.kb_ok = ctk.CTkEntry(self, width=120)
        self.kb_ok.insert(0, app_settings.get("keybind_ok", "<Control-1>"))
        self.kb_ok.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        ctk.CTkButton(self, text="Set", width=40, command=lambda: self.capture_keybind(self.kb_ok)).grid(row=2, column=2, padx=5, sticky="w")

        ctk.CTkLabel(self, text="DNF Keybind:").grid(row=3, column=0, padx=10, pady=5, sticky="e")
        self.kb_dnf = ctk.CTkEntry(self, width=120)
        self.kb_dnf.insert(0, app_settings.get("keybind_dnf", "<Control-2>"))
        self.kb_dnf.grid(row=3, column=1, padx=10, pady=5, sticky="w")
        ctk.CTkButton(self, text="Set", width=40, command=lambda: self.capture_keybind(self.kb_dnf)).grid(row=3, column=2, padx=5, sticky="w")

        ctk.CTkLabel(self, text="DEL Keybind:").grid(row=4, column=0, padx=10, pady=5, sticky="e")
        self.kb_delete = ctk.CTkEntry(self, width=120)
        self.kb_delete.insert(0, app_settings.get("keybind_delete", "<Control-3>"))
        self.kb_delete.grid(row=4, column=1, padx=10, pady=5, sticky="w")
        ctk.CTkButton(self, text="Set", width=40, command=lambda: self.capture_keybind(self.kb_delete)).grid(row=4, column=2, padx=5, sticky="w")

        self.apply_btn = ctk.CTkButton(self, text="Apply Keybinds", command=self.apply_keybinds)
        self.apply_btn.grid(row=5, column=0, columnspan=3, pady=10)

        self.update_btn = ctk.CTkButton(self, text="Check for Updates", command=lambda: parent.check_for_updates(manual=True), fg_color="blue", hover_color="darkblue")
        self.update_btn.grid(row=6, column=0, columnspan=3, pady=(0, 10))

        self.debug_btn = ctk.CTkButton(self, text="Open Debug Console", command=self.open_debug, fg_color="gray", hover_color="darkgray")
        self.debug_btn.grid(row=7, column=0, columnspan=3, pady=(0, 10))

    def capture_keybind(self, entry_widget):
        self.focus_set()
        entry_widget.delete(0, "end")
        entry_widget.insert(0, "Press key...")
        
        def on_key(event):
            if event.keysym in ['Control_L', 'Control_R', 'Shift_L', 'Shift_R', 'Alt_L', 'Alt_R', 'Win_L', 'Win_R']:
                return
                
            self.unbind("<Key>")
            modifiers = []
            if event.state & 0x0004: modifiers.append("Control")
            if event.state & 0x0001: modifiers.append("Shift")
            if event.state & 131072: modifiers.append("Alt")
                
            bind_str = f"<{'-'.join(modifiers + [event.keysym])}>" if modifiers else f"<{event.keysym}>"
            entry_widget.delete(0, "end")
            entry_widget.insert(0, bind_str)
            
        self.bind("<Key>", on_key)

    def apply_keybinds(self):
        try:
            self.parent.unbind(app_settings.get("keybind_ok", "<Control-1>"))
            self.parent.unbind(app_settings.get("keybind_dnf", "<Control-2>"))
            self.parent.unbind(app_settings.get("keybind_delete", "<Control-3>"))
        except:
            pass
            
        app_settings["keybind_ok"] = self.kb_ok.get()
        app_settings["keybind_dnf"] = self.kb_dnf.get()
        app_settings["keybind_delete"] = self.kb_delete.get()
        save_settings(app_settings)
        
        self.parent.bind(app_settings["keybind_ok"], self.parent.set_ok)
        self.parent.bind(app_settings["keybind_dnf"], self.parent.set_dnf)
        self.parent.bind(app_settings["keybind_delete"], self.parent.delete_last)
        
        import tkinter.messagebox
        tkinter.messagebox.showinfo("Success", "Keybinds applied!\n(Use Tkinter format like <Control-1>)")

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

        self.title(f"Firewall Tracker - {CURRENT_VERSION}")
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
        self.bind(app_settings.get("keybind_ok", "<Control-1>"), self.set_ok)
        self.bind(app_settings.get("keybind_dnf", "<Control-2>"), self.set_dnf)
        self.bind(app_settings.get("keybind_delete", "<Control-3>"), self.delete_last)
        
        self.update_stats_ui()
        self.update_timer_loop()
        
        if getattr(sys, 'frozen', False):
            self.check_for_updates()

    def check_for_updates(self, manual=False):
        def update_thread():
            try:
                req = urllib.request.Request(GITHUB_API_URL, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode())
                    latest_version = data.get("tag_name", "")
                    
                    if latest_version and latest_version.replace("v","") > CURRENT_VERSION.replace("v",""):
                        exe_url = None
                        for asset in data.get("assets", []):
                            if asset.get("name", "").endswith(".exe"):
                                exe_url = asset.get("browser_download_url")
                                break
                        
                        if exe_url:
                            self.after(2000 if not manual else 0, lambda: self.prompt_update(latest_version, exe_url))
                        elif manual:
                            self.after(0, lambda: __import__('tkinter.messagebox').messagebox.showinfo("Updater", "No .exe found in the latest release!"))
                    elif manual:
                        self.after(0, lambda: __import__('tkinter.messagebox').messagebox.showinfo("Updater", f"You are on the latest version! ({CURRENT_VERSION})"))
            except Exception as e:
                self.after(0, self.log_debug, f"Update check failed: {e}")
                if manual:
                    self.after(0, lambda: __import__('tkinter.messagebox').messagebox.showerror("Updater Error", f"Failed to check for updates:\n{e}"))
                
        threading.Thread(target=update_thread, daemon=True).start()

    def prompt_update(self, version, download_url):
        import tkinter.messagebox
        result = tkinter.messagebox.askyesno(
            "Update Available", 
            f"A new version of Firewall Tracker ({version}) is available!\n\nWould you like to download and install it now?"
        )
        if result:
            self.perform_update(download_url)

    def perform_update(self, download_url):
        dl_win = ctk.CTkToplevel(self)
        dl_win.title("Updating...")
        dl_win.geometry("300x120")
        dl_win.attributes("-topmost", True)
        dl_lbl = ctk.CTkLabel(dl_win, text="Downloading update, please wait...", font=("Arial", 14))
        dl_lbl.pack(expand=True)
        self.update()
        
        def download_thread():
            try:
                exe_path = sys.executable
                new_exe_path = os.path.join(APP_DIR, "firewall_tracker_new.exe")
                
                req = urllib.request.Request(download_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response, open(new_exe_path, 'wb') as out_file:
                    shutil.copyfileobj(response, out_file)
                
                bat_path = os.path.join(os.environ.get("TEMP", os.getcwd()), "update_tracker.bat")
                
                bat_content = f"""@echo off
timeout /t 2 /nobreak > NUL
move /Y "{new_exe_path}" "{exe_path}"
start "" "{exe_path}"
del "%~f0"
"""
                with open(bat_path, "w") as f:
                    f.write(bat_content)
                
                import subprocess
                DETACHED_PROCESS = 0x00000008
                subprocess.Popen(["cmd.exe", "/c", bat_path], creationflags=DETACHED_PROCESS)
                
                self.after(0, self.destroy)
                
            except Exception as e:
                self.after(0, lambda: dl_lbl.configure(text=f"Update failed:\n{e}"))
                self.after(0, self.log_debug, f"Update failed: {e}")
                
        threading.Thread(target=download_thread, daemon=True).start()

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
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        self.stats_frame.grid_columnconfigure((0, 1), weight=1)
        self.stats_frame.grid_rowconfigure((0, 1, 2), weight=1)

        # --- Left Column ---
        # 1. Current Stats
        self.current_stats_frame = ctk.CTkFrame(self.stats_frame)
        self.current_stats_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(self.current_stats_frame, text="CURRENT STATS", font=("Arial", 10, "bold"), text_color="gray").pack(anchor="w", padx=10, pady=(10, 0))
        
        ctk.CTkLabel(self.current_stats_frame, text="AO5", font=("Arial", 12), text_color="gray").pack(anchor="w", padx=10, pady=(5,0))
        self.lbl_curr_ao5 = ctk.CTkLabel(self.current_stats_frame, text="--.---", font=("Consolas", 22, "bold"))
        self.lbl_curr_ao5.pack(anchor="w", padx=10)
        
        ctk.CTkLabel(self.current_stats_frame, text="AO12", font=("Arial", 12), text_color="gray").pack(anchor="w", padx=10, pady=(5,0))
        self.lbl_curr_ao12 = ctk.CTkLabel(self.current_stats_frame, text="--.---", font=("Consolas", 22, "bold"))
        self.lbl_curr_ao12.pack(anchor="w", padx=10)
        
        ctk.CTkLabel(self.current_stats_frame, text="AO100", font=("Arial", 12), text_color="gray").pack(anchor="w", padx=10, pady=(5,0))
        self.lbl_curr_ao100 = ctk.CTkLabel(self.current_stats_frame, text="-", font=("Consolas", 18, "bold"))
        self.lbl_curr_ao100.pack(anchor="w", padx=10, pady=(0, 10))

        # 2. Best Single
        self.best_single_frame = ctk.CTkFrame(self.stats_frame, fg_color="#4B77FF")
        self.best_single_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(self.best_single_frame, text="BEST SINGLE", font=("Arial", 10, "bold"), text_color="white").pack(anchor="w", padx=10, pady=(10, 0))
        self.lbl_best_single = ctk.CTkLabel(self.best_single_frame, text="--.---", font=("Consolas", 28, "bold"), text_color="white")
        self.lbl_best_single.pack(anchor="w", padx=10, pady=(0, 10))

        # 3. Best Stats
        self.best_stats_frame = ctk.CTkFrame(self.stats_frame)
        self.best_stats_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(self.best_stats_frame, text="BEST STATS", font=("Arial", 10, "bold"), text_color="gray").pack(anchor="w", padx=10, pady=(10, 0))
        
        ctk.CTkLabel(self.best_stats_frame, text="AO12", font=("Arial", 12), text_color="gray").pack(anchor="w", padx=10, pady=(5,0))
        self.lbl_best_ao12 = ctk.CTkLabel(self.best_stats_frame, text="--.---", font=("Consolas", 22, "bold"))
        self.lbl_best_ao12.pack(anchor="w", padx=10)
        
        ctk.CTkLabel(self.best_stats_frame, text="AO100", font=("Arial", 12), text_color="gray").pack(anchor="w", padx=10, pady=(5,0))
        self.lbl_best_ao100 = ctk.CTkLabel(self.best_stats_frame, text="-", font=("Consolas", 18, "bold"))
        self.lbl_best_ao100.pack(anchor="w", padx=10, pady=(0, 10))

        # --- Right Column ---
        # 4. Count and Mean (stacked)
        self.right_top_frame = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
        self.right_top_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.right_top_frame.grid_columnconfigure(0, weight=1)
        self.right_top_frame.grid_rowconfigure((0,1), weight=1)
        
        self.count_frame = ctk.CTkFrame(self.right_top_frame)
        self.count_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        ctk.CTkLabel(self.count_frame, text="SOLVE COUNT", font=("Arial", 12, "bold"), text_color="gray").pack(anchor="w", padx=10, pady=(10, 0))
        self.lbl_count = ctk.CTkLabel(self.count_frame, text="0", font=("Consolas", 24, "bold"))
        self.lbl_count.pack(anchor="w", padx=10, pady=(0, 10))

        self.mean_frame = ctk.CTkFrame(self.right_top_frame)
        self.mean_frame.grid(row=1, column=0, sticky="nsew", pady=(5, 0))
        ctk.CTkLabel(self.mean_frame, text="SESSION MEAN", font=("Arial", 12, "bold"), text_color="gray").pack(anchor="w", padx=10, pady=(10, 0))
        self.lbl_mean = ctk.CTkLabel(self.mean_frame, text="--.---", font=("Consolas", 24, "bold"))
        self.lbl_mean.pack(anchor="w", padx=10, pady=(0, 10))

        # 5. Best AO5 Details
        self.best_ao5_frame = ctk.CTkFrame(self.stats_frame)
        self.best_ao5_frame.grid(row=1, column=1, rowspan=2, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(self.best_ao5_frame, text="BEST AO5", font=("Arial", 12, "bold"), text_color="gray").pack(anchor="w", padx=10, pady=(10, 0))
        self.lbl_best_ao5 = ctk.CTkLabel(self.best_ao5_frame, text="--.---", font=("Consolas", 28, "bold"), text_color="#4B77FF")
        self.lbl_best_ao5.pack(anchor="w", padx=10, pady=(0, 5))
        self.lbl_best_ao5_details = ctk.CTkLabel(self.best_ao5_frame, text="-\n-\n-\n-\n-", font=("Consolas", 12), text_color="gray", justify="left")
        self.lbl_best_ao5_details.pack(anchor="w", padx=10, pady=(0, 10))

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

    def set_ok(self, event=None):
        if self.timer_state in ["RUNNING", "PAUSED"]:
            self.stop_timer()
        if self.stats.runs and self.timer_state == "STOPPED":
            self.stats.runs[-1].penalty = None
            self.update_stats_ui()
            save_runs(self.stats.runs)

    def set_dnf(self, event=None):
        if self.timer_state in ["RUNNING", "PAUSED"]:
            self.stop_timer()
        if self.stats.runs and self.timer_state == "STOPPED":
            self.stats.runs[-1].penalty = "DNF"
            self.update_stats_ui()
            save_runs(self.stats.runs)

    def delete_last(self, event=None):
        if self.timer_state in ["RUNNING", "PAUSED"]:
            self.stop_timer()
        if self.stats.runs and self.timer_state == "STOPPED":
            self.stats.runs.pop()
            self.update_stats_ui()
            save_runs(self.stats.runs)

    def auto_dnf(self):
        if self.timer_state in ["RUNNING", "PAUSED"]:
            self.set_dnf()

    def on_roblox_log(self, time_str: str, level: str, message: str):
        msg_lower = message.lower().strip()
        self.log_debug(f"[{time_str}] {message}")
        
        # Teleport / New Server / Lobby
        if "joingame" in msg_lower or "connecting to server" in msg_lower:
            self.after(0, self.clear_console)
            self.log_debug("-> TRIGGER: NEW SERVER (CLEARED)")
            return

        # Auto DNF Conditions (during run)
        if self.timer_state in ("RUNNING", "PAUSED"):
            if "afterdeathmodifier" in msg_lower or "requesting admin command: kill with args" in msg_lower:
                self.after(0, self.auto_dnf)
                self.log_debug("-> TRIGGER: AUTO DNF")
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
        
        ao5 = self.stats.calculate_ao(5)
        ao12 = self.stats.calculate_ao(12)
        ao100 = self.stats.calculate_ao(100)
        
        self.ao5_label.configure(text=f"AO5: {format_time(ao5)}")
        
        self.lbl_curr_ao5.configure(text=format_time(ao5))
        self.lbl_curr_ao12.configure(text=format_time(ao12))
        self.lbl_curr_ao100.configure(text=format_time(ao100))
        
        best_ao5, best_ao5_details = self.stats.get_best_ao_details(5)
        best_ao12, _ = self.stats.get_best_ao_details(12)
        best_ao100, _ = self.stats.get_best_ao_details(100)
        
        self.lbl_best_single.configure(text=format_time(self.stats.get_best_single()))
        
        self.lbl_best_ao12.configure(text=format_time(best_ao12))
        self.lbl_best_ao100.configure(text=format_time(best_ao100))
        
        self.lbl_count.configure(text=str(len(self.stats.runs)))
        self.lbl_mean.configure(text=format_time(self.stats.get_session_mean()))
        
        self.lbl_best_ao5.configure(text=format_time(best_ao5))
        if best_ao5_details:
            self.lbl_best_ao5_details.configure(text=best_ao5_details)
        else:
            self.lbl_best_ao5_details.configure(text="-\n-\n-\n-\n-")

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
