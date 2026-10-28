#!/bin/bash
cd "$(dirname "$0")"

echo "============================================="
echo "   Firewall Tracker - macOS App & DMG Builder"
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
    echo "Step 3: Creating Firewall-Tracker.dmg (drag-and-drop installer)..."
    rm -rf dist/dmg_root
    mkdir -p dist/dmg_root
    cp -R "dist/Firewall Tracker.app" dist/dmg_root/
    ln -s /Applications dist/dmg_root/Applications
    rm -f "dist/Firewall-Tracker.dmg"
    hdiutil create -volname "Firewall Tracker" -srcfolder dist/dmg_root -ov -format UDZO "dist/Firewall-Tracker.dmg"
    rm -rf dist/dmg_root

    echo "Step 4: Creating distribution zip..."
    cd dist
    zip -rq "Firewall Tracker-macOS.zip" "Firewall Tracker.app"
    cd ..

    echo "============================================="
    echo " SUCCESS!"
    echo " 'Firewall-Tracker.dmg' is ready in your 'dist' folder!"
    echo " Double-click the DMG and drag Firewall Tracker into Applications!"
    echo "============================================="
else
    echo "Build completed. Check the 'dist' directory for the executable."
fi
