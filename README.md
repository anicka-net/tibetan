# བོད་སྐད་སློབ་ཚན། — Tibetan Learning App

An interactive Tibetan language learning app covering CEFR levels A0 through B1,
built from [Esukhia's](https://esukhia.online/) publicly available textbooks.

## What is this?

This repository contains **build scripts** that download Esukhia's CC-licensed
textbook PDFs and turn them into an interactive study app. No AI required —
just Python and `pdftotext`.

Esukhia's textbooks are published under a Creative Commons license that does
not permit derivative works. This repo respects that: it distributes no
textbook content, only the tools to build a personal study app from the
publicly available PDFs. Same pattern as a Linux package that downloads its
source at build time.

## Quick start

### Prerequisites

- Python 3.6+
- `pdftotext` (from poppler-utils)

```bash
# Install pdftotext if you don't have it
sudo apt install poppler-utils     # Debian/Ubuntu
# sudo zypper install poppler-tools  # openSUSE
# brew install poppler               # macOS
```

### Build

```bash
git clone https://github.com/anicka-net/tibetan.git
cd tibetan
./build.sh
```

That's it. The script downloads the PDFs, extracts text, parses lessons,
and generates a single `index.html` you can open in any browser.

## What you get

A single `index.html` file (~370 KB) containing:

- **83 sub-lessons** across 4 CEFR levels (A0 through B1)
- **671 vocabulary items** with Tibetan definitions (608 with English translations)
- **584 fill-in-the-blank exercises** from the textbooks
- **160 common phrases**, **60 proverbs**, **37 dialogue turns**
- Flashcards, multiple choice, matching, fill-in-the-blank practice
- Progress tracking, streaks, and XP (localStorage)
- Mobile-friendly, works offline once built

## Contributing translations

Translations live in `translations.json` — a standalone Tibetan-English
dictionary covering ~90% of vocabulary. It's just JSON key-value pairs:

```json
"བོད་སྐད": "Tibetan language",
"ཁ་ལག": "Food"
```

Edit the file, then re-run:

```bash
python3 parse_textbooks.py
python3 build_app.py
```

The beta textbooks use non-standard orthography, so many words need variant
spellings as separate entries (e.g., `སོབ` = `སློབ`, `སོད` = `སྤྱོད`).

## Repository contents

| File | Purpose | Contains textbook content? |
|------|---------|--------------------------|
| `build.sh` | One-command build script | No |
| `translations.json` | Tibetan-English dictionary | No (independent translations) |
| `parse_textbooks.py` | Extracts lesson data from text files | No (parsing logic only) |
| `build_app.py` | Generates the HTML app | No (HTML/CSS/JS template) |
| `CLAUDE.md` | Build instructions for Claude Code | No (topic names only) |
| `README.md` | This file | No |

Generated files (not in repo): `textbooks/`, `lesson_data.json`, `index.html`

## Using with Claude Code

If you have [Claude Code](https://docs.anthropic.com/en/docs/claude-code),
you can run `claude` in the repo directory. It reads `CLAUDE.md` and can
build the app, answer questions about the content, and expand translations.
But this is entirely optional — the build scripts work on their own.

## Credits

- **Textbooks**: [Esukhia](https://esukhia.online/textbooks/) (CC licensed)
- **App and tools**: Built with [Claude Code](https://docs.anthropic.com/en/docs/claude-code)

## License

The build scripts and app template in this repository are released under the
MIT License. The Esukhia textbook content (downloaded at build time) is subject
to Esukhia's Creative Commons license.
