"""The store, the gate in front of it, and what the ladder does with nothing."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from voiceprint import store
from voiceprint.corpus import Corpus, Ladder, NoCorpus, Sample
from voiceprint.profile import build
from voiceprint.render import to_markdown

PROSE = (
    "We shipped it on the Friday and spent the weekend finding out what we "
    "had missed. The logs were the useful part. Nobody reads them until "
    "something breaks, and then they are the only thing anyone reads. I "
    "would rather have written fewer of them and made each one say what "
    "actually happened. That is the whole lesson and it took a weekend. "
) * 8


def _profile(name="tester"):
    c = Corpus()
    c.add(Sample(PROSE, origin="test", register="note"))
    return build(c, name)


class Store(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.environ["VOICEPRINT_HOME"] = self.tmp

    def tearDown(self):
        os.environ.pop("VOICEPRINT_HOME", None)

    def test_home_follows_the_environment(self):
        self.assertEqual(store.home(), Path(self.tmp))

    def test_saved_as_markdown(self):
        p = store.save(_profile())
        self.assertEqual(p.suffix, ".md")
        body = p.read_text(encoding="utf8")
        self.assertTrue(body.startswith("# Voiceprint: tester"))
        self.assertIn("## How this person writes", body)

    def test_round_trip_keeps_the_measurements(self):
        original = _profile()
        store.save(original)
        loaded = store.load("tester")
        self.assertEqual(loaded.words, original.words)
        self.assertEqual(loaded.pooled.confidence, original.pooled.confidence)
        self.assertEqual(
            loaded.pooled.scalars["rhythm.words_per_sentence"].mean,
            original.pooled.scalars["rhythm.words_per_sentence"].mean)

    def test_will_not_overwrite_silently(self):
        store.save(_profile())
        with self.assertRaises(store.ProfileExists):
            store.save(_profile())
        self.assertTrue(store.save(_profile(), overwrite=True).is_file())

    def test_missing_profile_says_what_to_do(self):
        with self.assertRaises(store.ProfileMissing) as ctx:
            store.require("nobody")
        self.assertIn("vp build", str(ctx.exception))

    def test_exists_gate(self):
        self.assertFalse(store.exists("tester"))
        store.save(_profile())
        self.assertTrue(store.exists("tester"))

    def test_prose_survives_without_the_data_block(self):
        p = store.save(_profile())
        text = p.read_text(encoding="utf8")
        p.write_text(text.split("```json voiceprint")[0], encoding="utf8")
        with self.assertRaises(ValueError):
            store.load("tester")

    def test_names_are_slugged(self):
        self.assertEqual(store.slug("Yash Nairan"), "yash-nairan")
        self.assertEqual(store.slug("  "), "default")

    def test_delete(self):
        store.save(_profile())
        self.assertTrue(store.delete("tester"))
        self.assertFalse(store.delete("tester"))


class Rendering(unittest.TestCase):
    def test_readable_without_the_json(self):
        md = to_markdown(_profile())
        self.assertIn("Sentences run to about", md)
        self.assertIn("Confidence:", md)
        self.assertNotIn("{", md.split("## Sources")[0])


class Ingest(unittest.TestCase):
    def test_quoted_history_dropped(self):
        from voiceprint.ingest import quoted_reply_removed
        got = quoted_reply_removed(
            "My actual reply here.\n\nOn Tuesday someone wrote:\n> their words")
        self.assertEqual(got, "My actual reply here.")

    def test_signature_dropped(self):
        from voiceprint.ingest import quoted_reply_removed
        got = quoted_reply_removed("The point.\n--\nName\nTitle")
        self.assertEqual(got, "The point.")

    def test_missing_path_raises(self):
        from voiceprint.ingest import read_path
        with self.assertRaises(FileNotFoundError):
            list(read_path("no/such/place"))


class Ladder_(unittest.TestCase):
    def test_declined_connector_is_skipped_not_read(self):
        read = []

        class Nosy:
            name, label = "nosy", "nosy"
            def available(self): return True
            def describe(self): return "read everything"
            def fetch(self, limit):
                read.append(True)
                return [Sample(PROSE, origin="nosy")]

        with self.assertRaises(NoCorpus):
            Ladder(connectors=[Nosy()], ask=lambda _: False).gather()
        self.assertEqual(read, [], "a declined source must not be read")

    def test_accepted_connector_is_used(self):
        class Willing:
            name, label = "willing", "willing"
            def available(self): return True
            def describe(self): return "read my notes"
            def fetch(self, limit): return [Sample(PROSE, origin="willing")]

        corpus, log = Ladder(connectors=[Willing()], ask=lambda _: True).gather()
        self.assertEqual(len(corpus), 1)
        self.assertTrue(any("willing" in line for line in log))

    def test_broken_connector_does_not_stop_the_run(self):
        class Broken:
            name, label = "broken", "broken"
            def available(self): return True
            def describe(self): return "x"
            def fetch(self, limit): raise RuntimeError("nope")

        corpus, log = Ladder(connectors=[Broken()], ask=lambda _: True).gather(
            pasted=PROSE)
        self.assertEqual(len(corpus), 1)
        self.assertTrue(any("failed" in line for line in log))

    def test_falls_through_to_pasted_text(self):
        corpus, log = Ladder(connectors=[]).gather(pasted=PROSE)
        self.assertEqual(corpus.samples[0].origin, "pasted")

    def test_refusal_explains_itself(self):
        with self.assertRaises(NoCorpus) as ctx:
            Ladder(connectors=[]).gather()
        message = str(ctx.exception)
        self.assertIn("cannot be inferred", message)


if __name__ == "__main__":
    unittest.main()
