#!/usr/bin/env python3
"""The mechanical checks on one digest directory (dut/digest/README.txt, CHECKS). Standard library only.

Usage: python3 -I check.py <digest dir>            every check; writes CHECK.json and digest.html; exit 1 on a failure
       python3 -I check.py --export <digest dir>   the sandboxed marimo export only; prints its output; its exit code
Env: MARIMO (the marimo binary, default "marimo"); DIGEST_GATES (the latent_skeptic gate directory);
     BWRAP (default /usr/bin/bwrap; the export runs inside it, and falls back to no sandbox only if bwrap refuses).
"""
import ast, hashlib, importlib.util, json, os, re, shutil, subprocess, sys

sys.dont_write_bytecode = True   # the gate modules live in a submodule: leave no __pycache__ there
HEADINGS = ["Question", "Answer", "Problem and constraints", "Method and assumptions", "Analysis"]
ENUMS = {   # keep in step with pipeline.js
    "headline_kind": ["speedup", "negative", "void", "partial", "unknown"],
    "baseline_kind": ["stock", "tuned", "one_thread", "cpu_library", "other", "unknown"],
    "equivalence": ["bit_identical", "within_tolerance", "not_checked", "failed", "unknown"],
    "prediction_hit": ["yes", "partly", "no", "not_sealed", "unknown"],
    "evidence": ["measured", "inferred", "unknown"],
    "anchor": ["measured", "page_value_only", "not_run", "none", "unknown"],
}
CITE = re.compile(r"\(evidence/[^()\s]+\)")
EVPATH = re.compile(r"\(?evidence/[^()\s]+\)?")   # a citation or a bare evidence/ path: its digits are not numbers
NUMBER = re.compile(r"\d+(?:[.,]\d+)*")
SPLIT = re.compile(r"(?<=[.!?])\s+")   # the sentence rule of gate_scope.py
LIST = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s")
QUOTE = re.compile(r'^Quote \((evidence/[^()\s]+)\): "(.*)"\s*$')
NOTE = ("Sources:", "Checked:", "Contradicted:", "Not addressed:", "Quote")   # QA.md lines the script adds under an answer
OUTSIDE = re.compile(r"(?:^|[\s(`\"'])(?:\.\./|~/|/(?:home|tmp|root|Users|mnt|data|var|etc|opt|usr)/)")
DOTDOT = re.compile(r"(?:^|[/\\])\.\.(?:[/\\]|$)")
ABS = re.compile(r"^(?:/[\w.~-]|~[/\\]|[A-Za-z]:[\\/])|(?<![\w.])/(?:home|tmp|root|Users|mnt|data|var|etc|opt|usr|proc|dev)/")
DENIED = {"subprocess", "socket", "urllib", "http", "shutil", "ctypes", "multiprocessing", "ftplib", "smtplib"}
HERE = os.path.dirname(os.path.abspath(__file__))
GATES = os.environ.get("DIGEST_GATES") or os.path.join(HERE, "..", "latent_skeptic", "compositions", "gates")


def paragraphs(text):
    """Paragraphs that are not headings, each joined into one line."""
    out, cur = [], []
    for line in text.splitlines() + [""]:
        if line.strip() and not line.startswith("#"):
            cur.append(line.strip())
        elif cur:
            out.append(" ".join(cur))
            cur = []
    return out


def sentences(text):
    return [s for p in paragraphs(text) for s in SPLIT.split(p) if s.strip()]


def words(s):
    return len(CITE.sub(" ", s).split())


def numbers(s):
    return {n.replace(",", "") for n in NUMBER.findall(EVPATH.sub(" ", s))}


def flat(s):
    return " ".join(s.replace("*", "").replace("`", "").split())   # whitespace and markdown emphasis do not count


def gate(name):
    spec = importlib.util.spec_from_file_location("digest_" + name, os.path.join(GATES, name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def export(d):
    """marimo export inside bwrap: / read-only, the digest read-write, no network, a fresh /tmp."""
    d, marimo, bwrap = os.path.realpath(d), os.environ.get("MARIMO", "marimo"), os.environ.get("BWRAP", "/usr/bin/bwrap")
    cmd = [marimo, "export", "html", "digest.py", "-o", "digest.html", "-f"]
    jail = [bwrap, "--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc", "--tmpfs", "/tmp", "--bind", d, d,
            "--unshare-net", "--die-with-parent", "--chdir", d]
    cache, sandbox = os.path.join(d, "__marimo__"), "bwrap"
    fresh = not os.path.exists(cache)
    probe = subprocess.run(jail + ["/bin/true"], capture_output=True, text=True) if os.path.exists(bwrap) else None
    if probe is None or probe.returncode != 0:
        why = "not found" if probe is None else f"exit {probe.returncode}" + (f": {probe.stderr.strip()[:200]}" if probe.stderr.strip() else "")
        sandbox = f"none: bwrap refused ({why}); export ran unsandboxed"
        jail = []
    r = subprocess.run(jail + cmd, cwd=d, capture_output=True, text=True, timeout=600)
    if fresh and os.path.isdir(cache):
        shutil.rmtree(cache)   # the export's session cache is not part of the digest
    return r, sandbox


def run(d):
    text = lambda n: open(os.path.join(d, n), encoding="utf-8").read() if os.path.isfile(os.path.join(d, n)) else ""
    digest, qa, checks = text("DIGEST.md"), text("QA.md"), {}

    def check(name, fn):
        try:
            ok, detail = fn()
        except Exception as e:
            ok, detail = False, f"{type(e).__name__}: {e}"
        checks[name] = {"pass": bool(ok), "detail": detail}

    def headings():
        found = [l[3:].strip() for l in digest.splitlines() if l.startswith("## ")]
        return found == HEADINGS, found

    def digest_words():
        n = sum(words(p) for p in paragraphs(digest))
        return 500 <= n <= 700, n

    def qa_answer_words():
        blocks, head, n = [], None, 0
        for p in [l for l in qa.split("\n\n")] + ["#"]:
            p = p.strip()
            if p.startswith("#"):
                if head:
                    blocks.append((head, n))
                head, n, note = (p if re.match(r"^#{2,3} ", p) else None), 0, False
            elif head and not note:
                note = p.startswith(NOTE)
                n += 0 if note else words(p)
        over = [b for b in blocks if b[1] > 150]
        return bool(blocks) and not over, {"answers": len(blocks), "over_150": over}

    def sentence_rule():
        lens = [words(s) for s in sentences(digest)]
        mean = sum(lens) / len(lens) if lens else 0
        lists = [l for l in digest.splitlines() if LIST.match(l)]
        deep = [l for l in digest.splitlines() if re.match(r"^#{3,}\s", l)]
        long = [n for n in lens if n > 45]
        return 14 <= mean <= 26 and not long and not lists and not deep, {
            "sentences": len(lens), "mean": round(mean, 1), "over_45": long, "list_lines": lists[:5], "deep_headings": deep[:5]}

    def numbers_cited():
        uncited, missing = [], []
        for name, body in (("DIGEST.md", digest), ("QA.md", qa)):
            for c in CITE.findall(body):
                rel = c[1:-1]
                if ".." in rel.split("/") or not os.path.isfile(os.path.join(d, rel)):
                    missing.append(rel)
            claims = "\n\n".join(p for p in paragraphs(body) if not p.startswith("Checked:"))   # the check tally is not a claim
            uncited += [f"{name}: {s[:120]}" for s in sentences(claims) if re.search(r"\d", CITE.sub(" ", s)) and not CITE.search(s)]
        return bool(digest) and not uncited and not missing, {"uncited": uncited[:10], "missing": sorted(set(missing))[:10]}

    def digest_numbers_verified():
        v = json.loads(text("VERIFY.json"))
        ok = set().union(*[numbers(s["sentence"]) for s in v["sentences"] if s["verdict"] == "supported"])
        unverified = sorted(set().union(*[numbers(p) for p in paragraphs(digest)]) - ok)
        return bool(digest) and not unverified, {"supported_numbers": len(ok), "not_in_a_supported_sentence": unverified[:20]}

    def no_outside_paths():
        hits = [f"{n}: {l[:120]}" for n, body in (("DIGEST.md", digest), ("QA.md", qa)) for l in body.splitlines() if OUTSIDE.search(CITE.sub(" ", l))]
        return not hits, hits[:10]

    def gate_density():
        g = gate("gate_density")
        density, n, w = g.density(CITE.sub(" ", "\n\n".join(paragraphs(digest))))
        return density <= g.THRESHOLD, {"codes_per_1000_words": round(density, 1), "codes": n, "words": w, "threshold": g.THRESHOLD}

    def gate_scope():
        g = gate("gate_scope")
        g.MARKERS = re.compile(g.MARKERS.pattern + r"|\(evidence/[^()\s]+\)", re.I)   # a digest scopes a number by its citation
        v = g.violations("\n\n".join(paragraphs(digest)))
        return not v, {"unscoped_sentences": len(v), "first": [s[:120] for s in v[:5]]}

    def enums():
        e = json.loads(text("digest.json"))
        bad = {k: e.get(k) for k in ENUMS if e.get(k) not in ENUMS[k]}
        extra = sorted(set(e) - set(ENUMS))
        return not bad and not extra, {"bad": bad, "extra": extra}

    def quotes_verbatim():
        quotes = [(m[1], m[2], "QA.md") for m in map(QUOTE.match, qa.splitlines()) if m]
        for s in json.loads(text("VERIFY.json"))["sentences"]:
            if s["verdict"] != "not_addressed":
                quotes.append((s["path"], s["quote"], s["id"]))
        bad = [f"{where}: {path} {q[:80]!r}" for path, q, where in quotes
               if not flat(q) or not path.startswith("evidence/") or flat(q) not in flat(text(path))]
        return not bad, {"quotes": len(quotes), "not_found_or_empty": bad[:10]}

    source = text("digest.py")

    def notebook_imports():
        allowed, bad = set(sys.stdlib_module_names) | {"marimo"}, []
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                mods = [node.module or ""] if node.level == 0 else ["." * node.level]
            elif isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", "")) in ("__import__", "import_module"):
                mods = ["<dynamic import>"]
            else:
                continue
            bad += [m for m in mods if m.split(".")[0] not in allowed or m.split(".")[0] in DENIED]
        return bool(source) and not bad, bad

    def notebook_paths():
        bad = [n.value[:80] for n in ast.walk(ast.parse(source)) if isinstance(n, ast.Constant) and isinstance(n.value, str)
               and any(DOTDOT.search(line) or ABS.search(line) for line in n.value.splitlines() or [""])]
        return not bad, bad[:10]

    def manifest():
        m = json.loads(text("MANIFEST.json"))
        listed, bad = set(), []
        for f in m["files"]:
            p = f["copied"]
            listed.add(p)
            full = os.path.join(d, p)
            if not p.startswith("evidence/") or ".." in p.split("/") or not os.path.isfile(full):
                bad.append(f"{p}: missing or outside evidence/")
                continue
            data = open(full, "rb").read()
            if hashlib.sha256(data).hexdigest() != f["sha256"] or len(data) != f["bytes"]:
                bad.append(f"{p}: sha256 or bytes differ")
        on_disk = {os.path.relpath(os.path.join(r, n), d).replace(os.sep, "/") for r, _, ns in os.walk(os.path.join(d, "evidence")) for n in ns}
        unlisted = sorted(on_disk - listed)
        return bool(listed) and not bad and not unlisted, {"files": len(listed), "bad": bad[:10], "unlisted": unlisted[:10]}

    def notebook_export():
        r, sandbox = export(d)
        tail = (r.stderr or r.stdout).strip().splitlines()[-3:]
        return r.returncode == 0 and os.path.isfile(os.path.join(d, "digest.html")), {"exit": r.returncode, "sandbox": sandbox, "tail": tail}

    for name, fn in [("headings", headings), ("digest_words", digest_words), ("qa_answer_words", qa_answer_words),
                     ("sentences", sentence_rule), ("numbers_cited", numbers_cited), ("digest_numbers_verified", digest_numbers_verified),
                     ("no_outside_paths", no_outside_paths), ("gate_density", gate_density), ("gate_scope", gate_scope),
                     ("enums", enums), ("quotes_verbatim", quotes_verbatim), ("manifest", manifest),
                     ("notebook_imports", notebook_imports), ("notebook_paths", notebook_paths), ("notebook_export", notebook_export)]:
        check(name, fn)
    failed = [k for k, v in checks.items() if not v["pass"]]
    return {"pass": not failed, "failed": failed, "checks": checks}


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--export" and os.path.isdir(sys.argv[2]):
        r, sandbox = export(sys.argv[2])
        print(f"sandbox: {sandbox}\n{r.stdout}{r.stderr}".rstrip())
        sys.exit(r.returncode)
    if len(sys.argv) != 2 or not os.path.isdir(sys.argv[1]):
        sys.exit(__doc__)
    result = run(sys.argv[1])
    with open(os.path.join(sys.argv[1], "CHECK.json"), "w") as f:
        json.dump(result, f, indent=1)
        f.write("\n")
    for name, c in result["checks"].items():
        print(f"{'ok  ' if c['pass'] else 'FAIL'} {name}: {json.dumps(c['detail'])[:200]}")
    print("PASS" if result["pass"] else "FAIL: " + ", ".join(result["failed"]))
    sys.exit(0 if result["pass"] else 1)
