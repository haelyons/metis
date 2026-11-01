"""Validate and append content-free m5 signature envelopes using only stdlib."""
import argparse
import fcntl
import json
import math
import os
import re
import sys
import tempfile
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from measure.signature import EXIT, validate as validate_v1


COMMON = {"tokens_known": bool, "gpu_busy_known": bool}
FACTS = {
    "intake": dict(COMMON, found=bool, anchors_count=int,
                   data=("available", "partial", "unavailable", "unknown"),
                   licence=("permitted", "restricted", "unknown"), stock_environment=bool,
                   size=("tiny", "small", "medium", "large", "unknown")),
    "reproduce": dict(COMMON, anchors_passed=int, anchors_total=int,
                      stock_verified=bool, tuned_control_valid=bool),
    "profile": dict(COMMON, profile_complete=bool, timed_fraction=float, gpu_telemetry=bool),
    "seal": dict(COMMON, seal_present=bool, seal_verified=bool, prediction_count=int),
    "propose": dict(COMMON, method=("data-parallel over inputs", "batching", "multi-GPU",
                                  "ensembles", "pipelining", "none"),
                    expected_speedup=float, votes_approve=int, votes_total=int,
                    vote_share=float, gate_pass=bool),
    "implement": dict(COMMON, patch_applies=bool, tests_pass=bool, blind_tests=bool,
                      launch_review_pass=bool),
    "evaluate": dict(COMMON, validity_pass=bool, equivalence_pass=bool, performance_pass=bool,
                     equal_cost=bool, speedup_published=float, speedup_tuned=float,
                     cost_ratio=float, prediction_ratio=float, curve_points=int),
    "takeaways": dict(COMMON, operator_written=bool, research_written=bool,
                      teardown_confirmed=bool),
}


def validate(value):
    """Return validation errors without echoing untrusted values."""
    if (type(value) is not dict or set(value) != {"schema_version", "signature", "facts"}
            or type(value["schema_version"]) is not int or value["schema_version"] != 2):
        return ["invalid envelope"]
    record, facts = value["signature"], value["facts"]
    errors = validate_v1(record)
    if errors:
        return errors
    stage = record["stage"]
    if stage not in FACTS:
        return ["invalid stage"]
    if (not re.fullmatch(r"s[0-9]{2,}-" + stage, record["id"])
            or not re.fullmatch(r"(?:r[0-9]+|run[0-9]+|none)", record["run"])
            or record["type"] not in ("unknown", "none", "dev", "serve", *FACTS)):
        return ["invalid signature identifiers"]
    # The run summary is an optional extension, so existing v2 stage records remain readable.
    schema = dict(FACTS[stage])
    if stage == "intake" and type(facts) is dict and "anchored" in facts:
        schema["anchored"] = bool
    if stage == "intake" and type(facts) is dict and "licence_basis" in facts:
        schema["licence_basis"] = ("unreachable", "none", "owner", "distribution", "explicit")
    if stage == "takeaways" and type(facts) is dict and "run_box_usd" in facts:
        schema["run_box_usd"] = float
    if stage == "profile" and type(facts) is dict and "headroom" in facts:
        schema["headroom"] = float
    if stage == "profile" and type(facts) is dict and "host_only" in facts:
        schema["host_only"] = bool
    if stage == "propose" and type(facts) is dict:
        for key, spec in {"votes_reject": int, "votes_abstain": int,
                          "outcome": ("approved", "rejected", "conditions_unmet", "no_feasible_method")}.items():
            if key in facts:
                schema[key] = spec
    if stage in ("reproduce", "profile", "implement", "evaluate") and type(facts) is dict:
        for key, spec in {"timed_out": bool, "budget_s": int, "overrun": bool}.items():
            if key in facts:
                schema[key] = spec
    if type(facts) is not dict or facts.keys() != schema.keys():
        return ["invalid fact keys"]
    for key, spec in schema.items():
        item = facts[key]
        if item is None:
            continue
        valid = (type(item) is str and item in spec) if isinstance(spec, tuple) else (
            (type(item) in (int, float) if spec is float else type(item) is spec)
            and (spec is not int or item >= 0)
            and (spec is not float or math.isfinite(item)))
        if not valid:
            errors.append(f"{key}: invalid fact")
        elif key in ("timed_fraction", "vote_share") and not 0 <= item <= 1:
            errors.append(f"{key}: out of range")
        elif key == "votes_total" and item != 5:
            errors.append("votes_total: must be five")
        elif key == "run_box_usd" and item < 0:
            errors.append("run_box_usd: must be nonnegative")
        elif key == "headroom" and item <= 0:
            errors.append("headroom: must be positive")
    if record["status"] == "SKIPPED" and any(v is not None for v in facts.values()):
        errors.append("SKIPPED facts must be null")
    return errors


def envelope(stage, status, facts, **v1):
    """Build a validated v2 envelope; all fact keys are required, even when null."""
    if type(stage) is not str or stage not in FACTS:
        raise ValueError("invalid stage")
    record = dict(kind="stage", id=f"s{list(FACTS).index(stage) + 1:02d}-{stage}",
                  run="none", stage=stage, type="unknown", n=0, status=status,
                  exit_code=0 if status == "PASS" else -1, exit_kind="unknown",
                  error_class="none", depth=0, wall_s=0, gpu_s=0, usd=0,
                  tokens_in=0, tokens_out=0, model_family="none", run_valid=None,
                  calibration_valid=None, ratio_to_card=None, blockers=["none"])
    record.update(v1)
    if "exit_kind" not in v1:
        code = record["exit_code"]
        record["exit_kind"] = EXIT.get(code, "unknown") if type(code) is int else "unknown"
    result = {"schema_version": 2, "signature": record, "facts": facts}
    errors = validate(result)
    if errors:
        raise ValueError("; ".join(errors))
    return result


def emit(S_dir, envelope):
    """Stage and fsync one JSON line, then append under an exclusive file lock."""
    errors = validate(envelope)
    if errors:
        raise ValueError("; ".join(errors))
    payload = (json.dumps(envelope, allow_nan=False, separators=(",", ":")) + "\n").encode()
    directory = Path(S_dir)
    directory.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryFile(dir=directory) as staged:
        staged.write(payload)
        staged.flush()
        os.fsync(staged.fileno())
        staged.seek(0)
        with (directory / "signatures.jsonl").open("a+b", buffering=0) as output:
            fcntl.flock(output.fileno(), fcntl.LOCK_EX)
            output.seek(0, os.SEEK_END)
            start = output.tell()
            try:
                remaining = memoryview(staged.read())
                while remaining:
                    written = os.write(output.fileno(), remaining)
                    remaining = remaining[written:]
                os.fsync(output.fileno())
            except OSError:
                output.truncate(start)
                os.fsync(output.fileno())
                raise


def signatures(S_dir):
    """Read only signatures.jsonl, validating every envelope before use."""
    with (Path(S_dir) / "signatures.jsonl").open() as source:
        fcntl.flock(source.fileno(), fcntl.LOCK_SH)
        for line in source:
            value = json.loads(line)
            errors = validate(value)
            if errors:
                raise ValueError("; ".join(errors))
            yield value


class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(1, "invalid command arguments\n")


if __name__ == "__main__":
    parser = Parser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("emit")
    command.add_argument("--dir", required=True)
    command.add_argument("--stage", required=True)
    command.add_argument("--status", required=True)
    command.add_argument("--facts")
    command.add_argument("--v1", default="{}")
    try:
        args = parser.parse_args()
        facts = json.loads(args.facts) if args.facts is not None else (
            dict.fromkeys(FACTS.get(args.stage, {})) if args.status == "SKIPPED" else {})
        v1 = json.loads(args.v1)
        if type(v1) is not dict:
            raise ValueError("v1 must be an object")
        emit(args.dir, envelope(args.stage, args.status, facts, **v1))
    except (OSError, ValueError, TypeError, OverflowError):
        parser.exit(1, "invalid signature or output unavailable\n")
