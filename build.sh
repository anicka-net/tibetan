#!/bin/bash
# Build the Tibetan learning app from Esukhia's textbook PDFs.
# No AI needed — just bash, python3, and pdftotext.

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BOLD='\033[1m'
NC='\033[0m'

step() { echo -e "\n${GREEN}${BOLD}==> $1${NC}"; }
die()  { echo -e "${RED}Error: $1${NC}" >&2; exit 1; }

# Check prerequisites
command -v python3  >/dev/null || die "python3 not found. Install Python 3.6+"
command -v pdftotext >/dev/null || die "pdftotext not found. Install poppler-utils (apt install poppler-utils / zypper install poppler-tools / brew install poppler)"

# Download PDFs
step "Downloading textbooks from Esukhia..."
mkdir -p textbooks
cd textbooks
for f in A0-so-ri-me-bu A0-IntroWeek \
         A1-Book-1 A1-Book-2 A1-V2 A1-Jongdeb A1-Missions A1-Passport \
         A2-Book-1 A2-Book-2 A2-V2 A2-Jongdeb A2-Passport \
         B1-Book-1 B1-Book-2; do
  if [ -f "${f}.pdf" ]; then
    echo "  ${f}.pdf already exists, skipping"
  else
    echo "  Downloading ${f}.pdf..."
    curl -sS -L -O "https://esukhia.online/PDF/${f}.pdf" || echo "  Warning: failed to download ${f}.pdf"
  fi
done
cd ..

# Extract text
step "Extracting text from PDFs..."
for f in textbooks/*.pdf; do
  txt="${f%.pdf}.txt"
  if [ -f "$txt" ]; then
    echo "  $(basename "$txt") already exists, skipping"
  else
    echo "  Extracting $(basename "$f")..."
    pdftotext "$f" "$txt"
  fi
done

# Parse and build
step "Parsing textbooks..."
python3 parse_textbooks.py

step "Building app..."
python3 build_app.py

step "Done!"
echo -e "Open ${BOLD}index.html${NC} in your browser."
echo ""
echo "On Linux:  xdg-open index.html"
echo "On macOS:  open index.html"
