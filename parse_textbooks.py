#!/usr/bin/env python3
"""
Parse Esukhia textbook text extractions into structured lesson data (JSON).
See CLAUDE.md for textbook structure documentation.
"""

import json
import re
import sys
from pathlib import Path

def read_text(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def split_lessons(text, level_marker):
    """Split text into lessons based on lesson boundary markers."""
    # Pattern: གནས་ཚད་...། ༠X།༠Y
    lessons = {}
    lines = text.split('\n')
    current_key = None
    current_lines = []

    for line in lines:
        # Look for lesson markers like གནས་ཚད་གསུམ་པ། ༠༡།༠༡
        # Spacing varies wildly between books: ༠༡།༠༡, ༠༁ །༠༡, ༠༤ ། ༠༡, etc.
        m = re.search(r'གནས་ཚད.*?།\s*(\d+)\s*།\s*(\d+)', line)
        if m:
            # Python 3 int() handles Tibetan digits natively
            key = f"{int(m.group(1))}.{int(m.group(2))}"
            if key != current_key:
                if current_key and current_lines:
                    lessons.setdefault(current_key, []).extend(current_lines)
                current_key = key
                current_lines = []
        else:
            if current_key:
                current_lines.append(line)

    if current_key and current_lines:
        lessons.setdefault(current_key, []).extend(current_lines)

    return lessons

def extract_topic(lines):
    """Extract topic name from lines following བརོད་གཞི།"""
    for i, line in enumerate(lines):
        if 'བརོད་གཞི' in line:
            # Topic is on next non-empty line
            for j in range(i+1, min(i+5, len(lines))):
                stripped = lines[j].strip()
                if stripped and stripped != 'བརོད་གཞི།' and 'Second Beta' not in stripped and 'ཤོག་གྲངས' not in stripped:
                    return stripped
    return None

def extract_vocabulary(lines):
    """Extract vocabulary items from ཚིག་གསར section."""
    vocab = []
    in_vocab = False
    current_word = None
    current_def = None

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Start of vocab section
        if 'ཚིག་གསར' in stripped and ('ངོ་སོད' in stripped or 'ངོ་སྤྲོད' in stripped):
            in_vocab = True
            continue

        # End markers
        if in_vocab and any(marker in stripped for marker in [
            'སར་ཡང', 'སྐར་ཡང', 'ཚིག་གྲུབ་གོ་རིམ', 'རང་མོས', 'བསྐྱར་སྦྱོང',
            'Second Beta', 'ཤོག་གྲངས'
        ]):
            if current_word and current_def:
                vocab.append({'bo': current_word, 'defBo': current_def})
            in_vocab = False
            current_word = None
            current_def = None
            continue

        if not in_vocab:
            continue

        if not stripped:
            if current_word and current_def:
                vocab.append({'bo': current_word, 'defBo': current_def})
                current_word = None
                current_def = None
            continue

        # Skip instruction lines
        if 'དམིགས་ཡུལ' in stripped or 'བེད་སོ' in stripped or 'སྦྱོར་ཀོག' in stripped:
            continue
        if 'ཐེངས་ལྔ' in stripped:
            continue

        # A short line (likely a word) followed by a longer line (definition)
        if current_word is None:
            # Split "word། example sentence" patterns where the word repeats
            if '།' in stripped and len(stripped) > 15:
                parts = stripped.split('།', 1)
                candidate = parts[0].strip() + '།'
                rest = parts[1].strip() if len(parts) > 1 else ''
                # If the word appears again in the rest, it's word + example
                word_root = parts[0].strip().rstrip('་')
                if rest and word_root and word_root in rest and len(candidate) < 20:
                    stripped = candidate
            if len(stripped) < 30:  # Likely a vocabulary word (Tibetan is compact)
                current_word = stripped
        else:
            if current_def is None:
                current_def = stripped
            else:
                current_def += ' ' + stripped

    if current_word and current_def:
        vocab.append({'bo': current_word, 'defBo': current_def})

    return vocab

def extract_grammar(lines):
    """Extract grammar pattern and examples from བརྡ་སྤྲོད section."""
    grammar = {'pattern': None, 'example_bo': None, 'example_en': None}

    for i, line in enumerate(lines):
        stripped = line.strip()
        if 'བརྡ་སོད།' in stripped or 'བརྡ་སྤྲོད།' in stripped:
            # The pattern is often on the same line or the next
            # Look for pattern like (X+Y+Z)
            rest = stripped.split('།', 1)[-1].strip() if '།' in stripped else ''
            if rest and '+' in rest:
                grammar['pattern'] = rest
            else:
                # Check next lines
                for j in range(i+1, min(i+5, len(lines))):
                    next_line = lines[j].strip()
                    if '+' in next_line or ('མིང་ཚིག' in next_line and 'བ་ཚིག' in next_line):
                        grammar['pattern'] = next_line
                        break

        if 'ཚིག་གྲུབ།' in stripped:
            rest = stripped.split('།', 1)[-1].strip() if '།' in stripped else ''
            if rest:
                grammar['example_bo'] = rest

    return grammar if grammar['pattern'] else None

def extract_fill_blanks(lines):
    """Extract fill-in-the-blank exercises from བར་སྟོང section."""
    blanks = []
    in_section = False
    word_bank = None

    for i, line in enumerate(lines):
        stripped = line.strip()

        if 'བར་སྟོང' in stripped:
            in_section = True
            continue

        if in_section and any(marker in stripped for marker in [
            'སྦྱོང་བརྡར', 'གེང་མོལ', 'གླེང་མོལ', 'འཁྲབ་སྟོན', 'Second Beta', 'ཤོག་གྲངས'
        ]):
            in_section = False
            continue

        if not in_section or not stripped:
            continue

        # Word bank line (contains multiple short words separated by periods or spaces)
        if word_bank is None and ('དམིགས' not in stripped) and ('བེད་སོ' not in stripped):
            if '།' in stripped and len(stripped.split('།')) >= 3:
                word_bank = [w.strip() for w in stripped.split('།') if w.strip()]
                continue
            elif '་' in stripped and '_' not in stripped and '༡' not in stripped:
                # Could be a word bank with tsheg-separated words
                pass

        # Sentence with blank
        if '_' in stripped or '་་་་' in stripped:
            sentence = stripped
            blanks.append({'sentence': sentence, 'word_bank': word_bank})

    return blanks

def extract_common_phrases(lines):
    """Extract common phrases from རྒྱུན་སྤྱོད section."""
    phrases = []
    in_section = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        if 'རྒྱུན་སོད་སྐད་ཆ' in stripped or 'རྒྱུན་སྤྱོད་སྐད་ཆ' in stripped:
            # Phrases often on the same line after the marker
            rest = stripped.split('།', 1)[-1].strip() if 'སྐད་ཆ།' in stripped else ''
            if rest:
                for p in rest.split('།'):
                    p = p.strip()
                    if p and len(p) > 2:
                        phrases.append(p + '།')
            in_section = True
            continue

        if in_section:
            if stripped and not any(m in stripped for m in ['སར་ཡང', '༣', '༤', '༥', 'དམིགས', 'བེད་སོ', 'Second', 'ཤོག']):
                for p in stripped.split('།'):
                    p = p.strip()
                    if p and len(p) > 2:
                        phrases.append(p + '།')
            else:
                in_section = False

    return phrases

def extract_dialogue(lines):
    """Extract dialogue turns."""
    dialogue = []
    in_dialogue = False
    current_speaker = None
    current_text = []

    dialogue_markers = ['གེང་མོལ།', 'གླེང་མོལ།']

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Check for dialogue section (section 14)
        if any(m in stripped for m in dialogue_markers) and ('༡༤' in stripped or 'བཤད་རྩལ' in stripped):
            in_dialogue = True
            continue

        if in_dialogue and any(m in stripped for m in ['འཁྲབ་སྟོན', 'གཏམ་དཔེ', 'Second Beta', 'ཤོག་གྲངས']):
            if current_speaker and current_text:
                dialogue.append({'speaker': current_speaker, 'text': ' '.join(current_text)})
            in_dialogue = False
            break

        if not in_dialogue:
            continue

        if not stripped:
            if current_speaker and current_text:
                dialogue.append({'speaker': current_speaker, 'text': ' '.join(current_text)})
                current_speaker = None
                current_text = []
            continue

        # Speaker names are typically short standalone lines
        common_speakers = ['སློབ་ཕྲུག', 'རྒན་ལགས', 'སོབ་ཕྲུག', 'རྒན་ལག', 'བཀྲ་ཤིས', 'སྒྲོལ་མ',
                          'བསྟན་འཛིན', 'ནོར་བུ', 'བཟང་མོ', 'བློ་བཟང', 'རྒན་ལགས།', 'སོབ་མ།',
                          'སོབ་མ', 'རྒན་ལགས', 'སྐྱོན་མ', 'རྡོ་རྗེ', 'ཡོན་ཏན',
                          'རྒན་ཕྲུག', 'རིན་ཆེན', 'པ་སངས', 'སྐལ་བཟང']

        is_speaker = False
        for name in common_speakers:
            if stripped.startswith(name) and len(stripped) < 30:
                if current_speaker and current_text:
                    dialogue.append({'speaker': current_speaker, 'text': ' '.join(current_text)})
                current_speaker = stripped.rstrip('།').strip()
                current_text = []
                is_speaker = True
                break

        if not is_speaker and current_speaker:
            current_text.append(stripped)

    if current_speaker and current_text:
        dialogue.append({'speaker': current_speaker, 'text': ' '.join(current_text)})

    return dialogue

def extract_proverb(lines):
    """Extract proverb from གཏམ་དཔེ section."""
    for i, line in enumerate(lines):
        if 'གཏམ་དཔེ' in line or 'གོ་ས' in line:
            # Proverb is usually 1-2 lines after
            proverb_lines = []
            for j in range(i+1, min(i+6, len(lines))):
                stripped = lines[j].strip()
                if stripped and 'Second Beta' not in stripped and 'ཤོག་གྲངས' not in stripped and 'དམིགས' not in stripped and 'བེད་སོ' not in stripped:
                    proverb_lines.append(stripped)
                if len(proverb_lines) >= 2:
                    break
            if proverb_lines:
                return ' '.join(proverb_lines)
    return None

def parse_a0_introweek(text):
    """Parse A0-IntroWeek — 7 lessons, different structure."""
    lessons = []
    # A0 uses different markers. Lessons start with གླེང་མོལ། patterns
    # and are numbered ༡ through ༧
    # The structure is simpler - split by major sections

    # A0 topics (from investigation)
    topics = {
        '1': {'bo': 'འདི་ག་རེ་རེད།', 'en': 'What is this?'},
        '2': {'bo': 'འདི་སུའི་རེད།', 'en': 'Whose is this?'},
        '3': {'bo': 'དེབ་ག་ཚོད་ཡོད།', 'en': 'How many books?'},
        '4': {'bo': 'འདུག་དང་ཡོད་རེད།', 'en': 'འདུག vs ཡོད་རེད'},
        '5': {'bo': 'ག་རེ་བྱེད་ཀྱི་ཡོད།', 'en': 'What are you doing?'},
        '6': {'bo': 'ཁ་ལག་བཟས་པ་ཡིན།', 'en': 'I ate food (Past tense)'},
        '7': {'bo': 'སང་ཉིན་ཡོང་གི་ཡིན།', 'en': "I'll come tomorrow (Future)"},
    }

    # Extract vocabulary by looking for ཚིག་གསར sections
    vocab = extract_vocabulary(text.split('\n'))

    for num, topic in topics.items():
        lessons.append({
            'level': 'A0',
            'lesson': int(num),
            'sub': 1,
            'topicBo': topic['bo'],
            'topicEn': topic['en'],
            'vocab': [],  # Will be populated with translations
            'grammar': None,
            'phrases': [],
            'dialogue': [],
            'proverb': None,
            'fillBlanks': [],
        })

    return lessons

def parse_book(text, level, use_sub=True):
    """Generic parser for A1/A2/B1 textbooks."""
    lessons_raw = split_lessons(text, level)
    lessons = []

    for key, lines in sorted(lessons_raw.items()):
        parts = key.split('.')
        if len(parts) != 2:
            continue

        lesson_num = int(parts[0])
        sub_num = int(parts[1])

        topic = extract_topic(lines)
        vocab = extract_vocabulary(lines)
        grammar = extract_grammar(lines)
        fill_blanks = extract_fill_blanks(lines)
        phrases = extract_common_phrases(lines)
        dialogue = extract_dialogue(lines)
        proverb = extract_proverb(lines)

        lessons.append({
            'level': level,
            'lesson': lesson_num,
            'sub': sub_num,
            'topicBo': topic or '',
            'topicEn': '',  # Will be filled with translations
            'vocab': vocab,
            'grammar': grammar,
            'phrases': phrases,
            'dialogue': dialogue,
            'proverb': proverb,
            'fillBlanks': fill_blanks,
        })

    return lessons


# ===== ENGLISH TRANSLATIONS =====
# Loaded from translations.json — a standalone bilingual dictionary.
# Edit that file to add/fix translations, then re-run this script.

def _load_translations():
    """Load translation dictionaries from translations.json."""
    translations_path = Path(__file__).parent / 'translations.json'
    if not translations_path.exists():
        print(f"Warning: {translations_path} not found, no English translations")
        return {}, {}
    with open(translations_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('topics', {}), data.get('vocab', {})

TOPIC_TRANSLATIONS, VOCAB_TRANSLATIONS = _load_translations()



def translate_vocab(vocab_list):
    """Add English translations to vocabulary items."""
    for v in vocab_list:
        word = v['bo']
        en = _lookup_translation(word)
        if not en:
            # Try the first word if it's a compound like "མིང་།/ མཚན།"
            if '/' in word:
                first = word.split('/')[0].strip()
                en = _lookup_translation(first)
        v['en'] = en or ''
    return vocab_list

def _lookup_translation(word):
    """Look up a Tibetan word in the translation dictionary with fuzzy matching."""
    if word in VOCAB_TRANSLATIONS:
        return VOCAB_TRANSLATIONS[word]
    # Try without final tsheg/shad
    clean = word.rstrip('།').rstrip('་').strip()
    if clean in VOCAB_TRANSLATIONS:
        return VOCAB_TRANSLATIONS[clean]
    if clean + '།' in VOCAB_TRANSLATIONS:
        return VOCAB_TRANSLATIONS[clean + '།']
    if clean + '་' in VOCAB_TRANSLATIONS:
        return VOCAB_TRANSLATIONS[clean + '་']
    # Try substring match (word is contained in a dict key or vice versa)
    for bo, en in VOCAB_TRANSLATIONS.items():
        bo_clean = bo.rstrip('།').rstrip('་').strip()
        if bo_clean == clean:
            return en
    return None

def translate_topic(topic_bo):
    """Translate topic name to English."""
    if not topic_bo:
        return ''
    # Try exact match
    if topic_bo in TOPIC_TRANSLATIONS:
        return TOPIC_TRANSLATIONS[topic_bo]
    # Try without punctuation
    clean = topic_bo.rstrip('།').strip()
    if clean in TOPIC_TRANSLATIONS:
        return TOPIC_TRANSLATIONS[clean]
    # Try partial match
    for bo, en in TOPIC_TRANSLATIONS.items():
        if bo.rstrip('།') in topic_bo or topic_bo in bo:
            return en
    return ''


def main():
    base = Path('textbooks')
    all_lessons = []

    # Parse A0-IntroWeek
    print("Parsing A0-IntroWeek...")
    text = read_text(base / 'A0-IntroWeek.txt')
    # A0 has different structure, parse what we can
    vocab = extract_vocabulary(text.split('\n'))
    phrases = extract_common_phrases(text.split('\n'))
    a0_topics = [
        {'bo': 'འདི་ག་རེ་རེད།', 'en': 'What is this?'},
        {'bo': 'འདི་སུའི་རེད།', 'en': 'Whose is this?'},
        {'bo': 'དེབ་ག་ཚོད་ཡོད།', 'en': 'How many books?'},
        {'bo': 'འདུག་དང་ཡོད་རེད།', 'en': 'འདུག vs ཡོད་རེད'},
        {'bo': 'ག་རེ་བྱེད་ཀྱི་ཡོད།', 'en': 'What are you doing?'},
        {'bo': 'ཁ་ལག་བཟས་པ་ཡིན།', 'en': 'I ate food (Past tense)'},
        {'bo': 'སང་ཉིན་ཡོང་གི་ཡིན།', 'en': "I'll come tomorrow (Future)"},
    ]
    for i, topic in enumerate(a0_topics):
        all_lessons.append({
            'level': 'A0',
            'lesson': i + 1,
            'sub': 1,
            'topicBo': topic['bo'],
            'topicEn': topic['en'],
            'vocab': [],
            'grammar': None,
            'phrases': [],
            'dialogue': [],
            'proverb': None,
            'fillBlanks': [],
        })

    # Parse A1 (Book-1 has lessons 1-6, Book-2 has lessons 7-13)
    # Using beta books because V2 uses different structure without གནས་ཚད markers
    for book in ['A1-Book-1.txt', 'A1-Book-2.txt']:
        print(f"Parsing {book}...")
        text = read_text(base / book)
        lessons = parse_book(text, 'A1')
        for l in lessons:
            l['topicEn'] = translate_topic(l['topicBo'])
            l['vocab'] = translate_vocab(l['vocab'])
        all_lessons.extend(lessons)

    # Parse A2 (Book-1 has lessons 1-6, Book-2 has lessons 7-13)
    for book in ['A2-Book-1.txt', 'A2-Book-2.txt']:
        print(f"Parsing {book}...")
        text = read_text(base / book)
        lessons = parse_book(text, 'A2')
        for l in lessons:
            l['topicEn'] = translate_topic(l['topicBo'])
            l['vocab'] = translate_vocab(l['vocab'])
        all_lessons.extend(lessons)

    # Parse B1-Book-1
    print("Parsing B1-Book-1...")
    text = read_text(base / 'B1-Book-1.txt')
    b1_1_lessons = parse_book(text, 'B1')
    for l in b1_1_lessons:
        l['topicEn'] = translate_topic(l['topicBo'])
        l['vocab'] = translate_vocab(l['vocab'])
    all_lessons.extend(b1_1_lessons)

    # Parse B1-Book-2
    print("Parsing B1-Book-2...")
    text = read_text(base / 'B1-Book-2.txt')
    b1_2_lessons = parse_book(text, 'B1')
    for l in b1_2_lessons:
        l['topicEn'] = translate_topic(l['topicBo'])
        l['vocab'] = translate_vocab(l['vocab'])
    all_lessons.extend(b1_2_lessons)

    # Stats
    print(f"\n=== Parsing Results ===")
    print(f"Total lessons: {len(all_lessons)}")
    levels = {}
    total_vocab = 0
    total_phrases = 0
    total_dialogues = 0
    total_proverbs = 0
    for l in all_lessons:
        lev = l['level']
        levels[lev] = levels.get(lev, 0) + 1
        total_vocab += len(l['vocab'])
        total_phrases += len(l['phrases'])
        total_dialogues += len(l['dialogue'])
        total_proverbs += 1 if l['proverb'] else 0

    for lev, count in sorted(levels.items()):
        print(f"  {lev}: {count} sub-lessons")
    print(f"Total vocabulary items: {total_vocab}")
    print(f"  With English translation: {sum(1 for l in all_lessons for v in l['vocab'] if v.get('en'))}")
    print(f"  Without translation: {sum(1 for l in all_lessons for v in l['vocab'] if not v.get('en'))}")
    print(f"Total phrases: {total_phrases}")
    print(f"Total dialogue turns: {total_dialogues}")
    print(f"Total proverbs: {total_proverbs}")

    # Write JSON
    output = Path('lesson_data.json')
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(all_lessons, f, ensure_ascii=False, indent=2)
    print(f"\nWritten to {output} ({output.stat().st_size // 1024} KB)")


if __name__ == '__main__':
    main()
