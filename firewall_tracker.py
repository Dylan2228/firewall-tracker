import customtkinter as ctk
import time
import os
import sys
import json
import threading
import urllib.request
import webbrowser
from tkinter import messagebox
from typing import List
from roblox_console import RobloxConsoleStreamer

CURRENT_VERSION = "v1.1.1"
GITHUB_API_URL = "https://api.github.com/repos/Dylan2228/firewall-tracker/releases/latest"

# --- App Data Paths ---
if sys.platform == "darwin":
    APP_DIR = os.path.expanduser("~/Library/Application Support/FirewallTracker")
else:
    APP_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "FirewallTracker")
os.makedirs(APP_DIR, exist_ok=True)

SETTINGS_FILE = os.path.join(APP_DIR, "firewall_settings.json")

# --- Monospace Font Helper ---
MONO_FONT = "Menlo" if sys.platform == "darwin" else "Consolas"

# --- Default Keybinds ---
DEFAULT_KEYBINDS = {
    "keybind_ok": "<Command-1>" if sys.platform == "darwin" else "<Control-1>",
    "keybind_dnf": "<Command-2>" if sys.platform == "darwin" else "<Control-2>",
    "keybind_delete": "<Command-3>" if sys.platform == "darwin" else "<Control-3>",
}

# --- Load Settings ---
def load_settings():
    defaults = {
        "theme": "Default (Blue)",
        "keybind_ok": DEFAULT_KEYBINDS["keybind_ok"],
        "keybind_dnf": DEFAULT_KEYBINDS["keybind_dnf"],
        "keybind_delete": DEFAULT_KEYBINDS["keybind_delete"]
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
                defaults.update(data)
                return defaults
        except:
            pass
    return defaults

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
    def __init__(self, t: float, date: str = None):
        self.time = t
        self.penalty = None  # None or "DNF"
        self.date = date

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
                    r = Run(item["time"], item.get("date"))
                    r.penalty = item.get("penalty")
                    runs.append(r)
        except Exception:
            pass
    return runs

def save_runs(runs: List[Run]):
    data = []
    for r in runs:
        entry = {"time": r.time, "penalty": r.penalty}
        if r.date:
            entry["date"] = r.date
        data.append(entry)
    try:
        with open(STATS_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass

class StatsManager:
    def __init__(self):
        self.runs: List[Run] = load_runs()

    def add_time(self, t: float, date_str: str = None):
        if not date_str:
            import datetime
            date_str = datetime.datetime.now().strftime("%m/%d %H:%M")
        self.runs.append(Run(t, date_str))
        save_runs(self.runs)

    def get_best_single(self):
        valid = [r.time for r in self.runs if r.penalty != "DNF"]
        if not valid:
            return None
        return min(valid)

    def get_best_ao_details(self, n: int):
        valid = [r for r in self.runs if r.penalty != "DNF"]
        best = None
        best_details = None
        for i in range(n, len(valid) + 1):
            subset = valid[i-n:i]
            recent = [(r.time, idx) for idx, r in enumerate(subset)]
            sorted_recent = sorted(recent, key=lambda x: x[0])
            
            drop_count = math.ceil(n * 0.05)
            worst_indices = [x[1] for x in sorted_recent[-drop_count:]] if drop_count > 0 else []
            best_indices = [x[1] for x in sorted_recent[:drop_count]] if drop_count > 0 else []
            dropped_indices = set(worst_indices + best_indices)
            
            kept = [x[0] for x in sorted_recent[drop_count:-drop_count]] if drop_count > 0 else [x[0] for x in sorted_recent]
            
            avg = sum(kept) / len(kept)
            if best is None or avg < best:
                best = avg
                
                if n == 5:
                    details = []
                    for idx, r in enumerate(subset):
                        t_str = format_time(r.time)
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
        valid = [r for r in self.runs if r.penalty != "DNF"]
        if len(valid) < n:
            return None
        recent = [r.time for r in valid[-n:]]
        recent.sort()
        drop_count = math.ceil(n * 0.05)
        kept = recent[drop_count : -drop_count] if drop_count > 0 else recent
        if not kept:
            return None
        return sum(kept) / len(kept)

    def calculate_mo(self, n: int):
        valid = [r for r in self.runs if r.penalty != "DNF"]
        if len(valid) < n:
            return None
        recent = [r.time for r in valid[-n:]]
        return sum(recent) / len(recent)

def format_time(t) -> str:
    if t is None:
        return "-:--.---"
    if t == float('inf'):
        return "DNF"
    minutes = int(t // 60)
    seconds = t % 60
    return f"{minutes}:{seconds:06.3f}"

def export_stats(parent=None):
    from tkinter import filedialog, messagebox
    file_path = filedialog.asksaveasfilename(
        parent=parent,
        defaultextension=".json",
        filetypes=[("JSON Files", "*.json")],
        initialfile="firewall_stats_export.json"
    )
    if not file_path:
        return
    try:
        runs = load_runs()
        data = [{"time": r.time, "penalty": r.penalty} for r in runs]
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
        messagebox.showinfo("Export Success", f"Successfully exported {len(runs)} runs to:\n{file_path}", parent=parent)
    except Exception as e:
        messagebox.showerror("Export Failed", f"Failed to export stats:\n{e}", parent=parent)

def import_stats(parent=None, callback=None):
    from tkinter import filedialog, messagebox
    file_path = filedialog.askopenfilename(
        parent=parent,
        filetypes=[("JSON Files", "*.json")]
    )
    if not file_path:
        return
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("Stats file must contain a list of run objects.")
        
        imported_runs = []
        for item in data:
            if isinstance(item, dict) and "time" in item:
                r = Run(float(item["time"]), item.get("date"))
                r.penalty = item.get("penalty")
                imported_runs.append(r)
                
        if not imported_runs:
            messagebox.showwarning("Import Warning", "No valid runs found in selected file.", parent=parent)
            return

        choice = messagebox.askyesno(
            "Import Mode",
            f"Found {len(imported_runs)} valid runs.\n\n"
            f"Click [Yes] to MERGE (add to existing runs).\n"
            f"Click [No] to REPLACE (overwrite existing runs).",
            parent=parent
        )
        current = load_runs()
        if choice:  # Merge
            current.extend(imported_runs)
        else:       # Replace
            current = imported_runs
            
        save_runs(current)
        if callback:
            callback(current)
        messagebox.showinfo("Import Success", f"Successfully imported {len(imported_runs)} runs!", parent=parent)
    except Exception as e:
        messagebox.showerror("Import Error", f"Failed to import stats:\n{e}", parent=parent)


class TimerWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Timer")
        saved = app_settings.get("geometries", {}).get("timer")
        self.geometry(saved if saved else "500x200")
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.time_label = ctk.CTkLabel(self, text="0:00.000", font=(MONO_FONT, 120, "bold"))
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
            self.time_label.configure(font=(MONO_FONT, new_size, "bold"))


class DebugWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Debug Console")
        saved = app_settings.get("geometries", {}).get("debug")
        self.geometry(saved if saved else "600x400")
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.textbox = ctk.CTkTextbox(self, state="disabled", font=(MONO_FONT, 12))
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


class TimesHistoryWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Recorded Times History")
        saved = app_settings.get("geometries", {}).get("history")
        self.geometry(saved if saved else "560x620")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.sort_mode = "Newest First"
        self.loaded_count = 20
        self.indexed_runs = []
        self.load_more_frame = None
        self.is_loading = False
        
        # Header Toolbar
        self.top_toolbar = ctk.CTkFrame(self, fg_color="transparent")
        self.top_toolbar.pack(fill="x", padx=15, pady=(15, 5))
        
        self.count_label = ctk.CTkLabel(self.top_toolbar, text="", font=("Arial", 16, "bold"))
        self.count_label.pack(side="left")
        
        self.sort_menu = ctk.CTkOptionMenu(
            self.top_toolbar, 
            values=["Newest First", "Oldest First", "Fastest First", "Slowest First"], 
            width=135, 
            font=("Arial", 12),
            command=self.on_sort_change
        )
        self.sort_menu.pack(side="right", padx=5)

        self.btn_export = ctk.CTkButton(
            self.top_toolbar, 
            text="Export", 
            width=70, 
            fg_color="teal", 
            hover_color="darkcyan",
            font=("Arial", 12),
            command=lambda: export_stats(self)
        )
        self.btn_export.pack(side="right", padx=5)

        self.btn_import = ctk.CTkButton(
            self.top_toolbar, 
            text="Import", 
            width=70, 
            fg_color="royalblue", 
            hover_color="navy",
            font=("Arial", 12),
            command=self.handle_import
        )
        self.btn_import.pack(side="right", padx=5)

        # Summary Frame (Fastest & Slowest times)
        self.summary_frame = ctk.CTkFrame(self, fg_color=("gray85", "gray17"), corner_radius=8)
        self.summary_frame.pack(fill="x", padx=15, pady=5)
        self.summary_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.lbl_fastest = ctk.CTkLabel(
            self.summary_frame, 
            text="⚡ Fastest: -:--.---", 
            font=("Arial", 12, "bold"), 
            text_color="#2ECC71"
        )
        self.lbl_fastest.grid(row=0, column=0, padx=8, pady=8)

        self.lbl_slowest = ctk.CTkLabel(
            self.summary_frame, 
            text="🐢 Slowest: -:--.---", 
            font=("Arial", 12, "bold"), 
            text_color="#E67E22"
        )
        self.lbl_slowest.grid(row=0, column=1, padx=8, pady=8)

        self.lbl_valid_ratio = ctk.CTkLabel(
            self.summary_frame, 
            text="Done: 0 | DNF: 0", 
            font=("Arial", 12), 
            text_color="gray"
        )
        self.lbl_valid_ratio.grid(row=0, column=2, padx=8, pady=8)

        # Scrollable list of runs
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(expand=True, fill="both", padx=15, pady=10)

        if sys.platform == "darwin":
            try:
                self.scroll_frame._parent_canvas.configure(yscrollincrement=2)
            except Exception:
                pass

        self.bind_mousewheel(self.scroll_frame._parent_canvas)
        self.bind_mousewheel(self.scroll_frame)

        self.render_times()

        # Auto infinite-scroll listener loop
        self.after(300, self.check_scroll_loop)

    def bind_mousewheel(self, widget):
        widget.bind("<MouseWheel>", self.on_mousewheel, add="+")
        for child in widget.winfo_children():
            self.bind_mousewheel(child)

    def on_mousewheel(self, event):
        canvas = self.scroll_frame._parent_canvas
        if sys.platform == "darwin":
            # On macOS, trackpads send high-frequency small deltas (+/-1 to 5).
            # A multiplier of 3 gives buttery smooth, responsive native trackpad feel!
            scroll_units = -1 * int(event.delta * 3) if event.delta != 0 else 0
            if scroll_units != 0:
                canvas.yview_scroll(scroll_units, "units")
        else:
            scroll_units = -1 * int(event.delta / 40) if event.delta != 0 else 0
            if scroll_units != 0:
                canvas.yview_scroll(scroll_units, "units")

        self.check_auto_load()
        return "break"

    def check_auto_load(self):
        try:
            _, bottom = self.scroll_frame._parent_canvas.yview()
            # If scrolled past 70% of the list, load the next 20 seamlessly
            if bottom >= 0.70 and self.loaded_count < len(self.indexed_runs) and not self.is_loading:
                self.load_more()
        except Exception:
            pass

    def check_scroll_loop(self):
        if not self.winfo_exists():
            return
        self.check_auto_load()
        self.after(100, self.check_scroll_loop)

    def on_sort_change(self, choice):
        self.sort_mode = choice
        self.render_times(reset_page=True)

    def handle_import(self):
        def on_import(runs):
            self.parent.stats.runs = runs
            self.parent.update_stats_ui()
            self.render_times(reset_page=True)
        import_stats(self, on_import)

    def render_times(self, reset_page=True):
        if reset_page:
            self.loaded_count = 20

        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        runs = self.parent.stats.runs
        valid = [r.time for r in runs if r.penalty != "DNF"]
        dnf_count = sum(1 for r in runs if r.penalty == "DNF")

        self.count_label.configure(text=f"Total: {len(runs)}")
        fastest_str = format_time(min(valid)) if valid else "-:--.---"
        slowest_str = format_time(max(valid)) if valid else "-:--.---"
        self.lbl_fastest.configure(text=f"⚡ Fastest: {fastest_str}")
        self.lbl_slowest.configure(text=f"🐢 Slowest: {slowest_str}")
        self.lbl_valid_ratio.configure(text=f"Done: {len(valid)} | DNF: {dnf_count}")

        if not runs:
            ctk.CTkLabel(
                self.scroll_frame, 
                text="No runs recorded yet!", 
                font=("Arial", 14), 
                text_color="gray"
            ).pack(pady=40)
            return

        indexed_runs = list(enumerate(runs, start=1))

        if self.sort_mode == "Newest First":
            indexed_runs.reverse()
        elif self.sort_mode == "Oldest First":
            pass
        elif self.sort_mode == "Fastest First":
            def fastest_key(item):
                run = item[1]
                return (1 if run.penalty == "DNF" else 0, run.time)
            indexed_runs.sort(key=fastest_key)
        elif self.sort_mode == "Slowest First":
            def slowest_key(item):
                run = item[1]
                return (1 if run.penalty == "DNF" else 0, -run.time)
            indexed_runs.sort(key=slowest_key)

        self.indexed_runs = indexed_runs
        self.load_batch(start_idx=0)

    def load_batch(self, start_idx: int):
        self.is_loading = True
        if self.load_more_frame and self.load_more_frame.winfo_exists():
            self.load_more_frame.destroy()

        batch = self.indexed_runs[start_idx : self.loaded_count]

        for orig_idx, run in batch:
            row_frame = ctk.CTkFrame(self.scroll_frame, fg_color=("gray85", "gray20"), corner_radius=6)
            row_frame.pack(fill="x", pady=3, padx=2)
            row_frame.grid_columnconfigure(1, weight=1)

            # 1. Index #
            ctk.CTkLabel(
                row_frame, 
                text=f"#{orig_idx}", 
                font=("Arial", 12, "bold"), 
                text_color="gray", 
                width=45, 
                anchor="w"
            ).grid(row=0, column=0, padx=(10, 5), pady=8)

            # 2. Time
            time_str = format_time(run.time)
            color = "red" if run.penalty == "DNF" else ("#2ECC71" if run.penalty is None else "white")
            ctk.CTkLabel(
                row_frame, 
                text=time_str, 
                font=(MONO_FONT, 15, "bold"), 
                text_color=color, 
                anchor="w"
            ).grid(row=0, column=1, padx=5, pady=8, sticky="w")

            # 3. Date & Time
            date_str = run.date if run.date else "-"
            ctk.CTkLabel(
                row_frame, 
                text=date_str, 
                font=("Arial", 11), 
                text_color="gray", 
                width=85, 
                anchor="e"
            ).grid(row=0, column=2, padx=5, pady=8)

            # 4. Status
            status_text = "DNF" if run.penalty == "DNF" else "OK"
            status_color = "red" if run.penalty == "DNF" else "green"
            ctk.CTkLabel(
                row_frame, 
                text=status_text, 
                font=("Arial", 11, "bold"), 
                text_color=status_color, 
                width=40
            ).grid(row=0, column=3, padx=5, pady=8)

            # 5. Action Dots
            btn_dots = ctk.CTkButton(
                row_frame, 
                text="•••", 
                width=35, 
                height=26, 
                font=("Arial", 12, "bold"),
                fg_color=("gray75", "gray30"),
                hover_color=("gray65", "gray40"),
                command=lambda r_idx=orig_idx-1, f=row_frame: self.show_context_menu(r_idx, f)
            )
            btn_dots.grid(row=0, column=4, padx=(5, 10), pady=8)

            self.bind_mousewheel(row_frame)

        # Show load more footer if there are remaining runs
        if self.loaded_count < len(self.indexed_runs):
            self.load_more_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
            self.load_more_frame.pack(fill="x", pady=12)

            remaining = len(self.indexed_runs) - self.loaded_count
            next_step = min(20, remaining)

            lbl_info = ctk.CTkLabel(
                self.load_more_frame, 
                text=f"Showing {min(self.loaded_count, len(self.indexed_runs))} of {len(self.indexed_runs)} runs (Scroll down for more)", 
                font=("Arial", 11), 
                text_color="gray"
            )
            lbl_info.pack(pady=(0, 6))

            btn_box = ctk.CTkFrame(self.load_more_frame, fg_color="transparent")
            btn_box.pack()

            btn_more = ctk.CTkButton(
                btn_box, 
                text=f"Load More (+{next_step})", 
                width=140, 
                height=32,
                font=("Arial", 12, "bold"),
                command=self.load_more
            )
            btn_more.pack(side="left", padx=5)

            btn_all = ctk.CTkButton(
                btn_box, 
                text="Load All", 
                width=90, 
                height=32,
                font=("Arial", 12),
                fg_color="gray",
                hover_color="darkgray",
                command=self.load_all
            )
            btn_all.pack(side="left", padx=5)

        self.is_loading = False

    def load_more(self):
        prev = self.loaded_count
        self.loaded_count += 20
        self.load_batch(start_idx=prev)

    def load_all(self):
        prev = self.loaded_count
        self.loaded_count = len(self.indexed_runs)
        self.load_batch(start_idx=prev)

    def show_context_menu(self, run_index: int, widget):
        import tkinter as tk
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="✔ Set OK", command=lambda: self.set_run_status(run_index, None))
        menu.add_command(label="🚫 Set DNF", command=lambda: self.set_run_status(run_index, "DNF"))
        menu.add_separator()
        menu.add_command(label="🗑️ Delete", command=lambda: self.delete_run(run_index))
        
        try:
            x = widget.winfo_rootx() + widget.winfo_width() - 80
            y = widget.winfo_rooty() + widget.winfo_height()
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def set_run_status(self, run_index: int, penalty):
        if 0 <= run_index < len(self.parent.stats.runs):
            self.parent.stats.runs[run_index].penalty = penalty
            save_runs(self.parent.stats.runs)
            self.parent.update_stats_ui()
            self.render_times(reset_page=False)

    def delete_run(self, run_index: int):
        import tkinter.messagebox as mb
        if 0 <= run_index < len(self.parent.stats.runs):
            if mb.askyesno("Confirm Delete", f"Delete run #{run_index + 1}?", parent=self):
                self.parent.stats.runs.pop(run_index)
                save_runs(self.parent.stats.runs)
                self.parent.update_stats_ui()
                self.render_times(reset_page=False)

    def on_closing(self):
        app_settings.setdefault("geometries", {})["history"] = self.geometry()
        save_settings(app_settings)
        self.destroy()


class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Settings")
        saved = app_settings.get("geometries", {}).get("settings")
        self.geometry(saved if saved else "360x380")
        
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
        self.kb_ok.insert(0, app_settings.get("keybind_ok", DEFAULT_KEYBINDS["keybind_ok"]))
        self.kb_ok.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        ctk.CTkButton(self, text="Set", width=40, command=lambda: self.capture_keybind(self.kb_ok)).grid(row=2, column=2, padx=5, sticky="w")

        ctk.CTkLabel(self, text="DNF Keybind:").grid(row=3, column=0, padx=10, pady=5, sticky="e")
        self.kb_dnf = ctk.CTkEntry(self, width=120)
        self.kb_dnf.insert(0, app_settings.get("keybind_dnf", DEFAULT_KEYBINDS["keybind_dnf"]))
        self.kb_dnf.grid(row=3, column=1, padx=10, pady=5, sticky="w")
        ctk.CTkButton(self, text="Set", width=40, command=lambda: self.capture_keybind(self.kb_dnf)).grid(row=3, column=2, padx=5, sticky="w")

        ctk.CTkLabel(self, text="DEL Keybind:").grid(row=4, column=0, padx=10, pady=5, sticky="e")
        self.kb_delete = ctk.CTkEntry(self, width=120)
        self.kb_delete.insert(0, app_settings.get("keybind_delete", DEFAULT_KEYBINDS["keybind_delete"]))
        self.kb_delete.grid(row=4, column=1, padx=10, pady=5, sticky="w")
        ctk.CTkButton(self, text="Set", width=40, command=lambda: self.capture_keybind(self.kb_delete)).grid(row=4, column=2, padx=5, sticky="w")

        self.apply_btn = ctk.CTkButton(self, text="Apply Keybinds", command=self.apply_keybinds)
        self.apply_btn.grid(row=5, column=0, columnspan=3, pady=10)

        self.update_btn = ctk.CTkButton(self, text="Check for Updates", command=lambda: parent.check_for_updates(manual=True), fg_color="blue", hover_color="darkblue")
        self.update_btn.grid(row=6, column=0, columnspan=3, pady=(0, 10))

        self.debug_btn = ctk.CTkButton(self, text="Open Debug Console", command=self.open_debug, fg_color="gray", hover_color="darkgray")
        self.debug_btn.grid(row=7, column=0, columnspan=3, pady=(0, 10))

        # Data Management Frame
        self.data_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.data_frame.grid(row=8, column=0, columnspan=3, pady=(0, 10))
        
        self.export_btn = ctk.CTkButton(self.data_frame, text="Export Stats...", width=110, command=lambda: export_stats(self), fg_color="teal", hover_color="darkcyan")
        self.export_btn.pack(side="left", padx=5)
        
        self.import_btn = ctk.CTkButton(self.data_frame, text="Import Stats...", width=110, command=self.handle_import, fg_color="royalblue", hover_color="navy")
        self.import_btn.pack(side="left", padx=5)

    def handle_import(self):
        def on_import(runs):
            self.parent.stats.runs = runs
            self.parent.update_stats_ui()
            if self.parent.history_window and self.parent.history_window.winfo_exists():
                self.parent.history_window.render_times()
        import_stats(self, on_import)

    def capture_keybind(self, entry_widget):
        self.focus_set()
        entry_widget.delete(0, "end")
        entry_widget.insert(0, "Press key...")
        
        def on_key(event):
            ignore = [
                'Control_L', 'Control_R', 'Shift_L', 'Shift_R', 
                'Alt_L', 'Alt_R', 'Win_L', 'Win_R', 
                'Meta_L', 'Meta_R', 'Super_L', 'Super_R'
            ]
            if event.keysym in ignore:
                return
                
            self.unbind("<Key>")
            modifiers = []
            if sys.platform == "darwin":
                if event.state & 0x0008: modifiers.append("Command")
                if event.state & 0x0004: modifiers.append("Control")
                if event.state & 0x0001: modifiers.append("Shift")
                if event.state & 0x0010: modifiers.append("Option")
            else:
                if event.state & 0x0004: modifiers.append("Control")
                if event.state & 0x0001: modifiers.append("Shift")
                if event.state & 131072: modifiers.append("Alt")
                
            bind_str = f"<{'-'.join(modifiers + [event.keysym])}>" if modifiers else f"<{event.keysym}>"
            entry_widget.delete(0, "end")
            entry_widget.insert(0, bind_str)
            
        self.bind("<Key>", on_key)

    def apply_keybinds(self):
        default_ok = DEFAULT_KEYBINDS["keybind_ok"]
        default_dnf = DEFAULT_KEYBINDS["keybind_dnf"]
        default_del = DEFAULT_KEYBINDS["keybind_delete"]
        try:
            self.parent.unbind(app_settings.get("keybind_ok", default_ok))
            self.parent.unbind(app_settings.get("keybind_dnf", default_dnf))
            self.parent.unbind(app_settings.get("keybind_delete", default_del))
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
        self.history_window = None

        self.timer_state = "STOPPED"
        self.start_time = 0.0
        self.elapsed_time = 0.0 
        
        self.stats_visible = False

        self.setup_ui()
        self.setup_streamer()

        self.bind("<space>", self.manual_trigger)
        self.bind(app_settings.get("keybind_ok", DEFAULT_KEYBINDS["keybind_ok"]), self.set_ok)
        self.bind(app_settings.get("keybind_dnf", DEFAULT_KEYBINDS["keybind_dnf"]), self.set_dnf)
        self.bind(app_settings.get("keybind_delete", DEFAULT_KEYBINDS["keybind_delete"]), self.delete_last)
        
        self.update_stats_ui()
        self.update_timer_loop()
        
        if getattr(sys, 'frozen', False):
            self.check_for_updates()

    def check_for_updates(self, manual=False):
        def update_thread():
            try:
                req = urllib.request.Request(GITHUB_API_URL, headers={'User-Agent': 'FirewallTracker-App'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode())
                    latest_version = data.get("tag_name", "")
                    
                    if latest_version and latest_version.replace("v","") > CURRENT_VERSION.replace("v",""):
                        release_url = data.get("html_url", "https://github.com/Dylan2228/firewall-tracker/releases/latest")
                        self.after(2000 if not manual else 0, lambda: self.prompt_update(latest_version, release_url))
                    elif manual:
                        self.after(0, lambda: messagebox.showinfo("Updater", f"You are on the latest version! ({CURRENT_VERSION})"))
            except Exception as e:
                self.after(0, self.log_debug, f"Update check failed: {e}")
                if manual:
                    self.after(0, lambda: messagebox.showerror("Updater Error", f"Failed to check for updates:\n{e}"))
                
        threading.Thread(target=update_thread, daemon=True).start()

    def prompt_update(self, version, release_url):
        result = messagebox.askyesno(
            "Update Available", 
            f"A new version of Firewall Tracker ({version}) is available!\n\nWould you like to open the download page to update?"
        )
        if result:
            webbrowser.open(release_url)

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

        self.time_label = ctk.CTkLabel(self.top_frame, text="0:00.000", font=(MONO_FONT, 80, "bold"))
        self.time_label.pack(expand=True, pady=(20, 0))

        self.ao5_label = ctk.CTkLabel(self.top_frame, text="AO5: -:--.---", font=(MONO_FONT, 24, "underline"))
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

        self.btn_history = ctk.CTkButton(self.action_frame, text="📋 Times", width=90, height=35, font=("Arial", 14, "bold"), fg_color=("gray75", "gray25"), hover_color=("gray70", "gray30"), command=self.open_times_history)
        self.btn_history.pack(side="left", padx=5)

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
        self.lbl_curr_ao5 = ctk.CTkLabel(self.current_stats_frame, text="-:--.---", font=(MONO_FONT, 22, "bold"))
        self.lbl_curr_ao5.pack(anchor="w", padx=10)
        
        ctk.CTkLabel(self.current_stats_frame, text="AO12", font=("Arial", 12), text_color="gray").pack(anchor="w", padx=10, pady=(5,0))
        self.lbl_curr_ao12 = ctk.CTkLabel(self.current_stats_frame, text="-:--.---", font=(MONO_FONT, 22, "bold"))
        self.lbl_curr_ao12.pack(anchor="w", padx=10)
        
        ctk.CTkLabel(self.current_stats_frame, text="AO100", font=("Arial", 12), text_color="gray").pack(anchor="w", padx=10, pady=(5,0))
        self.lbl_curr_ao100 = ctk.CTkLabel(self.current_stats_frame, text="-", font=(MONO_FONT, 18, "bold"))
        self.lbl_curr_ao100.pack(anchor="w", padx=10, pady=(0, 10))

        # 2. Best Single
        self.best_single_frame = ctk.CTkFrame(self.stats_frame, fg_color="#4B77FF")
        self.best_single_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(self.best_single_frame, text="BEST SINGLE", font=("Arial", 10, "bold"), text_color="white").pack(anchor="w", padx=10, pady=(10, 0))
        self.lbl_best_single = ctk.CTkLabel(self.best_single_frame, text="-:--.---", font=(MONO_FONT, 28, "bold"), text_color="white")
        self.lbl_best_single.pack(anchor="w", padx=10, pady=(0, 10))

        # 3. Best Stats
        self.best_stats_frame = ctk.CTkFrame(self.stats_frame)
        self.best_stats_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(self.best_stats_frame, text="BEST STATS", font=("Arial", 10, "bold"), text_color="gray").pack(anchor="w", padx=10, pady=(10, 0))
        
        ctk.CTkLabel(self.best_stats_frame, text="AO12", font=("Arial", 12), text_color="gray").pack(anchor="w", padx=10, pady=(5,0))
        self.lbl_best_ao12 = ctk.CTkLabel(self.best_stats_frame, text="-:--.---", font=(MONO_FONT, 22, "bold"))
        self.lbl_best_ao12.pack(anchor="w", padx=10)
        
        ctk.CTkLabel(self.best_stats_frame, text="AO100", font=("Arial", 12), text_color="gray").pack(anchor="w", padx=10, pady=(5,0))
        self.lbl_best_ao100 = ctk.CTkLabel(self.best_stats_frame, text="-", font=(MONO_FONT, 18, "bold"))
        self.lbl_best_ao100.pack(anchor="w", padx=10, pady=(0, 10))

        # --- Right Column ---
        # 4. Count and Mean (stacked)
        self.right_top_frame = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
        self.right_top_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.right_top_frame.grid_columnconfigure(0, weight=1)
        self.right_top_frame.grid_rowconfigure((0,1), weight=1)
        
        self.count_frame = ctk.CTkFrame(self.right_top_frame)
        self.count_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        ctk.CTkLabel(self.count_frame, text="FIREWALL COUNT", font=("Arial", 12, "bold"), text_color="gray").pack(anchor="w", padx=10, pady=(10, 0))
        self.lbl_count = ctk.CTkLabel(self.count_frame, text="0", font=(MONO_FONT, 24, "bold"))
        self.lbl_count.pack(anchor="w", padx=10, pady=(0, 10))

        self.mean_frame = ctk.CTkFrame(self.right_top_frame)
        self.mean_frame.grid(row=1, column=0, sticky="nsew", pady=(5, 0))
        ctk.CTkLabel(self.mean_frame, text="SESSION MEAN", font=("Arial", 12, "bold"), text_color="gray").pack(anchor="w", padx=10, pady=(10, 0))
        self.lbl_mean = ctk.CTkLabel(self.mean_frame, text="-:--.---", font=(MONO_FONT, 24, "bold"))
        self.lbl_mean.pack(anchor="w", padx=10, pady=(0, 10))

        # 5. Best AO5 Details
        self.best_ao5_frame = ctk.CTkFrame(self.stats_frame)
        self.best_ao5_frame.grid(row=1, column=1, rowspan=2, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(self.best_ao5_frame, text="BEST AO5", font=("Arial", 12, "bold"), text_color="gray").pack(anchor="w", padx=10, pady=(10, 0))
        self.lbl_best_ao5 = ctk.CTkLabel(self.best_ao5_frame, text="-:--.---", font=(MONO_FONT, 28, "bold"), text_color="#4B77FF")
        self.lbl_best_ao5.pack(anchor="w", padx=10, pady=(0, 5))
        self.lbl_best_ao5_details = ctk.CTkLabel(self.best_ao5_frame, text="-\n-\n-\n-\n-", font=(MONO_FONT, 12), text_color="gray", justify="left")
        self.lbl_best_ao5_details.pack(anchor="w", padx=10, pady=(0, 10))

    def on_top_frame_resize(self, event):
        if event.widget == self.top_frame:
            h_size = int(event.height * 0.45)
            w_size = int(event.width * 0.12)
            new_size = max(10, min(h_size, w_size))
            self.time_label.configure(font=(MONO_FONT, new_size, "bold"))

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

    def open_times_history(self):
        if self.history_window is None or not self.history_window.winfo_exists():
            self.history_window = TimesHistoryWindow(self)
        else:
            self.history_window.focus()

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
            if self.history_window and self.history_window.winfo_exists():
                self.history_window.render_times()

    def set_dnf(self, event=None):
        if self.timer_state in ["RUNNING", "PAUSED"]:
            self.stop_timer()
        if self.stats.runs and self.timer_state == "STOPPED":
            self.stats.runs[-1].penalty = "DNF"
            self.update_stats_ui()
            save_runs(self.stats.runs)
            if self.history_window and self.history_window.winfo_exists():
                self.history_window.render_times()

    def delete_last(self, event=None):
        if self.timer_state in ["RUNNING", "PAUSED"]:
            self.stop_timer()
        if self.stats.runs and self.timer_state == "STOPPED":
            self.stats.runs.pop()
            self.update_stats_ui()
            save_runs(self.stats.runs)
            if self.history_window and self.history_window.winfo_exists():
                self.history_window.render_times()

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
        self.set_time_text("0:00.000")
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
            if self.history_window and self.history_window.winfo_exists():
                self.history_window.render_times()
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
            self.set_time_text("0:00.000")
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
        if self.history_window and self.history_window.winfo_exists():
            app_settings["geometries"]["history"] = self.history_window.geometry()
            self.history_window.destroy()
        save_settings(app_settings)
        self.streamer.stop()
        super().destroy()


if __name__ == "__main__":
    app = FirewallTrackerApp()
    app.mainloop()
