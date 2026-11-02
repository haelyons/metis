#!/usr/bin/env python3
"""Unit test of check.py on a synthetic digest: the good digest passes every check, and each bad variant fails
exactly the check named beside it. Standard library only; runs the real marimo export (MARIMO, default "marimo").

Usage: MARIMO=<marimo binary> python3 -I dut/digest/tests/test_check.py
"""
import hashlib, json, os, shutil, subprocess, sys, tempfile

CHECK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "check.py")
PLAIN = "The method and the baseline ran on the same machine with the same inputs and the same settings as before."
NUM = "The method ran 4.2 times faster than the stock code on the full input of the published benchmark (evidence/data.json)."
HEADS = ["Question", "Answer", "Problem and constraints", "Method and assumptions", "Analysis"]
QUOTE = "The method ran 4.2 times faster than the stock code on the full input."
NOTEBOOK = '''import marimo

app = marimo.App(width="medium")

with app.setup:
    DIGEST_DIR = ""  # empty: this notebook's own directory
    import json
    from pathlib import Path
    import marimo as mo
    ROOT = Path(DIGEST_DIR) if DIGEST_DIR else mo.notebook_dir()


@app.cell
def _():
    data = json.loads((ROOT / "evidence" / "data.json").read_text())
    mo.ui.table([{"item": k, "value": v} for k, v in data.items()], selection=None)
    return (data,)


if __name__ == "__main__":
    app.run()
'''


def section(body):
    return "\n\n".join(f"## {h}\n\n{body}" for h in HEADS)


def make(d):
    os.makedirs(os.path.join(d, "evidence"))
    files = {"evidence/data.json": '{"speedup": 4.2, "baseline_ms": 120.5}\n', "evidence/notes.md": QUOTE + "\nA second line.\n",
             "evidence/run.py": "print('measure')\n"}
    for p, t in files.items():
        open(os.path.join(d, p), "w").write(t)
    open(os.path.join(d, "DIGEST.md"), "w").write("# Digest\n\n" + section(" ".join([PLAIN, NUM] * 3)) + "\n")
    open(os.path.join(d, "QA.md"), "w").write(
        "# Questions and answers\n\n## Q1. What number answers the question?\n\n"
        "The method ran 4.2 times faster than the stock code on 17 inputs (evidence/data.json). "
        "The method was 9.9 times faster on a second input (evidence/notes.md).\n\nSources: (evidence/data.json).\n\n"
        "Checked: 1 sentences supported, 1 contradicted, 0 not addressed.\n\n"
        f'Contradicted: The method was 9.9 times faster on a second input (evidence/notes.md).\n\nQuote (evidence/notes.md): "{QUOTE}"\n')
    json.dump({"summary": {"sentences": 2, "supported": 1, "contradicted": 1, "not_addressed": 0}, "sentences": [
        {"id": "S1", "question": "Q1", "sentence": "The method ran 4.2 times faster than the stock code on 17 inputs (evidence/data.json).",
         "verdict": "supported", "quote": QUOTE, "path": "evidence/notes.md", "reason": "states it"},
        {"id": "S2", "question": "Q1", "sentence": "The method was 9.9 times faster on a second input (evidence/notes.md).",
         "verdict": "contradicted", "quote": QUOTE, "path": "evidence/notes.md", "reason": "the file gives 4.2"}]},
        open(os.path.join(d, "VERIFY.json"), "w"))
    json.dump({"headline_kind": "speedup", "baseline_kind": "stock", "equivalence": "within_tolerance", "prediction_hit": "partly",
               "evidence": "measured", "anchor": "none"}, open(os.path.join(d, "digest.json"), "w"))
    json.dump({"run_name": "synthetic", "files": [{"original": p[9:], "copied": p, "bytes": len(t.encode()), "supports": "",
               "sha256": hashlib.sha256(t.encode()).hexdigest()} for p, t in files.items()]}, open(os.path.join(d, "MANIFEST.json"), "w"))
    open(os.path.join(d, "digest.py"), "w").write(NOTEBOOK)


def edit(name, old, new):
    def f(d):
        p = os.path.join(d, name)
        text = open(p).read()
        assert old in text, (name, old)
        open(p, "w").write(text.replace(old, new, 1))
    return f


def rewrite(name, fn):
    def f(d):
        p = os.path.join(d, name)
        text = fn(open(p).read())
        open(p, "w").write(text)
    return f


def enums(fn):
    return rewrite("digest.json", lambda t: json.dumps(fn(json.loads(t))))


def verified(fn):
    def f(d):
        v = json.load(open(os.path.join(d, "VERIFY.json")))
        fn(v["sentences"])
        json.dump(v, open(os.path.join(d, "VERIFY.json"), "w"))
    return f


CASES = [  # (name, mutation, the checks expected to fail)
    ("headings out of order", edit("DIGEST.md", "## Question\n", "## Answer\n"), ["headings"]),
    ("extra ## heading", edit("DIGEST.md", "## Analysis\n", "## Notes\n\n" + PLAIN + "\n\n## Analysis\n"), ["headings"]),
    ("missing heading", edit("DIGEST.md", "## Analysis\n", ""), ["headings"]),
    ("digest too short", rewrite("DIGEST.md", lambda t: "# Digest\n\n" + section(" ".join([PLAIN] * 3))), ["digest_words"]),
    ("digest too long", rewrite("DIGEST.md", lambda t: "# Digest\n\n" + section(" ".join([PLAIN, NUM] * 4))), ["digest_words"]),
    ("QA answer over 150 words", edit("QA.md", "\n\nSources:", " " + " ".join([PLAIN] * 8) + "\n\nSources:"), ["qa_answer_words"]),
    ("mean sentence too short", rewrite("DIGEST.md", lambda t: "# Digest\n\n" + section(" ".join(["The method and the baseline ran on the same machine."] * 12))), ["sentences"]),
    ("sentence over 45 words", edit("DIGEST.md", PLAIN, PLAIN[:-1] + " and then " + PLAIN[0].lower() + PLAIN[1:-1] + " and so on to the end."), ["sentences"]),
    ("bullet line", edit("DIGEST.md", "\n\n" + PLAIN, "\n\n- " + PLAIN), ["sentences"]),
    ("heading below ##", edit("DIGEST.md", "## Analysis\n\n", "## Analysis\n\n### Detail\n\n"), ["sentences"]),
    ("uncited number", edit("DIGEST.md", PLAIN, PLAIN.replace("the same machine", "17 machines")), ["numbers_cited"]),
    ("citation to a missing file", edit("QA.md", "(evidence/notes.md).\n\nSources", "(evidence/nothere.json).\n\nSources"), ["numbers_cited"]),
    ("digest number only in a contradicted sentence", edit("DIGEST.md", "ran 4.2 times", "ran 9.9 times"), ["digest_numbers_verified"]),
    ("digest number in no checked sentence", edit("DIGEST.md", "ran 4.2 times", "ran 7.7 times"), ["digest_numbers_verified"]),
    ("path outside the digest", edit("DIGEST.md", PLAIN, PLAIN[:-1] + ", as the notes in ../other/run say."), ["no_outside_paths"]),
    ("density gate: coined codes", edit("DIGEST.md", PLAIN, "The XQZT and PDQR and ZZTOP and QQRS and KKLM and WWXY and VVBN and HHJK codes ran on the same machine."), ["gate_density"]),
    ("scope gate: unscoped result", edit("DIGEST.md", PLAIN, "The CI of the method and the baseline overlaps on the same machine with the same inputs as before."), ["gate_scope"]),
    ("enum value not allowed", enums(lambda e: {**e, "prediction_hit": "maybe"}), ["enums"]),
    ("enum key extra", enums(lambda e: {**e, "mood": "good"}), ["enums"]),
    ("enum key missing", enums(lambda e: {k: v for k, v in e.items() if k != "anchor"}), ["enums"]),
    ("quote not verbatim", edit("QA.md", 'faster than the stock code on the full input."', 'faster than the tuned code on the full input."'), ["quotes_verbatim"]),
    ("verify quote not verbatim", verified(lambda ss: ss[0].update(quote="The method ran 5.0 times faster.")), ["quotes_verbatim"]),
    ("verify supported with no quote", verified(lambda ss: ss[0].update(quote="")), ["quotes_verbatim"]),
    ("manifest sha256 differs", rewrite("evidence/run.py", lambda t: t + "# edited after copying\n"), ["manifest"]),
    ("evidence file not in manifest", lambda d: open(os.path.join(d, "evidence/extra.txt"), "w").write("x\n"), ["manifest"]),
    ("manifest file missing", lambda d: os.remove(os.path.join(d, "evidence/run.py")), ["manifest"]),
    ("notebook imports a denied module", edit("digest.py", "    import json\n", "    import json\n    import subprocess\n"), ["notebook_imports"]),
    ("notebook absolute path", edit("digest.py", "    return (data,)", '    _p = "/home/someone/run/x.json"\n    return (data,)'), ["notebook_paths"]),
    ("notebook .. component", edit("digest.py", "    return (data,)", '    _p = ROOT / ".." / "x"\n    return (data,)'), ["notebook_paths"]),
    ("notebook cell raises", edit("digest.py", "    return (data,)", '    raise ValueError("planted")\n    return (data,)'), ["notebook_export"]),
]


def check(d, env=None):
    r = subprocess.run([sys.executable, "-I", CHECK, d], capture_output=True, text=True, env={**os.environ, **(env or {})})
    result = json.load(open(os.path.join(d, "CHECK.json")))
    return r.returncode, result


def main():
    root, fails = tempfile.mkdtemp(prefix="digest_check_"), 0
    good = os.path.join(root, "good")
    make(good)
    code, result = check(good)
    ok = code == 0 and result["pass"]
    print(f"{'ok  ' if ok else 'FAIL'} good digest passes every check ({len(result['checks'])} checks)" + ("" if ok else f": {result['failed']}"))
    fails += not ok
    sandbox = result["checks"]["notebook_export"]["detail"]["sandbox"]
    code, result = check(good, {"BWRAP": "/bin/false"})
    detail = result["checks"]["notebook_export"]["detail"]["sandbox"]
    ok = code == 0 and detail.startswith("none: bwrap refused")
    print(f"{'ok  ' if ok else 'FAIL'} export sandbox: {sandbox}; with a refusing bwrap the export falls back and says so: {detail[:70]}")
    fails += not ok
    for i, (name, mutate, want) in enumerate(CASES):
        d = os.path.join(root, f"case{i:02d}")
        shutil.copytree(good, d, ignore=shutil.ignore_patterns("CHECK.json", "digest.html"))
        mutate(d)
        code, result = check(d)
        ok = code == 1 and result["failed"] == want
        print(f"{'ok  ' if ok else 'FAIL'} {name}: fails {result['failed']}" + ("" if ok else f", wanted {want}"))
        fails += not ok
    shutil.rmtree(root)
    print(f"test_check: {len(CASES) + 2 - fails} of {len(CASES) + 2} as expected")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
