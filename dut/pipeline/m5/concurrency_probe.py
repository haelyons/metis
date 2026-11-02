#!/usr/bin/env python3
"""Calibrate throughput of the unchanged baseline command, using only stdlib."""
from contextlib import ExitStack
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import stat
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


def unit_manifest(path):
    manifest = json.loads(Path(path).read_text())
    if not isinstance(manifest, dict) or set(manifest) != {"units"}:
        raise ValueError("invalid units")
    units = manifest["units"]
    if not isinstance(units, list) or len(units) < 4:
        raise ValueError("invalid units")
    identifiers = set()
    for unit in units:
        if not isinstance(unit, dict) or set(unit) != {"id", "outputs", "cost_s"}:
            raise ValueError("invalid unit")
        identifier, outputs, cost = unit["id"], unit["outputs"], unit["cost_s"]
        if (not isinstance(identifier, str)
                or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:+=-]{0,127}", identifier)
                or identifier in identifiers):
            raise ValueError("invalid unit id")
        identifiers.add(identifier)
        if (not isinstance(cost, (int, float)) or isinstance(cost, bool)
                or not math.isfinite(cost) or cost <= 0):
            raise ValueError("invalid unit cost")
        if not isinstance(outputs, list) or not outputs:
            raise ValueError("invalid unit outputs")
        paths = set()
        for path in outputs:
            if (not isinstance(path, str)
                    or not re.fullmatch(r"[A-Za-z0-9._+=-]+(?:/[A-Za-z0-9._+=-]+)*", path)
                    or any(part in (".", "..") for part in path.split("/"))
                    or path in paths):
                raise ValueError("invalid unit output")
            paths.add(path)
    return units


def memory_info():
    try:
        return {line.split()[0][:-1]: int(line.split()[1])
                for line in Path("/proc/meminfo").read_text().splitlines()}
    except (OSError, ValueError, IndexError):
        return {}


def cpu_times():
    try:
        values = [int(value) for value in Path("/proc/stat").read_text().splitlines()[0].split()[1:9]]
        return sum(values), values[3] + values[4]
    except (OSError, ValueError, IndexError):
        return None


def group_threads(groups):
    threads = 0
    for process in Path("/proc").iterdir():
        if not process.name.isdigit():
            continue
        try:
            fields = (process / "stat").read_text().rsplit(")", 1)[1].split()
            if int(fields[2]) in groups:
                for line in (process / "status").read_text().splitlines():
                    if line.startswith("Threads:"):
                        threads += int(line.split()[1])
                        break
        except (OSError, ValueError, IndexError):
            pass
    return threads


def shared_snapshot(root):
    snapshot = {}

    def visit(directory):
        with os.scandir(directory) as entries:
            for entry in entries:
                path = Path(entry.path).relative_to(root)
                if path.parts[0] in ("out", "concurrency-work", "profiler"):
                    continue
                try:
                    info = entry.stat(follow_symlinks=False)
                    if stat.S_ISDIR(info.st_mode):
                        visit(entry.path)
                    else:
                        snapshot[str(path)] = (info.st_size, info.st_mtime_ns)
                except OSError:
                    pass

    visit(root)
    return snapshot


def output_digest(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def same_output(first, second):
    with first.open("rb") as left, second.open("rb") as right:
        while True:
            block = left.read(1024 * 1024)
            if block != right.read(1024 * 1024):
                return False
            if not block:
                return True


def unit_probe(command, manifest, output, budget, reference):
    started = time.monotonic()
    root = Path.cwd()
    labels = ("a-1", "b-1", "c2-1", "c4-1", "c4-2", "c2-2", "b-2", "a-2")
    arms = [dict(label=label, wall_s=None, all_ok=False, skipped=True,
                 cpu_s=None, effective_cores=None, busy_fraction=None,
                 mem_available_min_kb=None, threads_max=None, shared_changes=None,
                 invocations=[]) for label in labels]
    result = dict(mode="units", mps=False, mps_failed=False, outcome="invalid_units",
                  units_total=None, sample=[], baseline_match=None, outputs_match=None,
                  serial_wall_s=None, separate_wall_s=None,
                  batches=[dict(n=n, wall_s=None, all_ok=False, skipped=True, factor=None)
                           for n in (2, 4)], arms=arms, nproc=os.cpu_count(),
                  mem_total_kb=memory_info().get("MemTotal"), factor=None)
    try:
        units = unit_manifest(manifest)
    except (OSError, ValueError, TypeError, OverflowError):
        return result
    indexes = sorted(range(len(units)), key=lambda index: units[index]["cost_s"])
    offset = (len(units) - 4) // 2
    indexes = indexes[offset:offset + 4]
    sample = [units[index] for index in indexes]
    result.update(units_total=len(units),
                  sample=[dict(index=index, cost_s=units[index]["cost_s"]) for index in indexes])
    expected = {path for unit in sample for path in unit["outputs"]}
    digests = None
    try:
        data = json.loads(Path(reference).read_text())
        if (isinstance(data, dict) and set(data) == {"sha256"}
                and isinstance(data["sha256"], dict) and set(data["sha256"]) == expected
                and all(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value)
                        for value in data["sha256"].values())):
            digests = data["sha256"]
    except (OSError, ValueError, TypeError):
        pass
    work = root / "concurrency-work"
    work.mkdir(exist_ok=True)
    logs = output / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    active = []
    failed = False

    def terminate(signum, frame):
        raise InterruptedError("probe terminated")

    def stop_children():
        for child, row, start in active:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        for child, row, start in active:
            try:
                pid, status, usage = os.wait4(child.pid, 0)
                child.returncode = os.waitstatus_to_exitcode(status)
            except ChildProcessError:
                pass
        active.clear()

    def check_outputs(directory, positions, baseline):
        try:
            if baseline:
                return digests is not None and all(
                    output_digest(directory / "out" / path) == digests[path]
                    for path in expected)
            return all(same_output(directory / "out" / path, work / "a-1" / "out" / path)
                       for position in positions for path in sample[position]["outputs"])
        except OSError:
            return False

    def run_arm(arm):
        label = arm["label"]
        baseline = label == "a-1"
        groups = ([[0, 1, 2, 3]] if label.startswith("a") else [[i] for i in range(4)])
        width = 2 if label.startswith("c2") else 4 if label.startswith("c4") else 1
        with ExitStack() as files:
            prepared = []
            for index, positions in enumerate(groups):
                name = label if len(groups) == 1 else f"{label}-{index + 1}"
                directory = work / name
                if directory.exists():
                    shutil.rmtree(directory)
                directory.mkdir()
                for entry in root.iterdir():
                    if entry.name not in ("out", "profiler", "concurrency-work", "evaluation-work"):
                        (directory / entry.name).symlink_to(entry)
                (directory / "out").mkdir()
                log = files.enter_context((logs / (name + ".log")).open("w"))
                prepared.append((directory, positions, log))
            before = shared_snapshot(root)
            previous_cpu = cpu_times()
            busy = []
            available = []
            threads = 0
            process_groups = set()

            def sample_resources():
                nonlocal previous_cpu, threads
                current = cpu_times()
                if current is not None and previous_cpu is not None:
                    total = current[0] - previous_cpu[0]
                    idle = current[1] - previous_cpu[1]
                    if total > 0:
                        busy.append(max(0.0, min(1.0, 1 - idle / total)))
                previous_cpu = current
                memory = memory_info().get("MemAvailable")
                if memory is not None:
                    available.append(memory)
                threads = max(threads, group_threads(process_groups))

            arm.update(skipped=False, all_ok=True)
            start = time.monotonic()
            next_sample = start
            for offset in range(0, len(prepared), width):
                for directory, positions, log in prepared[offset:offset + width]:
                    row = dict(units=positions, rc=None, wall_s=None, cpu_s=None,
                               max_rss_kb=None, nivcsw=None, inblock=None, oublock=None)
                    launch = time.monotonic()
                    child = subprocess.Popen(["bash", command] + [sample[i]["id"] for i in positions],
                                             cwd=directory, stdout=log, stderr=subprocess.STDOUT,
                                             start_new_session=True)
                    active.append((child, row, launch))
                    arm["invocations"].append(row)
                    process_groups.add(child.pid)
                while active:
                    now = time.monotonic()
                    if now >= next_sample:
                        sample_resources()
                        next_sample = now + 1
                    for child, row, launch in active[:]:
                        pid, status, usage = os.wait4(child.pid, os.WNOHANG)
                        if not pid:
                            continue
                        child.returncode = os.waitstatus_to_exitcode(status)
                        row.update(rc=child.returncode, wall_s=time.monotonic() - launch,
                                   cpu_s=usage.ru_utime + usage.ru_stime,
                                   max_rss_kb=usage.ru_maxrss, nivcsw=usage.ru_nivcsw,
                                   inblock=usage.ru_inblock, oublock=usage.ru_oublock)
                        active.remove((child, row, launch))
                    if active:
                        time.sleep(0.01)
                exited = time.monotonic()
                if offset + width >= len(prepared):
                    arm["wall_s"] = exited - start
                    after = shared_snapshot(root)
                    sample_resources()
                for directory, positions, log in prepared[offset:offset + width]:
                    matched = check_outputs(directory, positions, baseline)
                    if baseline:
                        result["baseline_match"] = matched
                    else:
                        result["outputs_match"] = matched and result["outputs_match"] is not False
                    arm["all_ok"] = arm["all_ok"] and matched
            arm["shared_changes"] = sum(before.get(path) != after.get(path)
                                        for path in before.keys() | after.keys())
            arm["all_ok"] = arm["all_ok"] and all(row["rc"] == 0 for row in arm["invocations"])
            arm["cpu_s"] = sum(row["cpu_s"] for row in arm["invocations"])
            arm["effective_cores"] = arm["cpu_s"] / arm["wall_s"]
            arm["busy_fraction"] = statistics.mean(busy) if busy else 0.0
            arm["mem_available_min_kb"] = min(available) if available else None
            arm["threads_max"] = threads

    previous = signal.signal(signal.SIGTERM, terminate)
    try:
        for arm in arms:
            estimate = sum(unit["cost_s"] for unit in sample) if arm["label"] == "a-1" else arms[0]["wall_s"]
            if estimate > 0.9 * budget - (time.monotonic() - started):
                break
            run_arm(arm)
            failed = failed or any(row["rc"] != 0 for row in arm["invocations"])
            if arm["label"] == "a-1" and not arm["all_ok"]:
                break
    finally:
        stop_children()
        signal.signal(signal.SIGTERM, previous)
    counted_concurrent = any(arm["all_ok"] for arm in arms if arm["label"].startswith("c"))
    result["outcome"] = ("failed" if failed else "baseline_mismatch" if result["baseline_match"] is False
                         else "outputs_mismatch" if result["outputs_match"] is False
                         else "measured" if counted_concurrent else "skipped")
    for prefix, key in (("a", "serial_wall_s"), ("b", "separate_wall_s")):
        walls = [arm["wall_s"] for arm in arms if arm["label"].startswith(prefix) and arm["all_ok"]]
        result[key] = statistics.mean(walls) if walls else None
    for batch in result["batches"]:
        executed = [arm for arm in arms if arm["label"].startswith(f"c{batch['n']}") and not arm["skipped"]]
        batch.update(wall_s=statistics.mean(arm["wall_s"] for arm in executed) if executed else None,
                     skipped=not executed, all_ok=bool(executed) and all(arm["all_ok"] for arm in executed))
        if batch["all_ok"] and result["outcome"] == "measured":
            batch["factor"] = result["serial_wall_s"] / batch["wall_s"]
    factors = [batch["factor"] for batch in result["batches"] if batch["factor"] is not None]
    result["factor"] = max(factors) if factors else None
    return result


def main():
    unit_mode = len(sys.argv) == 7 and sys.argv[1] == "--units"
    if not unit_mode and len(sys.argv) != 4:
        print("usage: concurrency_probe.py <run_command_file> <out_dir> <budget_s>\n"
              "       concurrency_probe.py --units <run_units_file> <units_json> <out_dir> <budget_s> <reference_json>",
              file=sys.stderr)
        return 2
    try:
        if unit_mode:
            command, manifest, directory, seconds, reference = sys.argv[2:]
        else:
            command, directory, seconds = sys.argv[1:]
        budget = int(seconds)
        if budget <= 0:
            raise ValueError("invalid budget")
        output = Path(directory).resolve()
        output.mkdir(parents=True, exist_ok=True)
        result = (unit_probe(command, manifest, output, budget, reference) if unit_mode
                  else probe(command, output, budget))
        temporary = output / "concurrency.json.tmp"
        temporary.write_text(json.dumps(result, allow_nan=False, indent=2) + "\n")
        os.replace(temporary, output / "concurrency.json")
        return 0
    except (OSError, ValueError, TypeError, OverflowError):
        print("concurrency output unavailable", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
