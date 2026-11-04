#!/usr/bin/env python3
"""Trusted wrapper of one sealed-comparison invocation (U57): python3 profiler/cmp_wrap.py i<k>.

Run from the shared run directory. Reads comparison-jobs/i<k>.json (the job) and comparison-jobs/i<k>.run.json (the
arm's commands and env, the input's spec, whether the design has an evaluator, and the time left in budget_s), builds
comparison-work/i<k>/, runs the arm part as cmp-arm and then the evaluator part as cmp-eval, and writes wrap.json last."""
import hashlib
import json
import math
import os
import pwd
import re
import shutil
import stat
import subprocess
import sys
import threading
import time

LINKED_NOT = {"out", "profiler", "concurrency-work", "evaluation-work", "units-check", "comparison-work",
              "comparison-jobs", "cmp-private"}
ARM, EVAL = "cmp-arm", "cmp-eval"
QUIET = dict(stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def sudo(*argv):
    return subprocess.run(["sudo", "-n", *argv], **QUIET).returncode


def digest(path):
    try:
        value = hashlib.sha256()
        with open(path, "rb") as handle:
            for block in iter(lambda: handle.read(1 << 20), b""):
                value.update(block)
        return value.hexdigest()
    except OSError:
        return None


def pointer(value, expr):
    for token in expr.split("/")[1:]:
        token = token.replace("~1", "/").replace("~0", "~")
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def substitute(text, values, spec):
    """{input}, {run}, {out} and {spec:<pointer>}; {{ and }} are literal braces. One pass, never repeated."""
    parts, index = [], 0
    while index < len(text):
        if text.startswith("{{", index) or text.startswith("}}", index):
            parts.append(text[index])
            index += 2
        elif text[index] == "{":
            end = text.index("}", index)
            token = text[index + 1:end]
            if token.startswith("spec:"):
                found = pointer(spec, token[5:])
                parts.append(found if isinstance(found, str) else json.dumps(found))
            else:
                parts.append(values[token])
            index = end + 1
        else:
            parts.append(text[index])
            index += 1
    return "".join(parts)


class Sampler:
    """GPU-busy seconds: nvidia-smi immediately and every second; each valid sample adds utilization / 100."""

    def __init__(self):
        self.busy, self.known, self.stop = 0.0, False, threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        while True:
            try:
                text = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                                      stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                      timeout=5).stdout.decode("utf-8", "replace")
            except (OSError, subprocess.SubprocessError):
                text = ""
            for line in text.splitlines():
                try:
                    value = float(line.strip())
                except ValueError:
                    continue
                if math.isfinite(value) and 0 <= value <= 100:
                    self.busy += value / 100
                    self.known = True
            if self.stop.wait(1):
                return

    def finish(self):
        self.stop.set()
        self.thread.join()
        return self.busy, self.known


class Invocation:
    def __init__(self, token):
        self.started = time.monotonic()
        self.shared = os.getcwd()
        with open(os.path.join("comparison-jobs", f"{token}.json")) as handle:
            self.job = json.load(handle)
        with open(os.path.join("comparison-jobs", f"{token}.run.json")) as handle:
            self.plan = json.load(handle)
        self.deadline = self.started + self.plan["budget_left_s"]
        # Every part ends by left_s after the wrapper started.
        self.limit = self.started + self.job["left_s"]
        self.directory = os.path.join(self.shared, "comparison-work", token)
        self.paths = {name: os.path.join(self.directory, name) for name in ("run", "out", "log", "eval", "home", "ehome")}
        # The wrapper's environment without any CMP_, SUDO_ or HOME name.
        self.base = {key: value for key, value in os.environ.items()
                     if not key.startswith(("CMP_", "SUDO_")) and key != "HOME"}

    def build(self):
        os.makedirs(os.path.dirname(self.directory), exist_ok=True)
        os.chmod(os.path.dirname(self.directory), 0o711)
        if os.path.lexists(self.directory):
            sudo("rm", "-rf", "--", self.directory)
        os.mkdir(self.directory)
        os.chmod(self.directory, 0o711)
        for name, mode in (("run", 0o755), ("out", 0o755), ("log", 0o700), ("eval", 0o700), ("home", 0o700),
                           ("ehome", 0o700)):
            os.mkdir(self.paths[name])
            os.chmod(self.paths[name], mode)
        for name in sorted(os.listdir(self.shared)):
            if name not in LINKED_NOT:
                os.symlink(os.path.join(self.shared, name), os.path.join(self.paths["run"], name))
        sudo("chown", "-R", "-h", f"{ARM}:", self.paths["run"], self.paths["out"], self.paths["home"])
        if self.plan["evaluator"]:
            sudo("chown", f"{EVAL}:", self.paths["eval"], self.paths["ehome"])

    def kill(self, user):
        """Kill every process of the user once per second until none is left, for at most the time left in budget_s."""
        while True:
            sudo("pkill", "-KILL", "-u", user)
            if subprocess.run(["pgrep", "-u", user], **QUIET).returncode != 0:
                return True
            if time.monotonic() + 1 > self.deadline:
                return False
            time.sleep(1)

    def cleanup(self, user):
        """Cleanup after a part user; never deletes or changes anything in the shared run directory."""
        left = self.kill(user)
        try:
            with open(os.path.join("profiler", "cmp_writable.json")) as handle:
                listed = json.load(handle)[user]
        except (OSError, ValueError, KeyError, TypeError):
            listed = []
        escaped = re.sub(r"([*?\[\\])", r"\\\1", self.shared)
        for item in listed:
            if not any(item != other and item.startswith(other.rstrip("/") + "/") for other in listed):
                sudo("find", item, "-mindepth", "1", "-user", user, "!", "-path", escaped, "!", "-path", f"{escaped}/*",
                     "-delete")
        uid = pwd.getpwnam(user).pw_uid
        for flag in ("-m", "-q", "-s"):
            # Listed as root (util-linux creators/owners format), so every object of the namespace is seen.
            try:
                listing = subprocess.run(["sudo", "-n", "ipcs", flag, "-c"], stdin=subprocess.DEVNULL,
                                         stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True).stdout
            except OSError:
                continue
            column = None
            for row in (line.split() for line in listing.splitlines()):
                if "uid" in row:
                    column = row.index("uid")
                elif column is not None and len(row) > column and row[0].isdigit() and row[column] in (user, str(uid)):
                    sudo("ipcrm", flag, row[0])
        return left

    def process(self, user, argv, cwd, env, name, end):
        """One process of a part: (rc, wall_s, timed out); rc is None on a timeout."""
        command = ["sudo", "-n", "-u", user, "--", "env", "-i", "-C", cwd,
                   *(f"{key}={value}" for key, value in env.items()), *argv]
        log = self.paths["log"]
        with open(os.path.join(log, f"{name}.stdout"), "wb") as out, open(os.path.join(log, f"{name}.stderr"), "wb") as err:
            start = time.perf_counter()
            try:
                child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=out, stderr=err, start_new_session=True)
            except OSError as error:
                return 127 if isinstance(error, FileNotFoundError) else 126, time.perf_counter() - start, False
            try:
                rc = child.wait(timeout=max(0.0, end - time.monotonic()))
            except subprocess.TimeoutExpired:
                # Every process of the part user, as in cleanup.
                self.kill(user)
                wall = time.perf_counter() - start
                try:
                    child.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    pass
                return None, wall, True
            return (rc if rc >= 0 else 128 - rc), time.perf_counter() - start, False

    def resolve(self, program, env):
        """The resolved executable path and its SHA-256, or None for both."""
        if "/" in program:
            found = os.path.join(self.paths["run"], program)
        else:
            found = shutil.which(program, path=env.get("PATH", os.defpath))
        if found is None:
            return None, None
        found = os.path.realpath(found)
        return (found, digest(found)) if os.path.isfile(found) else (None, None)

    def arm_part(self):
        job, plan = self.job, self.plan
        spec = plan["spec"]
        end = min(time.monotonic() + job["arm_timeout_s"], self.limit)
        variables = {**self.base, "HOME": self.paths["home"], "CMP_INPUT": job["input"],
                     "CMP_INPUT_SPEC": json.dumps(spec), "CMP_OUT": self.paths["out"]}
        values = {"input": job["input"], "run": self.paths["run"], "out": self.paths["out"]}
        sampler = Sampler()
        rc, wall, timed = self.process(ARM, ["bash", f"harness/arms/{job['arm']}.sh"], self.paths["run"], variables,
                                       "adapter", end)
        record = dict(adapter_rc=rc, adapter_wall_s=wall, commands=[])
        status = "timeout" if timed else "ok" if rc == 0 else "failed"
        if status == "ok":
            env = dict(variables)
            for key, value in (plan["env"] or {}).items():
                env[key] = substitute(value, values, spec)
            env.update({key: variables[key] for key in ("HOME", "CMP_INPUT", "CMP_INPUT_SPEC", "CMP_OUT")})
            for index, command in enumerate(plan["commands"], 1):
                argv = [substitute(part, values, spec) for part in command]
                executable, sha256 = self.resolve(argv[0], env)
                rc, wall, timed = self.process(ARM, argv, self.paths["run"], env, f"cmd{index}", end)
                record["commands"].append(dict(argv=argv, rc=rc, wall_s=wall, executable=executable, sha256=sha256))
                if timed or rc != 0:
                    status = "timeout" if timed else "failed"
                    break
        record["gpu_busy_s"], record["gpu_busy_known"] = sampler.finish()
        return status, record

    def after_arm(self, status):
        """Clean up after cmp-arm and hand run/ and out/ to the box user; any failure here makes the invocation invalid."""
        failed = []
        if not self.cleanup(ARM):
            failed.append("processes")
        sudo("rm", "-rf", "--", self.paths["home"])
        if sudo("chown", "-R", "-h", f"{os.getuid()}:{os.getgid()}", self.paths["run"], self.paths["out"]) != 0:
            failed.append("chown")
        # Owner access to everything under out/, whatever modes the arm left (chmod -R fixes a directory before reading
        # it, and never follows a link).
        if subprocess.run(["chmod", "-R", "u+rwX", "--", self.paths["out"]], **QUIET).returncode != 0:
            failed.append("chmod")
        try:
            os.chmod(self.paths["run"], 0o700)
            for root, dirs, names in os.walk(self.paths["out"], onerror=lambda error: failed.append("walk")):
                for name in dirs + names:
                    mode = os.lstat(os.path.join(root, name)).st_mode
                    if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
                        failed.append("type")
        except OSError:
            failed.append("check")
        if subprocess.run(["chmod", "-R", "go-w,o+rX", "--", self.paths["out"]], **QUIET).returncode != 0:
            failed.append("modes")
        return "invalid" if failed else status

    def evaluator_part(self):
        job = self.job
        if self.limit - time.monotonic() < 1:
            # Less than 1 s of left_s: the evaluator part is not run.
            return True, dict(eval_status="timeout", eval_rc=None, eval_wall_s=None, eval_gpu_busy_s=None,
                              eval_gpu_busy_known=False)
        variables = {**self.base, "HOME": self.paths["ehome"], "CMP_INPUT": job["input"],
                     "CMP_INPUT_SPEC": json.dumps(self.plan["spec"]), "CMP_ARM_OUT": self.paths["out"],
                     "CMP_EVAL_OUT": self.paths["eval"], "CMP_PRIVATE": os.path.join(self.shared, "cmp-private")}
        sampler = Sampler()
        rc, wall, timed = self.process(EVAL, ["bash", os.path.join(self.shared, "harness", "evaluate.sh")], self.shared,
                                       variables, "evaluator", min(time.monotonic() + job["eval_timeout_s"], self.limit))
        busy, known = sampler.finish()
        left = self.cleanup(EVAL)
        sudo("rm", "-rf", "--", self.paths["ehome"])
        sudo("chown", "-R", "-h", f"{os.getuid()}:{os.getgid()}", self.paths["eval"])
        return left, dict(eval_status="timeout" if timed else "ok" if rc == 0 else "failed", eval_rc=rc, eval_wall_s=wall,
                          eval_gpu_busy_s=busy, eval_gpu_busy_known=known)

    def run(self):
        self.build()
        status, record = self.arm_part()
        status = self.after_arm(status)
        evaluation = dict(eval_status="skipped", eval_rc=None, eval_wall_s=None, eval_gpu_busy_s=None,
                          eval_gpu_busy_known=False)
        if self.plan["evaluator"] and status == "ok":
            left, evaluation = self.evaluator_part()
            if not left:
                status = "invalid"
        # No later part reads this invocation's files; wrap.json is written atomically and last.
        os.chmod(self.directory, 0o700)
        wrap = dict(status=status, **record, **evaluation)
        temporary = os.path.join(self.directory, "wrap.json.tmp")
        handle = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(handle, "w") as out:
            json.dump(wrap, out, indent=2)
            out.write("\n")
        os.replace(temporary, os.path.join(self.directory, "wrap.json"))


if __name__ == "__main__":
    if len(sys.argv) != 2 or not re.fullmatch(r"i[1-9][0-9]*", sys.argv[1]):
        print("usage: cmp_wrap.py i<k>", file=sys.stderr)
        sys.exit(2)
    Invocation(sys.argv[1]).run()
