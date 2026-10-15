"""Rebuild every dataset in datasets/ from the archived reports.

    python3 scripts/extract/run_all.py

Needs pdftotext (poppler-utils) and reports/index.csv (scripts/build_index.py).
"""
import google
import meta
import sharechat_moj
import pinterest
import roblox
import snap
import validate
import whatsapp
import x

if __name__ == "__main__":
    for mod in (google, meta, whatsapp, x, snap, pinterest, roblox):
        mod.main()
    sharechat_moj.run("sharechat", "ShareChat")
    sharechat_moj.run("moj", "Moj")
    validate.main()
