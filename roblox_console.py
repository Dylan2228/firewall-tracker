"""
roblox_console.py
-----------------
Standalone Roblox live console streamer.

Tails the latest Roblox Player log and emits only Developer Console
(F9 / print/warn/error) lines in real time via a callback.

Usage
-----
    from roblox_console import RobloxConsoleStreamer

    def on_line(time_str, level, message):
        print(f"[{time_str}] [{level}] {message}")

    streamer = RobloxConsoleStreamer(on_line)
    streamer.start()

    # ... your app runs ...

    streamer.stop()

Callback signature
------------------
    on_line(time_str: str, level: str, message: str)

    time_str  - "HH:MM:SS" extracted from the log timestamp
    level     - "INFO", "WARNING", or "ERROR"
    message   - the raw Developer Console message text
"""

import glob
import os
import re
import threading
import time
from typing import Callable, Optional


# ---------------------------------------------------------------------------
# Log-line header parser
# ---------------------------------------------------------------------------
_HEADER = re.compile(
    r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\.(\d{3})Z"   # timestamp
    r",[0-9.]+,[a-f0-9]+,\d+"                               # elapsed, thread, level-int
    r"(?:,([A-Za-z]+))?"                                    # optional severity word
    r"\s+\[([^\]]+)\]\s*(.*)$"                              # [Tag] message
)

# Tags whose output counts as Developer Console (F9)
_CONSOLE_TAGS = {"creatoroutput", "creatorwarning", "creatorerror", "script", "gamejoinutil"}


def _is_console_tag(tag: str) -> bool:
    t = tag.lower()
    return any(ct in t for ct in _CONSOLE_TAGS)


def _parse_level(tag: str, severity: Optional[str]) -> str:
    tl = tag.lower()
    sl = (severity or "").lower()
    if "error" in tl or sl == "error":
        return "ERROR"
    if "warn" in tl or sl == "warning":
        return "WARNING"
    return "INFO"


# ---------------------------------------------------------------------------
# Log file locator
# ---------------------------------------------------------------------------
def _latest_log() -> Optional[str]:
    log_dir = os.path.expandvars(r"%LOCALAPPDATA%\Roblox\logs")
    if not os.path.isdir(log_dir):
        return None
    files = glob.glob(os.path.join(log_dir, "*Player*.log"))
    if not files:
        return None
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]


# ---------------------------------------------------------------------------
# Streamer
# ---------------------------------------------------------------------------
class RobloxConsoleStreamer:
    """
    Streams Roblox Developer Console lines to on_line in real time.

    Parameters
    ----------
    on_line : callable(time_str, level, message)
        Called on the streaming thread for every new console line.
    poll_interval : float
        Seconds between file reads (default 0.15 = ~150 ms).
    """

    def __init__(self, on_line: Callable[[str, str, str], None], poll_interval: float = 0.15):
        self._on_line = on_line
        self._poll_interval = poll_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._file_path: Optional[str] = None
        self._fh = None

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="RobloxConsoleStreamer"
        )
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._fh:
            try:
                self._fh.close()
            except Exception:
                pass
            self._fh = None

    def _loop(self) -> None:
        while self._running:
            try:
                latest = _latest_log()
                if latest and latest != self._file_path:
                    self._open(latest)
                if self._fh:
                    chunk = self._fh.read()
                    if chunk:
                        self._process(chunk)
            except Exception:
                pass
            time.sleep(self._poll_interval)

    def _open(self, path: str) -> None:
        if self._fh:
            try:
                self._fh.close()
            except Exception:
                pass
        self._file_path = path
        self._fh = open(path, "r", encoding="utf-8", errors="ignore")
        
        # Seek to the end of the file to ignore historical logs.
        # Reading old logs causes instant start/stop triggers and creates fake 0.001s runs!
        self._fh.seek(0, 2)

    def _process(self, text: str) -> None:
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            m = _HEADER.match(line)
            if not m:
                continue

            ts_date_time = m.group(1)
            severity     = m.group(3)
            tag          = m.group(4)
            message      = m.group(5)

            if not _is_console_tag(tag):
                continue

            time_str = ts_date_time.split("T")[1] if "T" in ts_date_time else ts_date_time
            level    = _parse_level(tag, severity)

            self._on_line(time_str, level, message)


# ---------------------------------------------------------------------------
# Quick CLI demo - run this file directly to see the live console
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    COLORS = {"ERROR": "\033[91m", "WARNING": "\033[93m", "INFO": "\033[0m"}
    RESET  = "\033[0m"

    def print_line(time_str: str, level: str, message: str) -> None:
        color = COLORS.get(level, "")
        print(f"{color}[{time_str}] [{level:7s}] {message}{RESET}")

    print("Roblox Console Streamer - waiting for Roblox log...  (Ctrl+C to quit)\n")
    s = RobloxConsoleStreamer(print_line)
    s.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        s.stop()
        print("\nStopped.")
