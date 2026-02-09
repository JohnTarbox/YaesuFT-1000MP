#!/usr/bin/env python3
"""Build standalone executable using PyInstaller."""

import subprocess
import sys


def main():
    cmd = [sys.executable, "-m", "PyInstaller", "--clean", "ft1000mp.spec"]
    print(f"Running: {' '.join(cmd)}")
    raise SystemExit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
