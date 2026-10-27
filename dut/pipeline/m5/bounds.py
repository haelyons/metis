#!/usr/bin/env python3
"""Compute deterministic profile-based bounds for the m5 method menu."""
import json
import math
import os
from pathlib import Path
import re
import sys


METHODS = {
    "data-parallel over inputs": ("whole", 8),
    "batching": ("whole", 4),
    "multi-GPU": ("compute", None),
    "ensembles": ("whole", 8),
    "pipelining": ("transfer", 2),
}


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def stage_kind(stage):
    """Explicit kinds win; legacy names use fixed tokens, transfer before compute."""
    if "kind" in stage:
        if stage["kind"] not in ("compute", "transfer", "other"):
            raise ValueError("invalid stage kind")
        return stage["kind"]
    tokens = set(re.findall(r"[a-z0-9]+", stage["stage"].lower()))
    if tokens & {"transfer", "transfers", "h2d", "d2h", "htod", "dtoh", "copy", "memcpy", "upload", "download"}:
        return "transfer"
    if tokens & {"compute", "kernel", "kernels", "inference", "training", "forward", "backward"}:
        return "compute"
    return "other"


def bounds(packet):
    total = packet["total_wall_s"]
    stages = packet["stages"]
    gpus = packet.get("gpu_count", 1)
    if (not number(total) or total <= 0 or not isinstance(stages, list) or not stages
            or type(gpus) is not int or gpus < 0):
        raise ValueError("invalid profile")
    concurrency = packet.get("concurrency")
    if concurrency is not None and not isinstance(concurrency, dict):
        raise ValueError("invalid concurrency")
    factor = concurrency.get("factor") if concurrency is not None else None
    if factor is not None and not number(factor):
        raise ValueError("invalid concurrency factor")
    mps = concurrency.get("mps") if factor is not None else None
    times = dict(compute=0.0, transfer=0.0, other=0.0)
    mapping = []
    for stage in stages:
        if (not isinstance(stage, dict) or not isinstance(stage.get("stage"), str)
                or not stage["stage"].strip() or not number(stage.get("wall_s")) or stage["wall_s"] < 0):
            raise ValueError("invalid stage")
        kind = stage_kind(stage)
        util = stage.get("mean_gpu_util")
        if util is not None and (not number(util) or not 0 <= util <= 1):
            raise ValueError("invalid stage utilization")
        times[kind] += stage["wall_s"]
        mapping.append(dict(stage=stage["stage"], kind=kind,
                            wall_fraction=min(1.0, stage["wall_s"] / total),
                            mean_gpu_util=util,
                            methods=[m for m, (k, _) in METHODS.items() if k in ("whole", kind)]))
    if not all(math.isfinite(value) for value in times.values()):
        raise ValueError("invalid stage times")
    result = {}
    for method, (kind, cap) in METHODS.items():
        p = 1 if kind == "whole" else min(1.0, times[kind] / total)
        if kind == "whole":
            k = min(cap, factor) if factor is not None and factor >= 1 else 1
            bound = k
            derivation = dict(rule="min(fixed_cap, concurrency factor)", fixed_cap=cap,
                              factor=factor, mps=mps)
        else:
            k = max(1, gpus) if cap is None else cap
            amdahl = 1.0 / ((1.0 - p) + p / k)
            bound = amdahl / k if cap is None else amdahl
            derivation = (dict(rule="max(1, gpu_count)", gpu_count=gpus, amdahl=amdahl,
                               cost_basis="equal_gpu_seconds") if cap is None else
                          dict(rule="fixed_cap", fixed_cap=cap))
        result[method] = dict(p=p, k=k, bound=bound, feasible=bound >= 1.05,
                              k_derivation=derivation, stages=[s for s in mapping if method in s["methods"]])
    return result


def main():
    if len(sys.argv) != 3:
        print("usage: bounds.py <profile-packet.json> <out.json>", file=sys.stderr)
        return 1
    try:
        result = bounds(json.loads(Path(sys.argv[1]).read_text()))
        output = Path(sys.argv[2])
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_name(output.name + ".tmp")
        temporary.write_text(json.dumps(result, allow_nan=False, indent=2) + "\n")
        os.replace(temporary, output)
        return 0
    except (OSError, ValueError, TypeError, KeyError, OverflowError):
        print("invalid profile input or output unavailable", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
