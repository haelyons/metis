#!/usr/bin/env python3
"""Randomised paired timing, measured cost, and outcome versus compute."""
import random
import operator
import statistics
import sys
from eval_common import cli, median_interval, number
from eval_equivalence import compare


def curve(evaluation, rng, price):
    target = evaluation.protocol["equal_outcome_target"]
    if target.get("not_applicable") is True:
        if not isinstance(target.get("reason"), str) or not target["reason"].strip():
            raise ValueError("missing not-applicable reason")
        evaluation.result("curve", "PASS", not_applicable=True, reason=target["reason"], curve_points=0, points=[])
        return
    metric = target["metric"]
    threshold = target["target"]
    comparisons = {">=": operator.ge, ">": operator.gt, "<=": operator.le, "<": operator.lt, "==": operator.eq}
    comparison = comparisons[target["comparison"]]
    if not number(threshold):
        raise ValueError("invalid outcome target")
    budgets = evaluation.protocol["compute_budgets"]
    if not isinstance(budgets, list) or len(budgets) < 3 or not all(number(b) and b > 0 for b in budgets) or len(set(budgets)) != len(budgets):
        raise ValueError("invalid budgets")
    basis = evaluation.protocol["hardware_cost_basis"]
    if basis["budget_unit"] != "gpu_s":
        raise ValueError("unsupported budget unit")
    points = []
    # Persist completed budgets even when a later workload fails.
    evaluation.result("curve", "VOID", not_applicable=False, curve_points=None, points=points)
    for index, budget in enumerate(budgets):
        arms = ["baseline", "method"]
        rng.shuffle(arms)
        point = dict(compute_budget=budget)
        for arm in arms:
            try:
                report, elapsed = evaluation.run(arm, "curve", index, budget)
                rows, aligned = evaluation.records(report)
                seconds, gpus = evaluation.timing(report, elapsed, arm)
                if not aligned or not number(report.get("compute_budget")) or report["compute_budget"] != budget or elapsed * gpus > budget:
                    raise ValueError("invalid budget measurement")
                outcomes = [row["metrics"][metric] for row in rows]
                point[arm] = dict(status="PASS", outcome=statistics.mean(outcomes),
                                  target_achieved=comparison(statistics.mean(outcomes), threshold),
                                  uncertainty=dict(min=min(outcomes), max=max(outcomes)),
                                  allocated_gpu_hours=elapsed * gpus / 3600,
                                  usd=elapsed * gpus / evaluation.manifest["gpu_count"] * price / 3600)
            except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError, RuntimeError):
                point[arm] = dict(status="VOID", outcome=None, reason_code="missing_or_invalid_measurements")
        points.append(point)
        complete = all(p[a]["status"] == "PASS" for p in points for a in ("baseline", "method"))
        evaluation.result("curve", "PASS" if complete and len(points) == len(budgets) else "VOID",
                          not_applicable=False, curve_points=sum(all(p[a]["status"] == "PASS" for a in ("baseline", "method")) for p in points) or None, points=points)


def evaluate(evaluation):
    protocol = evaluation.protocol
    evaluation.identities()
    repetitions, warmup = protocol["repetitions"], protocol["warmup"]
    scheduling = protocol["scheduling_order"]
    rule = protocol["confidence_rule"]["performance"]
    if type(repetitions) is not int or repetitions < 5 or type(warmup) is not int or warmup < 0:
        raise ValueError("invalid repetitions or warmup")
    if scheduling["kind"] != "randomized_pairs" or type(scheduling["seed"]) is not int:
        raise ValueError("unsupported scheduling")
    if rule["kind"] != "paired_median" or not number(rule["confidence"]) or not .5 <= rule["confidence"] < 1:
        raise ValueError("unsupported confidence rule")
    price = evaluation.manifest["box"]["price_usd_h"]
    if not number(price) or price <= 0:
        raise ValueError("unavailable tariff")
    minimum = protocol["minimum_worthwhile_gain"]
    interval = evaluation.manifest["prediction"]["expected_speedup_interval"]
    low, high = interval["low"], interval["high"]
    if not number(minimum) or minimum <= 1 or not number(low) or not number(high) or not 0 < low <= high:
        raise ValueError("invalid sealed gain")
    rng, pairs = random.Random(scheduling["seed"]), []
    matched = True
    for phase, count in (("warmup", warmup), ("performance", repetitions)):
        for index in range(count):
            order = ["baseline", "method"]
            rng.shuffle(order)
            reports, times, counts = {}, {}, {}
            for arm in order:
                report, elapsed = evaluation.run(arm, phase, index)
                reports[arm] = report
                times[arm], counts[arm] = evaluation.timing(report, elapsed, arm)
            equivalent, _ = compare(evaluation, reports["baseline"], reports["method"])
            matched = matched and equivalent
            if phase == "performance":
                ratio = times["baseline"] / times["method"]
                cost = times["method"] * counts["method"] / (times["baseline"] * counts["baseline"])
                if not number(ratio) or not number(cost) or ratio <= 0 or cost <= 0:
                    raise ValueError("invalid ratios")
                pairs.append(dict(index=index, order=order, baseline_s=times["baseline"], method_s=times["method"],
                                  baseline_gpus=counts["baseline"], method_gpus=counts["method"], speedup=ratio, cost_ratio=cost,
                                  baseline_usd=times["baseline"] * counts["baseline"] / evaluation.manifest["gpu_count"] * price / 3600,
                                  method_usd=times["method"] * counts["method"] / evaluation.manifest["gpu_count"] * price / 3600))
    speedup = statistics.median(p["speedup"] for p in pairs)
    cost = statistics.median(p["cost_ratio"] for p in pairs)
    confidence = median_interval([p["speedup"] for p in pairs], rule["confidence"], two_sided=False)
    if confidence is None:
        raise ValueError("insufficient timing pairs")
    equal_cost = cost <= 1
    passed = matched and confidence[0] >= minimum and equal_cost
    evaluation.result("performance", "PASS" if passed else "FAIL", performance_pass=passed,
                      equal_cost=equal_cost, speedup_published=speedup, speedup_tuned=None,
                      cost_ratio=cost, prediction_ratio=speedup / (low / 2 + high / 2),
                      confidence=rule["confidence"], speedup_interval=confidence, matched_outcome=matched, pairs=pairs)
    try:
        curve(evaluation, rng, price)
    except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError, OverflowError, RuntimeError):
        evaluation.result("curve", "VOID", not_applicable=False, curve_points=None, points=[], reason_code="invalid_curve_protocol")
        return 2 if passed else 5
    from eval_common import read
    if read(evaluation.output / "curve.json")["status"] != "PASS":
        return 2 if passed else 5
    return 0 if passed else 5


if __name__ == "__main__":
    sys.exit(cli("performance", evaluate))
