#!/usr/bin/env python3
"""Score a card's calibration inputs from the run's outputs (U54); exit 0/written, 1/invalid input."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys


ID = re.compile(r"[a-z][a-z0-9_]{0,30}")
PART = re.compile(r"[A-Za-z0-9._+=-]+")
POINTER = re.compile(r"(?:/(?:[^~/]|~[01])*)*")


def number(value):
    """A finite number: an integer too long for a double is not one."""
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(float(value))
    except OverflowError:
        return False


def sealed(file, seal, key):
    """Return the file's bytes and digest after checking them against the seal."""
    data = Path(file).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    stamp = json.loads(Path(seal).read_text())
    if type(stamp) is not dict or stamp.get(key) != digest:
        raise ValueError("seal mismatch")
    return data, digest


def has_anchor(record):
    anchor = record.get("anchor")
    return type(anchor) is dict and number(anchor.get("published_value"))


def check(card, extract):
    if type(card) is not dict or set(card) != {"source", "source_sha256", "record", "bands"}:
        raise ValueError("invalid card")
    record, bands = card["record"], card["bands"]
    required = record.get("required") if type(record) is dict else None
    if (type(required) is not list or not required or type(bands) is not dict
            or not all(type(item) is dict and type(item.get("id")) is str and ID.fullmatch(item["id"])
                       and item.get("basis") in ("GUESS", "PROXY") for item in required)
            or len({item["id"] for item in required}) != len(required)
            or not all(key in {item["id"] for item in required} and type(value) is dict and set(value) == {"abs"}
                       and number(value["abs"]) and value["abs"] > 0 for key, value in bands.items())):
        raise ValueError("invalid card")
    ids = [item["id"] for item in required] + (["anchor"] if has_anchor(record) else [])
    rules = extract.get("rules") if type(extract) is dict and set(extract) == {"rules"} else None
    if type(rules) is not list or len(rules) != len(ids):
        raise ValueError("invalid extract")
    for rule, ident in zip(rules, ids):
        if (type(rule) is not dict or set(rule) != {"id", "file", "kind", "expr"} or rule["id"] != ident
                or type(rule["file"]) is not str or type(rule["expr"]) is not str
                or not all(PART.fullmatch(part) and part not in (".", "..") for part in rule["file"].split("/"))):
            raise ValueError("invalid extract")
        if rule["kind"] == "json":
            if not POINTER.fullmatch(rule["expr"]):
                raise ValueError("invalid extract")
        elif rule["kind"] != "regex" or re.compile(rule["expr"]).groups != 1:
            raise ValueError("invalid extract")
    return record, bands, rules


def measure(rule, out):
    """Apply one extraction rule; anything unreadable or non-numeric is unmeasured."""
    try:
        file = Path(out) / rule["file"]
        if rule["kind"] == "json":
            value = json.loads(file.read_bytes())
            for token in rule["expr"].split("/")[1:]:
                token = token.replace("~1", "/").replace("~0", "~")
                if type(value) is dict:
                    value = value[token]
                elif type(value) is list and re.fullmatch(r"0|[1-9][0-9]*", token):
                    value = value[int(token)]
                else:
                    return None
            return value if number(value) else None
        matches = list(re.finditer(rule["expr"], file.read_bytes().decode("utf-8", errors="replace")))
        if not matches or matches[-1].group(1) is None:
            return None
        value = float(matches[-1].group(1))
        return value if math.isfinite(value) else None
    except (OSError, ValueError, KeyError, IndexError, TypeError, RecursionError, re.error):
        return None


def band(item, bands):
    """Return (band_source, lo, hi): launch or card absolute band, else multiplicative, else nulls."""
    value = item.get("value")
    if not number(value):
        return None, None, None
    own = item.get("band")
    absolute = bands.get(item["id"]) if item["id"] in bands else (
        own if type(own) is dict and set(own) == {"abs"} and number(own["abs"]) and own["abs"] > 0 else None)
    if absolute is not None:
        x = absolute["abs"]
        return ("launch" if item["id"] in bands else "card"), value - x, value + x
    k = 2.5 if item["basis"] == "PROXY" else 3
    if value > 0:
        return "multiplicative", value / k, value * k
    if value < 0:
        return "multiplicative", value * k, value / k
    return None, None, None


def row(item, rule, bands, out):
    measured = measure(rule, out)
    source, lo, hi = band(item, bands)
    if measured is None:
        verdict = "not_measured"
    elif source is None or not (number(lo) and number(hi)):
        source, lo, hi, verdict = None, None, None, "no_band"
    else:
        verdict = "within_band" if lo <= measured <= hi else "below_band" if measured < lo else "above_band"
    phase = item.get("phase")
    gate = phase.get("gate") if type(phase) is dict else None
    gate_passed = None
    if (type(gate) is dict and gate.get("on") == item["id"] and gate.get("op") in (">=", "<=")
            and number(gate.get("value")) and measured is not None):
        gate_passed = measured >= gate["value"] if gate["op"] == ">=" else measured <= gate["value"]
    if gate_passed is not None:
        decided_by, decision = "gate", "holds" if gate_passed else "refuted"
    elif verdict in ("within_band", "below_band", "above_band"):
        decided_by, decision = "band", "holds" if verdict == "within_band" else "refuted"
    else:
        decided_by, decision = None, "not_measured" if measured is None else "undecidable"
    return dict(id=item["id"], name=item.get("name"), unit=item.get("unit"), basis=item["basis"],
                value=item.get("value"), band_source=source, band_lo=lo, band_hi=hi, measured_value=measured,
                verdict=verdict, gate_passed=gate_passed, decided_by=decided_by, decision=decision,
                rule={key: rule[key] for key in ("file", "kind", "expr")})


def anchor_row(anchor, rule, out):
    published, tolerance = anchor["published_value"], anchor.get("tolerance")
    measured = measure(rule, out)
    difference = measured - published if measured is not None else None
    if difference is not None and not math.isfinite(difference):
        difference = None
    limit = None
    if number(tolerance) and tolerance >= 0:
        limit = tolerance
    elif type(tolerance) is dict and len(tolerance) == 1:
        (kind, amount), = tolerance.items()
        if kind in ("abs", "rel") and number(amount) and amount >= 0:
            limit = amount if kind == "abs" else amount * abs(published)
    passed = abs(difference) <= limit if difference is not None and limit is not None else None
    return dict(published_value=published, tolerance=tolerance, measured_value=measured,
                difference=difference, passed=passed)


def box():
    try:
        value = json.loads((Path(ARGS.control) / "box.json").read_text())
    except (OSError, ValueError):
        return None, None
    if type(value) is not dict:
        return None, None
    return value.get("type"), value.get("started_utc")


def main():
    control = Path(ARGS.control)
    output = control / "card_scored.json"
    output.unlink(missing_ok=True)  # a failed run never leaves an earlier output in place
    data, card_sha = sealed(control / "card.json", control / "card_seal.json", "card_sha256")
    raw, extract_sha = sealed(ARGS.extract, control / "card_extract_seal.json", "extract_sha256")
    record, bands, rules = check(json.loads(data), json.loads(raw))
    # rules belong to inputs by position; the anchor rule, when present, is the one after the last input
    required = record["required"]
    rows = [row(item, rule, bands, ARGS.out) for item, rule in zip(required, rules)]
    box_type, started = box()
    result = dict(key=record.get("key"), run=ARGS.run, pipeline_commit=None if ARGS.commit == "-" else ARGS.commit,
                  box_type=box_type, box_started_utc=started, card_sha256=card_sha, extract_sha256=extract_sha,
                  predictions=record.get("predictions"),
                  anchor=anchor_row(record["anchor"], rules[len(required)], ARGS.out)
                  if len(rules) > len(required) else None,
                  rows=rows, inputs_total=len(rows),
                  measured_total=sum(item["measured_value"] is not None for item in rows),
                  holds_total=sum(item["decision"] == "holds" for item in rows),
                  refuted_total=sum(item["decision"] == "refuted" for item in rows))
    temporary = output.with_name(f"{output.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(json.dumps(result, allow_nan=False, indent=2) + "\n")
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(1, "invalid command arguments\n")


if __name__ == "__main__":
    parser = Parser(description=__doc__)
    parser.add_argument("control")
    parser.add_argument("extract")
    parser.add_argument("out")
    parser.add_argument("--run", required=True)
    parser.add_argument("--commit", required=True)
    ARGS = parser.parse_args()
    try:
        main()
    except (OSError, ValueError, TypeError, KeyError, OverflowError, RecursionError, re.error):
        print("invalid card input, seal mismatch or output unavailable", file=sys.stderr)
        sys.exit(1)
