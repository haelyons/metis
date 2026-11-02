"""Pipe-test the blind guard: old guard vs new on blind-01 calls (must agree), new guard on blind-02 calls."""
import json, subprocess, sys

OLD, NEW = sys.argv[1], sys.argv[2]
E = "/home/hal/dev/interp/metis/experiments"


def deny(guard, tool, cwd="/home/hal/dev/interp/metis", **inp):
    out = subprocess.run(["python3", guard], input=json.dumps({"tool_name": tool, "tool_input": inp, "cwd": cwd}),
                         capture_output=True, text=True).stdout
    return bool(out.strip())


def cases(b):
    return [
        ("Read", dict(file_path=f"{E}/{b}/m5/BRIEF.md"), True),
        ("Read", dict(file_path=f"{E}/{b}/m5/predictions/run1.md"), False),
        ("Read", dict(file_path=f"{E}/{b}/m5/run1/operator/OPERATOR_TAKEAWAY.md"), False),
        ("Read", dict(file_path=f"{E}/{b}/m5/run1/agent/intake/brief.md"), True),
        ("Write", dict(file_path=f"{E}/{b}/m5/predictions/run1.md"), False),
        ("Write", dict(file_path=f"{E}/{b}/m5/BRIEF.md"), True),
        ("Edit", dict(file_path=f"{E}/{b}/m5/run1/args.json"), True),
        ("Grep", dict(pattern="x", path=f"{E}/{b}"), True),
        ("Grep", dict(pattern="x", path=E), True),
        ("Grep", dict(pattern="x", path="/home/hal/dev/interp"), True),
        ("Grep", dict(pattern="x", path="/home/hal/dev/interp/metis/dut/pipeline"), False),
        ("Glob", dict(pattern=f"**/{b}/**", path="/home/hal/dev/interp/metis/dut"), True),
        ("Bash", dict(command=f"cat {E}/{b}/m5/BRIEF.md"), True),
        ("Bash", dict(command=f"ls {E}/{b}/m5"), True),
        ("Bash", dict(command=f"python3 ~/.cache/blind01/blind_read.py {E}/{b}/m5/run3"), False),
        ("Bash", dict(command=f"python3 ~/.cache/blind01/blind_read.py {E}/{b}/m5/run3 | head"), True),
        ("Bash", dict(command=f"python3 ~/.cache/blind01/new_run.py {E}/{b}/m5/run2"), False),
        ("Bash", dict(command=f"python3 ~/.cache/blind01/new_run.py {E}/{b}/m5/run2 --units-probe=run1"), False),
        ("Bash", dict(command=f"bash ~/.cache/blind01/retry48.sh {E}/{b}/m5/run2 \"{b} m5 run2\""), False),
        ("Bash", dict(command=f"bash ~/.cache/blind01/retry48.sh {E}/{b}/m5/run2 \"x\"; cat {E}/{b}/m5/BRIEF.md"), True),
        ("Bash", dict(command=f"cd /home/hal/dev/interp/metis && git add experiments/{b}/m5/predictions/run2.md"), False),
        ("Bash", dict(command=f"cd /home/hal/dev/interp/metis && git add experiments/{b}/m5/BRIEF.md"), True),
        ("Bash", dict(command=f"git commit -m \"{b} m5 run2 predictions\""), False),
        ("Bash", dict(command="ls", cwd=f"{E}/{b}/m5"), True),
        ("Bash", dict(command="ls experiments/"), False),
    ]


bad = 0
for tool, inp, want in cases("blind-01"):
    o, n = deny(OLD, tool, **inp), deny(NEW, tool, **inp)
    if o != n or n != want:
        bad += 1; print("blind-01 MISMATCH", tool, inp, "old", o, "new", n, "want", want)
for b in ("blind-02", "blind-07"):
    for tool, inp, want in cases(b):
        n = deny(NEW, tool, **inp)
        if n != want:
            bad += 1; print(b, "WRONG", tool, inp, "new", n, "want", want)
for tool, inp, want in [("Read", dict(file_path=f"{E}/blind-openmm/m5/BRIEF.md"), False),
                        ("Read", dict(file_path=f"{E}/shakedown-m5/BRIEF.md"), False),
                        ("Bash", dict(command="echo blind-02"), True)]:  # bare name outside an allowlisted command: denied, as before
    if deny(NEW, tool, **inp) != want:
        bad += 1; print("OTHER WRONG", tool, inp)
print("FAILURES", bad)
