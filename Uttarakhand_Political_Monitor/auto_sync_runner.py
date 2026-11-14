import os
import sys
import time
import subprocess
from datetime import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

SYNC_SCRIPT = r"D:\Google-Dowanlod\Uttarakhand_Political_Monitor\sync_sheet_data.py"
META_SCRIPT = r"D:\Google-Dowanlod\Uttarakhand_Political_Monitor\update_meta_data.py"
INTERVAL_SECONDS = 3600  # Sync every 1 hour

def run_sync_cycle():
    now_str = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p IST")
    print(f"\n[{now_str}] Starting automated dashboard sync cycle...")
    try:
        res1 = subprocess.run([sys.executable, SYNC_SCRIPT], capture_output=True, text=True, timeout=180)
        print("  sync_sheet_data output:\n", res1.stdout.strip())
        if res1.returncode != 0:
            print("  sync_sheet_data error:\n", res1.stderr.strip())

        res2 = subprocess.run([sys.executable, META_SCRIPT], capture_output=True, text=True, timeout=60)
        print("  update_meta_data output:\n", res2.stdout.strip())
        if res2.returncode != 0:
            print("  update_meta_data error:\n", res2.stderr.strip())

        print(f"[{datetime.now().strftime('%I:%M:%S %p IST')}] Sync cycle completed successfully!")
    except Exception as e:
        print(f"  Sync cycle encountered an error: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("   AUTOMATED DASHBOARD SYNC RUNNER (UK & HP POLITICAL MONITOR)")
    print("   Target Google Sheet: 1GNGN-2dFiDcg59Vxm3Oa9gkzGujW4QiqTbMtyEF6itQ")
    print("   Interval: Every 60 minutes")
    print("=" * 60)

    # Run first sync immediately
    run_sync_cycle()

    # Loop for periodic background sync
    while True:
        try:
            print(f"\nWaiting {INTERVAL_SECONDS // 60} minutes for next automated check...")
            time.sleep(INTERVAL_SECONDS)
            run_sync_cycle()
        except KeyboardInterrupt:
            print("\nAuto-sync runner stopped by user.")
            break
