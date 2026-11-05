"""Self-check of the operator's sealed-number screen (rule quoted in s32 PROMPT.md).

Usage: python3 -I check_matches.py <design.json> <brief.md>
Prints every matching (token, sealed value) pair with where the token occurs, then the count.
Exact decimal arithmetic (Decimal) on both sides, so boundary cases resolve as written.
"""
import json
import re
import sys
from decimal import Decimal

TOKEN = re.compile(r"-?\d[\d,]*(?:\.\d+)?(?:[eE][-+]?\d+)?")
HEADING = "## Comparison request (science step"


def numbers(node, out):
    """Every JSON number at any depth (booleans excluded)."""
    if isinstance(node, bool):
        return
    if isinstance(node, (int, float)):
        out.append(node)
    elif isinstance(node, dict):
        for v in node.values():
            numbers(v, out)
    elif isinstance(node, list):
        for v in node:
            numbers(v, out)


def strings_and_numbers(node, where, out):
    """Every string or number at any depth, as text, with a location label."""
    if isinstance(node, bool):
        return
    if isinstance(node, str):
        out.append((where, node))
    elif isinstance(node, (int, float)):
        out.append((where, json.dumps(node)))
    elif isinstance(node, dict):
        for k, v in node.items():
            strings_and_numbers(v, f"{where}/{k}", out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            strings_and_numbers(v, f"{where}/{i}", out)


def main(design_path, brief_path):
    design = json.load(open(design_path, encoding="utf-8"), parse_float=Decimal)
    sealed = []
    for c in design["comparisons"]:
        for key in ("margin", "threshold", "confidence", "reference"):
            found = []
            numbers(c[key], found)
            sealed += [(c["id"], key, Decimal(str(v))) for v in found]

    visible = []
    brief = open(brief_path, encoding="utf-8").read()
    pos = brief.find(HEADING)
    if pos < 0:
        sys.exit("heading not found in brief")
    visible.append(("brief", brief[pos + len(HEADING):]))
    for group in ("arms", "inputs", "outputs", "metrics"):
        for i, item in enumerate(design[group]):
            for field in ("what", "spec", "select", "commands", "env"):
                if field in item:
                    strings_and_numbers(item[field], f"{group}/{i}/{field}", visible)
    for field in ("what", "spec"):
        strings_and_numbers(design["evaluator"][field], f"evaluator/{field}", visible)

    pairs = {}
    for where, text in visible:
        for m in TOKEN.finditer(text):
            raw = m.group(0).replace(",", "")
            mant = raw.split("e")[0].split("E")[0]
            d = len(mant.split(".")[1]) if "." in mant else 0
            tok = Decimal(raw)
            for cid, key, v in sealed:
                if abs(tok - v) <= Decimal("0.5") * Decimal(10) ** -d and (d > 0 or abs(tok) > 10):
                    pairs.setdefault((raw, str(v)), []).append((where, cid, key))
    for (raw, v), hits in sorted(pairs.items()):
        print(f"{raw} ~ {v}: {hits[0][1]}.{hits[0][2]} ; first seen in {hits[0][0]} ({len(hits)} hit(s))")
    print("sealed values:", len(sealed), "matches:", len(pairs))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
