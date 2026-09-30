#!/usr/bin/env python3
# Thanatos/tools/pack_bundle.py
"""
Portable Packaging Tool for Thanatos.
Archives the core codebase, configuration templates, prompt definitions,
and initial data into a clean, portable zip or tar.gz file.
Excludes virtual environments, cache files, and git history for easy transfer
to another PC, server, or Android phone (Termux).

Usage:
    python tools/pack_bundle.py
    python tools/pack_bundle.py --format tar.gz --output thanatos_portable.tar.gz
"""

import argparse
import os
import shutil
import sys
import tarfile
import zipfile
from typing import List

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

EXCLUDE_DIRS = {
    ".git",
    ".github",
    ".idea",
    ".vscode",
    "venv",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
    "egg-info",
}

EXCLUDE_EXTS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".log",
    ".tmp",
}


def should_exclude(rel_path: str) -> bool:
    parts = rel_path.replace("\\", "/").split("/")
    for part in parts:
        if part in EXCLUDE_DIRS:
            return True
    _, ext = os.path.splitext(rel_path)
    if ext.lower() in EXCLUDE_EXTS:
        return True
    return False


def get_bundle_files(root_dir: str) -> List[str]:
    files_to_pack = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Filter out directories in place so os.walk doesn't recurse into them
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]

        for fname in filenames:
            full_path = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(full_path, root_dir)
            if not should_exclude(rel_path):
                files_to_pack.append(rel_path)
    return files_to_pack


def create_zip(root_dir: str, out_file: str, files: List[str]) -> None:
    print(f"[•] Creating ZIP archive: {out_file}...")
    with zipfile.ZipFile(out_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel_path in files:
            full_path = os.path.join(root_dir, rel_path)
            zf.write(full_path, arcname=rel_path)
    size_mb = os.path.getsize(out_file) / (1024 * 1024)
    print(f"[✓] Package complete: {out_file} ({size_mb:.2f} MB, {len(files)} files)")


def create_tar(root_dir: str, out_file: str, files: List[str]) -> None:
    print(f"[•] Creating TAR.GZ archive: {out_file}...")
    with tarfile.open(out_file, "w:gz") as tf:
        for rel_path in files:
            full_path = os.path.join(root_dir, rel_path)
            tf.add(full_path, arcname=rel_path)
    size_mb = os.path.getsize(out_file) / (1024 * 1024)
    print(f"[✓] Package complete: {out_file} ({size_mb:.2f} MB, {len(files)} files)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Pack Thanatos into a portable archive for transfer")
    parser.add_argument("--format", choices=["zip", "tar.gz"], default="zip", help="Archive format")
    parser.add_argument("--output", type=str, default=None, help="Output destination file path")
    args = parser.parse_args()

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root_dir)

    out_file = args.output
    if not out_file:
        out_file = f"thanatos_portable.{'zip' if args.format == 'zip' else 'tar.gz'}"

    files = get_bundle_files(root_dir)
    print(f"[•] Found {len(files)} portable files to package from {root_dir}")

    if args.format == "zip":
        create_zip(root_dir, out_file, files)
    else:
        create_tar(root_dir, out_file, files)

    print(f"\nHow to unbundle on another PC or Termux:")
    if args.format == "zip":
        print(f"  unzip {out_file} -d Thanatos && cd Thanatos")
    else:
        print(f"  tar -xzf {out_file} -C Thanatos && cd Thanatos")
    print(f"  pip install -r requirements.txt")
    print(f"  ./install_cli.sh (or .\\install_cli.ps1 on Windows)\n")


if __name__ == "__main__":
    main()
