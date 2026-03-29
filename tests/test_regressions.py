import re
import unittest
from pathlib import Path

import parse_textbooks


REPO_ROOT = Path(__file__).resolve().parents[1]
BUILD_APP_SOURCE = (REPO_ROOT / "build_app.py").read_text(encoding="utf-8")


class OcrFixRegressionTests(unittest.TestCase):
    def test_spurious_subjoined_ma_is_removed_for_known_ocr_artifacts(self):
        self.assertEqual(parse_textbooks.fix_ocr_errors("གཏྨོང"), "གཏོང")
        self.assertEqual(parse_textbooks.fix_ocr_errors("པྨོས"), "པོས")

    def test_valid_padma_form_is_preserved(self):
        self.assertEqual(parse_textbooks.fix_ocr_errors("པདྨོ"), "པདྨོ")
        self.assertEqual(parse_textbooks.fix_ocr_errors("པདྨ"), "པདྨ")

    def test_valid_rma_and_sma_stacks_are_preserved(self):
        self.assertEqual(parse_textbooks.fix_ocr_errors("རྨོང"), "རྨོང")
        self.assertEqual(parse_textbooks.fix_ocr_errors("སྨུག་པ"), "སྨུག་པ")

    def test_broken_vowel_spacing_is_fixed(self):
        self.assertEqual(parse_textbooks.fix_ocr_errors("ཤ ོག"), "ཤོག")
        self.assertEqual(parse_textbooks.fix_ocr_errors("ག ོན"), "གོན")

    def test_unassigned_tibetan_letter_is_normalized(self):
        self.assertEqual(parse_textbooks.fix_ocr_errors("\u0F48མ"), "ཉམ")

    def test_nyal_khi_is_normalized_to_nyal_khri(self):
        self.assertEqual(parse_textbooks.fix_ocr_errors("ཉལ་ཁི།"), "ཉལ་ཁྲི།")


class LookupRegressionTests(unittest.TestCase):
    def test_fill_answer_lookup_uses_normalized_sentence_key(self):
        original_answers = parse_textbooks.FILL_ANSWERS
        original_normalized_answers = parse_textbooks.NORMALIZED_FILL_ANSWERS
        try:
            parse_textbooks.FILL_ANSWERS = {
                "༥ ང་ཚོའི་ནང་ལ་_______གཅིག་དང་ཁི་གཉིས་ཡོད།": "ཞི་མི"
            }
            parse_textbooks.NORMALIZED_FILL_ANSWERS = {
                parse_textbooks.fix_ocr_errors(k): v
                for k, v in parse_textbooks.FILL_ANSWERS.items()
            }
            fill_blanks = [{
                "sentence": "༥ ང་ཚོའི་ནང་ལ་_______གཅིག་དང་ཁྱི་གཉིས་ཡོད།",
                "word_bank": ["ཞི་མི", "ཁྱོ་ག ནང་མི", "གྲོགས་པོ", "བུ"],
            }]
            applied = parse_textbooks.apply_fill_answers(fill_blanks)
            self.assertEqual(applied, 1)
            self.assertEqual(fill_blanks[0]["answer"], "ཞི་མི")
        finally:
            parse_textbooks.FILL_ANSWERS = original_answers
            parse_textbooks.NORMALIZED_FILL_ANSWERS = original_normalized_answers

    def test_translation_lookup_uses_specific_ocr_correction(self):
        original_vocab = parse_textbooks.VOCAB_TRANSLATIONS
        original_normalized_vocab = parse_textbooks.NORMALIZED_VOCAB_TRANSLATIONS
        try:
            parse_textbooks.VOCAB_TRANSLATIONS = {"ཉལ་ཁྲི།": "Bed/cot"}
            parse_textbooks.NORMALIZED_VOCAB_TRANSLATIONS = {
                parse_textbooks.fix_ocr_errors(k.rstrip("།").rstrip("་").strip()): v
                for k, v in parse_textbooks.VOCAB_TRANSLATIONS.items()
            }
            self.assertEqual(parse_textbooks._lookup_translation("ཉལ་ཁི།"), "Bed/cot")
        finally:
            parse_textbooks.VOCAB_TRANSLATIONS = original_vocab
            parse_textbooks.NORMALIZED_VOCAB_TRANSLATIONS = original_normalized_vocab


class BuildTemplateRegressionTests(unittest.TestCase):
    def test_vocab_flashcards_show_all_words(self):
        """User feedback: learner must see ALL vocab before quizzes.
        Capping at 8 meant she got tested on words she hadn't seen yet."""
        self.assertIn("flashcardVocab = shuffle(vocab.filter(v => v.en));", BUILD_APP_SOURCE)
        self.assertNotIn(".slice(0, 8)", BUILD_APP_SOURCE.split("flashcardVocab")[1].split(";")[0])

    def test_phrase_flashcards_require_english(self):
        """User reported 'Practice reading this phrase!' as a bug —
        phrases without English translation are not useful for learners."""
        self.assertIn(".filter(p => p && p.bo && p.en);", BUILD_APP_SOURCE)

    def test_fill_blank_exercises_still_require_renderable_word_banks(self):
        self.assertIn("Array.isArray(fb.word_bank)", BUILD_APP_SOURCE)
        self.assertIn("fb.word_bank.length > 0", BUILD_APP_SOURCE)

    def test_fill_blank_exercises_skip_multi_blank(self):
        """User found exercises with 2 blanks where only 1 could be filled."""
        self.assertIn("(fb.sentence.match(/_+/g) || []).length === 1", BUILD_APP_SOURCE)


if __name__ == "__main__":
    unittest.main()
