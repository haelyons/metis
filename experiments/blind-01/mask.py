#!/usr/bin/env python3
"""Masks a line for the blind operator: keeps only tokens from a fixed vocabulary (process and infrastructure words),
environment-variable-like names (case-sensitive upper case with underscores), numbers, launcher and run file names,
and paths under out/ or frozen/ whose basename is one of the operator's own files. Everything else becomes '…'.
usage: ... | python3 mask.py"""
import re, sys
VOCAB = set("""operator gate reviewer build builds review launch launches before after set keep unchanged stand stands line lines
header the a an and or to of in on at with for by is are if then else not no yes none selftest hash hashes sha256 re-run rerun run
verify compare declare declared env environment value values index package pin pins extra extras release version versions file files
read list first second once twice only same both instance type region price cap budget time timeout per hour usd box gpu capacity
cheapest single record recorded checks check exit code stop proceed may must shall write written listing network offline inputs uses
mismatch hand edit edits ruling fetch default forwarded forward every each into from that this it its as into""".split())
FILES = re.compile(r"^(lambda_run_\w+\.sh|remote_run_\w+\.sh|onbox_\w+\.sh|run_\w+\.py|pipeline\.js|triage_workflow\.js|provenance\.py|ONBOX_CONTRACT\.md|EXEC_NOTE\.md|GATE_COMMIT\.md|QUESTION\.md|CARD\.json|RUN\.md|frozen/(lambda_run\.sh|remote_run\.sh|provenance\.py|ONBOX_CONTRACT\.md)|out/(pip_pins_check_\w+\.txt|operator_findings_\w+\.txt|selftest_\w+\.log|review_\w+\.(md|json)|design_record\.json|\w+_return\.json))$")
ENV = re.compile(r"^[A-Z][A-Z0-9]*_[A-Z0-9_]*(=[\w.:/-]*)?$")   # case-sensitive; must contain an underscore (a bare acronym, with or without digits, is masked)
NUM = re.compile(r"^(USD\s*)?\$?\d[\d,.:]*[a-z%]{0,3}$")
TYPE = re.compile(r"^(gpu_[a-z0-9_]+|us-[a-z]+-\d|eu-[a-z]+-\d)$")
for line in sys.stdin:
    out = []
    for raw in line.split():
        t = raw.strip("`*\"'(),;:.")
        ok = t.lower() in VOCAB or FILES.match(t) or ENV.match(t) or NUM.match(t) or TYPE.match(t) or t == "OPERATOR:"
        out.append(t if ok else "…")
    print(" ".join(out))
