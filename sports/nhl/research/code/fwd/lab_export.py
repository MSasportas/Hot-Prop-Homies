"""lab_export.py: research/fwd/lab.json for the page's Lab tab (Matt 2026-11-12: everything being tested shows in the Lab).
Reads the forward scorers' own files (ll.json, mm.json, nn.json) and writes one totals block per variant. Research only.
Run from sports/nhl (run_all.sh does, last): python3 research/code/fwd/lab_export.py
"""
import datetime
import json
import os

SRC = ("ll", "mm", "nn")


def main():
    base = os.path.join("research", "fwd")
    doc = {"version": 1, "active": True, "note": "Research only: forward tests, never picks. Updated by the daily Researcher run."}
    for s in SRC:
        try:
            d = json.load(open(os.path.join(base, s + ".json"), encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for name, v in d.items():
            if not isinstance(v, dict):
                continue
            g, w = int(v.get("graded") or 0), int(v.get("w") or 0)
            doc[name] = {"w": w, "l": g - w, "push": 0, "void": 0, "units": round(float(v.get("units") or 0), 2),
                         "pending": max(0, int(v.get("bets") or 0) - g), "clv": v.get("mean_clv")}
    path = os.path.join(base, "lab.json")
    try:
        old = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        old = None
    if old is None or {k: v for k, v in old.items() if k != "updated_at"} != doc:
        doc["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
        with open(path, "w", encoding="utf-8", newline=chr(10)) as fh:
            json.dump(doc, fh, indent=1, sort_keys=True)
            fh.write(chr(10))


if __name__ == "__main__":
    main()
