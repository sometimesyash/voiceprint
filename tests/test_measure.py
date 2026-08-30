"""Measurement behaviour: richness, windows, distance, blending."""
from __future__ import annotations

import unittest

from voiceprint.blend import blend
from voiceprint.corpus import Corpus, NoCorpus, Sample
from voiceprint.distance import burrows_delta, dispersion, measure
from voiceprint.doc import Doc
from voiceprint.features import registry
from voiceprint.features.lexical import function_word_vector
from voiceprint.features.richness import mattr, mtld, yules_k
from voiceprint.profile import build, confidence
from voiceprint.windows import Estimate, aggregate, window_size, windows

PROSE = (
    "The pilot ran for six weeks and by the end of it we had changed our minds "
    "about the thing we were most sure of. That is worth saying plainly. We "
    "thought the bottleneck was throughput, and it was not. It was that nobody "
    "could tell which queue a job was sitting in, so people asked, and the "
    "asking cost more than the queue ever did. I have seen this before in "
    "other teams and I expect to see it again. The fix was not clever. We put "
    "a status column on the board and the questions stopped. There is a "
    "temptation to write that up as a lesson about observability, but I think "
    "it is smaller and more useful than that: if people are asking you the "
    "same question every day, answer it once, in public, where they are "
    "already looking. Everything else we tried that quarter was more expensive "
    "and did less. The team was sceptical at first, which was reasonable, "
    "because we had tried three other things that had not worked. "
) * 6


class Richness(unittest.TestCase):
    def test_mattr_bounded(self):
        v = mattr(Doc(PROSE).words)
        self.assertGreater(v, 0.0)
        self.assertLessEqual(v, 1.0)

    def test_mattr_stable_across_lengths(self):
        words = Doc(PROSE).words
        short, long_ = mattr(words[:600]), mattr(words)
        self.assertLess(abs(short - long_), 0.15,
                        "MATTR should not collapse as the text grows")

    def test_raw_ttr_does_collapse(self):
        """The reason MATTR exists, asserted so the rationale stays visible."""
        words = Doc(PROSE).words
        ttr = lambda ws: len(set(ws)) / len(ws)
        self.assertGreater(ttr(words[:200]) - ttr(words), 0.15)

    def test_mtld_returns_zero_when_too_short(self):
        self.assertEqual(mtld(["a", "b", "c"]), 0.0)

    def test_yules_k_on_repetition(self):
        varied = yules_k("a b c d e f g h i j".split())
        repeated = yules_k("a a a a a b b b b b".split())
        self.assertGreater(repeated, varied)


class Windows(unittest.TestCase):
    def test_size_adapts_to_corpus(self):
        self.assertLess(window_size(1000), window_size(100_000))

    def test_enough_windows_to_estimate_spread(self):
        chunks = windows([PROSE])
        self.assertGreaterEqual(len(chunks), 4)

    def test_sentences_are_never_split(self):
        for chunk in windows([PROSE]):
            self.assertFalse(chunk.strip().endswith(("and", "the", "of")))

    def test_empty_corpus(self):
        self.assertEqual(windows([]), [])
        self.assertEqual(windows([""]), [])

    def test_aggregate_reports_support(self):
        est, cats = aggregate(windows([PROSE]))
        self.assertIn("rhythm.words_per_sentence", est)
        self.assertGreater(est["rhythm.words_per_sentence"].n, 1)
        self.assertIn("person.dominant", cats)


class Distance(unittest.TestCase):
    def setUp(self):
        c = Corpus()
        c.add(Sample(PROSE, origin="test", register="essay"))
        self.profile = build(c, "test").pooled

    def test_zero_variance_cannot_divide(self):
        self.assertGreaterEqual(dispersion(Estimate(0.0, 0.0, 9)), 0.001)
        self.assertGreater(dispersion(Estimate(10.0, 0.0, 9)), 0.5)

    def test_text_is_close_to_its_own_profile(self):
        d = measure(PROSE, self.profile)
        self.assertLess(d.delta, 0.6)
        self.assertIn(d.verdict(), ("close", "acceptable"))

    def test_foreign_text_is_further(self):
        alien = ("Leverage synergies. Unlock value. Transform outcomes. "
                 "Best-in-class. World-class. Cutting-edge. ") * 30
        near = measure(PROSE, self.profile)
        far = measure(alien, self.profile)
        self.assertGreater(far.overall, near.overall)

    def test_delta_of_identical_vectors_is_zero(self):
        v = function_word_vector(Doc(PROSE))
        delta, calibrated = burrows_delta(v, v)
        self.assertEqual(delta, 0.0)
        self.assertTrue(calibrated, "a between-author baseline should ship")

    def test_no_z_score_runs_away(self):
        d = measure(PROSE[:900], self.profile)
        self.assertTrue(all(abs(dev.z) <= 6.0 for dev in d.worst))


class Confidence(unittest.TestCase):
    def test_tiers_match_the_calibration(self):
        self.assertEqual(confidence(12000), "stable")
        self.assertEqual(confidence(6000), "usable")
        self.assertEqual(confidence(2000), "thin")
        self.assertEqual(confidence(900), "provisional")

    def test_tiers_are_not_more_optimistic_than_measured(self):
        """The calibration is the authority for these numbers, not taste."""
        import json
        from pathlib import Path

        from voiceprint import profile as P
        path = (Path(P.__file__).parent / "data" / "calibration.json")
        if not path.exists():
            self.skipTest("no calibration shipped")
        cal = json.loads(path.read_text(encoding="utf8"))
        best = max(v for k, v in cal["accuracy"].items()
                   if k.startswith(f"{P.STABLE_WORDS}x")
                   or k.startswith("40000x"))
        self.assertGreaterEqual(best, 0.8,
                                "stable tier claims more than was measured")


class Blending(unittest.TestCase):
    def setUp(self):
        mine = Corpus()
        mine.add(Sample(PROSE, origin="mine", register="essay"))
        self.mine = build(mine, "mine").pooled

        other = Corpus()
        other.add(Sample(
            "The organisation implemented a transformation. The "
            "implementation of the framework required consideration of "
            "several dimensions. Evaluation of the intervention demonstrated "
            "significant improvement in operational performance. " * 20,
            origin="other", register="report"))
        self.other = build(other, "other").pooled

    def test_rigid_features_never_move(self):
        rules = blend(self.mine, self.other, fidelity=0.5)
        for name, feat in registry().items():
            if feat.elasticity == 0.0 and name in rules.targets:
                self.assertEqual(rules.targets[name].source, "you", name)

    def test_lower_fidelity_moves_elastic_features_further(self):
        loose = blend(self.mine, self.other, fidelity=0.5)
        tight = blend(self.mine, self.other, fidelity=0.95)
        key = "register.nominalisation_per100"
        mine = self.mine.scalars[key].mean
        self.assertGreater(abs(loose.targets[key].value - mine),
                           abs(tight.targets[key].value - mine))

    def test_without_context_everything_is_yours(self):
        rules = blend(self.mine, None, fidelity=0.8)
        self.assertTrue(all(t.source == "you" for t in rules.targets.values()))

    def test_tolerances_are_never_zero(self):
        rules = blend(self.mine, None)
        self.assertTrue(all(t.tolerance > 0 for t in rules.targets.values()))


class CorpusRules(unittest.TestCase):
    def test_short_samples_rejected(self):
        c = Corpus()
        self.assertFalse(c.add(Sample("Too short.", origin="x")))

    def test_duplicates_rejected(self):
        c = Corpus()
        self.assertTrue(c.add(Sample(PROSE, origin="a")))
        self.assertFalse(c.add(Sample(PROSE, origin="b")))

    def test_registers_kept_apart(self):
        c = Corpus()
        c.add(Sample(PROSE, origin="a", register="essay"))
        c.add(Sample(PROSE.replace("pilot", "trial"), origin="b", register="email"))
        self.assertEqual(c.registers(), ["email", "essay"])


class NothingToMeasure(unittest.TestCase):
    def test_ladder_refuses_to_invent(self):
        from voiceprint.corpus import Ladder
        with self.assertRaises(NoCorpus):
            Ladder(connectors=[]).gather(files=None, pasted=None)

    def test_pasted_text_too_short_still_raises(self):
        from voiceprint.corpus import Ladder
        with self.assertRaises(NoCorpus):
            Ladder(connectors=[]).gather(pasted="Hello.")


if __name__ == "__main__":
    unittest.main()
