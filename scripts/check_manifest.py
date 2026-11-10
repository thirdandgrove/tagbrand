#!/usr/bin/env python3
"""Verify every entry in manifest.json, including size and SHA-256."""
import hashlib
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
files = json.loads((root / "manifest.json").read_text())["files"]
errors = []
for name, expected in files.items():
    path = root / name
    if not path.is_file():
        errors.append(f"Missing: {name}")
        continue
    data = path.read_bytes()
    if len(data) != expected["bytes"]:
        errors.append(f"Size mismatch: {name}")
    if hashlib.sha256(data).hexdigest() != expected["sha256"]:
        errors.append(f"SHA-256 mismatch: {name}")
if errors:
    sys.exit("\n".join(errors))
print(f"Manifest verified: {len(files)} files")
