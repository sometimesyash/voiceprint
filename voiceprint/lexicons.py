"""Closed word lists.

The function word inventory is fixed rather than corpus-derived so that
vectors from different profiles are aligned and directly comparable. Burrows's
Delta needs a shared coordinate space; a per-corpus most-frequent-word list
would not give one.
"""
from __future__ import annotations

FUNCTION_WORDS = (
    "a about above across after again against all almost along already also "
    "although always am among an and another any anybody anyone anything are "
    "around as at away back be became because become been before behind being "
    "below beneath beside besides between beyond both but by came can cannot "
    "could did do does doing done down during each either else enough even "
    "ever every everybody everyone everything except far few for from further "
    "get gets got had has have having he her here hers herself him himself his "
    "how however i if in indeed inside instead into is it its itself just "
    "least less let like little made make many may me might mine more most "
    "much must my myself near neither never next no nobody none nor not "
    "nothing now of off often on once one only onto or other others otherwise "
    "ought our ours ourselves out outside over own perhaps quite rather really "
    "same seem seems several shall she should since so some somebody someone "
    "something sometimes somewhat soon still such than that the their theirs "
    "them themselves then there therefore these they this those though "
    "through throughout thus till to together too toward towards under unless "
    "until up upon us used very was way we well were what whatever when "
    "whenever where whereas whether which while who whom whose why will with "
    "within without would yet you your yours yourself yourselves"
).split()

CONTRACTED = (
    "aren't can't couldn't didn't doesn't don't hadn't hasn't haven't he'd "
    "he'll he's here's i'd i'll i'm i've isn't it's let's shan't she'd she'll "
    "she's shouldn't that's there's they'd they'll they're they've wasn't "
    "we'd we'll we're we've weren't what's won't wouldn't you'd you'll "
    "you're you've"
).split()

# Stay lowercase inside a Title Cased heading, so "The Cost of Delay" is not
# mistaken for Sentence case.
TITLE_MINOR = set(
    "a an and as at but by for from in into nor of off on onto or over per so "
    "the to up via vs with yet".split())

CLAUSE_MARKERS = set(
    "is are was were be been being am has have had do does did will would can "
    "could shall should may might must isn't aren't wasn't weren't hasn't "
    "haven't hadn't don't doesn't didn't won't wouldn't can't cannot couldn't "
    "shouldn't needs need gets get got goes go went comes come came makes "
    "make made takes take took gives give gave shows show showed means mean "
    "meant says say said sees see saw knows know knew wants want works work "
    "worked runs run ran costs cost fails fail failed grew grow grows fell "
    "falls fall rose rise rises lets let keeps keep kept puts put finds find "
    "found built build builds there's here's it's we're they're you're i'm "
    "that's what's".split())

# Biber-derived closed classes. Countable without a tagger.
SUBORDINATORS_CAUSATIVE = set("because since as".split())
SUBORDINATORS_CONCESSIVE = set("although though whereas while whilst".split())
SUBORDINATORS_CONDITIONAL = set("if unless whether".split())

PREPOSITIONS = set(
    "about above across after against along among around at before behind "
    "below beneath beside besides between beyond by despite down during "
    "except for from in inside into near of off on onto outside over past "
    "since through throughout to toward towards under underneath until up "
    "upon with within without".split())

AMPLIFIERS = set(
    "absolutely altogether completely enormously entirely extremely fully "
    "greatly highly intensely perfectly strongly thoroughly totally utterly "
    "very".split())

DOWNTONERS = set(
    "almost barely hardly merely mildly nearly partially partly practically "
    "scarcely slightly somewhat".split())

HEDGES = set(
    "maybe perhaps possibly probably apparently arguably presumably roughly "
    "sort kind about".split())

DISCOURSE_PARTICLES = set(
    "actually anyway basically honestly however meanwhile moreover "
    "nevertheless nonetheless obviously ok okay right so still therefore "
    "though thus well".split())

DEMONSTRATIVES = set("this that these those".split())
WH_WORDS = set("what when where which who whom whose why how".split())

PRONOUNS_FIRST_SG = set("i me my mine myself".split())
PRONOUNS_FIRST_PL = set("we us our ours ourselves".split())
PRONOUNS_SECOND = set("you your yours yourself yourselves".split())
PRONOUNS_THIRD = set(
    "he him his himself she her hers herself they them their theirs "
    "themselves".split())

NOMINAL_SUFFIXES = ("tion", "sion", "ment", "ity", "ness", "ance", "ence",
                    "ism", "ability", "isation", "ization")

STOPWORDS = set(FUNCTION_WORDS) | set("i he she it they we you".split())

# British and American variant pairs, counted to detect and quarantine dialect
# confound rather than to individuate.
ORTHOGRAPHIC_VARIANTS = {
    "ise_ize": (r"\w+is(e|ed|es|ing|ation)\b", r"\w+iz(e|ed|es|ing|ation)\b"),
    "our_or": (r"\b(colour|behaviour|favour|honour|labour|neighbour)\w*\b",
               r"\b(color|behavior|favor|honor|labor|neighbor)\w*\b"),
    "re_er": (r"\b(centre|theatre|metre|litre|fibre)\w*\b",
              r"\b(center|theater|meter|liter|fiber)\w*\b"),
    "ll_l": (r"\b(travelled|travelling|cancelled|labelled|modelling)\b",
             r"\b(traveled|traveling|canceled|labeled|modeling)\b"),
}
