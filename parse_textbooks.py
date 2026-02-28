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
            if len(stripped) < 40:  # Likely a vocabulary word (Tibetan is compact)
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

TOPIC_TRANSLATIONS = {
    # B1 topics (standard spellings)
    'འཚམས་འདི་དང་ངོ་སོད།': 'Greetings & Introductions',
    'འཚམས་འདྲི་དང་ངོ་སྤྲོད།': 'Greetings & Introductions',
    'ནང་མི་དང་ཕ་ཡུལ།': 'Family & Homeland',
    'ཟ་ཁང་དང་ཁ་ལག': 'Restaurant & Food',
    'ཉོ་ཆ།': 'Shopping',
    'གནམ་གཤིས་དང་ལུས་ཚོར།': 'Weather & Body Feelings',
    'དགའ་ཕྱོགས་དང་སེམས་ཚོར།': 'Preferences & Emotions',
    'སློབ་གྲྭ་དང་སློབ་སྦྱོང་།': 'School & Learning',
    'སོབ་གྲྭ་དང་སོབ་སོང་།': 'School & Learning',
    'གྲངས་ཀ་དང་དུས་ཚོད།': 'Numbers & Time',
    'མགྲོན་ཁང་།': 'Hotel',
    'བཟོ་ལྟ་དང་མཚོན་མདོག': 'Shapes & Colors',
    'གཟུགས་པོ་དང་དུག་སློག': 'Body & Clothing',
    'ཉེ་འཁོར་དང་ཁ་ཕྱོགས།': 'Surroundings & Directions',
    'འགྲིམ་འགྲུལ།': 'Transportation',
    'ནང་ཆས་དང་གཙང་སྦྲ།': 'Household & Cleanliness',
    'ཉིན་རེའི་བྱེད་སྒོ།': 'Daily Activities',
    'སྐྱོན་དང་ཁྱད་ཆོས།': 'Faults & Characteristics',
    'ལས་རིགས་དང་ཡོང་འབབ།': 'Occupations & Income',
    'འཁྲུག་འཛིང་དང་དམོད་མོ།': 'Conflicts & Curses',
    'ཉོ་ཆ་དང་གོང་སྒྲིག': 'Shopping & Bargaining',
    'འགྲིམ་འགྲུལ་དང་མི་རིགས།': 'Travel & Ethnic Perspectives',
    'འགྲིམ་འགྲུལ་དང་མི་རིགས་ཀི་ལྟ་སྟངས།': 'Travel & Ethnic Perspectives',
    'ཁ་ལག་དང་བཟོ་སྟངས།': 'Food & Cooking',
    'རྩེད་མོ་དང་སྤྲོ་སྐྱིད།': 'Games & Entertainment',
    'སེམས་ཅན་དང་རྩི་ཤིང་།': 'Animals & Plants',
    'ན་ཚ་དང་ལུས་ཚོར།': 'Illness & Body Sensations',
    'སློབ་སྦྱོང་དང་ལས་ཀ': 'Education & Work',
    'ཕ་ཡུལ་དང་ཕྱི་རྒྱལ།': 'Homeland & Abroad',
    'མདོ་དབུས་ཁམས་གསུམ།': 'Three Regions of Tibet',
    'དེང་དུས་འཕྲུལ་ཆས།': 'Modern Technology',
    'ངོ་ཚ་དང་འཛེམ་དོགས།': 'Shyness & Hesitation',
    'བསོད་ར་དང་སོན་བརོད།': 'Merit & Aspirations',
    'བྱུས་གཏོགས་དང་བཟང་ངན།': 'Strategy & Good vs Bad',
    'བརྩེ་དུང་དང་མི་ཚེ།': 'Love & Life',
    'མདུན་ལམ་དང་ལས་དབང་།': 'Future & Destiny',
    # A1 topics (beta book spelling variants)
    'འཚམས་འདི་དང་ངོ་སོད།': 'Greetings & Introductions',
    'ནང་མི་དང་ཕ་ཡུལ།': 'Family & Homeland',
    'ཟ་ཁང་དང་ཁ་ལག།': 'Restaurant & Food',
    'གནམ་གཤིས་དང་ལུས་ཚོར།': 'Weather & Body Feelings',
    'དགའ་ཕོགས་དང་སེམས་ཚོར།': 'Preferences & Emotions',
    'དགའ་ཕྱོགས་དང་སེམས་ཚོར།': 'Preferences & Emotions',
    'སོབ་གྲྭ་དང་སོབ་སྦྱོང་།': 'School & Learning',
    'སོབ་གྲྭ་དང་སྱོབ་སྦྱོང་།': 'School & Learning',
    'གྲངས་ཀ་དང་དུས་ཚོད།': 'Numbers & Time',
    'མགྲོན་ཁང་།': 'Hotel',
    'བཟོ་ལྟ་དང་ཚོན་མདོག': 'Shapes & Colors',
    'བཟོ་ལྟ་དང་མཚོན་མདོག།': 'Shapes & Colors',
    'གཟུགས་པོ་དང་དུག་སོག': 'Body & Clothing',
    'གཟུགས་པོ་དང་དུག་སྱོག': 'Body & Clothing',
    'ཉེ་འཁོར་དང་ཁ་ཕོགས།': 'Surroundings & Directions',
    'འགིམ་འགྲུལ།': 'Transportation',
    # A2 topics (beta book spelling variants)
    'ནང་ཆས་དང་གཙང་སྦྲ།': 'Household & Cleanliness',
    'ཉིན་རེའ་ི བེད་སོ།': 'Daily Activities',
    'ཉིན་རེའི་བེད་སོ།': 'Daily Activities',
    'ཉིན་རེའི་བྱེད་སོ།': 'Daily Activities',
    'སོན་དང་ཁྱད་ཆོས།': 'Faults & Characteristics',
    'སྐྱོན་དང་ཁྱད་ཆོས།': 'Faults & Characteristics',
    'ལས་རིགས་དང་ཡོང་འབབ།': 'Occupations & Income',
    'འཁྲུག་འཛིང་དང་དམོད་མོ།': 'Conflicts & Curses',
    'ཉོ་ཆ་དང་གོང་སྒྲིག།': 'Shopping & Bargaining',
    'འགིམ་འགྲུལ་དང་མི་རིགས།': 'Travel & Ethnic Perspectives',
    'འགིམ་འགུལ་དང་མི་རིགས།': 'Travel & Ethnic Perspectives',
    'ཁ་ལག་དང་བཟོ་སྟངས།': 'Food & Cooking',
    'རྩེད་མོ་དང་སོ་སིད།': 'Games & Entertainment',
    'རྩེད་མོ་དང་སྤྲོ་སྐྱིད།': 'Games & Entertainment',
    'སེམས་ཅན་དང་རི་ཤིང་།': 'Animals & Plants',
    'སེམས་ཅན་དང་རྩི་ཤིང་།': 'Animals & Plants',
    'ན་ཚ་དང་ལུས་ཚོར།': 'Illness & Body Sensations',
    'སོབ་སོང་དང་ལས་ཀ': 'Education & Work',
    'སོབ་སྦྱོང་དང་ལས་ཀ': 'Education & Work',
    'ཕ་ཡུལ་དང་ཕི་རྒྱལ།': 'Homeland & Abroad',
    'ཕ་ཡུལ་དང་ཕྱི་རྒྱལ།': 'Homeland & Abroad',
}

# Common vocabulary translations (Tibetan → English)
# This is the core knowledge Claude brings - translating the immersion content
VOCAB_TRANSLATIONS = {
    # === GREETINGS (B1 L1) ===
    'ལོ་གསར།': 'New Year',
    'ཚེ་རིང་ནད་མེད།': 'Long life, no illness',
    'ཚེ་རིང་ནད་མྱེད།': 'Long life, no illness',
    'ཞྭ་ཕུད་ཞུ་བ།': 'Removing hat (respect)',
    'སྐྱེས་སྐར།': 'Birthday',
    'སྱེས་སྐར།': 'Birthday',
    'ཐོད་པ་གཏུགས་པ།': 'Touching foreheads',
    'གཉེན་སྒྲིག': 'Wedding',
    'ག཈ྱེན་སིག': 'Wedding',
    'ཐལ་མོ་སྦྱར་བ།': 'Joining palms',
    'ཚེས་བཟང་དུས་བཟང།': 'Auspicious day',
    'འཐམ་པ།': 'Hugging',
    'ལག་པ་གཏོང་བ།': 'Handshake',
    # === A0 BASICS ===
    'ཅོག་ཙེ': 'Desk',
    'རྐུབ་བཀྱག': 'Chair',
    'སྨྱུ་གུ': 'Pen',
    'དེབ': 'Book',
    'སློབ་ཕྲུག': 'Student',
    'སོབ་ཕྲུག': 'Student',
    'དགེ་རྒན': 'Teacher',
    'བུ': 'Boy/son',
    'བུ་མོ': 'Girl/daughter',
    # === A1 L1: GREETINGS & INTRODUCTIONS ===
    'ཞོགས་པ།': 'Morning',
    'འཚམས་འདི།': 'Greeting',
    'འཚམས་འདྲི།': 'Greeting',
    'གོགས་མོ།': 'Female friend',
    'གྲོགས་མོ།': 'Female friend',
    'གོགས་པོ།': 'Male friend',
    'གྲོགས་པོ།': 'Male friend',
    'བདེ་པོ།': 'Well/comfortable',
    'འཛིན་གྲྭ།': 'Classroom',
    'བསྡད།': 'Stayed/lived',
    'ཐུག': 'Met',
    'ཁོམ།': 'Market/free time',
    'མཉམ་དུ།': 'Together',
    'དགོང་དག': 'Evening',
    'དགོང་མོ།': 'Evening',
    'མིང་།': 'Name',
    'མཚན།': 'Name (honorific)',
    'ཕ་ཡུལ།': 'Homeland',
    'ལུང་པ།': 'Country/region',
    'སེས་ས།': 'Birthplace',
    'སྐྱེས་ས།': 'Birthplace',
    'ལོ།': 'Year/age',
    'དགུང་ལོ།': 'Age (honorific)',
    'བོད།': 'Tibet',
    'ལས་ཀ': 'Work/job',
    'དགའ་པོ།': 'Like/fond of',
    'ཨ་རི།': 'America',
    'རྒྱ་གར།': 'India',
    'སེབས།': 'Arrived',
    'སླེབས།': 'Arrived',
    'མིང་།/ མཚན།': 'Name',
    'ཕ་ཡུལ།/ ལུང་པ།': 'Homeland/country',
    'ལོ།/ དགུང་ལོ།': 'Age',
    # === A1 L2: FAMILY & HOMELAND ===
    'ཨ་མ': 'Mother',
    'ཨ་ཕ': 'Father',
    'ཨ་མ།': 'Mother',
    'ཨ་ཕ།': 'Father',
    'སྤུན་མཆེད': 'Siblings',
    'སྤུན་མཆྱེད།': 'Siblings',
    'ནང་མི': 'Family member',
    'ནང་མི།': 'Family member',
    'ཕ་ཡུལ': 'Homeland',
    'སིད་པོ།': 'Beautiful/pleasant',
    'སྐྱིད་པོ།': 'Beautiful/pleasant',
    'ཚང་མ།': 'All/everyone',
    'སྱེས་སྨན།': 'Wife',
    'སྐྱེས་དམན།': 'Wife',
    'ཁོ་ག': 'Husband',
    'ཁྱོ་ག': 'Husband',
    'གོང་ཁྱེར།': 'City',
    'གོང་གསྱེབ།': 'Village',
    'གྲོང་གསེབ།': 'Village',
    'ཁིམ་མཚེས།': 'Neighbor',
    'ཁྱིམ་མཚེས།': 'Neighbor',
    'རོ་ལགས།': 'Wife (respectful)',
    'ཨ་ཅག': 'Older sister',
    'ཨ་ཅག།': 'Older sister',
    'ཇོ་ཇོ།': 'Older brother',
    'ཇོ་ཇོ': 'Older brother',
    'ཨ་ཁུ།': 'Uncle',
    'ཨ་ནེ།': 'Aunt',
    'སྤུ་གུ།': 'Child',
    'ཕྲུ་གུ།': 'Child',
    # === A1 L3: RESTAURANT & FOOD ===
    'ཁ་ལག': 'Food',
    'ཁ་ལག།': 'Food',
    'ཇ': 'Tea',
    'ཇ།': 'Tea',
    'ཆང': 'Beer/alcohol',
    'ཆང་།': 'Beer/alcohol',
    'ཐུག་པ': 'Noodle soup',
    'ཐུག་པ།': 'Noodle soup',
    'མོག་མོག': 'Momos/dumplings',
    'མོག་མོག།': 'Momos/dumplings',
    'འབྲས': 'Rice',
    'འབྲས།': 'Rice',
    'ཟ་ཁང་།': 'Restaurant',
    'ཟ་ཁང་': 'Restaurant',
    'ཁ་ཕེ།': 'Coffee',
    'ཞིམ་པོ།': 'Delicious',
    'ཞིམ་པྫོ།': 'Delicious',
    'ཚ་པོ།': 'Hot/spicy',
    'གྲང་མོ།': 'Cold',
    'སྐྱུར་མོ།': 'Sour',
    'མངར་མོ།': 'Sweet',
    'ཚིལ་པོ།': 'Oily/fatty',
    'ཁ་ཟས།': 'Food/cuisine',
    'བོད་ཁ་ཟས།': 'Tibetan food',
    'རྒྱ་ཁ་ཟས།': 'Chinese food',
    'ཤ།': 'Meat',
    'ཤ': 'Meat',
    'ཚོད་མ།': 'Vegetables',
    'ཤིང་ཏོག': 'Fruit',
    'ཤིང་ཏོག།': 'Fruit',
    'མར།': 'Butter',
    'འོ་མ།': 'Milk',
    'ཆུ།': 'Water',
    'སྦྱང་རྩི།': 'Honey',
    'ཚྭ།': 'Salt',
    'སྤེན་མ།': 'Sugar',
    'གོ་རེ།': 'Egg',
    'སྒོ་ང་།': 'Egg',
    'བག་ལེབ།': 'Bread/flat bread',
    # === A1 L4: SHOPPING ===
    'ཉོ་ཆ།': 'Shopping',
    'གོང་ཚད།': 'Price',
    'རིན་གོང་།': 'Price',
    'ཕལ་ཆེར།': 'Mostly/generally',
    'ཚོང་ཁང་།': 'Shop/store',
    'ཚོང་པ།': 'Merchant',
    'ཁེ་བཟང་།': 'Profit/bargain',
    'ཁེ་པོ།': 'Profitable',
    'ཁྱེ་པྡོ།': 'Profitable',
    'གོང་རག': 'Discount/affordable',
    'ཕོགས།': 'Salary',
    'དངུལ།': 'Money/silver',
    'སྒོར་མོ།': 'Rupee/money unit',
    'རྫས།': 'Things/goods',
    'ཚོང་རྫས།': 'Merchandise',
    # === A1 L5: WEATHER & BODY FEELINGS ===
    'གནམ་གཤིས།': 'Weather',
    'གནམ་གཤྱིས།': 'Weather',
    'ཚ་པོ།': 'Hot',
    'གྲང་མོ།': 'Cold',
    'ཆར་པ།': 'Rain',
    'གངས།': 'Snow',
    'རླུང་།': 'Wind',
    'ཉི་མ།': 'Sun/day',
    'ཟླ་བ།': 'Moon/month',
    'སྐར་མ།': 'Star',
    'སྤྲིན་པ།': 'Cloud',
    'ནམ་མཁའ།': 'Sky',
    'གནམ་དྭངས།': 'Clear sky',
    'ཁ་བ།': 'Snow (falling)',
    'སེར་བ།': 'Hail',
    'མུན་པ།': 'Darkness',
    'འོད།': 'Light',
    'ལུས་ཚོར།': 'Body sensation',
    'སྐོམ།': 'Thirsty',
    'ལྟོགས།': 'Hungry',
    'ཐང་ཆད།': 'Tired/exhausted',
    'ཉལ་ཁ།': 'Sleepy',
    'ན་གི་འདུག': 'I am sick',
    # === A1 L6: PREFERENCES & EMOTIONS ===
    'དགའ་པོ།': 'Like/fond of',
    'སྡུག་པོ།': 'Ugly/unpleasant',
    'སེམས་ཚོར།': 'Emotions/feelings',
    'དགའ་པོ': 'Like/fond of',
    'སིང་པོ།': 'Sad',
    'སེམས་པ།': 'Mind/thought',
    'སྐྱོ་པོ།': 'Sad',
    'སིད་པོ།': 'Happy/joyful',
    'དགའ་སོད།': 'Happiness',
    # === A1 L7-13: SCHOOL, NUMBERS, HOTEL, etc. ===
    'སོབ་གྲྭ།': 'School',
    'སློབ་གྲྭ།': 'School',
    'སོབ་སོང་།': 'Study/learning',
    'སློབ་སྦྱོང་།': 'Study/learning',
    'དཔེ་ཆ།': 'Textbook',
    'ཤོག་བུ།': 'Paper',
    'སྨྱུ་གུ།': 'Pen',
    'ཉག་ཕྲན།': 'Pencil',
    'ནག་པང་།': 'Blackboard',
    'གྲངས་ཀ།': 'Number',
    'གཅིག': 'One',
    'གཉིས': 'Two',
    'གསུམ': 'Three',
    'བཞི': 'Four',
    'ལྔ': 'Five',
    'དྲུག': 'Six',
    'བདུན': 'Seven',
    'བརྒྱད': 'Eight',
    'དགུ': 'Nine',
    'བཅུ': 'Ten',
    'དུས་ཚོད།': 'Time/hour',
    'ཆུ་ཚོད།': 'Hour',
    'སྐར་མ།': 'Minute/star',
    'མགྲོན་ཁང་།': 'Hotel',
    'ཁང་མིག': 'Room',
    'ཁང་མིག།': 'Room',
    'ཁང་གླ།': 'Room rent',
    'སྒོ་ལྡེ།': 'Key',
    'གཟུགས་པོ།': 'Body',
    'མགོ།': 'Head',
    'མགོ': 'Head',
    'ལག་པ': 'Hand',
    'ལག་པ།': 'Hand',
    'རྐང་པ': 'Foot/leg',
    'རྐང་པ།': 'Foot/leg',
    'མིག': 'Eye',
    'མིག།': 'Eye',
    'རྣ་བ': 'Ear',
    'རྣ་བ།': 'Ear',
    'ཁ': 'Mouth',
    'ཁ།': 'Mouth',
    'སྣ།': 'Nose',
    'ཐོད་པ།': 'Skull/forehead',
    'མཛུབ་མོ།': 'Finger',
    'རྐེད་པ།': 'Waist',
    'བྲང་ཁ།': 'Chest',
    'སྐེད་པ།': 'Waist',
    'དཔུང་པ།': 'Shoulder',
    'མགུལ་པ།': 'Neck',
    'དུག་སོག': 'Clothing',
    'དུག་སློག': 'Clothing',
    'གོས།': 'Clothes',
    'ཕྱུ་པ།': 'Hat',
    'ཞྭ་མོ།': 'Hat',
    'ལྷམ།': 'Shoes',
    'ཁ་ཕོགས།': 'Direction',
    'ཤར།': 'East',
    'ནུབ།': 'West',
    'ལྷོ།': 'South',
    'བྱང་།': 'North',
    'གཡས།': 'Right',
    'གཡོན།': 'Left',
    'སྟེང་།': 'Above/on top',
    'འོག': 'Below/under',
    'ནང་།': 'Inside',
    'ཕི་ལོགས།': 'Outside',
    'ཕྱི་ལོགས།': 'Outside',
    'ཉེ་འཁོར།': 'Surroundings',
    'བཟོ་ལྟ།': 'Shape/appearance',
    'ཚོན་མདོག': 'Color',
    'མཚོན་མདོག': 'Color',
    'དཀར་པོ།': 'White',
    'ནག་པོ།': 'Black',
    'དམར་པོ།': 'Red',
    'སེར་པོ།': 'Yellow',
    'སྔོན་པོ།': 'Blue',
    'ལྗང་ཁུ།': 'Green',
    'ཁྲ་ཁྲ།': 'Multicolored',
    # === A1 TRANSPORT ===
    'གནམ་གྲུ': 'Airplane',
    'གནམ་གྲུ།': 'Airplane',
    'རླངས་འཁོར': 'Car',
    'རླངས་འཁོར།': 'Car',
    'མེ་འཁོར': 'Train',
    'མེ་འཁོར།': 'Train',
    'རྐང་འཁོར': 'Bicycle',
    'རྐང་འཁོར།': 'Bicycle',
    'འགིམ་འགྲུལ།': 'Transportation',
    'འགྲིམ་འགྲུལ།': 'Transportation',
    'ཐོན།': 'Departed',
    'སླེབས།': 'Arrived',
    'གྲུ།': 'Boat',
    'ལམ།': 'Road/path',
    'ཟམ་པ།': 'Bridge',
    'ས་ཆ།': 'Place',
    # === A2 L1: HOUSEHOLD & CLEANLINESS ===
    'ནང་ཆས།': 'Household items',
    'གཙང་སྦྲ།': 'Cleanliness',
    'ཁྲུས་ཁང་།': 'Bathroom',
    'གསང་སྤྱོད།': 'Toilet',
    'ཁང་།': 'House',
    'ཁང་པ།': 'House',
    'སྒོ།': 'Door',
    'སྒེའུ་ཁུང་།': 'Window',
    'རྩིག་པ།': 'Wall',
    'ཐོག་ཁ།': 'Ceiling/floor',
    'གདན།': 'Cushion/seat',
    'མལ་ཁྲི།': 'Bed',
    'ཐབ།': 'Stove',
    'སྣོད།': 'Container/pot',
    'ཕོར་པ།': 'Cup/bowl',
    'གད་ཕགས།': 'Sweeping',
    # === A2 L2: DAILY ACTIVITIES ===
    'ཉིན་རེའི།': 'Daily',
    'བྱེད་སྒོ།': 'Activities',
    'ལངས།': 'Got up/woke up',
    'ཁ་བཏགས།': 'Scarf (khata)',
    'ཞལ་འདོན།': 'Prayer recitation',
    'ལས་ཀ་བྱེད།': 'To work',
    'ཉལ།': 'To sleep',
    'ཟ།': 'To eat',
    'འཐུང་།': 'To drink',
    'བྲི།': 'To write',
    'ཀློག': 'To read',
    'ལྟ།': 'To look/watch',
    'ཉན།': 'To listen',
    'བཤད།': 'To say/speak',
    # === A2 L3: FAULTS & CHARACTERISTICS ===
    'ཁྱད་ཆྲོས།': 'Characteristics',
    'ཁྱད་ཆོས།': 'Characteristics',
    'སྐྱོན།': 'Fault/defect',
    'ཡག་པོ།': 'Good',
    'སྡུག་པོ།': 'Bad/ugly',
    'ཆེན་པོ།': 'Big',
    'ཆུང་ཆུང་།': 'Small',
    'རིང་པོ།': 'Long/tall',
    'ཐུང་ཐུང་།': 'Short',
    'རྒྱ་ཆེ།': 'Wide/vast',
    'དོག་པོ།': 'Narrow',
    'གུ་དོག་པོ།': 'Stubborn',
    'དྲང་པོ།': 'Honest/straight',
    'ཕྲ་མ།': 'Gossip/slander',
    'གཡོ་སྒྱུ།': 'Deceit',
    'བཟང་པོ།': 'Good/virtuous',
    'ངན་པ།': 'Bad/evil',
    # === A2 L4-6: OCCUPATIONS, CONFLICTS, SHOPPING ===
    'ལས་རིགས།': 'Occupation',
    'ཡོང་འབབ།': 'Income',
    'སྨན་པ།': 'Doctor',
    'ཁྲིམས་རྩོད་པ།': 'Lawyer',
    'ཚོང་པ།': 'Merchant',
    'རི་མོ་མཁན།': 'Artist/painter',
    'དྲུང་ཡིག': 'Secretary',
    'ཁོང་དྲུང་ཡིག': 'Secretary (variant)',
    'འཁྲུག་འཛིང་།': 'Conflict/quarrel',
    'དམོད་མོ།': 'Curse',
    'ཁོང་ཁོ།': 'Anger',
    'གཞུས།': 'Hit/struck',
    'འཕངས།': 'Threw',
    'གོང་སྒྲིག': 'Bargaining',
    'ཁེ་ཕན།': 'Benefit/profit',
    # === A2 L7-13: TRAVEL, FOOD, GAMES, etc. ===
    'མི་རིགས།': 'Ethnicity/nationality',
    'ཞིང་ཆེན།': 'Province',
    'བོད་རང་སྐྱོང་ལྗོངས།': 'Tibet Autonomous Region',
    'ཀུ་ཤུ།': 'Apple',
    'ཀུ་ཤུ': 'Apple',
    'སེ་ཡབ།': 'Carrot',
    'ཚོད་མ།': 'Vegetables',
    'ལ་ཕུག': 'Radish',
    'གཏུབ།': 'To chop/cut',
    'བཙོས།': 'Cooked/boiled',
    'བསྲེས།': 'Mixed',
    'རྩེད་མོ།': 'Game/play',
    'སོ་སིད།': 'Entertainment',
    'སྤྲོ་སྐྱིད།': 'Entertainment',
    'གཞས།': 'Song',
    'འཆམ།': 'Dance (religious)',
    'བྲོ།': 'Dance (secular)',
    'སེམས་ཅན།': 'Animal/sentient being',
    'རི་ཤིང་།': 'Plant/tree',
    'རྩི་ཤིང་།': 'Plant/tree',
    'ཁི།': 'Dog',
    'ཞིམ་བུ།': 'Cat',
    'རྟ།': 'Horse',
    'བ་ལང་།': 'Cow/ox',
    'འབྲི་མོ།': 'Female yak',
    'ཡག': 'Male yak',
    'ལུག': 'Sheep',
    'ར།': 'Goat',
    'བྱ།': 'Bird',
    'ཉ།': 'Fish',
    'ན་ཚ།': 'Illness/sick',
    'མགོ་ན།': 'Headache',
    'ལྟོ་ན།': 'Stomachache',
    'ཚད་པ།': 'Fever',
    'གློ་ན།': 'Cough/cold',
    'སྨན།': 'Medicine',
    'སྨན་ཁང་།': 'Hospital',
    'སོབ་སོང་།': 'Learning/study',
    'ཕི་རྒྱལ།': 'Abroad/foreign',
    'ཕྱི་རྒྱལ།': 'Abroad/foreign',
    'རྒྱལ་ཁབ།': 'Country/nation',
    # === B1 L1-13: ADVANCED TOPICS ===
    'འཚེར་སྣང་།': 'Embarrassment',
    'ག཈ོམ་ཆུང་།': 'Shy/timid',
    'སེམས་ཤོར།': 'Lost composure',
    'ཁ་བྲལ།': 'Parting/separation',
    'སིང་སྡུག': 'Heartache/love story',
    'སྙིང་སྡུག': 'Heartache/love story',
    'རེ་སྒུག': 'Waiting/expectation',
    'མིག་བཙུམ།': 'Winking/closing eyes',
    'སིང་རེ་པོ།': 'Lovable/adorable',
    'སྙིང་རྗེ་པོ།': 'Lovable/adorable',
    'ཀོག་ཀོག': 'Coy/coquettish',
    'ཁ་པར།': 'Telephone',
    'གློག་ཀླད།': 'Computer',
    'དྲ་རྒྱ།': 'Internet',
    'འཕྲིན་ཐུང་།': 'Text message',
    'ངོ་དེབ།': 'Facebook',
    'བརྙན་འཕྲིན།': 'Television',
    'གློག་བརྙན།': 'Movie/film',
    'གསར་འགྱུར།': 'News',
    'བསམ་བློ།': 'Thought/idea',
    'ཤེས་ཚད།': 'Knowledge/skill',
    'གདེང་ཚོད།': 'Confidence',
    'ཁ་གསང་།': 'Secret',
    'ཁ་བང་།': 'Letter/envelope',
    'གནས་སོར།': 'Transfer/relocation',
    'གནས་སྐོར།': 'Pilgrimage/tour',
    'གཏན་གོགས།': 'Close friend',
    'གཏའ་མ།': 'Bride/dowry',
    'བསོད་ནམས།': 'Merit/good fortune',
    'གཏིང་གསལ།': 'Transparent/clear',
    'མགོ་སྐོར།': 'Trick/deception',
    'ཁ་རོད།': 'Verbal quarrel',
    'གདོང་ལྱེན།': 'Welcome/reception',
    'འཆར་གཞི།': 'Plan/project',
    'འཆར་གཞྩི།': 'Plan/project',
    'གནོན་ཤུགས།': 'Pressure/stress',
    'ཕན་ཐོགས།': 'Benefit/helpful',
    'ཕན་ཐོགས་པ།': 'Benefit/helpful',
    'མདོ།': 'Amdo (region)',
    'དབུས།': 'Central Tibet',
    'ཁམས།': 'Kham (region)',
    'ཁས་བླངས།': 'Promised/vowed',
    'ངོ་ཚ།': 'Shame/embarrassment',
    'འཛེམ་དོགས།': 'Hesitation/reluctance',
    'བྱུས།': 'Strategy/plan',
    'བརྩེ་དུང་།': 'Love/affection',
    'མི་ཚེ།': 'Life/lifetime',
    'མདུན་ལམ།': 'Future/path ahead',
    'ལས་དབང་།': 'Destiny/karma',
    # === EXPANDED TRANSLATIONS (batch 1: daily life, time, weather) ===
    'ཀློག་དེབ།': 'Reading book',
    'ཁ་ཐུག': 'Face to face',
    'ཁ་བལ།': 'Wool',
    'ཁ་རི་ཁ་ཐུག': 'Direct encounter',
    'ཁ་རོད་ཤ ོར།': 'Lost an argument',
    'ཁ་ལ་ཉན་པྫོ།': 'Obedient',
    'ཁ་ལ་མི་ཉན།': 'Disobedient',
    'ཁ་ལན་སྫོག': 'Reply/answer back',
    'ཁ་སང་།': 'Yesterday',
    'ཁག': 'Part/group',
    'ཁྩིམ་གཞྩིས།': 'Home/homeland',
    'གཅག': 'To break/crush',
    'གཉྫོམ་ཆུང་།': 'Shy/timid',
    'གད་སོད།': 'Joke/humor',
    'གདོང་ལེན།': 'Welcome/reception',
    'གནས་བབ།': 'Situation/circumstances',
    'གནས་ཚང་།': 'Residence/dwelling',
    'གནོན།': 'To press/suppress',
    'གབ།': 'To hide',
    'གཙང་མ།': 'Clean/pure',
    'གཞག': 'To place/set down',
    'གཞུང་ལམ།': 'Highway/main road',
    'གཟའ་འཁོར།': 'Week',
    'གཡག': 'Male yak',
    'གཡར།': 'To borrow/lend',
    'གཡོལ་བ།': 'To avoid/evade',
    'གལ་ཆེན་པོ་རེད།': 'Very important',
    'གཤིས་ཀ': 'Character/temperament',
    'གསང་སོད།': 'Toilet/restroom',
    'གསར་པ།': 'New',
    'གསོ་རིག': 'Medical science',
    'གུ་ཡངས་པློ།': 'Generous',
    'གུག་གུག': 'Crooked/bent',
    'གུར།': 'Tent',
    'གུས་ཞབས།': 'Respect/politeness',
    'གོ་སྐབས།': 'Opportunity',
    'གོག་གསོག': 'Battery/storage',
    'གོག་པར།': 'Photograph',
    'གོག་བརྙན།': 'Movie/film',
    'གོང་གསེབ།': 'Village',
    'གོན།': 'To wear/put on',
    'གོམས་གཤིས།': 'Habit/custom',
    'གོས་བསྡུར།': 'Discussion/consultation',
    'གྟོས་ཐུང་།': 'Short skirt/dress',
    'གྡོག་སྐས།': 'Stairs/ladder',
    'གྱིང་ཆེན།': 'Continent',
    'གྲ་སིག': 'Preparation',
    'གྲང་ངར།': 'Severe cold/freezing',
    'གྲུ་གཟིངས།': 'Ship/boat',
    'གྲུ་བཞི།': 'Rectangle/square',
    'གྲུ་བཞི་ནར་མོ།': 'Rectangle',
    'གྲུབ་འབྲས།': 'Result/achievement',
    'གྲོང་སིག': 'Village/settlement',
    'གླ་ཆ།': 'Wages/salary',
    'གླ་ཕོག': 'Wages/income',
    'གླ་འཁོར།': 'Taxi/hired car',
    'གླུུ་གཞས།': 'Song/music',
    'གློད་ཆག': 'Discount/relaxation',
    'གློལ།': 'To separate/come apart',
    'ང་རྒྱལ།': 'Pride/arrogance',
    'ངལ་གསོ།': 'Rest/relaxation',
    'ངོ་ཚ་ཁེལ་མེད།': 'Shameless',
    'ཅ་ལག་རྫུན་མ།': 'Counterfeit goods',
    'ཆ་རེན།': 'Cause/condition',
    'ཆ་རྱེན།': 'Cause/condition',
    'ཆ་ལུགས།': 'Costume/attire',
    'ཆང་ས།': 'Bar/tavern',
    'ཆབ་སྩིད།': 'Politics',
    'ཆར་དུས།': 'Rainy season',
    'ཆར་པ་བབ།': 'It rained',
    'ཆུ་ཁོལ།': 'Boiling water',
    'ཆུ་ཁོལ་མ།': 'Boiled water',
    'ཆུ་ཆེན་བཞྱི།': 'The four great rivers',
    'ཆུ་འགམ།': 'Riverside/bank',
    'ཆུ་རྐྱལ།': 'Swimming',
    'ཆུ་ལོག': 'Flood',
    'ཆུ་ལློག': 'Flood',
    'ཆུང་དུས་ཀྱི་': 'Of childhood',
    'ཆེ་ཆུང་།': 'Big and small/size',
    'ཆེ་མཐོང་།': 'Respect/high regard',
    'ཆྲོས་ལུགས།': 'Religion',
    'ཉལ་ཁི།': 'Sleepy',
    'ཉལ་ཆས།': 'Bedding',
    'ཉིན་གང་།།': 'Whole day',
    'ཉིན་གུང་།': 'Noon/midday',
    'ཉེས་ཆད།': 'Punishment/penalty',
    'ཏག་ཏག': 'Exactly/precisely',
    'ཐབ་ཆས།': 'Cooking utensils',
    'ཐུག་འཕྲད།': 'Meeting/encounter',
    'ཐོ་རེངས།': 'Dawn/daybreak',
    'ཐོན་ཁུངས།': 'Source/resource',
    'ཐོལ་པ།': 'Suddenly/impromptu',
    'ཐློན་གསར་པ།': 'New product/invention',
    # === EXPANDED TRANSLATIONS (batch 2: དཀ-ད) ===
    'དཀའ་ངལ།': 'Difficulty/problem',
    'དཀར་ཟས།': 'Dairy food',
    'དགའ་ཞེན།': 'Fondness/attachment',
    'དགོས་མཁོ།': 'Need/necessity',
    'དང་པོ།': 'First',
    'དངུལ་འདྐོན་ས།': 'Bank/ATM',
    'དཔལ་འབོར།': 'Economy/wealth',
    'དཔལ་འབྱོར།': 'Economy/wealth',
    'དཔེ་མཛོད།': 'Library',
    'དབིངས།': 'Space/expanse',
    'དབུས་གཙང་།': 'Ü-Tsang (Central Tibet)',
    'དབྱར་ཁ།': 'Summer',
    'དབྱིབས།': 'Shape/form',
    'དམ་པྟོ།': 'Precious/holy',
    'དམ་བཅའ།': 'Vow/oath/promise',
    'དུས་ཐོག': 'On time',
    'དུས་བཀག': 'Deadline',
    'དུས་ཡུན།': 'Duration',
    'དོགས་པ།': 'Doubt/suspicion',
    'དྭངས།': 'Clear/pure',
    'དྱེང་སང་།': 'Nowadays/today',
    'དྲ་ལམ།': 'Internet/web',
    'དྲང་པྷོ།': 'Honest/straight',
    'དྲན།': 'To remember',
    'དྲན་པ་ཐོར།': 'Absent-minded',
    'དྲི་བ།': 'Question',
    # === EXPANDED TRANSLATIONS (batch 3: ན-ཕ) ===
    'ན་ཟུག': 'Pain/aching',
    'ནང་ཆོས།': 'Buddhism',
    'ནང་འཁྲུག': 'Civil war/internal conflict',
    'ནམ་ཕེད།': 'Midnight',
    'ནུས་ཤུགས།': 'Power/capability',
    'པགས་པ།': 'Skin/leather',
    'ཕམ།': 'Defeat/loss',
    'ཕམ་ཁ།': 'Defeat',
    'ཕར་ཚུར།': 'Back and forth',
    'ཕུགས་བསམ།': 'Long-term vision',
    'ཕེད་ཀ': 'Half',
    'ཕོག': 'Salary/wages',
    'ཕྲ་པོ།': 'Thin/fine/subtle',
    # === EXPANDED TRANSLATIONS (batch 4: བ) ===
    'བཀལ།': 'Loaded/placed upon',
    'བགློ་གེང་།': 'Discussion/debate',
    'བང་ཁྲི།': 'Throne/shelf',
    'བཅུག་པ།': 'Put in/inserted',
    'བཏུང་བྱ།': 'Beverage/drink',
    'བདེ་འཇགས།': 'Peace/safety',
    'བཙོག་པ།': 'Dirty',
    'བཟའ་ཆས།': 'Food/provisions',
    'བཟོ་བཅོས།': 'Repair/fix',
    'བཟོད་པ།': 'Patience/endurance',
    'བཟྟོ་ལྟ།': 'Shape/appearance',
    'བཟློ་བཅློས།': 'Repair/fix',
    'བར།': 'Gap/space/between',
    'བརི་བཀུར།': 'Respect/honor',
    'བརྒྱ།': 'Hundred',
    'བརྒྱུད་ནས།': 'Through/via',
    'བརྒྱུད་རྱིམ།': 'Process/procedure',
    'བརྗེ་དུང་།': 'Love/affection',
    'བརྙན་འཕིན།': 'Television',
    'བརྙས་བཅོས།': 'Contempt/disrespect',
    'བརྟན་པྷོ།': 'Stable/steady',
    'བརྡབ་གསིག': 'Catastrophe/disaster',
    'བརྡབ་སོན།': 'Notification/signal',
    'བཤལ།': 'Diarrhea',
    'བསིལ་པོ།': 'Cool/refreshing',
    'བསྐུར།': 'To send/dispatch',
    'བསྐྱར་སོང་།': 'Reviewed again',
    'བསྐྱར་སློང་།': 'Re-apply/restart',
    'བསྒུགས།': 'Waited',
    'བུ་ལོན།': 'Debt/loan',
    'བོད་ཇ།': 'Tibetan butter tea',
    'བོས།': 'Called/summoned',
    'བྱེད་རྩིས།': 'Plan/intention',
    'བླ་ཆྗེན།': 'High official/minister',
    # === EXPANDED TRANSLATIONS (batch 5: མ-ཚ) ===
    'མ་རྩ།': 'Capital/investment',
    'མཁས་པ།': 'Scholar/expert',
    'མགྐོགས་ལམ།': 'Highway/expressway',
    'མགློགས་ཚད།': 'Speed',
    'མང་ཉུང་།': 'More or less/quantity',
    'མངགས།': 'Ordered (goods/food)',
    'མངོན་འདོད།': 'Desire/ambition',
    'མཆོང་།': 'To jump/leap',
    'མཆོད་ཁང་།': 'Chapel/shrine',
    'མཆྲོད་སྱིན།': 'Offering/gift',
    'མཐུད་པ།': 'Connected/continued',
    'མཐུན་པྷོ།': 'Compatible/agreeable',
    'མཐུན་རེན།': 'Favorable condition',
    'མཐུན་རྱེན།།': 'Favorable condition',
    'མཐོང་ཆུང་།': 'Looking down on/contempt',
    'མདུན་ལ།': 'In front/ahead',
    'མཚན་ཚོགས།': 'Evening class',
    'མཚར་གཏམ།': 'Joke/funny story',
    'མཚེའུ།': 'Small lake/pond',
    'མཚོ།': 'Lake',
    'མཚོ་འགྲམ།': 'Lakeside/lakeshore',
    'མཛེས་སྡུག': 'Beauty/beautiful',
    'མཛོ་མོ།': 'Female dzo (yak hybrid)',
    'མི་འབོར།': 'Population',
    'མེ།': 'Fire',
    'ཙན་དན།': 'Sandalwood',
    'ཙོག་ཙོག': 'Sitting upright',
    'ཚ་གི་ཚི་གི': 'Bustling/noisy',
    'ཚ་གི་ཚི་གྱེ།': 'Bustling/noisy',
    'ཚ་གྲང་།': 'Hot and cold/temperature',
    'ཚ་བ།': 'Heat/fever',
    'ཚེས་པ།': 'Date (calendar)',
    'ཚོང་མགྲོན།': 'Customer',
    'ཚོང་ཤག': 'Receipt/invoice',
    'ཚོད་ལྟ།': 'Experiment/test',
    'ཚོན་མདྟོག': 'Color',
    'ཚྭ་ཁུ།': 'Brine/salt water',
    # === EXPANDED TRANSLATIONS (batch 6: ཞ-ཟ) ===
    'ཞབས་འདྲེན།': 'Invitation',
    'ཞབས་འདྲྱེན།': 'Invitation',
    'ཞབས་བོ།': 'Dance',
    'ཞབས་བློ།': 'Dance',
    'ཞེ་མེར་ལང་།': 'Got angry',
    'ཞེན།': 'Attachment/clinging',
    'ཞོགས་ཇ།': 'Breakfast',
    'ཞོན།': 'To ride',
    'ཞྩིབ་འཇུག': 'Research/investigation',
    'ཞྱིང་ལས།': 'Agriculture/farming',
    'ཟས་ཐོ།': 'Menu',
    'ཟས་བཅུད།': 'Nutrition',
    'ཟས་རིགས།': 'Types of food',
    'ཟས་ལྷག': 'Leftovers',
    'ཟིང་ཚ་པོ།': 'Chaotic/hectic',
    'ཟུག་གཅོག': 'Pain relief',
    'ཟུར།': 'Corner/side',
    # === EXPANDED TRANSLATIONS (batch 7: འ) ===
    'འཁབ་མཁན།': 'Actor/performer',
    'འགན་འཛིན།': 'Person in charge',
    'འགན་ལྱེན།': 'To take responsibility',
    'འགེལ་བཤད།': 'Explanation/commentary',
    'འགྱུར་བ།།': 'Change/transformation',
    'འགྲུལ་པ།': 'Traveler',
    'འགྲེམས་སོན་': 'Exhibition/display',
    'འགྲོ་སོང་།': 'Expenses/spending',
    'འཆམ་པྨོ།': 'Compatible/harmonious',
    'འཇམ་པོ།': 'Soft/smooth/gentle',
    'འཇའ།': 'Rainbow',
    'འཇུ།': 'To digest',
    'འཇོན་ཐང་།': 'Ability/capability',
    'འཐམ།': 'To hug/embrace',
    'འཐེན།': 'To pull/draw/smoke',
    'འདྲ་མི་འདྲ།': 'Similar and different',
    'འདྲི་ཞུ།': 'Inquiry/request',
    'འཕོ་བརླག': 'Waste/squandering',
    'འཕོག་བཅོམ།': 'Damage/destruction',
    'འབད་བརོན།': 'Effort/diligence',
    'འབྱུང་ཁུངས།': 'Source/origin',
    'འབྱེལ་པོ།': 'Related/busy',
    'འབྱེལ་བ།': 'Connection/relation',
    'འབྲས་བསིལ།': 'Cooked rice',
    'འབྲུ་རྱིགས།': 'Grains/cereals',
    'འཚོ་བ།': 'Livelihood/life',
    'འཚོང་།': 'To sell',
    'འཛམ་གིང་།': 'World',
    'འཛིང་།': 'To fight/struggle',
    'འཛིན་བཟུང་།': 'Arrested/detained',
    'འཛིན་བྱང་།': 'ID card/certificate',
    'འཛུགས་སྐྲུན།': 'Construction',
    'འཛོམས་པྲོ།': 'Gathering/assembly',
    # === EXPANDED TRANSLATIONS (batch 8: ཡ-ར) ===
    'ཡ་རབས།': 'Polite/well-mannered',
    'ཡག་སྡུག': 'Good and bad/quality',
    'ཡར་ཐོན།': 'Progress/improvement',
    'ཡར་མར།': 'Up and down',
    'ཡར་རྒྱས།': 'Development/progress',
    'ཡིད་ཆེས།': 'Trust/faith',
    'ཡིད་ཆྱེས།': 'Trust/faith',
    'ཡུལ་ལྐོངས།': 'Scenery/landscape',
    'ཡུལ་ལྡོངས།': 'Scenery/landscape',
    'ཡུལ་སོར།': 'Local tradition',
    'ཡུལ་སོལ་': 'Local tradition',
    'ཡློང་འབབ།': 'Income',
    'ར་ལུག': 'Goats and sheep',
    'རང་འདོད་ཚ་པོ།': 'Very selfish/willful',
    'རན་པོ།': 'Suitable/appropriate',
    'རལ།': 'Torn/tattered',
    'རིག་གཞུང་།': 'Culture/civilization',
    'རིང་པ།': 'Long',
    'རིང་པྟོ།': 'Long',
    'རིལ་རིལ།': 'Round/spherical',
    'རོ་པོ།': 'Tasty/flavorful',
    'རྐུབ་རིབ་པ།': 'Numb (from sitting)',
    'རྒྱ་ཆེན་པོ།': 'Very vast/extensive',
    'རྒྱ་མ་གང་།': 'One kilogram',
    'རྒྱགས།': 'Provisions/fodder',
    'རྒྱལ་ཁ།': 'Victory',
    'རྒྱལ་ཞྱེན།': 'Patriotism',
    'རྒྱུ་ཆ།': 'Material/ingredient',
    'རྔན་པ།': 'Reward/prize',
    'རྟག་པར།': 'Always/constantly',
    'རྣམ་པ།': 'Appearance/form',
    'རྣམ་འགྱུར།': 'Expression/attitude',
    'རྣམ་རོག': 'Thought/conception',
    'རྨ་དཀྲིས།': 'Bandage',
    'རྨ་རྩེས།': 'Scar',
    'རྩམ་པ།': 'Tsampa (barley flour)',
    'རྫས་རླངས།': 'Gas/vapor',
    'རྱིག་གནས།': 'Culture/civilization',
    'རྱེན་འབྱེལ།': 'Interdependence',
    'རླིང་བུ།': 'Flute',
    'རླུང་ཚ་པོ།': 'Very windy',
    'རློལ་ཆ།': 'Ornament/decoration',
    # === EXPANDED TRANSLATIONS (batch 9: ལ-ཤ) ===
    'ལག་འཁྱེར།': 'Mobile phone',
    'ལག་རྩལ།': 'Skill/craftsmanship',
    'ལམ་སོན།': 'Guidance/direction',
    'ལས་བྱེད།།': 'Worker/employee',
    'ལས་འཆར།': 'Work plan',
    'ལུས་རྩལ།': 'Physical exercise/sports',
    'ལོ་རྒྱུས།': 'History',
    'ལོག་ཟ།': 'Corruption/bribery',
    'ལོད་ལོད།': 'Loose/slack/relaxed',
    'ལྕང་མ།': 'Willow tree',
    'ལྟད་མོ།': 'Show/spectacle',
    'ལྡུམ་རྭ།': 'Garden',
    'ལྱེ་མིག': 'Key',
    'ལྷུག་ལྷུག': 'Loose/relaxed',
    'ལྷོད་ལྷོད།': 'Relaxed/calm',
    'ཤག': 'Paper/document',
    'ཤུག་པ།': 'Juniper/cypress',
    'ཤེས་ཡོན།': 'Education',
    'ཤོ་རྒྱག་པ།': 'Dice player/gambler',
    'ཤོར།': 'Lost/escaped',
    'ཤྙིང་ནགས།': 'Dense forest',
    # === EXPANDED TRANSLATIONS (batch 10: ས) ===
    'ས': 'Earth/ground',
    'ས་ཁུལ།': 'Area/region',
    'ས་གདན།': 'Seat cushion',
    'ས་ཡློམ།': 'Earthquake',
    'ས་སྣུམ།': 'Petroleum/fuel',
    'སིམ་སིམ།': 'Drizzle',
    'སེང་གེ།': 'Lion',
    'སེམས་གསློ།': 'Consolation/comfort',
    'སོ་ནད།': 'Toothache',
    'སོང་ཕྲག': 'Thousand',
    'སོད་ཆས།': 'Utensils/supplies',
    'སོད་པ།': 'Behavior/conduct',
    'སོད་པ་ངན་པ།': 'Bad behavior',
    'སོད་བཟང་།': 'Good behavior',
    'སོབ་ཁིད།': 'Lesson/teaching',
    'སོབ་སོང་བརྒྱུད་རྩིམ།': 'Curriculum',
    'སོབ་སོང་སོད་སྟངས།': 'Study methods',
    'སྐད་ཅོར།': 'Noise/clamor',
    'སྐད་ཡྩིག': 'Language/script',
    'སྐད་ཡྱིག': 'Language/script',
    'སྐད་སྒྱུར།': 'Translation',
    'སྐམ་པོ།': 'Dry/dried up',
    'སྐྱ་བྟོ།': 'Light/pale (color)',
    'སྐྱིལ་ཀྲུང་།': 'Cross-legged sitting',
    'སྐྱུག་པ།': 'Nausea/vomiting',
    'སྒང་ལ།': 'On top of/plateau',
    'སྒུག': 'To wait',
    'སྒྲུང་དེབ།': 'Storybook',
    'སྗེམས་པ་ཤ ོར།': 'Lost composure',
    'སྟག་དང་གཟིག': 'Tiger and leopard',
    'སྣ་འཛོམས་པོ།': 'Various/diverse',
    'སྣང་མྱེད།': 'Indifferent/uncaring',
    'སྣུམ།': 'Oil/grease',
    'སྤང།': 'Meadow/lawn',
    'སྤུས་ཀ': 'Quality',
    'སྤུས་ཀ་ཞན་པློ།': 'Poor quality',
    'སྨན་བཅོས།': 'Medical treatment',
    'སྨུག་པ།': 'Smoke/haze',
    'སྨྱུག་མ།': 'Bamboo',
    'སྩི་ཚོགས།': 'Society',
    'སྩི་ཚོགས་ཞབས་ཞུ།': 'Social service',
    'སྱེམས་ཁྲལ།': 'Worry/anxiety',
    'སྱེམས་ཤུགས།': 'Courage/morale',
    'སྱེམས་སྡུག': 'Sad/heartbroken',
    'སྲ་ཐག་ཐག': 'Very hard/solid',
    'སྲབ་སྲབ།': 'Thin/flimsy',
    'སྲེག': 'Burn/combustion',
    'སྲོག': 'Life (vital force)',
    'སློབ་ཁིད།': 'Lesson/teaching',
    'སློབ་ཐུན།': 'Class period',
    'སློབ་ཚན།': 'Lesson/subject',
    'སློབ་ཡློན།': 'Scholarship',
    # === EXPANDED TRANSLATIONS (batch 11: ཧ-ཨ) ===
    'ཧམ་པ་ཚ་པོ།': 'Very greedy',
    'ཧུར་ཐག': 'Diligent/earnest',
    'ཨ་མདོ།': 'Amdo (NE Tibet)',
    'ཨང་གྲངས།': 'Number/digit',
    # === EXPANDED TRANSLATIONS (batch 12: remaining identifiable) ===
    '཈མས་མོང་།': 'Experience',
    '཈མས་རྒུད།': 'Decline/deterioration',
    '཈ར་ཚགས།': 'Preservation/filing',
    'ཐྡོ་འགྡོད།': 'To register/record',
    'དཀླིལ།': 'Center/circle',
    'བརེ་པོ།': 'Busy',
    'བརྙས་བརོ།': 'Contempt/insult',
    'བོོས།': 'Called/summoned',
    'བྱ་བྱྗེའུ།': 'Chick/baby bird',
    'མངའ་རྐྱིས།': 'Ngari (W. Tibet region)',
    'མུ་གེ།': 'Famine',
    'འཐུང་ཡ།': 'Something to drink',
    'འདོང་པོ།': 'Stem/trunk',
    'ཡོད།': 'Have/exist',
    'རིས་སྡོད།': 'Taking turns',
    'རེས་ཟྱིན།': 'Diary/journal',
    'རེས་ལུས།': 'Remainder/leftover',
    'རོ་འགོག': 'Anesthesia',
    'རྒོག་བཙོས།': 'Stew/boiled dish',
    'རྒྱ་ཁློན།': 'Area/extent',
    'རྒྱས་སྒོས།': 'In detail',
    'རྙི་དྭགས།': 'Wild animals/game',
    'སག་རྫུན།': 'Lie/falsehood',
    'སིན་བདག': 'Patron/donor',
    'སིལ་ཚོང།': 'Retail',
    'སོ་སྱིད་ཁང་།': 'Entertainment hall',
    'སོང་།': 'Went',
    'སོར་སོར།': 'Individually/each',
    'སོལ།': 'Custom/tradition',
    'སྣ་ཁ།': 'Nose tip',
    'སྱིག་གཞྱི།': 'Basis/foundation',
    'སྲུང་སློབ།': 'Security guard',
    'སློང་ཚན།': 'Lesson/subject',
    'ཧར་པྟོ།': 'Funny/amusing',
    'ལེན་པྟོ།': 'To take/receive',
    'ལས་ས་པློ།': 'Workplace',
    'ཤྱེས་ཚད།': 'Knowledge level',
    'ཤྱེས་ཚད།།': 'Knowledge level',
    'འགན་བསྡུར།': 'Responsibility transfer',
    'ཟུར་བསྱེན།': 'Supplement',
    'ཚན་རྩིག་པ།': 'Scientist',
    'མིག་ལོག': 'Lightning',
    'ཡྱིག་ཚད།': 'Writing standard',
    'ཤ་མར་ཐུད།': 'Meat and butter dish',
    'རྒྱུག་ཤར།': 'Started running',
    'བེལ་བ་ཚ་པློ།': 'Very busy',
    'སོད་ཆས།': 'Utensils/supplies',
    'སེད་ཀ': 'Cold/chill',
    'སོན་མ།': 'Before/previously',
    'མ།': 'Mother',
}


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
