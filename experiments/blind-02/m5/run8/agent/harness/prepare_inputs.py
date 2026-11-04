import hashlib
import json
import urllib.request
from pathlib import Path


def checked_download(spec, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        contents = path.read_bytes()
    else:
        with urllib.request.urlopen(spec['url'], timeout=120) as response:
            contents = response.read()
    if len(contents) != spec['bytes'] or hashlib.sha256(contents).hexdigest() != spec['sha256']:
        raise ValueError('Invalid source bytes/hash: ' + spec['name'])
    path.write_bytes(contents)
    return contents


def main():
    inputs = json.loads(Path('harness/inputs.json').read_text())
    hashes = {}
    for item in inputs:
        spec = item['spec']
        for role, chain in [('receptor', b'R'), ('ligand', b'L')]:
            source = spec[role + '_source']
            original = checked_download(source, Path('data/sources') / source['name'])
            lines = []
            for line in original.splitlines(keepends=True):
                if line[:6] in (b'ATOM  ', b'HETATM', b'ANISOU', b'TER   '):
                    if len(line.rstrip(b'\r\n')) < 22:
                        raise ValueError('Short chain-bearing record')
                    line = line[:21] + chain + line[22:]
                lines.append(line)
            prepared = b''.join(lines)
            destination = Path(spec['prepared'][role])
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(prepared)
            hashes[str(destination)] = hashlib.sha256(prepared).hexdigest()
    Path('out/setup/prepared_sha256.json').write_text(json.dumps(hashes, indent=2) + '\n')


if __name__ == '__main__':
    main()
