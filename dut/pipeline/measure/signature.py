"""Fixed, content-free signatures for the on-box execution contract."""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

ID = r"^[A-Za-z0-9_.-]{1,64}$"
NAMED_RECORD_ID = r"^(endpoint-(C[0-9]+|anchor)(_tag-[a-z0-9]+)?|RUN_VALID|[a-z0-9]+_summary)$"
EXIT = {0: "ok", 2: "infra", 3: "guard", 4: "anchor", 5: "later_stage"}


def enum(words):
    return {"type": "string", "enum": words.split()}


FIELDS = {
    "kind": enum("launch envbuild stage record model_call"),
    **{k: {"type": "string", "pattern": ID} for k in ("id", "run", "stage", "type")},
    "status": enum("PASS FAIL VOID ERROR RUNNING SKIPPED"),
    "exit_kind": enum("ok infra guard anchor later_stage unknown"),
    "error_class": enum("none infra env install download parse numeric guard anchor timeout oom quota network other"),
    **{k: {"type": "integer"} for k in ("exit_code", "tokens_in", "tokens_out", "n")},
    **{k: {"type": "number"} for k in ("wall_s", "gpu_s", "usd")},
    "model_family": enum("opencode codex claude lambda none"),
    **{k: {"type": ["boolean", "null"]} for k in ("run_valid", "calibration_valid")},
    "ratio_to_card": {"type": ["number", "null"]},
    "depth": {"type": ["integer", "null"], "minimum": 0, "maximum": 8},
    "blockers": {"type": "array", "items": enum(
        "data_unavailable licence env_irreproducible files_local_only compute_cap capacity none")},
}
SCHEMA = {"type": "object", "properties": FIELDS, "required": list(FIELDS), "additionalProperties": False}


def number(value):
    return type(value) in (int, float) and (type(value) is int or math.isfinite(value))


def validate(rec):
    """Return schema errors without including any untrusted values."""
    def valid(value, spec):
        types = spec["type"] if isinstance(spec["type"], list) else [spec["type"]]
        checks = {"null": value is None, "boolean": type(value) is bool,
                  "integer": type(value) is int, "number": number(value),
                  "string": type(value) is str, "array": type(value) is list}
        if not any(checks[t] for t in types):
            return False
        if "enum" in spec and value not in spec["enum"]:
            return False
        if "pattern" in spec and not re.fullmatch(spec["pattern"], value):
            return False
        if value is not None and "minimum" in spec and not spec["minimum"] <= value <= spec["maximum"]:
            return False
        return "items" not in spec or all(valid(v, spec["items"]) for v in value)
    if not isinstance(rec, dict):
        return ["record must be an object"]
    errors = ["unknown fields"] if rec.keys() - FIELDS.keys() else []
    return errors + [f"{k}: missing or invalid" for k, spec in FIELDS.items()
                     if k not in rec or not valid(rec[k], spec)]


def ident(value):
    value = str(value).lower()
    return value if re.fullmatch(ID, value) else hashlib.sha256(value.encode()).hexdigest()


def read(path):
    try:
        data = json.loads(Path(path).read_text())
        if isinstance(data, dict):
            return data
    except (OSError, ValueError):
        pass
    return {"status": "ERROR", "error_class": "parse"}


def exit_code(value):
    if type(value) is int:
        return value
    if isinstance(value, str) and re.fullmatch(r"[+-]?[0-9]+", value):
        try:
            return int(value)
        except ValueError:
            pass
    return -1


def base(path, kind):
    path = Path(path)
    run = next((p.name for p in path.parents if re.fullmatch(r"launch[0-9]+", p.name)), None)
    run = run or next((p.name for p in path.parents if p.name.startswith("results_")), path.stem)
    return dict(kind=kind, id=ident(path.stem), run=ident(run), stage="none", type="unknown",
                n=0, status="VOID", exit_code=-1, exit_kind="unknown", error_class="none",
                depth=None, wall_s=0, gpu_s=0, usd=0, tokens_in=0, tokens_out=0,
                model_family="none", run_valid=None, calibration_valid=None, ratio_to_card=None, blockers=["none"])


def populate(rec, data):
    for key in ("wall_s", "gpu_s", "usd", "tokens_in", "tokens_out", "run_valid",
                "calibration_valid", "model_family", "error_class", "blockers", "depth"):
        candidate = dict(rec, **{key: data.get(key, rec[key])})
        if not validate(candidate):
            rec[key] = candidate[key]
    decision = data.get("decision", data.get("status"))
    rec["status"] = decision if decision in FIELDS["status"]["enum"] else (
        "PASS" if rec["run_valid"] is True else "FAIL" if rec["run_valid"] is False else "VOID")
    rc = data.get("exit_code", data.get("rc", 0 if rec["status"] == "PASS" else -1))
    rec["exit_code"] = exit_code(rc)
    rec["exit_kind"] = EXIT.get(rec["exit_code"], "unknown")
    if rec["error_class"] == "none":
        rec["error_class"] = {2: "env", 3: "guard", 4: "anchor", 124: "timeout"}.get(rec["exit_code"], "none")
    return rec


def from_record(path):
    data = read(path)
    rec = populate(base(path, "record"), data)
    name = Path(path).stem
    rec["id"] = name if re.fullmatch(NAMED_RECORD_ID, name) else (
        "rec-" + hashlib.sha256(Path(path).name.encode()).hexdigest()[:8])
    rec["stage"] = rec["id"]
    if rec["run"] == ident(name):
        rec["run"] = rec["id"]
    values = data.get("values", {})
    if isinstance(values, dict):
        measured, card = values.get("measured"), values.get("card_value")
        if number(measured) and number(card) and card != 0:
            try:
                ratio = measured / card
                rec["ratio_to_card"] = ratio if number(ratio) else None
            except OverflowError:
                pass
    compute = data.get("compute")
    rows = list(compute.items()) if isinstance(compute, dict) else (
        [(r.get("stage", "none"), r) for r in compute if isinstance(r, dict)]
        if isinstance(compute, list) else [])
    if rows:
        aliases = {"wall_s": ("wall_s", "wall_seconds", "wall_clock_s", "wall_clock_seconds"),
                   "gpu_s": ("gpu_s", "gpu_seconds", "gpu_busy_s", "gpu_busy_seconds"), "usd": ("usd", "usd_est")}
        for key, names in aliases.items():
            rec[key] = sum(next((r[n] for n in names if number(r.get(n))), 0)
                           for _, r in rows if isinstance(r, dict))
        codes = [exit_code(r.get("exit_code", r.get("rc"))) for _, r in rows if isinstance(r, dict)]
        if "exit_code" not in data and "rc" not in data:
            rec["exit_code"] = next((c for c in reversed(codes) if type(c) is int and c != 0),
                                    0 if codes and all(type(c) is int and c == 0 for c in codes) else -1)
            rec["exit_kind"] = EXIT.get(rec["exit_code"], "unknown")
    return rec


def from_launch(path):
    data = read(path)
    kind = "envbuild" if Path(path).stem.startswith("envbuild") else "launch"
    rec = populate(base(path, kind), data)
    rec["run"] = ident("launch" + re.sub(r"\D", "", Path(path).stem))
    rec["n"] = data.get("n") if type(data.get("n")) is int else int(re.sub(r"\D", "", Path(path).stem) or 0)
    rec["type"] = data["type"] if isinstance(data.get("type"), str) and re.fullmatch(ID, data["type"]) else "unknown"
    rec["wall_s"] = data["hours_wall"] * 3600 if number(data.get("hours_wall")) else rec["wall_s"]
    rec["usd"] = data["usd_est"] if number(data.get("usd_est")) else rec["usd"]
    if rec["exit_code"] >= 0:
        rec["status"] = "PASS" if rec["exit_code"] == 0 else "FAIL"
    elif rec["error_class"] != "parse":
        rec["status"] = "ERROR" if data.get("terminated") is True else "SKIPPED" if data.get("started") is False else "RUNNING"
    return rec


def signatures(directory):
    """Yield validated signatures; never read logs or non-JSON payloads."""
    root = Path(directory)
    paths = sorted(p for pattern in ("out/launch*.json", "out/envbuild*.json")
                   for p in root.glob(pattern) if re.fullmatch(r"(?:launch|envbuild)[0-9]+\.json", p.name))
    launches = sorted((from_launch(p) for p in paths), key=lambda r: r["n"])
    records = [from_record(p) for folder in sorted(set(root.glob("out/launch[0-9]*/results_*/out")) |
                                                set(root.glob("results_*/out"))) for p in sorted(folder.rglob("*.json"))]
    for rec in launches + records:
        if validate(rec):
            raise ValueError("invalid signature")
        yield rec


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("measure_dir")
    args = parser.parse_args()
    try:
        for record in signatures(args.measure_dir):
            print(json.dumps(record, allow_nan=False))
    except ValueError:
        parser.exit(1, "invalid signature\n")
