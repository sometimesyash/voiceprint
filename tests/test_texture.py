"""The texture arm and the elicitation prompts."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from voiceprint import elicit
from voiceprint import texture as TX
from voiceprint.corpus import Corpus, Sample
from voiceprint.distance import measure
from voiceprint.doc import Doc
from voiceprint.profile import build

SHORT = ("We shipped on Friday and spent the weekend finding what we missed. "
         "The logs were the useful part, and nobody reads them until "
         "something breaks.")

LONG = (
    "We shipped on the Friday and spent the weekend finding what we had "
    "missed. The logs were the useful part. Nobody reads them until "
    "something breaks, and then they are the only thing anyone reads. I would "
    "rather have written fewer of them and made each one say what actually "
    "happened. That is the whole lesson, and it took a weekend to learn. "
) * 20

OTHER = (
    "The organisation implemented a transformation programme. Implementation "
    "of the framework required consideration of several dimensions. "
    "Evaluation of the intervention demonstrated significant improvement in "
    "operational performance across the relevant business units. "
) * 20


def profile_of(text: str):
    c = Corpus()
    c.add(Sample(text, origin="x", register="note"))
    return build(c, "x").pooled


class TextureProfile(unittest.TestCase):
    def test_covers_the_orders(self):
        p = TX.profile(Doc(LONG))
        self.assertEqual(sorted(p), ["3", "4", "5"])
        self.assertTrue(all(p[k] for k in p))

    def test_frequencies_are_normalised(self):
        p = TX.profile(Doc(LONG))
        for order in p.values():
            self.assertLess(max(order.values()), 1000.0)

    def test_empty_text_is_survivable(self):
        p = TX.profile(Doc(""))
        self.assertEqual(TX.distance(p, p), 0.0)

    def test_identical_text_is_zero(self):
        p = TX.profile(Doc(LONG))
        self.assertEqual(TX.distance(p, p), 0.0)

    def test_different_authors_are_further_than_the_same_one(self):
        mine = TX.profile(Doc(LONG))
        near = TX.profile(Doc(LONG[:2000]))
        far = TX.profile(Doc(OTHER))
        self.assertLess(TX.distance(near, mine), TX.distance(far, mine))


class Weighting(unittest.TestCase):
    def test_short_text_leans_entirely_on_texture(self):
        self.assertEqual(TX.delta_weight(100), 0.0)
        self.assertEqual(TX.delta_weight(TX.FLOOR_WORDS), 0.0)

    def test_weight_rises_with_support(self):
        weights = [TX.delta_weight(n) for n in (600, 1500, 3000, 6000)]
        self.assertEqual(weights, sorted(weights))

    def test_weight_is_capped(self):
        self.assertLessEqual(TX.delta_weight(1_000_000), TX.MAX_DELTA_WEIGHT)

    def test_blend_returns_the_weight_it_used(self):
        blended, w = TX.blend(4.0, 1.0, 100)
        self.assertEqual(w, 0.0)
        self.assertEqual(blended, 1.0)


class TwoArmDistance(unittest.TestCase):
    def setUp(self):
        self.profile = profile_of(LONG)

    def test_reports_which_arm_decided(self):
        d = measure(SHORT, self.profile)
        self.assertEqual(d.arm, "texture")
        self.assertEqual(d.delta_weight, 0.0)

    def test_support_is_the_smaller_side(self):
        d = measure(SHORT, self.profile)
        self.assertEqual(d.support_words, Doc(SHORT).n_words)

    def test_identity_matches_the_stated_weighting(self):
        d = measure(LONG[:3000], self.profile)
        expected = round(d.delta_weight * d.delta
                         + (1 - d.delta_weight) * d.texture, 4)
        self.assertAlmostEqual(d.identity, expected, places=3)

    def test_texture_beats_delta_on_a_short_sample(self):
        """The reason the arm exists, asserted so it cannot regress."""
        own = measure(LONG[:900], self.profile)
        other = measure(OTHER[:900], self.profile)
        self.assertLess(own.texture, other.texture)

    def test_short_own_text_is_nearer_than_short_foreign_text(self):
        own = measure(LONG[:700], self.profile)
        other = measure(OTHER[:700], self.profile)
        self.assertLess(own.overall, other.overall)


class ProfileCarriesTexture(unittest.TestCase):
    def test_texture_is_stored(self):
        self.assertTrue(profile_of(LONG).texture)

    def test_texture_survives_a_round_trip(self):
        import os
        import tempfile

        from voiceprint import store
        tmp = tempfile.mkdtemp()
        os.environ["VOICEPRINT_HOME"] = tmp
        try:
            c = Corpus()
            c.add(Sample(LONG, origin="x", register="note"))
            vp = build(c, "rt")
            store.save(vp, overwrite=True)
            loaded = store.load("rt")
            self.assertEqual(loaded.pooled.texture, vp.pooled.texture)
        finally:
            os.environ.pop("VOICEPRINT_HOME", None)


class Calibration(unittest.TestCase):
    def test_both_arms_are_recorded(self):
        path = Path(TX.__file__).parent / "data" / "calibration.json"
        cal = json.loads(path.read_text(encoding="utf8"))
        self.assertIn("by_arm", cal)
        self.assertEqual(sorted(cal["by_arm"]), ["blended", "delta", "texture"])

    def test_texture_wins_on_the_shortest_passages(self):
        path = Path(TX.__file__).parent / "data" / "calibration.json"
        cal = json.loads(path.read_text(encoding="utf8"))["by_arm"]
        short = f"{cal_key()}x400"
        self.assertGreater(cal["texture"][short], cal["delta"][short],
                           "texture no longer beats delta on short text")

    def test_blend_never_collapses_to_the_worse_arm(self):
        """It may lose a little to the better arm; it must not lose a lot.

        Texture alone scores about as well as any weighting across the whole
        grid, so the blend earns its place by capping the worst case rather
        than by raising the average. Forty trials per cell puts the standard
        error near eight points, so only a gap well beyond that means
        anything.
        """
        path = Path(TX.__file__).parent / "data" / "calibration.json"
        cal = json.loads(path.read_text(encoding="utf8"))
        noise = 1.0 / cal["trials_per_cell"] ** 0.5 / 2
        arms = cal["by_arm"]
        losses = [max(arms["delta"][k], arms["texture"][k]) - arms["blended"][k]
                  for k in arms["blended"]]
        self.assertLess(sum(losses) / len(losses), 0.03,
                        "blend is systematically worse than picking one arm")
        collapsed = [k for k in arms["blended"]
                     if arms["blended"][k]
                     < min(arms["delta"][k], arms["texture"][k]) - noise]
        self.assertEqual(collapsed, [],
                         "blend fell below both arms by more than noise")

    def test_blend_beats_delta_alone_on_average(self):
        path = Path(TX.__file__).parent / "data" / "calibration.json"
        cal = json.loads(path.read_text(encoding="utf8"))["by_arm"]
        mean = lambda d: sum(d.values()) / len(d)
        self.assertGreater(mean(cal["blended"]), mean(cal["delta"]) + 0.05)


def cal_key() -> int:
    return 20000


class Elicit(unittest.TestCase):
    def test_nothing_asked_when_the_corpus_is_big_enough(self):
        self.assertEqual(elicit.plan(5000), [])
        self.assertIn("enough", elicit.brief(5000))

    def test_registers_are_spread_before_repeating(self):
        chosen = elicit.plan(0, target=800)
        registers = [p.register for p in chosen]
        self.assertEqual(len(registers), len(set(registers)))

    def test_plan_covers_the_gap(self):
        chosen = elicit.plan(500, target=2500)
        self.assertGreaterEqual(sum(p.words for p in chosen), 1500)

    def test_brief_names_the_gap(self):
        text = elicit.brief(890, target=2500)
        self.assertIn("890", text)
        self.assertIn("2,500", text)

    def test_prompts_ask_for_writing_not_description(self):
        for p in elicit.PROMPTS:
            self.assertNotIn("describe how you write", p.ask.lower())
            self.assertTrue(p.why, f"{p.ask} has no rationale")


if __name__ == "__main__":
    unittest.main()
