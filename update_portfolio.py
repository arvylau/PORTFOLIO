#!/usr/bin/env python3
"""
Portfolio Update Automation Script
Automatically updates PORTFOLIO.csv from Downloads and regenerates the portal
"""

import shutil
import os
from datetime import datetime
import subprocess

# Paths
DOWNLOADS_PATH = r"C:\Users\lauar\Downloads\PORTFOLIO.csv"
PORTFOLIO_DIR = r"C:\Users\lauar\Documents\GitHub\PORTFOLIO"
PORTFOLIO_CSV = os.path.join(PORTFOLIO_DIR, "PORTFOLIO.csv")
BACKUP_DIR = os.path.join(PORTFOLIO_DIR, "backups")
GENERATOR_SCRIPT = os.path.join(PORTFOLIO_DIR, "create_portfolio_portal_v2.py")

def main():
    print("=" * 70)
    print("Portfolio Update Automation")
    print("=" * 70)

    # Check if new file exists
    if not os.path.exists(DOWNLOADS_PATH):
        print(f"ERROR: No PORTFOLIO.csv found in Downloads folder")
        print(f"Expected: {DOWNLOADS_PATH}")
        return

    # Create backup directory if it doesn't exist
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        print(f"Created backup directory: {BACKUP_DIR}")

    # Backup current file if it exists
    if os.path.exists(PORTFOLIO_CSV):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BACKUP_DIR, f"PORTFOLIO_{timestamp}.csv")
        shutil.copy2(PORTFOLIO_CSV, backup_path)
        print(f"[OK] Backed up current file to: {backup_path}")

    # Move new file from Downloads
    try:
        shutil.move(DOWNLOADS_PATH, PORTFOLIO_CSV)
        print(f"[OK] Moved new PORTFOLIO.csv from Downloads")
    except PermissionError:
        print("\nERROR: Cannot overwrite PORTFOLIO.csv - file is locked!")
        print("Please close Excel or any other program that has this file open.")
        print("\nPress Enter after closing the file to retry...")
        input()
        shutil.move(DOWNLOADS_PATH, PORTFOLIO_CSV)
        print(f"[OK] Moved new PORTFOLIO.csv from Downloads")

    # Get file info
    file_size = os.path.getsize(PORTFOLIO_CSV) / 1024  # KB
    mod_time = datetime.fromtimestamp(os.path.getmtime(PORTFOLIO_CSV))
    print(f"  File size: {file_size:.1f} KB")
    print(f"  Modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Regenerate portal
    print("\nRegenerating portfolio portal...")
    result = subprocess.run(
        [r"C:\Program Files\Python311\python.exe", GENERATOR_SCRIPT],
        cwd=PORTFOLIO_DIR,
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("[OK] Portal regenerated successfully!")
        print(result.stdout)
    else:
        print("ERROR: Portal generation failed")
        print(result.stderr)
        return

    print("\n" + "=" * 70)
    print("Update complete! Open portfolio_portal.html to view changes.")
    print("=" * 70)

if __name__ == "__main__":
    main()
