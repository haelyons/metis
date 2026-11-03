"""Content hashes for the implementation boundary; usable locally or via python -I."""
import hashlib
import json
import os
import stat
import sys


def digest(root):
    rows = []

    def visit(directory, relative=""):
        for name in sorted(os.listdir(directory)):
            file = os.path.join(directory, name)
            label = relative + name
            mode = os.lstat(file).st_mode
            if stat.S_ISLNK(mode):
                rows.append([label, "link", stat.S_IMODE(mode), os.readlink(file)])
            elif stat.S_ISDIR(mode):
                rows.append([label, "directory", stat.S_IMODE(mode)])
                visit(file, label + "/")
            elif stat.S_ISREG(mode):
                sha = hashlib.sha256()
                with open(file, "rb") as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b""):
                        sha.update(block)
                rows.append([label, "file", stat.S_IMODE(mode), sha.hexdigest()])
            else:
                raise ValueError("unsupported file")

    if os.path.islink(root) or not os.path.isdir(root):
        raise ValueError("invalid tree")
    visit(root)
    payload = json.dumps(rows, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


if __name__ == "__main__":
    try:
        # Arguments are key/path pairs; stdout contains only the digest object.
        if len(sys.argv) < 3 or len(sys.argv) % 2 != 1:
            raise ValueError("invalid arguments")
        print(json.dumps({sys.argv[i]: digest(sys.argv[i + 1]) for i in range(1, len(sys.argv), 2)}))
    except (OSError, ValueError):
        print("implementation state unavailable", file=sys.stderr)
        sys.exit(1)
