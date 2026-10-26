#!/usr/bin/env python3
"""Rerun the method anchor protocol and score every published anchor."""
import sys
from eval_common import cli
from score_anchors import score


def evaluate(evaluation):
    try:
        measured = evaluation.run("method", "anchors", 0)
    except RuntimeError:
        evaluation.result("validity", "FAIL", validity_pass=False, reason_code="anchor_execution")
        return 4
    result = score(evaluation.manifest["anchors"], measured)
    if any(row.get("reason") in ("missing", "non_numeric") for row in result["anchors"]):
        evaluation.result("validity", "VOID", validity_pass=None, reason_code="missing_or_invalid_measurements", **result)
        return 2
    passed = result["all_passed"]
    evaluation.result("validity", "PASS" if passed else "FAIL", validity_pass=passed, **result)
    return 0 if passed else 4


if __name__ == "__main__":
    sys.exit(cli("validity", evaluate))
