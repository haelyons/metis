#!/usr/bin/env python3
"""Compute deterministic profile-based Amdahl bounds for the m5 method menu."""
import json
import math
import os
from pathlib import Path
import re
import sys


METHODS = {
    "data-parallel over inputs": ("compute", 8),
    "batching": ("transfer", 4),
    "multi-GPU": ("compute", None),
    "ensembles": ("compute", 8),
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
    times = dict(compute=0.0, transfer=0.0, other=0.0)
    for stage in stages:
        if (not isinstance(stage, dict) or not isinstance(stage.get("stage"), str)
                or not stage["stage"].strip() or not number(stage.get("wall_s")) or stage["wall_s"] < 0):
            raise ValueError("invalid stage")
        times[stage_kind(stage)] += stage["wall_s"]
    if not all(math.isfinite(value) for value in times.values()):
        raise ValueError("invalid stage times")
    result = {}
    for method, (kind, cap) in METHODS.items():
        p = min(1.0, times[kind] / total)
        k = max(1, gpus) if cap is None else cap
        bound = 1.0 / ((1.0 - p) + p / k)
        result[method] = dict(p=p, k=k, bound=bound, feasible=bound >= 1.05)
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
