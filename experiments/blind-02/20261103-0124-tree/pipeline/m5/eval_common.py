"""Shared deterministic evaluation IO, execution, and exact median intervals."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import signal
import time


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, allow_nan=False, indent=2) + "\n")
    os.replace(temporary, path)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def invocation(root, protocol, arm, phase, index, budget=None, mode=None, protocol_path=None):
    # Each invocation gets a new working directory and empty output tree.
    work = root / "evaluation-work" / phase / str(index) / arm
    if work.exists():
        raise ValueError("reused evaluation workspace")
    work.mkdir(parents=True)
    for name in ("baseline-published", "method", "data", "harness", "payload", "baseline-out"):
        (work / name).symlink_to(root / name, target_is_directory=True)
    out = work / "out"
    out.mkdir()
    environment = dict(os.environ, BASELINE_DIR=str(root / "baseline-published"),
                       METHOD_DIR=str(root / "method"), BASELINE_OUT=str(root / "baseline-out"),
                       METHOD_OUT=str(out), EVAL_OUT=str(out), EVAL_ARM=arm, EVAL_MODE=mode or phase,
                       EVAL_PROTOCOL=str(protocol_path or root / "evaluation-payload" / "predictions.json"),
                       EVAL_INPUTS=json.dumps(protocol.get("evaluation_inputs")),
                       EVAL_SEEDS=json.dumps(protocol.get("paired_seed_tests")),
                       EVAL_COMPUTE_BUDGET="" if budget is None else str(budget))
    if arm == "method":
        script = root / "payload/method/run_anchors.sh" if phase == "anchors" else root / "payload/method/run_method.sh"
        if not script.exists():
            script = root / "payload/method/run_method.sh"
    else:
        script = root / "harness/run_evaluation.sh"
        if not script.exists():
            script = root / "harness/run_anchors.sh"
    return work, out, environment, script


def median_interval(values, confidence, two_sided=True):
    """Exact sign-test interval for the population median, no asymptotics."""
    if not values or not all(number(v) for v in values) or not number(confidence) or not .5 <= confidence < 1:
        raise ValueError("invalid confidence inputs")
    values = sorted(values)
    n = len(values)
    tail = (1 - confidence) / (2 if two_sided else 1)
    allowed = [k for k in range(1, (n + 1) // 2 + 1)
               if sum(math.comb(n, j) for j in range(k)) / 2**n <= tail]
    if not allowed:
        return None
    k = max(allowed)
    return [values[k - 1], values[n - k]] if two_sided else [values[k - 1], None]


class Evaluation:
    def __init__(self, manifest, output):
        self.manifest = read(manifest)
        self.root = Path(self.manifest["remote_directory"]).resolve()
        self.protocol = self.manifest["protocol"]
        self.output = Path(output).resolve()
        self.output.mkdir(parents=True, exist_ok=True)
        self.hashes = self.manifest["input_hashes"]
        self.raw = self.output / "raw.jsonl"

    def result(self, name, status, **values):
        result = dict(status=status, input_hashes=self.hashes, **values)
        write(self.output / (name + ".json"), result)
        return result

    def append(self, row):
        with self.raw.open("a") as stream:
            stream.write(json.dumps(row, allow_nan=False) + "\n")

    def seeds(self):
        rule = self.protocol["paired_seed_tests"]
        if rule.get("kind") == "deterministic" and isinstance(rule.get("justification"), str) and rule["justification"].strip():
            return [None]
        seeds = rule.get("seeds")
        if rule.get("kind") != "paired_median" or not isinstance(seeds, list) or not seeds or any(type(s) is not int for s in seeds) or len(set(seeds)) != len(seeds):
            raise ValueError("unsupported seed rule")
        return seeds

    def identities(self):
        ids = self.protocol["evaluation_inputs"]["ids"]
        if not isinstance(ids, list) or not ids or any(not isinstance(i, str) or not i.strip() for i in ids) or len(set(ids)) != len(ids):
            raise ValueError("invalid input identities")
        seeds = self.seeds()
        sizes = self.protocol["sample_sizes"]
        if type(sizes.get("inputs")) is not int or sizes["inputs"] != len(ids) or type(sizes.get("seeds")) is not int or sizes["seeds"] != len(seeds):
            raise ValueError("invalid sample sizes")
        return [(i, s) for s in seeds for i in ids]

    def run(self, arm, phase, index, budget=None):
        work, out, environment, script = invocation(self.root, self.protocol, arm, phase, index, budget)
        limit = self.manifest["run_timeout_s"]
        if type(limit) is not int or limit <= 0:
            raise ValueError("invalid timeout")
        if budget is not None:
            gpus = self.protocol["hardware_cost_basis"][arm + "_gpus"]
            if not number(budget) or budget <= 0 or type(gpus) is not int or gpus < 1:
                raise ValueError("invalid budget")
            limit = min(limit, budget / gpus)
        start = time.perf_counter()
        log = self.output / f"{phase}-{index}-{arm}.log"
        try:
            with log.open("wb") as stream:
                process = subprocess.Popen(["bash", str(script)], cwd=work, env=environment,
                                           stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
                try:
                    rc = process.wait(timeout=limit)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                    rc = 124
        except OSError:
            rc = 127
        elapsed = time.perf_counter() - start
        row = dict(phase=phase, index=index, arm=arm, compute_budget=budget, rc=rc, process_wall_s=elapsed)
        self.append(row)
        if rc == 124:
            raise TimeoutError("workload timed out")
        if rc:
            raise RuntimeError("workload failed")
        if phase == "anchors":
            measured = read(out / "anchors_measured.json")
            write(self.output / "anchors_measured.json", measured)
            return measured
        report_path = out / "evaluation.json"
        report = read(report_path)
        row["output_sha256"] = digest(report_path)
        row["report"] = report
        self.append(row)
        # Preserve every measured output, including warmups and curve runs.
        shutil.copyfile(report_path, self.output / f"{phase}-{index}-{arm}.json")
        return report, elapsed

    def records(self, report):
        records = report["records"]
        if not isinstance(records, list):
            raise ValueError("invalid records")
        actual = []
        for row in records:
            ident, seed = row["input_id"], row["seed"]
            if not isinstance(ident, str) or (seed is not None and type(seed) is not int):
                raise ValueError("invalid identity")
            if not isinstance(row["metrics"], dict) or not row["metrics"] or not all(number(v) for v in row["metrics"].values()):
                raise ValueError("invalid metrics")
            actual.append((ident, seed))
        return records, actual == self.identities()

    def timing(self, report, elapsed, arm):
        scope = self.protocol["timing_scope"]
        if report["timing_scope"] != scope or scope.get("kind") not in ("process_wall", "reported_wall") or scope.get("gpu_synchronization") != "adapter":
            raise ValueError("invalid timing scope")
        value = elapsed if scope["kind"] == "process_wall" else report["wall_s"]
        basis = self.protocol["hardware_cost_basis"]
        count = basis[arm + "_gpus"]
        available = self.manifest["gpu_count"]
        if type(count) is not int or count < 1 or count > available or type(report.get("gpu_count")) is not int or report["gpu_count"] != count:
            raise ValueError("invalid GPU count")
        if not number(value) or value <= 0:
            raise ValueError("invalid time")
        return value, count


def cli(stage, evaluate):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=[stage], default=stage)
    parser.add_argument("--in", dest="manifest", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    evaluation = None
    try:
        evaluation = Evaluation(args.manifest, args.out)
        return evaluate(evaluation)
    except TimeoutError:
        if evaluation:
            evaluation.result(stage, "VOID", reason_code="timeout", **{stage + "_pass": None})
        return 3
    except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError, OverflowError, RuntimeError):
        if evaluation:
            evaluation.result(stage, "VOID", reason_code="missing_or_invalid_measurements", **{stage + "_pass": None})
        else:
            write(Path(args.out) / (stage + ".json"), dict(status="VOID", reason_code="invalid_manifest", **{stage + "_pass": None}))
        return 2
