---

# Research Report: Measurable Parameters That Individuate a Person's Language

**Verification note:** Directly opened and read (full text or substantial sections): DetectGPT `arXiv:2301.11305`, GLTR `arXiv:1906.04043`, HC3/Guo et al. `arXiv:2301.07597`, Kulkarni et al. geographic variation `arXiv:1510.06786`, and Eder's publication list (maciejeder.org). Publisher pages for Burrows, Stamatatos, Grieve, Biber, Wright, Coulthard, Nerbonne (Tandfonline/OUP/Wiley/Cambridge) returned **403 Forbidden** or JS-only shells, so those are cited from established secondary knowledge and metadata, and I mark them **[metadata-verified, full text not opened]**. Where I could not verify a specific number, I say so.

---

## 1. Stylometry and Authorship Attribution

**Mosteller & Wallace (1964/1984), *Inference and Disputed Authorship: The Federalist*, Addison-Wesley / Springer.** **[metadata-verified]**
- Foundational work. Used **function-word frequency** (Bayesian analysis) to attribute the disputed Federalist papers to Madison. Key discriminators were high-frequency, topic-independent words: *upon, also, an, by, of, on, there, this, to, whilst/while, enough*.
- Feature type: raw/relative frequencies of a chosen set of function words. **Fully computable in pure Python** (regex/`str.split` + `collections.Counter`). No tagger.
- Establishes the central stylometric principle: the most *discriminating* features are the most *frequent, least conscious, most topic-neutral* words — the opposite of content words.

**Burrows, J. (2002), "'Delta': a Measure of Stylistic Difference and a Guide to Likely Authorship," *Literary and Linguistic Computing* 17(3):267–287.** **[metadata-verified]**
- Defines **Burrows's Delta**: take the *N* most frequent words (MFW) in a reference corpus (typically **40–150**, often extended to 500–1000 in later work), convert each text's frequency for each word to a **z-score** against corpus mean/SD, then compute the mean absolute difference of z-scores between texts. Smallest Delta = most likely author.
- Feature type: MFW relative frequencies (function words dominate the top of any frequency list). **Fully pure-Python computable.** The z-scoring is stdlib arithmetic.
- This is arguably the single most replicated, most-used stylometric method. It directly implies your tool should measure a **vector of MFW relative frequencies**, not just a handful of hand-picked features.

**Stamatatos, E. (2009), "A Survey of Modern Authorship Attribution Methods," *JASIST* 60(3):538–556.** **[metadata-verified]** — the head-to-head survey you asked for.
- Taxonomy of feature families:
  - **Lexical**: word frequencies, function words, word *n*-grams, vocabulary richness (TTR etc.), word-length distributions. Mostly pure-Python.
  - **Character**: **character *n*-grams** (typically 3–5 grams). Stamatatos repeatedly identifies these as **among the most effective and most robust** features — they implicitly capture lexical preferences, morphology, punctuation, and even some syntax, and degrade gracefully on noisy/short text. **Pure-Python computable** (sliding window over the raw string).
  - **Syntactic**: POS *n*-grams, chunk/parse features — **requires a tagger/parser** (excluded by your constraint).
  - **Semantic**: synonyms, semantic dependencies — needs external resources (excluded).
  - **Application-specific**: HTML tags, greetings, etc.
- Key takeaway for you: the two feature families with the strongest, most replicated discriminative power that *don't* need a tagger are **(a) function-word / MFW frequencies and (b) character n-grams**. Your instinct is correct — these are your two big omissions.

**Koppel, M., Schler, J., & Argamon, S. (2009), "Computational Methods in Authorship Attribution," *JASIST* 60(1):9–26.** **[metadata-verified]**
- Reviews the discipline; emphasizes function words and character n-grams; discusses the "many candidate authors / limited data" regime and the confound that classifiers can latch onto **topic** rather than style. Introduces methodological cautions (unmasking, etc.).

**Grieve, J. (2007), "Quantitative Authorship Attribution: An Evaluation of Techniques," *LLC* 22(3):251–270.** **[metadata-verified]** — the controlled head-to-head bake-off you wanted.
- Tested ~39 different feature sets on a controlled corpus (single genre, 40 authors, newspaper columns) to isolate feature power from topic.
- Reported finding (widely cited): **character-level features (character n-grams) and punctuation** were among the **most successful**; individual word/word-n-gram and especially very high-order features did less well or overfit. **Function words and character n-grams again top the list.** Punctuation frequency was a notably strong, simple, pure-Python feature — which supports the per-mark punctuation rates you already measure.

**Supporting / theoretical:**
- **Kestemont, M. (2014), "Function Words in Authorship Attribution: From Black Magic to Theory?", *Proc. 3rd Workshop on Computational Linguistics for Literature (CLfL), EACL*, ACL Anthology W14-0908.** Argues character n-grams work *because* they capture function words and bound morphemes — i.e., the two top feature families are mechanistically the same signal. **[metadata-verified]**
- **Juola, P. (2006), "Authorship Attribution," *Foundations and Trends in IR* 1(3):233–334.** Broad survey; same conclusion hierarchy.
- **Holmes, D. (1998), "The Evolution of Stylometry in Humanities Scholarship," *LLC* 13(3):111–117.** Historical review; covers word-length distributions (Mendenhall 1887 — the original "characteristic curves of composition," a word-length histogram) and vocabulary-richness measures.
- **Mendenhall, T.C. (1887), "The Characteristic Curves of Composition," *Science* 9(214S):237–246.** The original **word-length distribution** method — you already do mean word length and long-word rate, which is a compressed version of this. The literature suggests the *full distribution* (histogram of word lengths, or at least the SD/shape) carries more signal than the mean alone.

---

## 2. Idiolect and Forensic Linguistics

**Coulthard, M. (2004), "Author Identification, Idiolect, and Linguistic Uniqueness," *Applied Linguistics* 25(4):431–447.** **[metadata-verified]**
- The canonical statement of the **idiolect** hypothesis in forensic linguistics: every speaker has a distinctive, individual version of the language, observable statistically through preferences among available options. Introduces the "uniqueness of utterance" argument — that longer word **n-grams / strings** rapidly become unique to an individual (he used web-search counts of phrases). Directly motivates **word n-grams** as an idiolectal feature. Pure-Python computable.

**Johnson, A. & Wright, D. (2014), "Identifying idiolect in forensic authorship attribution: an n-gram textbite approach," *Language and Law / Linguagem e Direito* 1(1):37–69.** **[metadata-verified]** and
**Wright, D. (2017), "Using word n-grams to identify authors and idiolects: A corpus approach to a forensic linguistic problem," *International Journal of Corpus Linguistics* 22(2):212–241.** **[metadata-verified]**
- Wright analyzed the **Enron email corpus** (176 employees). Core method: **word n-grams** (1- to ~6-grams) as markers of idiolectal co-selection. Finding: individuals are characterized less by unique *single* words than by **recurrent multi-word sequences and collocational preferences** ("lexical bundles" / "textbites"). Supports adding word bigrams/trigrams to your tool. Pure-Python computable.
- Methodological point relevant to you: idiolect is best captured by **habitual preference among alternatives**, not by any single rare form.

**Nini, A. (2023), *A Theory of Linguistic Individuality: With Application to Forensic Authorship Analysis*, Cambridge University Press.** **[metadata-verified]** and related papers:
- **Nini, A. (2018), "An authorship analysis of the Jack the Ripper letters," *Digital Scholarship in the Humanities* 33(3):621–636.** **[metadata-verified]**
- **Nini, A., Halvani, O., Graner, L., et al. (2024/2025)** work on **idiolectal similarity** and the **Cognitively-inspired / n-gram-based** measures.
- Nini formalizes idiolect as a probabilistic grammar of individual choice and argues the observable trace is a distribution over **grammatical and lexical alternations** and **character/word n-grams**. He is careful about the theoretical status: a stable idiolect is a working hypothesis supported by attribution success, not a proven biometric.

**The "does a stable idiolect exist / how much data" debate — the sample-size question:**

**Eder, M. (2015), "Does size matter? Authorship attribution, small samples, big problem," *Digital Scholarship in the Humanities* 30(2):167–182.** **[verified: publication record + pre-print located; PDF binary could not be text-extracted]** — pre-print: `github.com/computationalstylistics/preprints/blob/master/Eder_Does_size_matter.pdf`.
- This is *the* paper for your 300-word question. Eder's well-established, widely-cited findings: authorship signal in **most-frequent-word** methods becomes **reliable only around ~5,000 words per sample** for English prose; performance degrades sharply below **~2,500–3,000 words**, and samples of only a **few hundred words are essentially unreliable / dominated by noise**. He recommends a **minimum of ~5,000 words** as a rule of thumb (with the caveat that the exact figure depends on language — inflected languages need more — and on the number of candidate authors).
- **Direct implication for your 300-word floor: the literature does not support 300 words as sufficient for a *stable* stylometric profile.** 300 words is roughly an order of magnitude below Eder's reliability threshold. Your floor will produce profiles dominated by sampling noise, especially for frequency-based features (MFW, TTR, punctuation rates all have high variance at n≈300). If 300 is a hard practical minimum, you should (a) treat sub-~2,000-word profiles as **low-confidence**, (b) prefer **length-robust estimators** (see §D), and (c) ideally target **≥5,000 words** for a "stable" profile.
- Related: **Eder & Rybicki (2013), "Do birds of a feather really flock together…," *LLC* 28(2):229–236** (sample selection); and **Eder (2016), "Rolling stylometry," *DSH* 31(3):457–469** (windowed measurement over a text, relevant if you want to profile with overlapping windows to estimate stability). **[metadata-verified]**

**Other sample-size anchors:**
- Burrows's Delta is generally considered to need **on the order of thousands of words** per sample to be stable; short-text attribution (tweets, SMS) is an active, harder subfield precisely because the frequency estimates are noisy.
- General statistical point (verifiable from first principles, not a citation): to estimate a function word occurring at ~1% with a relative standard error near ~25%, you need on the order of ~1,600 words; at 300 words you have ~3 expected occurrences and a relative SE near ~60%. This is why the floor matters.

---

## 3. Dialectometry and Sociolinguistic Variation (the group level)

These matter to you mainly as the **confound boundary**: they identify variables that reflect *community* origin, not the *individual*.

**Labov, W. (1966/2006), *The Social Stratification of English in New York City*; and Labov (1972), *Sociolinguistic Patterns*.** **[metadata-verified]**
- Variationist sociolinguistics: the classic **linguistic variables** are (ing) [walking~walkin'], (r) [rhoticity], (th)/(dh). These are **phonological** and mostly **not recoverable from prose orthography** — so they're largely irrelevant to a text tool *except* where they surface as spelling (e.g., *-in'* vs *-ing*, which you could count). The key conceptual import: a variable is a **choice among equivalent alternatives whose distribution correlates with a social group**. That's the definition of a confound you need to separate from individual style.

**Nerbonne, J. & Heeringa, W.; Wieling, M. & Nerbonne, J. (2010s), Levenshtein-based dialectometry.** e.g. **Wieling, Nerbonne & Baayen (2011), "Quantitative Social Dialectology," *PLoS ONE* 6(9):e23613**; **Nerbonne (2009), "Data-driven dialectology," *Language and Linguistics Compass*.** **[metadata-verified]**
- Method: **Levenshtein (edit) distance** between **phonetic transcriptions** of the same words across dialects, aggregated. **Not applicable to your raw-prose use case** (requires aligned transcriptions of the same items across speakers), but the edit-distance idea is pure-Python if you ever wanted string-similarity between authors on shared vocabulary. The main lesson: dialect signal lives in **systematic form variants of the same lexical items**, which is a group signal to be quarantined from the individual signal.

**Eisenstein, J., O'Connor, B., Smith, N.A., Xing, E. (2010), "A Latent Variable Model for Geographic Lexical Variation," *EMNLP 2010*, ACL Anthology D10-1124.** **[metadata-verified]**
- Latent-variable topic-style model over geotagged tweets; recovers regional lexical variants (e.g., regional slang). Group-level. Feature = **lexical frequency by region**. Shows that **content/lexical choice is heavily geographically conditioned** — i.e., "top content words" (which your tool measures) are **contaminated by community/region**, not pure individual signal.

**Bamman, D., Eisenstein, J., Schnoebelen, T. (2014), "Gender identity and lexical variation in social media," *Journal of Sociolinguistics* 18(2):135–160.** **[metadata-verified]**
- Lexical features (emoticons, spellings, topic words) predict gender **but** the mapping is probabilistic and identity-driven, not deterministic. Directly relevant caution: features you might read as "individual" (emoticons, expressive lengthening, specific content words) are substantially **group-identity markers**. Reinforces that **content words and expressive orthography carry group signal**; **function words / structural features are the more individual-specific layer.**

**Boundary summary for your tool:** *Individual-specific* signal concentrates in **function-word proportions, punctuation/structural habits, character n-grams, and syntactic-alternation preferences**. *Group-specific* (dialect/register/topic) signal concentrates in **content-word choice, spelling variants, and regional lexis**. Your current "top content words" feature is mostly a *group/topic* signal, not an *individual* one — useful but easily confounded.

---

## 4. Register and Genre Variation — Biber's Multidimensional Analysis

**Biber, D. (1988), *Variation across Speech and Writing*, Cambridge University Press.** **[metadata-verified]** — plus **Biber (1995), *Dimensions of Register Variation*** and **Conrad & Biber (2001)**.
- Method: count **~67 linguistic features** across a large corpus (LOB + London-Lund), then **factor analysis** on their co-occurrence patterns → a small number of interpretable **dimensions**.
- The dimensions (Biber 1988):
  1. **Involved vs. Informational Production**
  2. **Narrative vs. Non-Narrative Concerns**
  3. **Explicit/Elaborated vs. Situation-Dependent Reference**
  4. **Overt Expression of Persuasion / Argumentation**
  5. **Abstract vs. Non-Abstract (Impersonal) Information**
  6. **On-line Informational Elaboration**
- **The feature list (grouped as Biber grouped them), with your countability constraint marked:**
  - **Pure-Python countable (regex/lexicon):** first-person pronouns, second-person pronouns, third-person pronouns, it, demonstrative pronouns, contractions, *that*-deletion (approximable), analytic negation (*not*) vs synthetic (*n't*), discourse particles, coordinating conjunctions, causative/concessive/conditional **subordinators** (closed-list words: *because, if, unless, though, whereas…*), **prepositions**, WH-questions/words, amplifiers/downtoners/hedges (closed lists), **place & time adverbials** (closed lists), sentence length, **type-token ratio**, average word length, nominalizations via **-tion/-ment/-ness/-ity suffixes**.
  - **Needs a POS tagger (Biber used one):** present vs past tense, private/public/suasive **verbs by class**, perfect aspect, passives (agentless & by-passives), split infinitives, attributive vs predicative adjectives, pro-verb *do*, present participial clauses, pied-piping, gerunds — anything requiring word-class or clause-structure disambiguation.
- **Why this matters for your tool's organization:** Biber gives you a *principled, empirically-derived grouping* to replace ad hoc grouping. Notably, **many of your existing features load onto Dimension 1**: contractions, first/second-person pronouns, and short sentences are all **"Involved"** markers; nominalizations (-tion/-ment), long words, prepositions, and high TTR are **"Informational"** markers. So your "involved↔informational" axis already exists in your feature set implicitly — you could compute an explicit Dimension-1-like score from features you already have.
- **The genre/register confound (your explicit worry):** Biber's central empirical result is that **register accounts for a large share of linguistic variation — often more than individual authorship.** A person's email vs. their essays will differ on Biber's dimensions *more* than two different people writing in the *same* register. **This means your tool, if fed mixed-genre corpora, will measure genre, not the person.** Standard mitigation: **hold register constant** (profile per-genre), or at minimum **record the register** and treat cross-register comparison as low-confidence. This is the single biggest silent-failure mode in your design.

---

## 5. Stylistic Signatures of Machine-Generated Text (incl. the burstiness claim)

**Gehrmann, S., Strobelt, H., Rush, A. (2019), "GLTR: Statistical Detection and Visualization of Generated Text," *ACL 2019 (demo)*, `arXiv:1906.04043`.** ✅ **[directly verified — full text read]**
- Method (three tests): at each token position, use a language model to rank the actual token. Generated text over-uses **high-probability / top-ranked tokens**; human text has more **low-rank ("purple/red") tokens** and higher **entropy** in the predictive distribution. Their default buckets: **top-10 (green), top-100 (yellow), top-1,000 (red), else (purple)** — verified verbatim from the paper.
- Concrete qualitative finding (verified): in GPT-2-generated text, "**not a single token … is highlighted in purple and very few in red**," whereas human NYT/scientific text has "**significantly higher fraction of red and purple**" tokens and lower fraction of low-entropy contexts.
- **Constraint note: GLTR *requires* a language model** (BERT/GPT-2) to compute per-token rank/probability. **Not computable in pure Python over raw text.** This is the perplexity family — inaccessible under your constraint. Worth knowing so you don't try to reimplement it heuristically.

**Mitchell, E., Lee, A., Khazatsky, A., Manning, C., Finn, C. (2023), "DetectGPT: Zero-Shot Machine-Generated Text Detection using Probability Curvature," *ICML 2023*, `arXiv:2301.11305`.** ✅ **[directly verified — full text read]**
- Method: machine text sits at **local maxima of the model's log-probability**; perturbing it (T5 mask-filling, masking 2-word spans until 15% masked, 100 samples) **lowers log-prob more for machine text than human text** ("perturbation discrepancy"). Evaluated on **500 XSum news articles** vs. GPT-2/GPT-Neo/GPT-J/GPT-NeoX outputs (prompted with first 30 tokens). Normalizing by SD improved **AUROC by ~0.02** (verified).
- **Also requires a source LM** to score log-probabilities. **Not pure-Python.** Same exclusion as GLTR.

**Guo, B., et al. (2023), "How Close is ChatGPT to Human Experts? Comparison Corpus, Evaluation, and Detection," `arXiv:2301.07597` (HC3 corpus).** ✅ **[directly verified — read §3, human-eval methodology]**
- Builds the **HC3** human/ChatGPT parallel corpus and reports descriptive contrasts. Widely-cited **surface-level findings** from this paper (from its analysis section; I read the human-eval section directly and report the corpus's headline contrasts as commonly summarized — **treat the specific stats below as HC3-attributed but not line-verified by me**): ChatGPT text tends to be **longer, more organized, more neutral/formal**, uses **more conjunctions/discourse connectives**, **fewer** informal markers, and has **lower burstiness / more uniform structure** than human answers, which are **shorter, more subjective, and more variable**. HC3 is the standard source of concrete human-vs-ChatGPT descriptive statistics.

**Muñoz-Ortiz, A., Gómez-Rodríguez, C., Vilares, D. (2023/2024), "Contrasting Linguistic Patterns in Human and LLM-Generated News Text," `arXiv:2308.09067` (published in *Artificial Intelligence Review*).** **[metadata-verified; ar5iv HTML render failed, numbers not line-verified]**
- Reports concrete morphosyntactic/surface contrasts: LLM news text tends to have **more uniform sentence lengths**, **different dependency-length and constituent patterns**, **higher use of determiners/adpositions/nominal structures**, **fewer contractions and question marks**, and **less variance** in several distributional measures than human text. This is the best single source of **countable descriptive contrasts**, but I could not extract the exact tables — **flag as unverified numbers**.

**Ippolito, D., Duckworth, D., Callison-Burch, C., Eck, D. (2020), "Automatic Detection of Generated Text is Easiest when Humans are Fooled," *ACL 2020*, ACL Anthology 2020.acl-main.164.** **[metadata-verified]**
- Finding relevant to you: sampling strategy (top-k, nucleus/top-p) strongly shapes surface statistics; generated text's **statistical signature depends on decoding**, so any fixed threshold you set will be **decoding-dependent and non-stationary across models**.

### On "burstiness" specifically (your CV thresholds)

- **Origin of the term:** "burstiness" in text long predates LLMs — **Katz, S. (1996), "Distribution of content words and phrases in text and language modelling," *Natural Language Engineering* 2(1):15–59**, and **Church & Gale (1995)** on word "burstiness" (words cluster rather than distribute Poisson). In LLM-detection discourse, "perplexity + burstiness" was popularized by **GPTZero (Edward Tian, 2023)** — which is a **product/blog, not a peer-reviewed source**, and does **not** publish validated numeric thresholds.
- **What the literature supports:** the *directional* claim that **human text has higher variance in sentence length and in local perplexity than LLM text** is supported qualitatively (HC3; Muñoz-Ortiz et al.; the GLTR entropy result is the token-level analog). 
- **What I could NOT find:** any peer-reviewed paper reporting that **human sentence-length coefficient of variation ≈ 0.5–0.8 and generated ≈ 0.25**. **I searched and did not locate a citable published source for those specific CV thresholds.** My honest assessment: **the direction is literature-supported, but the specific numeric cutoffs appear to be your own calibration, not established values.** You should (a) not present them as literature-derived, and (b) validate them empirically on your own paired human/LLM corpus, because they will vary by **genre** (technical prose is naturally more uniform than fiction) and by **decoding temperature** (per Ippolito et al.). A single global CV threshold is fragile.

---

## Synthesis

### (a) Feature families ranked by evidence-backed discriminative power for individuating a person

| Rank | Feature family | Evidence | Pure-Python? |
|---|---|---|---|
| 1 | **Function-word / most-frequent-word (MFW) relative frequencies** (Burrows's Delta vector, ~100–500 words) | Mosteller & Wallace; Burrows 2002; Stamatatos 2009; Grieve 2007; Kestemont 2014 — strongest, most replicated | ✅ Yes |
| 2 | **Character n-grams (3–5)** | Stamatatos 2009; Grieve 2007; Kestemont 2014 — top-2 across benchmarks, robust to short/noisy text | ✅ Yes |
| 3 | **Punctuation frequency (per-mark)** | Grieve 2007 (among strongest simple features) | ✅ Yes — *you already have this* |
| 4 | **Word n-grams / recurrent multi-word sequences (bi/tri-grams, lexical bundles)** | Coulthard 2004; Johnson & Wright 2014; Wright 2017 (idiolect) | ✅ Yes |
| 5 | **Word-length distribution (full histogram/SD, not just mean)** | Mendenhall 1887; Holmes 1998 | ✅ Yes — *you have mean+long-word rate; add SD/shape* |
| 6 | **Vocabulary-richness measures (length-corrected)** | Tweedie & Baayen 1998; Stamatatos 2009 | ✅ Yes (with corrections — see §d) |
| 7 | **Syntactic alternation preferences / POS n-grams** | Biber 1988; Stamatatos 2009 | ❌ Needs tagger/parser |
| — | **Per-token perplexity / rank / entropy** (best LLM-vs-human signal) | GLTR; DetectGPT | ❌ Needs an LM |
| — | **Content-word / topic features** ("top content words") | Eisenstein 2010; Bamman et al. 2014 — high discriminative power but for **group/topic**, not individual; a confound | ✅ computable but ⚠️ measures the wrong thing |

**Headline:** the two highest-value additions that fit your constraint are **#1 function-word/MFW frequency vectors** and **#2 character n-grams**. Both are pure-Python. Your suspicion is confirmed.

### (b) Minimum viable sample size

- **Eder (2015)** is the primary source: **~5,000 words** for a *reliable* frequency-based authorial profile in English; **noticeable degradation below ~2,500–3,000 words**; **a few hundred words ≈ noise**.
- **Your 300-word floor is not supported by the literature** — it is ~10× below the reliability threshold and ~5× below the "starting to work" range. Recommendation: keep 300 only as a hard *floor for producing any output at all*, but (i) **label profiles under ~2,000 words as low-confidence**, (ii) target **≥5,000 words** for "stable," and (iii) use only **length-robust estimators** at small n (avoid raw TTR entirely — see below).

### (c) Well-established parameters your feature set is missing

Your current set (capitalisation, terminal punctuation, sentence length mean/SD/CV, verbless-fragment rate, stacked-fragment detector, pronoun person, contractions/100w, mean word length, long-word rate, nominalisation via suffixes, per-mark punctuation rates, numeral/percentage style, top content words, TTR) is a solid *structural/register* profile — it maps well onto **Biber's Dimension 1 (Involved↔Informational)**. But it is **missing the two highest-evidence individuating families**:

1. **Function-word / MFW frequency vector** *(rank #1)* — a normalized frequency table over the ~100–300 most frequent words (articles, prepositions, conjunctions, auxiliaries, pronouns, particles: *the, of, and, to, a, in, that, is, was, it, for, but, with, as, his, on…*). This is the backbone of Burrows's Delta and the single biggest omission. **Add this.**
2. **Character n-grams (3–5)** *(rank #2)* — top-*k* most frequent character trigrams/4-grams with relative frequencies. Captures morphology, spelling habits, and punctuation context that whole-word features miss. **Add this.**
3. **Word n-grams (bi/tri-grams)** *(rank #4)* — recurrent phrases / lexical bundles; the forensic idiolect signal (Wright 2017). **Add this.**
4. **Full word-length distribution** — you have mean and long-word rate; add the **SD / histogram shape** (Mendenhall).
5. **Function-word-based involved/informational and persuasion features from Biber** that are pure-Python and you're not counting: **preposition rate**, **subordinator/conjunction rates by class**, **amplifier/hedge/downtoner rates** (closed lists), **place/time adverbial rates**, **demonstrative pronoun rate**, **WH-word rate**, **analytic vs. synthetic negation** (*not* vs *n't*). These give you Biber Dimensions 3–4 signal cheaply.
6. **Length-corrected lexical richness** to replace raw TTR (see below).
7. **Spelling/orthographic variant counts** as a *group/register* control (e.g., *-ize/-ise*, *-in'/-ing*, British/American variants) — not to individuate, but to *detect and quarantine* dialect confound (Bamman et al.).

### (d) Confounds and failure modes (things that make a naïve implementation quietly wrong)

1. **Topic/content contamination of the author signal.** Content-word features ("top content words") track *subject matter*, not the person (Eisenstein 2010; Koppel et al. 2009). Two texts by one author on different topics can look less similar than two authors on the same topic. **Mitigation:** rely on **function words and character n-grams** for identity; treat content words as topic descriptors only. This is the most-cited stylometric pitfall.

2. **Genre/register dominates individual style (your biggest silent bug).** Biber (1988): register variation is often *larger* than inter-author variation. If your corpus mixes emails, essays, and chat, you measure genre. **Mitigation:** profile **per-register**, record the register, and refuse/flag cross-register comparisons.

3. **TTR is length-dependent and *must not* be compared across texts of different length.** TTR falls monotonically as N grows (more tokens → proportionally fewer new types). At your 300-word floor, TTR is both high-variance and non-comparable to a 5,000-word profile. **Standard corrections (Tweedie & Baayen 1998, "How variable may a constant be? Measures of lexical richness in perspective," *Computers and the Humanities* 32:323–352):**
   - **MATTR** — Moving-Average TTR over a fixed window (Covington & McFall 2010) — simplest robust fix, **pure-Python**.
   - **MTLD** — Measure of Textual Lexical Diversity (McCarthy & Jarvis 2010) — **pure-Python**, length-robust.
   - **vocd-D / HD-D** (McCarthy & Jarvis 2007, 2010) — hypergeometric; **pure-Python** (uses `math`/`statistics`, no libs).
   - **Yule's K** (Yule 1944) — length-robust by construction; **pure-Python**.
   - **Guiraud's R** = V/√N, **Herdan's C** = logV/logN — cheap partial corrections.
   - **Action:** replace raw TTR with **MATTR or MTLD**; keep raw TTR only if you fix the window length.

4. **Small-sample noise on all frequency features.** At n≈300, function-word rates, punctuation rates, and nominalisation rates all have large relative standard error (§2). Sentence-length **CV** in particular is unstable with few sentences. **Mitigation:** confidence-weight by token count; report CIs; don't threshold hard at small n.

5. **Sentence-length CV thresholds are non-stationary.** They depend on **genre** (technical prose is naturally more uniform) and, for the LLM-vs-human use, on **decoding temperature** (Ippolito et al. 2020). A fixed global CV cutoff (your 0.25/0.5–0.8) will misclassify uniform-but-human technical writing as machine, and high-temperature LLM output as human. **Mitigation:** calibrate per-genre; never present these numbers as literature-derived (they aren't — see §5).

6. **Perplexity/burstiness at the *token* level (the strongest machine-text signal) is off-limits under your constraint** — GLTR and DetectGPT both require an LM. Your sentence-length-CV heuristic is a weak surrogate for the real burstiness signal; treat it as suggestive, not diagnostic.

7. **Suffix-based nominalisation counting (-tion/-ment) has false positives** (*mention, cement, station, question* are not nominalisations of a verb). This is inherent to doing it without a tagger; acceptable, but know it introduces noise proportional to those words' frequency.

8. **Character n-grams partially re-encode topic**, so they're not perfectly topic-clean either (Koppel et al.). Function words remain the cleanest identity signal.

---

## Gaps / uncertainties (explicit)

- **Could not open full text** (403/JS/paywall) for: Burrows 2002, Stamatatos 2009, Grieve 2007, Biber 1988, Coulthard 2004, Wright 2017, Nerbonne/Wieling, Tweedie & Baayen. These are cited from metadata + established secondary knowledge; **specific numbers attributed to them (e.g., Delta's 40–150 MFW, Grieve's ~39 techniques, Biber's ~67 features/6 dimensions) are from well-established summaries, not line-verified from the PDFs today.**
- **Eder (2015) "Does size matter?"**: publication and pre-print confirmed, but the PDF was binary-encoded and I could not extract exact figures; the **~5,000-word** threshold I report is the paper's widely-cited headline conclusion, **not line-verified from the file today.** Recommend the main agent confirm the exact numeral against the pre-print if it will be quoted.
- **Muñoz-Ortiz et al. (2023) `2308.09067`**: ar5iv HTML render failed; its concrete tables are **not verified** — I report only the directional findings.
- **HC3 (`2301.07597`)**: I verified the corpus/method directly but the specific descriptive-statistic contrasts I list are the paper's commonly-cited summary, **not line-verified from its analysis tables.**
- **The specific CV thresholds (0.25 / 0.5–0.8): no citable published source found.** Treat as your own calibration. This is the clearest "cannot verify" in the request.
- Verified directly and quotable: **DetectGPT `2301.11305`** and **GLTR `1906.04043`** (methods, bucket thresholds, XSum 500 articles, AUROC +0.02, 15%-mask/100-samples).

**Suggested follow-ups for the main agent:** (1) pull the Eder 2015 pre-print through a PDF text extractor to lock the exact word-count numbers; (2) pull Muñoz-Ortiz Table data for real human-vs-LLM sentence-length/punctuation stats to replace the invented CV thresholds; (3) locate Grieve 2007's ranking table to cite exact feature-set accuracies.
