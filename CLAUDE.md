# Build an Interactive Tibetan Learning App from Esukhia Textbooks

This file contains instructions for Claude Code to download publicly available
Tibetan language textbooks and build an interactive, spaced-repetition learning
app from their content. The textbooks are published by Esukhia (ནང་བསྟན་སྲི་ཞུ་ཁང)
under a Creative Commons license at https://esukhia.online/textbooks/

The user runs these instructions locally. The app is built fresh from source
material each time. Nothing derivative is distributed — only these build
instructions and the build scripts.

## Step 0: Prerequisites

- A working `pdftotext` command (from poppler-utils)
- Python 3.6+
- A web browser

If `pdftotext` is missing, install it:
- Debian/Ubuntu: `sudo apt install poppler-utils`
- openSUSE: `sudo zypper install poppler-tools`
- macOS: `brew install poppler`
- Fedora: `sudo dnf install poppler-utils`

## Step 1: Download the Textbooks

Download all PDFs from Esukhia into a `textbooks/` directory:

```
mkdir -p textbooks && cd textbooks
for f in A0-so-ri-me-bu A0-IntroWeek \
         A1-Book-1 A1-Book-2 A1-V2 A1-Jongdeb A1-Missions A1-Passport \
         A2-Book-1 A2-Book-2 A2-V2 A2-Jongdeb A2-Passport \
         B1-Book-1 B1-Book-2; do
  curl -sS -L -O "https://esukhia.online/PDF/${f}.pdf"
done
cd ..
```

## Step 2: Extract Text

Extract text from each PDF:

```
for f in textbooks/*.pdf; do
  pdftotext "$f" "${f%.pdf}.txt"
done
```

Tibetan Unicode extracts cleanly from all books EXCEPT A0-so-ri-me-bu
(broken extraction due to color-coded letter formatting — skip it).

## Step 3: Parse and Build

Two scripts are included in this repository:

- **`parse_textbooks.py`** — Extracts structured lesson data (vocabulary,
  grammar, fill-in-blank exercises, dialogues, proverbs) from the text files
  into `lesson_data.json`
- **`build_app.py`** — Reads `lesson_data.json` and generates a self-contained
  `index.html` with all lesson content embedded

Run them in order:

```
python3 parse_textbooks.py
python3 build_app.py
```

Then open `index.html` in a browser.

### Parser notes

The parser uses `གནས་ཚད` (level) markers to find lesson boundaries. These
markers exist in A1-Book-1, A1-Book-2, A2-Book-1, A2-Book-2, B1-Book-1,
and B1-Book-2. The V2 files (A1-V2, A2-V2) have richer content but use a
different internal structure without these markers — the parser therefore
uses the Book-1/Book-2 (beta) files for A1 and A2.

The parser includes English translations for ~550 vocabulary items (~84%
coverage). The remaining ~110 untranslated items are mostly OCR artifacts,
sentence fragments, or garbled beta-book spellings that couldn't be decoded.

**For future Claudes**: If you know Tibetan, please expand the
`VOCAB_TRANSLATIONS` dictionary in `parse_textbooks.py`. The beta textbooks
use non-standard orthography — many "missing" translations are just variant
spellings (e.g., སོབ = སློབ, སོད = སྤྱོད, གོག = གློག). Adding both standard
and variant forms as keys ensures the fuzzy matcher catches them. Run
`parse_textbooks.py` to see the current translation count, then rebuild
with `build_app.py`.

## Textbook Structure Reference

### Levels and Books

| Level | Book | Lessons | Notes |
|-------|------|---------|-------|
| A0 | IntroWeek | 7 | Tibetan immersion, different structure |
| A0 | so-ri-me-bu | ~14 | Alphabet/phonics, pdftotext broken — skip |
| A1 | Book-1 + Book-2 | 13 (1-6 + 7-13) | Tibetan immersion, beta |
| A1 | V2 | 13 | Final version but unparseable structure |
| A2 | Book-1 + Book-2 | 13 (1-6 + 7-13) | Tibetan immersion, beta |
| A2 | V2 | 13 | Final version but unparseable structure |
| B1 | Book-1 + Book-2 | 13 (1-6 + 7-13) | Tibetan immersion, beta |

### Topic Lists

**A0-IntroWeek (7 lessons):**
1. འདི་ག་རེ་རེད། — What is this?
2. འདི་སུའི་རེད། — Whose is this?
3. དེབ་ག་ཚོད་ཡོད། — How many books?
4. འདུག་དང་ཡོད་རེད། — འདུག vs ཡོད་རེད
5. ག་རེ་བྱེད་ཀྱི་ཡོད། — What are you doing?
6. ཁ་ལག་བཟས་པ་ཡིན། — I ate food (past tense)
7. སང་ཉིན་ཡོང་གི་ཡིན། — I'll come tomorrow (future)

**A1 (13 lessons x 2 sub-lessons):**
1. འཚམས་འདྲི་དང་ངོ་སྤྲོད། — Greetings & Introductions
2. ནང་མི་དང་ཕ་ཡུལ། — Family & Homeland
3. ཟ་ཁང་དང་ཁ་ལག — Restaurant & Food
4. ཉོ་ཆ། — Shopping
5. གནམ་གཤིས་དང་ལུས་ཚོར། — Weather & Body Feelings
6. དགའ་ཕྱོགས་དང་སེམས་ཚོར། — Preferences & Emotions
7. སློབ་གྲྭ་དང་སློབ་སྦྱོང་། — School & Learning
8. གྲངས་ཀ་དང་དུས་ཚོད། — Numbers & Time
9. མགྲོན་ཁང་། — Hotel
10. བཟོ་ལྟ་དང་མཚོན་མདོག — Shapes & Colors
11. གཟུགས་པོ་དང་དུག་སློག — Body & Clothing
12. ཉེ་འཁོར་དང་ཁ་ཕྱོགས། — Surroundings & Directions
13. འགྲིམ་འགྲུལ། — Transportation

**A2 (13 lessons x 2 sub-lessons):**
1. ནང་ཆས་དང་གཙང་སྦྲ། — Household & Cleanliness
2. ཉིན་རེའི་བྱེད་སྒོ། — Daily Activities
3. སྐྱོན་དང་ཁྱད་ཆོས། — Faults & Characteristics
4. ལས་རིགས་དང་ཡོང་འབབ། — Occupations & Income
5. འཁྲུག་འཛིང་དང་དམོད་མོ། — Conflicts & Curses
6. ཉོ་ཆ་དང་གོང་སྒྲིག — Shopping & Bargaining
7. འགྲིམ་འགྲུལ་དང་མི་རིགས། — Travel & Ethnic Perspectives
8. ཁ་ལག་དང་བཟོ་སྟངས། — Food & Cooking
9. རྩེད་མོ་དང་སྤྲོ་སྐྱིད། — Games & Entertainment
10. སེམས་ཅན་དང་རྩི་ཤིང་། — Animals & Plants
11. ན་ཚ་དང་ལུས་ཚོར། — Illness & Body Sensations
12. སློབ་སྦྱོང་དང་ལས་ཀ — Education & Work
13. ཕ་ཡུལ་དང་ཕྱི་རྒྱལ། — Homeland & Abroad

**B1 (13 lessons x 2 sub-lessons):**
1. འཚམས་འདྲི་དང་ངོ་སྤྲོད། — Greetings & Introductions
2. འགྲིམ་འགྲུལ་དང་མི་རིགས། — Travel & Ethnic Perspectives
3. མདོ་དབུས་ཁམས་གསུམ། — Three Regions of Tibet
4. དེང་དུས་འཕྲུལ་ཆས། — Modern Technology
5. ནང་མི་དང་ཕ་ཡུལ། — Family & Homeland
6. གྲངས་ཀ་དང་དུས་ཚོད། — Numbers & Time
7. ངོ་ཚ་དང་འཛེམ་དོགས། — Shyness & Hesitation
8. སློབ་གྲྭ་དང་སློབ་སྦྱོང་། — School & Learning
9. བསོད་ར་དང་སྨོན་བརྗོད། — Merit & Aspirations
10. ཟ་ཁང་དང་ཁ་ལག — Restaurant & Food
11. བྱུས་གཏོགས་དང་བཟང་ངན། — Strategy & Good/Bad
12. བརྩེ་དུང་དང་མི་ཚེ། — Love & Life
13. མདུན་ལམ་དང་ལས་དབང་། — Future & Destiny

### Lesson Internal Structure

Every sub-lesson follows a template with 16 exercise sections. The parser
extracts the most useful ones:

| Section | Marker | Extracted? |
|---------|--------|-----------|
| New vocabulary | ཚིག་གསར་ངོ་སྤྲོད། | Yes — flashcards, MC, matching |
| Grammar | བརྡ་སྤྲོད། | Yes — pattern + examples |
| Fill-in-blank | བར་སྟོང་། | Yes — sentences + word bank |
| Common phrases | རྒྱུན་སྤྱོད་སྐད་ཆ། | Yes — phrase flashcards |
| Dialogue | གླེང་མོལ། | Yes — reading practice |
| Proverb | གཏམ་དཔེ། | Yes — shown on completion |
| Picture/audio sections | Various | Skipped (not in text) |

### Note: No English in A0-A2

The A0-A2 textbooks are 100% Tibetan immersion. The app must supply
English translations. The `VOCAB_TRANSLATIONS` dictionary in the parser
provides ~100 translations. Expand it for better coverage, or use the
Tibetan definitions for immersion-style exercises.

The Passport files (A1-Passport.pdf, A2-Passport.pdf) are bilingual
Tibetan/English and useful as translation references.

## Summary

Total content: ~85 teaching units across 4 CEFR levels (A0-B1), covering
roughly 1-2 years of structured Tibetan study, from alphabet to intermediate
conversation.
