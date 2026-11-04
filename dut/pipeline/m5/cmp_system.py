#!/usr/bin/env python3
"""System record of a sealed comparison (U57): python3 profiler/cmp_system.py, from the shared run directory.

Reads out/comparison/versions.json and writes out/comparison/system.json; any field that cannot be read is null."""
import hashlib
import json
import os
import re
import subprocess


def output(argv):
    try:
        result = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.decode("utf-8", "replace") if result.returncode == 0 else None


def digest(path):
    try:
        value = hashlib.sha256()
        with open(path, "rb") as handle:
            for block in iter(lambda: handle.read(1 << 20), b""):
                value.update(block)
        return value.hexdigest()
    except (OSError, TypeError, ValueError):
        return None


def field(text, label):
    match = re.search(rf"^\s*{label}:\s*(.+?)\s*$", text or "", re.MULTILINE)
    return match.group(1) if match else None


def libraries(executable):
    text = output(["ldd", executable])
    if text is None or "statically linked" in text or "not a dynamic executable" in text:
        return []
    rows = []
    for line in text.splitlines():
        match = re.match(r"^\s*(\S+) => (/\S+)", line)
        if match:
            rows.append(dict(name=match.group(1), path=match.group(2), sha256=digest(os.path.realpath(match.group(2)))))
    return rows


def executable(entry):
    if not isinstance(entry, dict):
        return dict(version=None, executable=None, sha256=None, libraries=[])
    version, path = entry.get("version"), entry.get("executable")
    if not isinstance(path, str) or not path:
        return dict(version=version, executable=None, sha256=None, libraries=[])
    resolved = os.path.realpath(os.path.join(os.getcwd(), path))
    return dict(version=version, executable=path, sha256=digest(resolved), libraries=libraries(resolved))


def main():
    lscpu = output(["lscpu"])
    logical = field(lscpu, r"CPU\(s\)")
    smi = output(["nvidia-smi"])
    driver = re.search(r"Driver Version:\s*(\S+)", smi or "")
    cuda = re.search(r"CUDA Version:\s*(\S+)", smi or "")
    gpus = None
    query = output(["nvidia-smi", "--query-gpu=index,name,uuid,memory.total", "--format=csv,noheader"])
    if query is not None:
        gpus = []
        for line in query.splitlines():
            parts = [part.strip() for part in line.split(",")]
            if len(parts) == 4:
                gpus.append(dict(index=int(parts[0]) if parts[0].isdigit() else None, name=parts[1] or None,
                                 uuid=parts[2] or None, memory_total=parts[3] or None))
    executables = None
    try:
        with open("out/comparison/versions.json") as handle:
            versions = json.load(handle)
        if isinstance(versions, dict):
            executables = {key: executable(entry) for key, entry in versions.items()}
    except (OSError, ValueError, RecursionError):
        pass
    kernel = output(["uname", "-r"])
    record = dict(cpu_model=field(lscpu, "Model name"), cpu_logical=int(logical) if logical and logical.isdigit() else None,
                  kernel=kernel.strip() or None if kernel is not None else None,
                  driver_version=driver.group(1) if driver else None, cuda_version=cuda.group(1) if cuda else None,
                  gpus=gpus, executables=executables)
    os.makedirs("out/comparison", exist_ok=True)
    with open("out/comparison/system.json.tmp", "w") as handle:
        json.dump(record, handle, indent=2)
        handle.write("\n")
    os.replace("out/comparison/system.json.tmp", "out/comparison/system.json")


if __name__ == "__main__":
    main()
