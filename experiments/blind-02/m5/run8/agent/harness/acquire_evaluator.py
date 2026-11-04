import hashlib
import io
import tarfile
import urllib.request
from pathlib import Path

pin = 'ebeb28a2f8411363cef722b7d293c978f7442672'
archive = Path('baseline-published/pinder.tar.gz')
if archive.exists():
    data = archive.read_bytes()
else:
    with urllib.request.urlopen('https://codeload.github.com/pinder-org/pinder/tar.gz/' + pin, timeout=180) as response:
        data = response.read()
if hashlib.sha256(data).hexdigest() != 'b577532820ebbe5c16432b78c5e9c197690e863cb70a0a35a8ebcbe5277b76dd':
    raise ValueError('PINDER source archive SHA-256 mismatch')
archive.write_bytes(data)
destination = Path('baseline-published/pinder-src')
destination.mkdir(exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as tf:
    for member in tf.getmembers():
        parts = Path(member.name).parts
        if not parts or parts[0] != 'pinder-' + pin or '..' in parts:
            raise ValueError('Unexpected source archive member')
        if len(parts) == 1:
            continue
        if member.issym() or member.islnk():
            raise ValueError('Unexpected source archive link')
        member.name = str(Path(*parts[1:]))
        tf.extract(member, destination)
