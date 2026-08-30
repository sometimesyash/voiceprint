"""Primitives. If these drift, every number above them is quietly wrong."""
from __future__ import annotations

import unittest

from voiceprint import text as T
from voiceprint.doc import Doc
from voiceprint.features.structure import is_fragment, is_stacked
from voiceprint.features.surface import caps_style, terminal_punct


class Sentences(unittest.TestCase):
    def test_splits_on_terminal_punctuation(self):
        self.assertEqual(len(T.sentences("One thing. Then another. And a third.")), 3)

    def test_keeps_abbreviations_intact(self):
        self.assertEqual(len(T.sentences("Ask Dr. Smith about it.")), 1)
        self.assertEqual(len(T.sentences("Costs approx. ten pounds each.")), 1)

    def test_line_breaks_are_boundaries(self):
        self.assertEqual(len(T.sentences("First line\nSecond line\nThird")), 3)

    def test_empty_input(self):
        self.assertEqual(T.sentences(""), [])
        self.assertEqual(T.sentences("   \n  "), [])

    def test_question_and_exclamation(self):
        self.assertEqual(len(T.sentences("Why? Because! Now.")), 3)


class Words(unittest.TestCase):
    def test_lowercases_and_keeps_apostrophes(self):
        self.assertEqual(T.words("Don't Stop"), ["don't", "stop"])

    def test_drops_bare_numerals(self):
        self.assertEqual(T.words("we saw 42 of them"), ["we", "saw", "of", "them"])

    def test_hyphenated_stays_one_word(self):
        self.assertEqual(T.words("well-worn path"), ["well-worn", "path"])


class Ngrams(unittest.TestCase):
    def test_char_ngrams_count(self):
        self.assertEqual(len(T.char_ngrams("abcd", 3)), 2)

    def test_char_ngrams_shorter_than_n(self):
        self.assertEqual(T.char_ngrams("ab", 3), [])

    def test_word_ngrams(self):
        self.assertEqual(T.word_ngrams(["a", "b", "c"], 2),
                         [("a", "b"), ("b", "c")])


class Capitalisation(unittest.TestCase):
    def test_all_caps(self):
        self.assertEqual(caps_style("THE PROBLEM"), "upper")

    def test_title_case_ignores_minor_words(self):
        self.assertEqual(caps_style("The Cost of Delay"), "title")

    def test_sentence_case(self):
        self.assertEqual(caps_style("The cost of delay"), "sentence")

    def test_lowercase(self):
        self.assertEqual(caps_style("the cost of delay"), "lower")

    def test_no_letters(self):
        self.assertEqual(caps_style("123 456"), "none")


class Terminal(unittest.TestCase):
    def test_marks(self):
        for s, want in (("Done.", "full_stop"), ("Really?", "question"),
                        ("Stop!", "exclamation"), ("Note:", "colon"),
                        ("Well...", "ellipsis"), ("No mark", "none")):
            self.assertEqual(terminal_punct(s), want, s)


class Fragments(unittest.TestCase):
    def test_verbless_noun_phrase_is_a_fragment(self):
        self.assertTrue(is_fragment("Problem Analysis"))

    def test_finite_clause_is_not(self):
        self.assertFalse(is_fragment("The pilot failed"))

    def test_stacked_declarative_detected(self):
        self.assertTrue(is_stacked("Two reasonable people. One permitted answer."))

    def test_ordinary_prose_is_not_stacked(self):
        self.assertFalse(is_stacked(
            "The pilot ran for six weeks and we learned that the first "
            "assumption was wrong. That changed the plan."))

    def test_single_sentence_is_not_stacked(self):
        self.assertFalse(is_stacked("One permitted answer."))


class DocCaching(unittest.TestCase):
    def test_counts_agree(self):
        d = Doc("First one here. Second one here too.")
        self.assertEqual(d.n_words, len(d.words))
        self.assertEqual(len(d.sentences), 2)
        self.assertEqual(d.sentence_lengths, [3, 4])

    def test_empty_doc(self):
        d = Doc("")
        self.assertEqual(d.n_words, 0)
        self.assertEqual(d.sentences, [])


if __name__ == "__main__":
    unittest.main()
