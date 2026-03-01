#!/usr/bin/env python3
"""
Build the Tibetan learning app from Esukhia's textbook PDFs.
Cross-platform (Linux, macOS, Windows). No dependencies beyond Python 3.6+
and pdftotext (from poppler-utils).
"""

import os
import shutil
import subprocess
import sys
import urllib.request
import urllib.error

TEXTBOOKS = [
    "A0-so-ri-me-bu", "A0-IntroWeek",
    "A1-Book-1", "A1-Book-2", "A1-V2", "A1-Jongdeb", "A1-Missions", "A1-Passport",
    "A2-Book-1", "A2-Book-2", "A2-V2", "A2-Jongdeb", "A2-Passport",
    "B1-Book-1", "B1-Book-2",
]

BASE_URL = "https://esukhia.online/PDF/"


def step(msg):
    print(f"\n\033[1;32m==> {msg}\033[0m")


def die(msg):
    print(f"\033[0;31mError: {msg}\033[0m", file=sys.stderr)
    sys.exit(1)


def check_prerequisites():
    if shutil.which("pdftotext") is None:
        die(
            "pdftotext not found. Install poppler:\n"
            "  Debian/Ubuntu:  sudo apt install poppler-utils\n"
            "  openSUSE:       sudo zypper install poppler-tools\n"
            "  macOS:          brew install poppler\n"
            "  Fedora:         sudo dnf install poppler-utils\n"
            "  Windows:        https://github.com/oschwartz10612/poppler-windows/releases"
        )


def download_pdfs():
    step("Downloading textbooks from Esukhia...")
    os.makedirs("textbooks", exist_ok=True)
    for name in TEXTBOOKS:
        path = os.path.join("textbooks", f"{name}.pdf")
        if os.path.exists(path):
            print(f"  {name}.pdf already exists, skipping")
            continue
        url = f"{BASE_URL}{name}.pdf"
        print(f"  Downloading {name}.pdf...")
        try:
            urllib.request.urlretrieve(url, path)
        except urllib.error.URLError as e:
            print(f"  Warning: failed to download {name}.pdf ({e})")


def extract_text():
    step("Extracting text from PDFs...")
    for name in os.listdir("textbooks"):
        if not name.endswith(".pdf"):
            continue
        pdf_path = os.path.join("textbooks", name)
        txt_path = os.path.join("textbooks", name[:-4] + ".txt")
        if os.path.exists(txt_path):
            print(f"  {name[:-4]}.txt already exists, skipping")
            continue
        print(f"  Extracting {name}...")
        subprocess.run(["pdftotext", pdf_path, txt_path], check=True)


def run_script(script, description):
    step(description)
    subprocess.run([sys.executable, script], check=True)


def main():
    check_prerequisites()
    download_pdfs()
    extract_text()
    run_script("parse_textbooks.py", "Parsing textbooks...")
    run_script("build_app.py", "Building app...")

    step("Done!")
    print("Open index.html in your browser.")
    if sys.platform == "linux":
        print("  xdg-open index.html")
    elif sys.platform == "darwin":
        print("  open index.html")
    elif sys.platform == "win32":
        print("  start index.html")


if __name__ == "__main__":
    main()
