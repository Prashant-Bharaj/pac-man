"""Zip the pygbag web build output for itch.io upload."""

import os
import sys
import zipfile

web_dir, out_zip = sys.argv[1], sys.argv[2]

with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
    for name in os.listdir(web_dir):
        zf.write(os.path.join(web_dir, name), name)

size_kb = os.path.getsize(out_zip) / 1024
print(f"Created {out_zip} ({size_kb:.1f} KB) — ready for itch.io upload")
