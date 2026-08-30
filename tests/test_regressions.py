"""Regressions for the defects found in review.

Each of these passed silently before the fix, which is why they are here as
named tests rather than folded into the general suite.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from voiceprint import distance as D
from voiceprint.corpus import Corpus, Ladder, NoCorpus, Sample
from voiceprint.doc import Doc
from voiceprint.features import group_of, groups, registry
from voiceprint.features.lexical import function_word_vector
from voiceprint.mcp import dispatch, handle
from voiceprint.profile import build
from voiceprint.windows import Estimate

PROSE = (
    "We shipped on the Friday and spent the weekend finding what we had "
    "missed. The logs were the useful part. Nobody reads them until "
    "something breaks, and then they are the only thing anyone reads. I would "
    "rather have written fewer of them and made each one say what actually "
    "happened. That is the whole lesson, and it took a weekend to learn. "
) * 20


class Nosy:
    """A connector that records whether it was read."""

    name, label = "nosy", "everything you have ever written"

    def __init__(self):
        self.read = False

    def available(self):
        return True

    def describe(self):
        return "READ EVERYTHING"

    def fetch(self, limit):
        self.read = True
        return [Sample(PROSE, origin="nosy")]


class ConsentFailsClosed(unittest.TestCase):
    """A host that forgets to wire consent must get nothing, not a mailbox."""

    def test_no_callback_means_declined(self):
        c = Nosy()
        with self.assertRaises(NoCorpus):
            Ladder(connectors=[c]).gather()
        self.assertFalse(c.read, "connector was read with no consent prompt")

    def test_callback_that_raises_means_declined(self):
        c = Nosy()

        def boom(_):
            raise RuntimeError("no prompt available")

        with self.assertRaises(NoCorpus):
            Ladder(connectors=[c], ask=boom).gather()
        self.assertFalse(c.read)

    def test_callback_returning_none_means_declined(self):
        c = Nosy()
        with self.assertRaises(NoCorpus):
            Ladder(connectors=[c], ask=lambda _: None).gather()
        self.assertFalse(c.read)

    def test_explicit_yes_is_honoured(self):
        c = Nosy()
        corpus, _ = Ladder(connectors=[c], ask=lambda _: True).gather()
        self.assertTrue(c.read)
        self.assertEqual(len(corpus), 1)

    def test_refusal_is_logged_not_silent(self):
        c = Nosy()
        try:
            Ladder(connectors=[c]).gather()
        except NoCorpus:
            pass
        _, log = Ladder(connectors=[c]).gather.__self__, None
        corpus = Corpus()
        ladder = Ladder(connectors=[c])
        entries: list[str] = []
        ladder._consented(c, entries)
        self.assertTrue(any("consent" in e for e in entries), entries)


class DeltaIsCalibrated(unittest.TestCase):
    """Delta needs between-author variation or it is not Delta."""

    def test_baseline_ships(self):
        self.assertTrue(D.delta_is_calibrated(),
                        "data/baseline.json missing, Delta falls back")

    def test_baseline_is_multi_author(self):
        base = D.baseline()
        self.assertGreaterEqual(base["authors"], 10)
        self.assertEqual(base["kind"], "function_word_between_author")

    def test_distance_reports_whether_it_was_calibrated(self):
        v = function_word_vector(Doc(PROSE))
        _, calibrated = D.burrows_delta(v, v)
        self.assertIsInstance(calibrated, bool)

    def test_calibration_table_ships_and_converges(self):
        path = Path(D.__file__).parent / "data" / "calibration.json"
        self.assertTrue(path.exists(), "no calibration table")
        cal = json.loads(path.read_text(encoding="utf8"))
        best = max(cal["accuracy"].values())
        self.assertGreater(best, 0.8,
                           "attribution never converges; implementation suspect")
        self.assertGreater(best, cal["chance"] * 10)


class NoDoubleCounting(unittest.TestCase):
    """One habit must move the distance once, not three times."""

    def test_apostrophes_are_not_measured_twice(self):
        self.assertNotIn("punct.apostrophe_per100", registry())

    def test_contraction_family_shares_a_group(self):
        self.assertEqual(group_of("register.contractions_per100"),
                         group_of("register.negation_synthetic_rate"))

    def test_correlated_features_are_grouped(self):
        for a, b in (("rhythm.words_per_sentence", "rhythm.length_cv"),
                     ("person.first_sg_per100", "person.first_pl_per100"),
                     ("richness.mattr", "richness.mtld"),
                     ("word.mean_length", "word.long_rate")):
            self.assertEqual(group_of(a), group_of(b), f"{a} vs {b}")

    def test_grouping_actually_reduces_the_count(self):
        self.assertLess(len(groups()), len(registry()))

    def test_one_group_contributes_once(self):
        devs = [
            D.Deviation("a", "f", 1.0, 0.0, 0.1, 6.0),
            D.Deviation("b", "f", 1.0, 0.0, 0.1, 6.0),
        ]
        devs[0].__dict__["feature"] = "register.contractions_per100"
        devs[1].__dict__["feature"] = "register.negation_synthetic_rate"
        self.assertEqual(D.aggregate_scalar(devs), 6.0,
                         "two views of one habit averaged to more than one")

    def test_mutual_absence_is_ignored(self):
        present = [D.Deviation("punct.comma_per100", "punctuation",
                               5.0, 1.0, 1.0, 4.0)]
        padded = present + [
            D.Deviation(f"punct.{m}_per100", "punctuation", 0.0, 0.0, 0.01, 0.0)
            for m in ("ampersand", "bracket", "slash", "ellipsis")]
        self.assertEqual(D.aggregate_scalar(present),
                         D.aggregate_scalar(padded),
                         "marks absent from both texts diluted the distance")


class OverlapIsDiscounted(unittest.TestCase):
    """Overlapping windows are not independent observations."""

    def test_effective_n_discounts_overlap(self):
        self.assertEqual(Estimate(1.0, 0.5, 10, 0.0).effective_n, 10)
        self.assertEqual(Estimate(1.0, 0.5, 10, 0.5).effective_n, 5)

    def test_thin_profile_records_its_overlap(self):
        c = Corpus()
        c.add(Sample(PROSE[:1200], origin="x", register="note"))
        p = build(c, "x").pooled
        est = next(iter(p.scalars.values()))
        self.assertGreater(est.overlap, 0.0,
                           "short corpus was windowed with overlap but did "
                           "not record it")
        self.assertLess(est.effective_n, est.n)

    def test_overlap_survives_a_round_trip(self):
        e = Estimate(1.0, 0.5, 9, 0.5)
        self.assertEqual(Estimate.from_dict(e.as_dict()).effective_n,
                         e.effective_n)


class JsonRpc(unittest.TestCase):
    """Protocol defects that would break a real client."""

    def test_notifications_are_never_answered(self):
        for method in ("notifications/initialized", "notifications/progress",
                       "notifications/anything_at_all"):
            self.assertIsNone(handle({"jsonrpc": "2.0", "method": method}),
                              f"responded to notification {method}")

    def test_requests_are_always_answered(self):
        r = handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        self.assertEqual(r["id"], 1)
        self.assertIn("tools", r["result"])

    def test_unknown_method_with_an_id_gets_an_error(self):
        r = handle({"jsonrpc": "2.0", "id": 9, "method": "nope"})
        self.assertEqual(r["error"]["code"], -32601)

    def test_batch_does_not_crash(self):
        out = dispatch([
            {"jsonrpc": "2.0", "id": 1, "method": "ping"},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        ])
        self.assertEqual(len(out), 2, "batch dropped or invented responses")

    def test_non_object_does_not_crash(self):
        self.assertEqual(handle("not an object")["error"]["code"], -32600)
        self.assertEqual(dispatch([])["error"]["code"], -32600)


class NoDeadCode(unittest.TestCase):
    def test_windows_has_no_unreachable_duplicate(self):
        from voiceprint import windows
        source = Path(windows.__file__).read_text(encoding="utf8")
        body = source.split("def windows(")[1].split("\ndef ")[0]
        self.assertEqual(body.count("out: list[str] = []"), 1,
                         "duplicated loop after the return is back")


class ShortTextIsFlagged(unittest.TestCase):
    """Attribution on short passages is near chance, so say so."""

    def test_short_draft_is_marked_unreliable(self):
        from voiceprint.check import against_profile
        c = Corpus()
        c.add(Sample(PROSE, origin="x", register="note"))
        p = build(c, "x").pooled
        report = against_profile("Short note. Only a few words here.", p)
        self.assertFalse(report.reliable)

    def test_long_draft_is_not_flagged(self):
        from voiceprint.check import against_profile
        c = Corpus()
        c.add(Sample(PROSE, origin="x", register="note"))
        p = build(c, "x").pooled
        self.assertTrue(against_profile(PROSE, p).reliable)


if __name__ == "__main__":
    unittest.main()
