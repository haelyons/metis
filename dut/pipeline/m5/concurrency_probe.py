#!/usr/bin/env python3
"""Calibrate throughput of the unchanged baseline command, using only stdlib."""
from contextlib import ExitStack
import json
import os
from pathlib import Path
import re
import shutil
import signal
import statistics
import subprocess
import sys
import tempfile
import time


def measurements(mps, mps_failed):
    return dict(mps=mps, mps_failed=mps_failed, single_wall_s=[None] * 3,
                batches=[dict(n=n, wall_s=None, all_ok=False, skipped=True, factor=None)
                         for n in (2, 4)], factor=None)


def probe(command, output, budget):
    root = Path.cwd()
    work = root / "concurrency-work"
    work.mkdir(exist_ok=True)
    logs = output / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    active = []
    mps_environment = None
    mps_client_count = 0
    mps_binary = shutil.which("nvidia-cuda-mps-control")
    result = measurements(False, False)

    def stop_children():
        for child in active:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        for child in active:
            child.wait()
        active.clear()

    def stop_mps():
        nonlocal mps_environment
        if mps_environment is not None:
            try:
                subprocess.run([mps_binary], input="quit\n", text=True,
                               env=mps_environment, timeout=5, check=False)
            except (OSError, subprocess.SubprocessError):
                pass
            mps_environment = None

    def terminate(signum, frame):
        raise InterruptedError("probe terminated")

    def run(labels, environment):
        nonlocal mps_client_count
        with ExitStack() as files:
            directories = []
            for label in labels:
                directory = work / label
                if directory.exists():
                    shutil.rmtree(directory)
                directory.mkdir()
                for entry in root.iterdir():
                    if entry.name not in ("out", "profiler", "concurrency-work", "evaluation-work"):
                        (directory / entry.name).symlink_to(entry)
                (directory / "out").mkdir()
                log = files.enter_context((logs / (label + ".log")).open("w"))
                directories.append((directory, log))
            start = time.monotonic()
            try:
                for directory, log in directories:
                    active.append(subprocess.Popen(["bash", command], cwd=directory,
                                                   env=environment, stdout=log,
                                                   stderr=subprocess.STDOUT, start_new_session=True))
                codes = [child.wait() for child in active]
                wall = time.monotonic() - start
                active.clear()
                ok = all(code == 0 for code in codes)
                if environment is not None:
                    with (Path(environment["CUDA_MPS_LOG_DIRECTORY"]) / "control.log").open("rb") as control_log:
                        count = sum(bool(re.search(rb"NEW CLIENT [0-9]+ from user ", line))
                                    for line in control_log)
                    ok = ok and count - mps_client_count >= len(labels)
                    mps_client_count = count
                return wall, ok
            except InterruptedError:
                raise
            except OSError:
                stop_children()
                return time.monotonic() - start, False

    previous = signal.signal(signal.SIGTERM, terminate)
    try:
        for use_mps in ([True, False] if mps_binary else [False]):
            result = measurements(use_mps, result["mps_failed"])
            environment = None
            failed = False
            if use_mps:
                environment = dict(os.environ,
                                   CUDA_MPS_PIPE_DIRECTORY=tempfile.mkdtemp(prefix="mps-pipe-", dir=work),
                                   CUDA_MPS_LOG_DIRECTORY=tempfile.mkdtemp(prefix="mps-log-", dir=work))
                mps_environment = environment
                try:
                    failed = subprocess.run([mps_binary, "-d"], env=environment,
                                            timeout=10, check=False).returncode != 0
                except InterruptedError:
                    raise
                except (OSError, subprocess.SubprocessError):
                    failed = True
            if not failed:
                for index in range(3):
                    wall, ok = run([f"single-{index + 1}"], environment)
                    if not ok:
                        failed = True
                        break
                    result["single_wall_s"][index] = wall
                if not failed:
                    t1 = statistics.median(result["single_wall_s"])
                    for batch in result["batches"]:
                        n = batch["n"]
                        if n * t1 > 0.9 * budget - (time.monotonic() - started):
                            continue
                        wall, ok = run([f"n{n}-{index + 1}" for index in range(n)], environment)
                        batch.update(wall_s=wall, all_ok=ok, skipped=False,
                                     factor=n * t1 / wall if ok else None)
                        if use_mps and not ok:
                            failed = True
                            break
                    factors = [batch["factor"] for batch in result["batches"] if batch["factor"] is not None]
                    result["factor"] = max(factors) if factors else None
            stop_mps()
            if use_mps and failed:
                result["mps_failed"] = True
                # Discard the MPS attempt; repeat every measurement in fresh directories.
                for directory in work.iterdir():
                    if directory.name.startswith(("single-", "n2-", "n4-")):
                        shutil.rmtree(directory)
                for log in logs.glob("*.log"):
                    log.unlink()
                continue
            break
    except (OSError, InterruptedError):
        factors = [batch["factor"] for batch in result["batches"] if batch["factor"] is not None]
        result["factor"] = max(factors) if factors else None
    finally:
        stop_children()
        stop_mps()
        signal.signal(signal.SIGTERM, previous)
    return result


def main():
    if len(sys.argv) != 4:
        print("usage: concurrency_probe.py <run_command_file> <out_dir> <budget_s>", file=sys.stderr)
        return 2
    try:
        command, directory, seconds = sys.argv[1:]
        budget = int(seconds)
        if budget <= 0:
            raise ValueError("invalid budget")
        output = Path(directory).resolve()
        output.mkdir(parents=True, exist_ok=True)
        result = probe(command, output, budget)
        temporary = output / "concurrency.json.tmp"
        temporary.write_text(json.dumps(result, allow_nan=False, indent=2) + "\n")
        os.replace(temporary, output / "concurrency.json")
        return 0
    except (OSError, ValueError, TypeError, OverflowError):
        print("concurrency output unavailable", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
