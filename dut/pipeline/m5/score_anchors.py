#!/usr/bin/env python3
"""Score published anchors deterministically; exit 0/pass, 4/mismatch, 1/parse."""
import json
import math
import operator
import os
from pathlib import Path
import sys


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def score(anchors, measured):
    if not isinstance(anchors, list) or type(measured) is not dict:
        raise ValueError("invalid inputs")
    rows, ids = [], set()
    for anchor in anchors:
        if type(anchor) is not dict:
            raise ValueError("invalid anchor")
        ident = anchor.get("id")
        published = anchor.get("published_value")
        tolerance = anchor.get("tolerance")
        comparison = anchor.get("comparison", "==")
        reference = comparison == "==" and tolerance is None
        if not isinstance(ident, str) or not ident.strip() or ident in ids or not number(published):
            raise ValueError("invalid anchor")
        ids.add(ident)
        if "tolerance" not in anchor:
            raise ValueError("invalid tolerance")
        uncertainty = anchor.get("uncertainty")
        if uncertainty is not None and (type(uncertainty) is not dict
                or set(uncertainty) != {"kind", "value"}
                or uncertainty["kind"] not in ("standard_error", "standard_deviation", "interval_halfwidth")
                or not number(uncertainty["value"]) or uncertainty["value"] < 0):
            raise ValueError("invalid uncertainty")
        if tolerance is not None:
            if number(tolerance):
                absolute = tolerance
            elif type(tolerance) is dict and set(tolerance) in ({"abs"}, {"rel"}):
                amount = next(iter(tolerance.values()))
                if not number(amount) or amount < 0:
                    raise ValueError("invalid tolerance")
                absolute = amount * abs(published) if comparison == "==" and "rel" in tolerance else amount
            else:
                raise ValueError("invalid tolerance")
            if not number(absolute) or absolute < 0:
                raise ValueError("invalid tolerance")
        value = measured.get(ident)
        reason = None
        if comparison not in ("==", ">", ">=", "<", "<="):
            reason = "unknown_comparison"
        elif ident not in measured:
            reason = "missing"
        elif not number(value):
            reason = "non_numeric"
        elif comparison == "==":
            difference = value - published
            if not number(difference):
                raise ValueError("invalid difference")
            if not reference and abs(difference) > absolute:
                reason = "out_of_tolerance"
        else:
            compare = {">": operator.gt, ">=": operator.ge, "<": operator.lt, "<=": operator.le}
            if not compare[comparison](value, published):
                reason = "threshold_not_met"
        row = dict(id=ident, kind="reference" if reference else "anchor", published_value=published,
                   measured_value=value if number(value) else None,
                   tolerance=tolerance, passed=None if reference else reason is None)
        if "uncertainty" in anchor:
            row["uncertainty"] = uncertainty
        if reference:
            row["difference"] = difference if reason is None else None
        if reason is not None:
            row["reason"] = reason
        rows.append(row)
    passed = sum(row["passed"] is True for row in rows)
    total = sum(row["kind"] == "anchor" for row in rows)
    return dict(anchors=rows, anchors_passed=passed, anchors_total=total,
                all_passed=passed == total, references_total=len(rows) - total)


def main():
    if len(sys.argv) != 4:
        print("usage: score_anchors.py <anchors.json> <measured.json> <out.json>", file=sys.stderr)
        return 1
    try:
        result = score(json.loads(Path(sys.argv[1]).read_text()),
                       json.loads(Path(sys.argv[2]).read_text()))
        output = Path(sys.argv[3])
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_name(output.name + ".tmp")
        temporary.write_text(json.dumps(result, allow_nan=False, indent=2) + "\n")
        os.replace(temporary, output)
        return 0 if result["all_passed"] else 4
    except (OSError, ValueError, TypeError, OverflowError):
        print("invalid anchor input or output unavailable", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
