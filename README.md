# Firewall Tracker

A lightweight, overlay-style timer and statistics tracker for Roblox speedruns, specifically designed for the Pressure Firewall minigame. 

## Features
- **Auto-Tracking**: Automatically reads from the Roblox log files to accurately trigger timer starts, stops, and resets based on in-game events.
- **WCA Statistics**: Automatically calculates your MO3, AO5, AO12, and AO100 (dropping the top/bottom 5% of solves just like the World Cube Association).
- **Session Management**: Penalty buttons allow you to mark a run as a DNF (Did Not Finish) or completely delete a scuffed run. 
- **OBS Popout Timer**: Includes a borderless popout timer window that scales dynamically and stays on top of other windows—perfect for OBS capture!
- **Theming**: Comes with multiple color themes including Default Blue, Catppuccin, and Custom Firewall.
- **State Persistence**: Remembers your exact window positions, sizes, and theme preferences between sessions.

## Installation
1. Go to the **Releases** tab on the right side of this GitHub page.
2. Download the latest `firewall_tracker.exe`.
3. Run the executable. (Note: Windows Defender may show a "Windows protected your PC" warning since the `.exe` is not code-signed. Click "More info" -> "Run anyway").

## Development
To build the executable from source:
1. Install Python 3.
2. Install the required dependencies: `pip install customtkinter`
3. Build using PyInstaller: `pyinstaller --noconsole --onefile --collect-all customtkinter firewall_tracker.py`
