#!/usr/bin/env python3
"""Score a sealed comparison from its replicate invocations (U58); exit 0/written, 1/invalid input."""
from fractions import Fraction
import glob
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import stat
import sys


NAME = re.compile(r"[a-z][a-z0-9_]{0,30}")
INPUT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
CID = re.compile(r"K[0-9]{1,2}")
PART = re.compile(r"[A-Za-z0-9._+=-]+")
GLOB_PART = re.compile(r"[A-Za-z0-9._+=*?\[\]-]+")
POINTER = re.compile(r"(?:/(?:[^~/]|~[01])*)*")
HEX = re.compile(r"[0-9a-f]{64}")
# text_numbers: the design's number pattern, plus nan, inf and -inf as whole tokens
NUMBERS = re.compile(r"(?<![A-Za-z0-9_])(?:-inf|inf|nan)(?![A-Za-z0-9_])|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
DESIGN = {"arms", "inputs", "outputs", "metrics", "evaluator", "replicates", "warmup", "order_seed", "timeout_s",
          "budget_s", "bootstrap_seed", "bootstrap_resamples", "comparisons"}
COMPARISON = {"id", "arm", "against", "measure", "criterion", "direction", "unit", "pairing", "rule", "confidence",
              "margin", "threshold", "strict", "reference", "missing", "given", "parts"}
WRAP = {"status", "adapter_rc", "adapter_wall_s", "commands", "gpu_busy_s", "gpu_busy_known", "eval_status", "eval_rc",
        "eval_wall_s", "eval_gpu_busy_s", "eval_gpu_busy_known"}
TOLERANCE = {"exact": None, "elementwise_abs": {"abs"}, "elementwise_abs_plus_rel_max": {"abs", "rel"}}


def number(value):
    """A finite number: an integer too long for a double is not one."""
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(float(value))
    except OverflowError:
        return False


def written(exact):
    """A value as written: null when no finite double holds it."""
    if exact is None:
        return None
    try:
        value = float(exact)
    except OverflowError:
        return None
    return value if math.isfinite(value) else None


def require(condition):
    if not condition:
        raise ValueError("invalid input")


def reject_constant(name):
    raise ValueError("invalid input")


def strict(data):
    """Sealed JSON as intake's JSON.parse reads it: NaN, Infinity and -Infinity are invalid."""
    return json.loads(data, parse_constant=reject_constant)


def relative(path, part=PART, first=("out", "log", "eval")):
    parts = path.split("/") if type(path) is str else []
    return bool(parts) and parts[0] in first and all(part.fullmatch(item) and item not in (".", "..") for item in parts)


def text(value):
    return type(value) is str and value != ""


def integer(value, low=None):
    return type(value) is int and (low is None or value >= low)


def check_placeholders(item, inputs):
    """{input}, {run}, {out} and {spec:<pointer>} resolving to a string or finite number in every input's spec; {{ and
    }} are literal braces; any other brace is invalid."""
    def resolves(expr):
        for item in inputs:
            node = item["spec"]
            for raw in expr.split("/")[1:]:
                key = raw.replace("~1", "/").replace("~0", "~")
                if type(node) is list:
                    require(re.fullmatch(r"0|[1-9][0-9]*", key) and int(key) < len(node))
                    node = node[int(key)]
                else:
                    require(type(node) is dict and key in node)
                    node = node[key]
            require(type(node) is str or number(node))

    index = 0
    while index < len(item):
        if item[index] == "}":
            require(item[index + 1:index + 2] == "}")
            index += 1
        elif item[index] == "{" and item[index + 1:index + 2] == "{":
            index += 1
        elif item[index] == "{":
            end = item.find("}", index)
            require(end >= 0)
            token = item[index + 1:end]
            if token not in ("input", "run", "out"):
                require(token.startswith("spec:") and POINTER.fullmatch(token[5:]))
                resolves(token[5:])
            index = end
        index += 1


def check_design(design):
    """Every rule intake applies to a design."""
    require(type(design) is dict and set(design) == DESIGN)
    arms, inputs, outputs, metrics = (design[key] for key in ("arms", "inputs", "outputs", "metrics"))
    require(type(inputs) is list and 1 <= len(inputs) <= 10
            and all(type(item) is dict and set(item) == {"id", "spec"} and type(item["id"]) is str
                    and INPUT.fullmatch(item["id"]) for item in inputs)
            and len({item["id"] for item in inputs}) == len(inputs))
    require(type(arms) is list and 2 <= len(arms) <= 5
            and all(type(arm) is dict and set(arm) == {"id", "what", "commands", "env"} and arm["id"] == f"A{i}"
                    and text(arm["what"]) and type(arm["commands"]) is list and 1 <= len(arm["commands"]) <= 8
                    and all(type(command) is list and command and all(text(part) for part in command)
                            for command in arm["commands"])
                    and (arm["env"] is None or type(arm["env"]) is dict)
                    for i, arm in enumerate(arms)))
    for arm in arms:
        for part in (part for command in arm["commands"] for part in command):
            check_placeholders(part, inputs)
        for key, value in (arm["env"] or {}).items():
            require(re.fullmatch(r"[A-Z_][A-Z0-9_]{0,63}", key) and not key.startswith("CMP_") and type(value) is str)
            check_placeholders(value, inputs)
    require(type(outputs) is list and len(outputs) <= 10
            and all(type(item) is dict and set(item) == {"name", "what", "format", "select"} and type(item["name"]) is str
                    and NAME.fullmatch(item["name"]) and text(item["what"])
                    and item["format"] in ("bytes", "text_numbers", "json_numbers")
                    for item in outputs)
            and len({item["name"] for item in outputs}) == len(outputs))
    for item in outputs:
        select = item["select"]
        require(select is None or item["format"] != "json_numbers" and type(select) is str
                and re.compile(select).groups >= 1)
    require(type(metrics) is list and 1 <= len(metrics) <= 10
            and all(type(item) is dict and set(item) == {"name", "unit", "what", "source", "reduce", "expect_count"}
                    and type(item["name"]) is str and NAME.fullmatch(item["name"]) and text(item["unit"])
                    and text(item["what"]) for item in metrics)
            and len({item["name"] for item in metrics}) == len(metrics))
    for item in metrics:
        if item["source"] == "trusted_wall":
            require(item["reduce"] is None and item["expect_count"] is None)
        else:
            count = item["expect_count"]
            require(item["source"] == "sealed_extraction" and item["reduce"] in ("first", "max", "value_at_max_key")
                    and (count is None or type(count) is int and count > 0))
    resamples, evaluator = design["bootstrap_resamples"], design["evaluator"]
    require((evaluator is None or type(evaluator) is dict and set(evaluator) == {"what", "spec", "timeout_s"}
             and text(evaluator["what"]) and (evaluator["timeout_s"] is None or integer(evaluator["timeout_s"], 1)))
            and type(design["replicates"]) is int and 1 <= design["replicates"] <= 30
            and integer(design["warmup"], 0) and design["warmup"] <= 3 and integer(design["order_seed"])
            and integer(design["budget_s"], 1)
            and type(design["bootstrap_seed"]) is int and type(resamples) is int and 1000 <= resamples <= 1000000
            and type(design["comparisons"]) is list and len(design["comparisons"]) <= 12)
    timeout, ids, input_ids = design["timeout_s"], {arm["id"] for arm in arms}, {item["id"] for item in inputs}
    require(timeout is None or integer(timeout, 1)
            or type(timeout) is dict and set(timeout) == ids
            and all(integer(value, 1) or type(value) is dict and set(value) == input_ids
                    and all(integer(item, 1) for item in value.values()) for value in timeout.values()))
    earlier = []
    for comparison in design["comparisons"]:
        check_comparison(comparison, design, earlier)
        earlier.append(comparison["id"])


def check_comparison(c, design, earlier):
    arms = [arm["id"] for arm in design["arms"]]
    inputs = {item["id"] for item in design["inputs"]}
    require(type(c) is dict and set(c) == COMPARISON)
    require(type(c["id"]) is str and CID.fullmatch(c["id"]) and c["id"] not in earlier and c["arm"] in arms
            and c["against"] != c["arm"] and (c["against"] in arms or c["against"] == "reference"))
    parts = c["parts"]
    require(type(parts) is list and parts and all(type(item) is str and item for item in parts)
            and len(set(parts)) == len(parts))
    measure, criterion, unit = c["measure"], c["criterion"], c["unit"]
    output = type(measure) is dict and set(measure) == {"output", "comparator"}
    require(output and measure["output"] in [item["name"] for item in design["outputs"]]
            and measure["comparator"] in TOLERANCE and c["against"] in arms
            or type(measure) is dict and set(measure) == {"metric"}
            and measure["metric"] in [item["name"] for item in design["metrics"]])
    require(criterion in ("agreement", "non_inferiority", "superiority", "ratio_at_least")
            and (criterion == "agreement") == output)
    require(c["direction"] == "two_sided" if criterion in ("agreement", "superiority")
            else c["direction"] in ("higher_better", "lower_better"))
    per_input = unit in ("per_input_all", "per_input_each")
    require((unit, c["pairing"], c["rule"]) == ("pooled_mean", "paired_replicate", "bootstrap")
            if criterion == "ratio_at_least" else
            c["rule"] == "all_pairs" and per_input and c["pairing"] in ("paired_replicate", "unpaired")
            and (criterion != "agreement" or c["pairing"] == "paired_replicate"))
    confidence = c["confidence"]
    require(number(confidence) and 0.5 <= confidence < 1 if c["rule"] == "bootstrap" else confidence is None)
    margin = c["margin"]
    if output:
        keys = TOLERANCE[measure["comparator"]]
    else:
        keys = {"abs"} if criterion in ("non_inferiority", "superiority") and margin is not None else None
    require(margin is None if keys is None else type(margin) is dict and set(margin) == keys
            and all(number(value) and value >= 0 for value in margin.values()))
    if criterion == "ratio_at_least":
        require(number(c["threshold"]) and c["threshold"] > 0 and type(c["strict"]) is bool)
    else:
        require(c["threshold"] is None and c["strict"] is None)
    reference = c["reference"]
    if c["against"] == "reference":
        require(type(reference) is dict and set(reference) == {"source", "values"} and type(reference["source"]) is str
                and reference["source"] and type(reference["values"]) is dict and set(reference["values"]) == inputs
                and all(number(value) for value in reference["values"].values())
                and not output and per_input and c["pairing"] == "unpaired")
    else:
        require(reference is None)
    given = c["given"]
    require(c["missing"] in ("void", "fail") and type(given) is list and all(item in earlier for item in given)
            and len(set(given)) == len(given))


def check_files(files, design):
    arms = [arm["id"] for arm in design["arms"]]
    names = {item["name"] for item in design["outputs"]}
    first = ("out", "log", "eval") if design["evaluator"] is not None else ("out", "log")
    require(type(files) is dict and set(files) == {"files"} and type(files["files"]) is dict
            and set(files["files"]) == set(arms))
    for locations in files["files"].values():
        require(type(locations) is dict and set(locations) == names)
        for location in locations.values():
            require(relative(location, first=first) if type(location) is str else
                    type(location) is dict and set(location) == {"glob"}
                    and relative(location["glob"], GLOB_PART, first))
    return files["files"]


def check_rules(extract, design):
    reduce = {item["name"]: item["reduce"] for item in design["metrics"] if item["source"] == "sealed_extraction"}
    expected = {(arm["id"], name) for arm in design["arms"] for name in reduce}
    rules = extract.get("rules") if type(extract) is dict and set(extract) == {"rules"} else None
    require(type(rules) is list and len(rules) == len(expected))
    found = {}
    for rule in rules:
        require(type(rule) is dict and set(rule) == {"arm", "metric", "file", "kind", "expr"}
                and (rule["arm"], rule["metric"]) in expected and (rule["arm"], rule["metric"]) not in found
                and relative(rule["file"]) and type(rule["expr"]) is str)
        if rule["kind"] == "json":
            require(POINTER.fullmatch(rule["expr"]))
        else:
            groups = 2 if reduce[rule["metric"]] == "value_at_max_key" else 1
            require(rule["kind"] == "regex" and re.compile(rule["expr"]).groups == groups)
        found[(rule["arm"], rule["metric"])] = rule
    return found


def sealed_harness(c_dir, harness, design):
    """Check every sealed harness file; return the bytes of cmp_files.json and cmp_extract.json."""
    seal = strict((c_dir / "arms_seal.json").read_text())
    require(type(seal) is dict and set(seal) == {"files", "sealed_utc"})
    files = seal["files"]
    names = {f"arms/{arm['id']}.sh" for arm in design["arms"]} | {"cmp_files.json", "cmp_extract.json", "versions.sh"}
    if design["evaluator"] is not None:
        names |= {"fetch_private.sh", "evaluate.sh"}
    require(type(files) is dict and set(files) == names)  # an unsealed harness file could change unnoticed
    data = {}
    for name, digest in files.items():
        require(relative(name, first=(name.split("/")[0],)) and type(digest) is str and HEX.fullmatch(digest))
        data[name] = (harness / name).read_bytes()
        if hashlib.sha256(data[name]).hexdigest() != digest:
            raise ValueError("seal mismatch")
    return data["cmp_files.json"], data["cmp_extract.json"]


def regular(root, rel):
    """True when every component under root is a real directory and the last one a regular file (no link)."""
    path = Path(root)
    try:
        parts = rel.split("/")
        for index, part in enumerate(parts):
            path = path / part
            mode = os.lstat(path).st_mode
            if not (stat.S_ISREG(mode) if index == len(parts) - 1 else stat.S_ISDIR(mode)):
                return False
        return True
    except (OSError, ValueError):
        return False


def read(root, rel):
    if not regular(root, rel):
        raise OSError("not a regular file")
    return (Path(root) / rel).read_bytes()


def valid_wrap(value, count):
    """wrap.json's keys and types; status ok exactly when every exit status is 0 and every command (count) has a row;
    eval_status ok only when eval_rc is 0; an exit status null exactly on a timeout (the last process started for the
    arm part, eval_rc for the evaluator part, which is also null when skipped)."""
    def seconds(item, nullable=False):
        return nullable and item is None or number(item) and item >= 0

    def rc(item):
        return item is None or type(item) is int

    if type(value) is not dict or set(value) != WRAP or type(value["commands"]) is not list:
        return False
    rows = value["commands"]
    if not all(type(row) is dict and "rc" in row for row in rows):
        return False
    statuses = [value["adapter_rc"], *(row["rc"] for row in rows)]
    return (value["status"] in ("ok", "failed", "timeout", "invalid")
            and all(item is not None for item in statuses[:-1])
            and (value["status"] != "timeout" or statuses[-1] is None)
            and (value["status"] not in ("ok", "failed") or statuses[-1] is not None)
            and (value["eval_rc"] is None) == (value["eval_status"] in ("timeout", "skipped"))
            and value["eval_status"] in ("ok", "failed", "timeout", "skipped")
            and rc(value["adapter_rc"]) and seconds(value["adapter_wall_s"]) and seconds(value["gpu_busy_s"])
            and type(value["gpu_busy_known"]) is bool and rc(value["eval_rc"])
            and seconds(value["eval_wall_s"], True) and seconds(value["eval_gpu_busy_s"], True)
            and type(value["eval_gpu_busy_known"]) is bool
            and all(type(row) is dict and set(row) == {"argv", "rc", "wall_s", "executable", "sha256"}
                    and type(row["argv"]) is list and row["argv"] and all(type(part) is str for part in row["argv"])
                    and rc(row["rc"]) and seconds(row["wall_s"])
                    and (row["executable"] is None or type(row["executable"]) is str)
                    and (row["sha256"] is None or type(row["sha256"]) is str) for row in rows)
            and (value["status"] == "ok") == (value["adapter_rc"] == 0 and len(rows) == count
                                               and all(row["rc"] == 0 for row in rows))
            and (value["eval_status"] != "ok" or value["eval_rc"] == 0))


def load(path, count):
    """An invocation: its directory and its wrap.json, None when missing or invalid (count: the arm's commands)."""
    try:
        value = json.loads(read(path, "wrap.json"))
    except (OSError, ValueError, RecursionError):
        value = None
    return dict(dir=path, wrap=value if valid_wrap(value, count) else None)


def ok(job, location=None):
    """True when the invocation is ok and, for a location under eval, its evaluator part too."""
    wrap = job["wrap"]
    return (wrap is not None and wrap["status"] == "ok"
            and (location is None or location.split("/")[0] != "eval" or wrap["eval_status"] == "ok"))


def pointer(value, expr):
    for token in expr.split("/")[1:]:
        token = token.replace("~1", "/").replace("~0", "~")
        if type(value) is dict:
            value = value[token]
        elif type(value) is list and re.fullmatch(r"0|[1-9][0-9]*", token):
            value = value[int(token)]
        else:
            raise KeyError(token)
    return value


def extract(rule, metric, job):
    """A sealed_extraction value, exact, or None."""
    if not ok(job, rule["file"]):
        return None
    pairs = metric["reduce"] == "value_at_max_key"
    try:
        data = read(job["dir"], rule["file"])
        if rule["kind"] == "json":
            value = pointer(json.loads(data), rule["expr"])
            if pairs:
                if type(value) is not list or not all(type(item) is list and len(item) == 2
                                                      and all(number(x) for x in item) for item in value):
                    return None
                matched = value
            elif number(value):
                matched = [value]
            elif type(value) is list and all(number(x) for x in value):
                matched = value
            else:
                return None
        else:
            matched = []
            for match in re.finditer(rule["expr"], data.decode("utf-8", errors="replace")):
                parsed = [float(group) for group in match.groups()]
                if not all(math.isfinite(x) for x in parsed):
                    return None
                matched.append(parsed if pairs else parsed[0])
    except (OSError, ValueError, KeyError, IndexError, TypeError, RecursionError, re.error):
        return None
    if not matched or metric["expect_count"] is not None and len(matched) != metric["expect_count"]:
        return None
    if metric["reduce"] == "first":
        return Fraction(matched[0])
    if metric["reduce"] == "max":
        return max(map(Fraction, matched))
    keys = [Fraction(key) for key, _ in matched]
    return Fraction(matched[keys.index(max(keys))][1])


def trusted_wall(job, evaluator):
    if not ok(job):
        return None
    wrap = job["wrap"]
    walls = [wrap["adapter_wall_s"]] + [row["wall_s"] for row in wrap["commands"]]
    if evaluator:
        if wrap["eval_status"] != "ok":
            return None
        walls.append(wrap["eval_wall_s"])
    return sum(map(Fraction, walls), Fraction(0)) if all(number(x) for x in walls) else None


def natural(path):
    parts = re.split(r"([0-9]+)", path)
    return [int(part) if index % 2 else part for index, part in enumerate(parts)], path


def leaves(value):
    if type(value) in (int, float):
        yield value
    elif type(value) is list:
        for item in value:
            yield from leaves(item)
    elif type(value) is dict:
        for item in value.values():
            yield from leaves(item)


def content(output, location, job):
    """(selected bytes, numbers or None for bytes) of one side, or None when that side is missing."""
    path = location if type(location) is str else location["glob"]
    if not ok(job, path):
        return None
    if type(location) is str:
        names = [location]
    else:
        names = sorted((name for name in glob.glob(path, root_dir=job["dir"]) if regular(job["dir"], name)),
                       key=natural)
    try:
        parts = []
        for name in names:
            data = read(job["dir"], name)
            if output["select"] is not None:
                text = data.decode("utf-8", errors="replace")
                data = "\n".join(group or "" for match in re.finditer(output["select"], text, re.MULTILINE)
                                 for group in match.groups()).encode("utf-8")
            parts.append(data)
        if not parts:
            return None
        data = b"\n".join(parts)
        if output["format"] == "bytes":
            return (data, None) if data else None
        if output["format"] == "text_numbers":
            numbers = [float(token) for token in NUMBERS.findall(data.decode("utf-8", errors="replace"))]
        else:
            numbers = list(leaves(json.loads(data)))
    except (OSError, ValueError, RecursionError, re.error):
        return None
    return (data, numbers) if numbers else None


def finite(value):
    return type(value) is int or math.isfinite(value)


def element(a, b, tol_abs, tol_rel):
    """(agrees, abs error, rel error) of two numbers; the errors are None unless both are finite."""
    nan_a, nan_b = type(a) is float and math.isnan(a), type(b) is float and math.isnan(b)
    if nan_a or nan_b:
        return nan_a and nan_b, None, None
    if not finite(a) or not finite(b):
        return a == b, None, None
    if a == b:
        return True, 0, 0
    if type(a) is float and type(b) is float:
        # doubles decide when far from the bound; near it, or out of double range, exact arithmetic does
        d, m = abs(a - b), max(abs(a), abs(b))
        bound = tol_abs + tol_rel * m
        if math.isfinite(d) and math.isfinite(bound) and bound >= 1e-290 and abs(d - bound) > bound * 1e-12:
            return d < bound, d, d / m
    d = abs(Fraction(a) - Fraction(b))
    m = max(abs(Fraction(a)), abs(Fraction(b)))
    return d <= Fraction(tol_abs) + Fraction(tol_rel) * m, d, d / m


def agree(comparator, margin, left, right):
    """(agrees, max_abs_error, max_rel_error) of two present sides."""
    (left_bytes, left_numbers), (right_bytes, right_numbers) = left, right
    agrees = left_bytes == right_bytes if comparator == "exact" else None
    if left_numbers is None or right_numbers is None or len(left_numbers) != len(right_numbers):
        return bool(agrees), None, None
    tol_abs = margin["abs"] if margin else 0
    tol_rel = margin.get("rel", 0) if margin else 0
    every, top_abs, top_rel = True, None, None
    for a, b in zip(left_numbers, right_numbers):
        same, error, rel = element(a, b, tol_abs, tol_rel)
        every = every and same
        if error is not None:
            top_abs = error if top_abs is None else max(top_abs, error)
            top_rel = rel if top_rel is None else max(top_rel, rel)
    return (every if agrees is None else agrees), written(top_abs), written(top_rel)


def quantile(items, index):
    """The exact ratio at a position of items sorted by their double key; equal keys are ordered exactly."""
    key = items[index][0]
    start, end = index, index + 1
    while start > 0 and items[start - 1][0] == key:
        start -= 1
    while end < len(items) and items[end][0] == key:
        end += 1
    return sorted(Fraction(num, den) for _, (num, den) in items[start:end])[index - start]


def bootstrap(pairs, higher, rng, resamples, confidence):
    """(estimate, lo, hi) of the ratio of means; a bound is None when a resample's ratio is undefined."""
    scale = math.lcm(*(value.denominator for pair in pairs for value in pair))
    top = [int(x * scale) for x, _ in pairs]
    bottom = [int(y * scale) for _, y in pairs]
    if not higher:
        top, bottom = bottom, top
    estimate = Fraction(sum(top), sum(bottom)) if sum(bottom) else None
    population, size, defined, items = range(len(pairs)), len(pairs), True, []
    for _ in range(resamples):  # every resample is drawn, so the stream is the same whatever the data
        pick = rng.choices(population, k=size)
        num, den = sum(top[i] for i in pick), sum(bottom[i] for i in pick)
        if den == 0:
            defined = False
            continue
        if den < 0:
            num, den = -num, -den
        try:
            key = num / den
        except OverflowError:
            key = math.inf if num > 0 else -math.inf
        items.append((key, (num, den)))
    if not defined:
        return estimate, None, None
    items.sort(key=lambda item: item[0])
    last = resamples - 1
    lo = quantile(items, math.floor((1 - confidence) / 2 * last))
    hi = quantile(items, math.floor((1 + confidence) / 2 * last))
    return estimate, lo, hi


def decide(c, lo, hi, m):
    """(outcome, sign) of a unit from its interval."""
    if lo is None or hi is None:
        return "inconclusive", None
    if c["criterion"] == "non_inferiority":
        if c["direction"] == "higher_better":
            yes, no = lo >= -m, hi < -m
        else:
            yes, no = hi <= m, lo > m
    elif c["criterion"] == "superiority":
        if lo > m:
            return "supported", "higher"
        if hi < -m:
            return "supported", "lower"
        yes, no = False, -m <= lo and hi <= m
    else:
        t = Fraction(c["threshold"])
        yes, no = (lo > t, hi <= t) if c["strict"] else (lo >= t, hi < t)
    return ("supported" if yes else "not_supported" if no else "inconclusive"), None


def void(row, reason):
    return {**row, "estimate": None, "lo": None, "hi": None, "margin_value": None, "threshold": None,
            "outcome": "void", "reason": reason}


def missing_rule(c, row, arm_missing):
    if c["missing"] == "fail" and arm_missing:
        return {**row, "outcome": "not_supported", "reason": "missing_values"}
    return void(row, "missing_values")


class Scorer:
    def __init__(self, design, files, rules, root):
        self.design, self.files, self.rules, self.root = design, files, rules, Path(root)
        self.inputs = [item["id"] for item in design["inputs"]]
        self.outputs = {item["name"]: item for item in design["outputs"]}
        self.metrics = {item["name"]: item for item in design["metrics"]}
        # replicate rounds are fetched as r<round index>; the index counts from 0 when an r0 round was fetched,
        # otherwise from 1
        base = 0 if (self.root / "r0").is_dir() else 1
        self.replicates = list(range(base, base + design["replicates"]))
        self.rng = random.Random(design["bootstrap_seed"])
        self.jobs, self.values, self.contents, self.results = {}, {}, {}, {}

    def job(self, arm, replicate, item):
        key = (arm, replicate, item)
        if key not in self.jobs:
            count = len(next(entry for entry in self.design["arms"] if entry["id"] == arm)["commands"])
            self.jobs[key] = load(self.root / f"r{replicate}" / arm / item, count)
        return self.jobs[key]

    def value(self, metric, arm, replicate, item):
        key = (metric, arm, replicate, item)
        if key not in self.values:
            job, spec = self.job(arm, replicate, item), self.metrics[metric]
            self.values[key] = (trusted_wall(job, self.design["evaluator"] is not None)
                                if spec["source"] == "trusted_wall" else extract(self.rules[(arm, metric)], spec, job))
        return self.values[key]

    def content(self, name, arm, replicate, item):
        key = (name, arm, replicate, item)
        if key not in self.contents:
            self.contents[key] = content(self.outputs[name], self.files[arm][name], self.job(arm, replicate, item))
        return self.contents[key]

    def series(self, metric, arm, item):
        """An arm's value per replicate: for one input, or the mean over inputs (None when any is missing)."""
        if item is not None:
            return [self.value(metric, arm, replicate, item) for replicate in self.replicates]
        result = []
        for replicate in self.replicates:
            values = [self.value(metric, arm, replicate, name) for name in self.inputs]
            result.append(None if None in values else sum(values, Fraction(0)) / len(values))
        return result

    def eligible(self, c, item):
        for ident in c["given"]:
            prior = self.results[ident]
            if item is not None and prior["unit"] != "pooled_mean":
                outcome = prior["rows"][item]
            elif prior["outcome"] == "per_input":
                outcome = "supported" if all(value == "supported" for value in prior["rows"].values()) else None
            else:
                outcome = prior["outcome"]
            if outcome != "supported":
                return False
        return True

    def agreement(self, c, item):
        name, comparator = c["measure"]["output"], c["measure"]["comparator"]
        pairs, arm_missing, disagree = [], False, False
        for replicate in self.replicates:
            left, right = self.content(name, c["arm"], replicate, item), self.content(name, c["against"], replicate, item)
            if left is None or right is None:
                arm_missing = arm_missing or left is None
                pairs.append(dict(replicate=replicate, agrees=None, missing=True, max_abs_error=None, max_rel_error=None))
                continue
            agrees, top_abs, top_rel = agree(comparator, c["margin"], left, right)
            disagree = disagree or not agrees
            pairs.append(dict(replicate=replicate, agrees=agrees, missing=False, max_abs_error=top_abs,
                              max_rel_error=top_rel))
        n_missing = sum(pair["missing"] for pair in pairs)
        row = dict(input=item, n=len(pairs) - n_missing, n_missing=n_missing, estimate=None, lo=None, hi=None,
                   margin_value=None, threshold=None, outcome=None, sign=None, reason=None, pairs=pairs)
        if not self.eligible(c, item):
            return void(row, "not_eligible")
        if disagree:
            return {**row, "outcome": "not_supported"}
        if n_missing:
            return missing_rule(c, row, arm_missing)
        if not row["n"]:
            return void(row, "insufficient_replicates")
        return {**row, "outcome": "supported"}

    def metric(self, c, item):
        metric, ratio = c["measure"]["metric"], c["criterion"] == "ratio_at_least"
        arm = self.series(metric, c["arm"], item)
        against = None if c["against"] == "reference" else self.series(metric, c["against"], item)
        n_missing = arm.count(None) + (against.count(None) if against is not None else 0)
        if c["pairing"] == "paired_replicate":
            pairs = [(x, y) for x, y in zip(arm, against) if x is not None and y is not None]
            differences = [x - y for x, y in pairs]
        else:
            others = ([Fraction(c["reference"]["values"][item])] if against is None
                      else [y for y in against if y is not None])
            differences = [x - y for x in arm if x is not None for y in others]
        margin = c["margin"]["abs"] if c["margin"] is not None else 0
        row = dict(input=item, n=len(pairs) if ratio else len(differences), n_missing=n_missing, estimate=None,
                   lo=None, hi=None, margin_value=margin, threshold=c["threshold"], outcome=None, sign=None,
                   reason=None, pairs=None)
        if not self.eligible(c, item):
            return void(row, "not_eligible")
        if n_missing:
            return missing_rule(c, row, None in arm)
        if row["n"] < (2 if ratio else 1):
            return void(row, "insufficient_replicates")
        if ratio:
            estimate, lo, hi = bootstrap(pairs, c["direction"] == "higher_better", self.rng,
                                         self.design["bootstrap_resamples"], c["confidence"])
        else:
            estimate, lo, hi = sum(differences, Fraction(0)) / len(differences), min(differences), max(differences)
        outcome, sign = decide(c, lo, hi, Fraction(margin))
        return {**row, "estimate": written(estimate), "lo": written(lo), "hi": written(hi), "outcome": outcome,
                "sign": sign}

    def score(self):
        comparisons = []
        for c in self.design["comparisons"]:
            units = [None] if c["unit"] == "pooled_mean" else self.inputs
            rows = [self.agreement(c, item) if c["criterion"] == "agreement" else self.metric(c, item) for item in units]
            outcomes = [row["outcome"] for row in rows]
            if c["unit"] == "pooled_mean":
                outcome = outcomes[0]
            elif c["unit"] == "per_input_each":
                outcome = "per_input"
            elif all(value == "supported" for value in outcomes):
                outcome = "supported"
            else:
                outcome = ("not_supported" if "not_supported" in outcomes else "void" if "void" in outcomes
                           else "inconclusive")
            self.results[c["id"]] = dict(unit=c["unit"], outcome=outcome,
                                         rows={row["input"]: row["outcome"] for row in rows})
            comparisons.append(dict(id=c["id"], arm=c["arm"], against=c["against"], criterion=c["criterion"],
                                    unit=c["unit"], outcome=outcome, rows=rows))
        outcomes = [row["outcome"] for comparison in comparisons for row in comparison["rows"]]
        totals = {key: outcomes.count(key) for key in ("supported", "not_supported", "inconclusive", "void")}
        return comparisons, totals


def main(argv):
    c_dir, root, harness, output = (Path(arg) for arg in argv)
    output.unlink(missing_ok=True)  # a failed run never leaves an earlier output in place
    data = (c_dir / "comparison.json").read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    stamp = strict((c_dir / "comparison_seal.json").read_text())
    if type(stamp) is not dict or stamp.get("comparison_sha256") != digest:
        raise ValueError("seal mismatch")
    record = strict(data)
    require(type(record) is dict and set(record) == {"source", "source_sha256", "design"})
    design = record["design"]
    check_design(design)
    files_raw, extract_raw = sealed_harness(c_dir, harness, design)
    files = check_files(strict(files_raw), design)
    rules = check_rules(strict(extract_raw), design)
    comparisons, totals = Scorer(design, files, rules, root).score()
    result = dict(comparison_sha256=digest, comparisons=comparisons, totals=totals)
    temporary = output.with_name(f"{output.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(json.dumps(result, allow_nan=False, indent=2) + "\n")
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("usage: score_comparison.py <C dir> <comparison dir> <harness dir> <comparison_scored.json>",
              file=sys.stderr)
        sys.exit(1)
    try:
        main(sys.argv[1:])
    except (OSError, ValueError, TypeError, KeyError, OverflowError, RecursionError, re.error):
        print("invalid comparison input, seal mismatch or output unavailable", file=sys.stderr)
        sys.exit(1)
