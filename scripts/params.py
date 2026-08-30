from voiceprint.features import registry
from voiceprint.lexicons import FUNCTION_WORDS

r = registry()
fams = {}
for f in r.values():
    fams.setdefault(f.family, []).append(f)

ELAST = {0.0: "rigid", 0.25: "firm", 0.6: "supple", 1.0: "convention"}

print(f"{'family':13s} {'n':>3s}  {'scalar':>6s} {'categ':>5s}   elasticity")
print("-" * 62)
for fam in sorted(fams):
    fs = fams[fam]
    sc = sum(1 for f in fs if f.kind == "scalar")
    el = sorted({f.elasticity for f in fs})
    names = "/".join(ELAST.get(e, str(e)) for e in el)
    print(f"{fam:13s} {len(fs):3d}  {sc:6d} {len(fs)-sc:5d}   {names}")

print("-" * 62)
print(f"{'TOTAL':13s} {len(r):3d}  "
      f"{sum(1 for f in r.values() if f.kind=='scalar'):6d} "
      f"{sum(1 for f in r.values() if f.kind=='categorical'):5d}")
print()
print("Vector features stored per profile (not in the registry):")
print(f"  function words       {len(FUNCTION_WORDS)} dimensions")
print(f"  character 4-grams    300 most frequent")
print(f"  punctuation shapes    80 most frequent")
print(f"  word n-grams 2-5     40 bundles + 20 openers + 20 closers + 20 fillers")
print(f"  topic words           30 (descriptor only, not identity)")
print(f"  exemplars              8 verbatim sentences")
print()
tot = len(r) + len(FUNCTION_WORDS) + 300 + 80
print(f"Total numeric dimensions per profile: ~{tot}")
print()
print("Every scalar is stored as mean + sd + n over windows, so the")
print(f"registry alone yields {sum(1 for f in r.values() if f.kind=='scalar')*3} stored numbers.")
