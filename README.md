# !!!DISCLAIMER: This timer is not approved nor official to the SRC Leaderboard Rules. This is made as a baseline of what your final firewall time would look like.!!!

# Firewall Tracker

A vibe coded (sorry) firewall tracker and timer used to track your time based on certain console outputs in the console itself.

## Features
- **Accurate Timing**: Automatically reads from the Roblox log files to accurately trigger timer based on certain console outputs. Also accounts for time spent waiting at the gate!
- **Stats Page**: Automatically calculates your MO3, AO5, AO12, and AO100.
- **Session Management**: Penalty buttons allow you to mark a run as a DNF (Did Not Finish) or completely delete a scuffed run. 
- **Popout Timer**: Includes a borderless popout timer window. Useful for OBS :D
- **Theming**: Comes with multiple color themes because I'm such a theme larper

## Installation
1. Go to the **Releases** tab on the right side of this GitHub page.
2. Download the latest `firewall_tracker.exe`.
3. Run the executable. (Note: Windows Defender may show a "Windows protected your PC" warning since the `.exe` is not code-signed. Click "More info" -> "Run anyway").

## Development
To build the executable from source:
1. Install Python 3.
2. Install the required dependencies: `pip install customtkinter`
3. Build using PyInstaller: `pyinstaller --noconsole --onefile --collect-all customtkinter firewall_tracker.py`
