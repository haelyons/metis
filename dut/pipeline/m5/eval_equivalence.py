#!/usr/bin/env python3
"""Exact output alignment and sealed deterministic or paired-seed equivalence."""
import statistics
import sys
from eval_common import cli, median_interval, number


def compare(evaluation, baseline, method):
    left, aligned_left = evaluation.records(baseline)
    right, aligned_right = evaluation.records(method)
    if not aligned_left or not aligned_right:
        return False, [dict(passed=False, reason_code="counts_or_alignment")]
    metrics = evaluation.protocol["equivalence_metrics"]
    if not isinstance(metrics, list) or not metrics or len({m["name"] for m in metrics}) != len(metrics):
        raise ValueError("invalid metrics")
    stochastic = evaluation.protocol["paired_seed_tests"]["kind"] == "paired_median"
    results = []
    for metric in metrics:
        name = metric["name"]
        if not isinstance(name, str) or not name.strip() or not isinstance(metric.get("source"), str) or not metric["source"].strip():
            raise ValueError("invalid metric")
        tolerance = metric["tolerance"]
        if number(tolerance):
            tolerance = {"abs": tolerance}
        if not isinstance(tolerance, dict) or set(tolerance) not in ({"abs"}, {"rel"}):
            raise ValueError("invalid tolerance")
        amount = next(iter(tolerance.values()))
        if not number(amount) or amount < 0:
            raise ValueError("invalid tolerance")
        differences, normalized, by_seed = [], [], {}
        for a, b in zip(left, right):
            reference, actual = a["metrics"][name], b["metrics"][name]
            difference = actual - reference
            bound = amount * abs(reference) if "rel" in tolerance else amount
            if not number(difference) or not number(bound):
                raise ValueError("invalid difference")
            differences.append(difference)
            normalized.append(abs(difference) <= bound)
            by_seed.setdefault(a["seed"], []).append(difference)
        if stochastic:
            # A relative per-row margin is not a fixed margin for a median test.
            if "abs" not in tolerance:
                raise ValueError("paired test requires absolute margin")
            rule = evaluation.protocol["confidence_rule"]["equivalence"]
            confidence = rule["confidence"]
            if rule["kind"] != "paired_median" or not number(confidence) or not .5 <= confidence < 1:
                raise ValueError("unsupported confidence rule")
            adjusted = 1 - (1 - confidence) / len(metrics)
            interval = median_interval([statistics.mean(v) for v in by_seed.values()], adjusted)
            if interval is None:
                raise ValueError("insufficient paired seeds")
            passed = interval[0] >= -amount and interval[1] <= amount
            results.append(dict(metric=name, passed=passed, difference_interval=interval, confidence=adjusted))
        else:
            passed = all(normalized)
            results.append(dict(metric=name, passed=passed, max_abs_difference=max(map(abs, differences))))
    return all(row["passed"] for row in results), results


def evaluate(evaluation):
    evaluation.identities()
    baseline, _ = evaluation.run("baseline", "equivalence", 0)
    method, _ = evaluation.run("method", "equivalence", 0)
    passed, metrics = compare(evaluation, baseline, method)
    evaluation.result("equivalence", "PASS" if passed else "FAIL", equivalence_pass=passed, metrics=metrics)
    return 0 if passed else 5


if __name__ == "__main__":
    sys.exit(cli("equivalence", evaluate))
