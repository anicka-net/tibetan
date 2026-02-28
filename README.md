# བོད་སྐད་སློབ་ཚན། — Tibetan Learning App

An interactive Tibetan language learning app covering CEFR levels A0 through B1,
built from [Esukhia's](https://esukhia.online/) publicly available textbooks.

## What is this?

This repository contains **build instructions and scripts** — not the app itself.
The app is generated locally on your machine by downloading Esukhia's CC-licensed
textbook PDFs and processing them into an interactive lesson format.

This is the same pattern used for years in Linux packaging: the spec file
describes how to fetch and build from source, but the source material itself
is not redistributed. Only the instructions travel.

## Why?

Esukhia publishes excellent Tibetan textbooks under a Creative Commons license
that does not permit derivative works. We respect that. This repo distributes
no textbook content — only the tools to build a personal study app from the
publicly available PDFs.

The textbooks cover ~85 teaching units across 4 levels (A0 through B1),
roughly 1-2 years of structured Tibetan study, from the alphabet to
intermediate conversation. The generated app turns this into an interactive
experience with flashcards, multiple-choice exercises, matching, fill-in-the-blank
practice, dialogues, and proverbs.

## How to build

### Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (or any Claude
  instance that can run shell commands)
- `pdftotext` (from poppler-utils)
- Python 3.6+

### Quick start

Clone this repo and let Claude Code do the rest:

```
git clone https://github.com/anicka-net/tibetan.git
cd tibetan
claude
```

Claude will read `CLAUDE.md` and follow the instructions: download the PDFs,
extract text, parse lessons, and build the app. Or you can run the steps
manually — see `CLAUDE.md` for details.

### Manual build

```bash
# Install pdftotext
sudo zypper install poppler-tools  # openSUSE
# sudo apt install poppler-utils   # Debian/Ubuntu
# brew install poppler              # macOS

# Download textbooks
mkdir -p textbooks && cd textbooks
for f in A0-so-ri-me-bu A0-IntroWeek \
         A1-Book-1 A1-Book-2 A1-V2 A1-Jongdeb A1-Missions A1-Passport \
         A2-Book-1 A2-Book-2 A2-V2 A2-Jongdeb A2-Passport \
         B1-Book-1 B1-Book-2; do
  curl -sS -L -O "https://esukhia.online/PDF/${f}.pdf"
done
cd ..

# Extract text and build
for f in textbooks/*.pdf; do pdftotext "$f" "${f%.pdf}.txt"; done
python3 parse_textbooks.py
python3 build_app.py

# Open the app
xdg-open index.html  # or just open in your browser
```

## What you get

A single `index.html` file (~360 KB) containing:

- **83 sub-lessons** across 4 CEFR levels
- **663 vocabulary items** with Tibetan definitions (103 with English translations)
- **584 fill-in-the-blank exercises** from the textbooks
- **160 common phrases**, **60 proverbs**, **37 dialogue turns**
- Progress tracking, streaks, and XP (localStorage)
- Mobile-friendly, works offline once built

## Cost estimate

If you let Claude Code build the app from `CLAUDE.md`, expect roughly:

| Model | Input tokens | Output tokens | Estimated cost |
|-------|-------------|---------------|----------------|
| Sonnet | ~300K | ~50K | $3-5 |
| Opus | ~300K | ~50K | $8-15 |

Most tokens go to reading the extracted PDF text files.

## Repository contents

| File | Purpose | Contains textbook content? |
|------|---------|--------------------------|
| `CLAUDE.md` | Build instructions for Claude | No (topic names only) |
| `parse_textbooks.py` | Extracts lesson data from text files | No (parsing logic + translations) |
| `build_app.py` | Generates the HTML app | No (HTML/CSS/JS template) |
| `README.md` | This file | No |

Generated files (not in repo): `textbooks/`, `lesson_data.json`, `index.html`

## Credits

- **Textbooks**: [Esukhia](https://esukhia.online/textbooks/) (CC licensed)
- **App and tools**: Built with [Claude Code](https://docs.anthropic.com/en/docs/claude-code)

## License

The build scripts and app template in this repository are released under the
MIT License. The Esukhia textbook content (downloaded at build time) is subject
to Esukhia's Creative Commons license.
