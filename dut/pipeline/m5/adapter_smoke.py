"""Run the baseline adapter once with the first sealed seed, without scoring."""
from pathlib import Path
import shutil
import signal
import subprocess
import sys

from eval_common import invocation, read


root = Path.cwd().resolve()
protocol_path = root / "adapter-payload" / "predictions.json"
protocol = read(protocol_path)
rule = protocol["paired_seed_tests"]
if rule.get("kind") == "paired_median":
    protocol = dict(protocol, paired_seed_tests=dict(rule, seeds=rule["seeds"][:1]))
work, out, environment, script = invocation(
    root, protocol, "baseline", "smoke", 0, mode="equivalence", protocol_path=protocol_path)
# boxrun owns the timeout; preserve outputs when its process group receives TERM.
signal.signal(signal.SIGTERM, lambda *_: sys.exit(124))
try:
    rc = subprocess.call(["bash", str(script)], cwd=work, env=environment)
finally:
    shutil.copytree(out, root / "out" / "adapter", dirs_exist_ok=True)
    shutil.rmtree(root / "evaluation-work" / "smoke")
    (root / "evaluation-work").rmdir()
sys.exit(rc)
