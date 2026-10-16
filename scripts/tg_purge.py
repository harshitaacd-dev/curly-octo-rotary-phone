"""Delete all Telegram study data: collection, analysis outputs and the login session.

Usage: python scripts/tg_purge.py data/telegram [telegram_chats.json]

Run it once the thesis is submitted (the retention period ends on DELETE_AFTER in
tg_privacy.py). Asks for confirmation, then removes the folder and, if given, the chat
list. Also log the research account out of Telegram (Settings > Devices) and delete the
account if it was made for the study.
"""
import os, shutil, sys

sys.path.insert(0, os.path.dirname(__file__))
from tg_privacy import DELETE_AFTER  # noqa: E402


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    targets = [p for p in sys.argv[1:] if os.path.exists(p)]
    if not targets:
        sys.exit("Nothing to delete.")
    for p in targets:
        size = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(p) for f in fs) \
            if os.path.isdir(p) else os.path.getsize(p)
        print(f"  {p}  ({size / 1e6:.1f} MB)")
    print(f"Retention period ends {DELETE_AFTER}.")
    if input("Permanently delete the above? Type DELETE: ").strip() != "DELETE":
        sys.exit("Cancelled.")
    for p in targets:
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
        print(f"deleted {p}")


if __name__ == "__main__":
    main()
