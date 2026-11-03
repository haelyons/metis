#!/usr/bin/env python3
"""Convert fixed Nsight Systems CSV reports and telemetry to m5 profile files."""
import csv
import io
import json
import math
from pathlib import Path
import re
import sys


def seconds(value, unit):
    scale = {"ns": 1e-9, "us": 1e-6, "µs": 1e-6, "ms": 1e-3, "s": 1}
    result = float(value.replace(",", "")) * scale[unit]
    if not math.isfinite(result) or result < 0:
        raise ValueError("invalid duration")
    return result


def report_rows(file):
    """Ignore nsys status lines; require a recognizable duration header."""
    content = file.read_text(encoding="utf-8-sig") if file.exists() else ""
    if not content.strip():
        activity = {"stats_cuda_gpu_kern_sum.csv": "CUDA kernel data",
                    "stats_cuda_gpu_mem_time_sum.csv": "GPU memory data",
                    "stats_cuda_api_sum.csv": "CUDA trace data"}[file.name]
        if "does not contain " + activity in (file.parent / "stats.log").read_text():
            return
    lines = content.splitlines()
    for index, line in enumerate(lines):
        header = next(csv.reader([line]))
        columns = [(i, re.fullmatch(r"Total (?:Time|Duration) \((ns|us|µs|ms|s)\)", name.strip()))
                   for i, name in enumerate(header)]
        duration = next(((i, match[1]) for i, match in columns if match), None)
        if duration is None:
            continue
        name_column = next(i for i, name in enumerate(header) if name.strip() in ("Name", "Operation"))
        for row in csv.reader(io.StringIO("\n".join(lines[index + 1:]))):
            if not row:
                continue
            if len(row) != len(header):
                raise ValueError("invalid CSV row")
            yield row[name_column], seconds(row[duration[0]], duration[1])
        return
    # nsys skips a report when no matching activity was collected.
    if "SKIPPED" not in "\n".join(lines):
        raise ValueError("missing CSV header")


def summarise(directory):
    timing = json.loads((directory / "raw_wall_s.json").read_text())
    wall = timing["total_wall_s"]
    origin = timing["start_monotonic_s"]
    if type(origin) not in (float, int) or not math.isfinite(origin) or origin < 0:
        raise ValueError("invalid clock origin")
    if type(wall) not in (float, int) or not math.isfinite(wall) or wall <= 0:
        raise ValueError("invalid wall time")
    kernels = sum(value for _, value in report_rows(directory / "stats_cuda_gpu_kern_sum.csv"))
    h2d = d2h = 0.0
    for name, value in report_rows(directory / "stats_cuda_gpu_mem_time_sum.csv"):
        token = re.sub(r"[^a-z]", "", name.lower())
        if "htod" in token or "hosttodevice" in token or "h2d" in name.lower():
            h2d += value
        elif "dtoh" in token or "devicetohost" in token or "d2h" in name.lower():
            d2h += value
    api = sum(value for _, value in report_rows(directory / "stats_cuda_api_sum.csv"))
    durations = [kernels, h2d, d2h, api]
    measured = sum(durations)
    if not math.isfinite(measured):
        raise ValueError("invalid report totals")
    # Aggregate reports can overlap across streams, devices and blocking APIs.
    # Bound their wall allocation proportionally, preserving raw GPU seconds.
    factor = min(1.0, wall / measured) if measured else 1.0
    allocated = [value * factor for value in durations]
    stages = [dict(stage=name, kind=kind, wall_s=value, gpu_s=gpu)
              for name, kind, value, gpu in zip(
                  ("kernels", "memcpy H2D", "memcpy D2H", "CUDA API host time"),
                  ("compute", "transfer", "transfer", "other"), allocated,
                  (kernels, h2d, d2h, None))]
    stages.append(dict(stage="other host time", kind="other",
                       wall_s=max(0.0, wall - sum(allocated)), gpu_s=None))
    samples = []
    for line in (directory / "gpu_util_raw.jsonl").read_text().splitlines():
        sample = json.loads(line)
        t, util = sample["t"], sample["util"]
        if (type(t) not in (int, float) or not math.isfinite(t) or t < 0
                or type(util) not in (int, float) or not math.isfinite(util) or not 0 <= util <= 100):
            raise ValueError("invalid telemetry")
        if origin <= t <= origin + wall:
            samples.append(dict(t=t - origin, util=util))
    for name, value in (("stages.json", stages), ("total_wall_s.json", dict(total_wall_s=wall)),
                        ("gpu_util.json", samples)):
        output = directory / name
        temporary = output.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(value, allow_nan=False, indent=2) + "\n")
        temporary.replace(output)


def main():
    if len(sys.argv) != 2:
        print("usage: profile_summarise.py <out_dir>", file=sys.stderr)
        return 1
    try:
        summarise(Path(sys.argv[1]))
        return 0
    except (OSError, ValueError, TypeError, KeyError, StopIteration, OverflowError):
        print("invalid profiler output", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
