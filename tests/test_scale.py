"""Length-aware verdicts.

Both identity arms shrink as text grows, so a fixed threshold means something
different at every length. Measured across 24 authors: a person's own 200-word
passage scores about 2.3 while a stranger's 6,400-word passage scores about
1.0, so a band set at 1.5 failed the author and passed the stranger. These
tests pin the fix.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from voiceprint import distance as D
from voiceprint.corpus import Corpus, Sample
from voiceprint.profile import build

PROSE = (
    "We shipped on the Friday and spent the weekend finding what we had "
    "missed. The logs were the useful part. Nobody reads them until "
    "something breaks, and then they are the only thing anyone reads. I would "
    "rather have written fewer of them and made each one say what actually "
    "happened. That is the whole lesson, and it took a weekend to learn. "
) * 20


class ScaleTable(unittest.TestCase):
    def test_it_ships(self):
        self.assertIsNotNone(D.scale(), "data/scale.json missing")

    def test_covers_a_useful_range(self):
        sizes = D.scale()["sizes"]
        self.assertLessEqual(min(sizes), 400)
        self.assertGreaterEqual(max(sizes), 3200)

    def test_distance_really_does_shrink_with_length(self):
        """The reason the table exists, asserted so the rationale survives."""
        table = D.scale()["table"]
        sizes = sorted(int(s) for s in table)
        medians = [table[str(s)]["same"]["0.5"] for s in sizes]
        self.assertGreater(medians[0], medians[-1] * 2,
                           "a fixed threshold would be defensible after all")

    def test_same_author_is_nearer_than_others_at_every_length(self):
        for size, row in D.scale()["table"].items():
            self.assertLess(row["same"]["0.5"], row["other"]["0.5"], size)

    def test_separation_improves_with_length(self):
        table = D.scale()["table"]
        sizes = sorted(int(s) for s in table)
        self.assertGreater(table[str(sizes[0])]["overlap"],
                           table[str(sizes[-1])]["overlap"])


class Strangeness(unittest.TestCase):
    def test_returns_a_proportion(self):
        s = D.strangeness(1.5, 800)
        self.assertIsNotNone(s)
        self.assertGreaterEqual(s, 0.0)
        self.assertLessEqual(s, 1.0)

    def test_a_near_text_is_unusual_and_a_far_one_is_not(self):
        near = D.strangeness(0.3, 3200)
        far = D.strangeness(3.0, 3200)
        self.assertLess(near, far)

    def test_the_same_raw_distance_means_different_things_by_length(self):
        short = D.strangeness(1.5, 200)
        long_ = D.strangeness(1.5, 6400)
        self.assertLess(short, long_,
                        "length is not being taken into account")

    def test_the_old_inversion_is_gone(self):
        """A stranger at length used to pass while the author at short length
        failed. Both should now read the same way round."""
        author_short = D.strangeness(2.34, 200)
        stranger_long = D.strangeness(1.04, 6400)
        self.assertLessEqual(author_short, stranger_long,
                             "the author still looks stranger than a stranger")

    def test_unknown_length_degrades_quietly(self):
        self.assertIsNone(D.strangeness(1.0, 0))


class Verdicts(unittest.TestCase):
    def setUp(self):
        c = Corpus()
        c.add(Sample(PROSE, origin="x", register="note"))
        self.profile = build(c, "x").pooled

    def test_verdict_uses_the_percentile_when_available(self):
        d = D.measure(PROSE, self.profile)
        self.assertIsNotNone(d.strangeness)
        self.assertIn(d.verdict(), ("close", "acceptable", "drifting", "off"))

    def test_own_text_reads_as_close(self):
        self.assertIn(D.measure(PROSE, self.profile).verdict(),
                      ("close", "acceptable"))

    def test_foreign_text_reads_worse_than_own(self):
        other = (
            "The organisation implemented a transformation programme. "
            "Implementation of the framework required consideration of "
            "several dimensions across the relevant business units. "
        ) * 20
        own = D.measure(PROSE, self.profile)
        alien = D.measure(other, self.profile)
        self.assertGreater(alien.strangeness, own.strangeness)

    def test_distance_carries_its_own_length(self):
        d = D.measure(PROSE[:900], self.profile)
        self.assertGreater(d.words, 0)
        self.assertLess(d.words, 300)

    def test_serialises_the_percentile(self):
        payload = D.measure(PROSE, self.profile).as_dict()
        self.assertIn("strangeness", payload)
        self.assertIn("words", payload)

    def test_falls_back_to_bands_without_a_table(self):
        d = D.measure(PROSE, self.profile)
        raw = D.Distance(d.delta, d.scalar, d.ngram, 0.5, [], 0,
                         texture=d.texture, words=0)
        self.assertIsNone(raw.strangeness)
        self.assertEqual(raw.verdict(), "close")


if __name__ == "__main__":
    unittest.main()
