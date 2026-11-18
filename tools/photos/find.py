import sys
from pathlib import Path
R = Path("E:/Spring Lakes Photos/01 By Event")
idx = {}
for f in R.rglob("*.jpg"):
    if "Sneak Peak" in str(f) and f.stem in idx: continue
    idx.setdefault(f.stem, f)
out = []
for s in open(sys.argv[1]).read().split():
    k = s if s in idx else next((k for k in idx if k.endswith(s)), None)
    if k: out.append(str(idx[k]).replace("\\", "/"))
    else: print("MISSING", s)
open(sys.argv[2], "w", encoding="utf-8").write("\n".join(out)); print(len(out))
