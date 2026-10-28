#!/bin/bash
cd "$(dirname "$0")"

echo "============================================="
echo "   Firewall Tracker - macOS App Builder"
echo "============================================="

# Verify python3
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required. Please install it from https://python.org or via Homebrew."
    exit 1
fi

echo "Step 1: Installing required Python packages..."
python3 -m pip install --upgrade pip
python3 -m pip install customtkinter pyinstaller darkdetect

echo "Step 2: Building Firewall Tracker.app..."
python3 -m PyInstaller \
    --noconsole \
    --windowed \
    --onefile \
    --collect-all customtkinter \
    --name "Firewall Tracker" \
    firewall_tracker.py

if [ -d "dist/Firewall Tracker.app" ]; then
    echo "Step 3: Creating distribution zip..."
    cd dist
    zip -rq "Firewall Tracker-macOS.zip" "Firewall Tracker.app"
    cd ..
    echo "============================================="
    echo " SUCCESS!"
    echo " 'Firewall Tracker.app' is ready in your 'dist' folder."
    echo "============================================="
else
    echo "Build completed. Check the 'dist' directory for the executable."
fi

