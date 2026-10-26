import json, math, pathlib, re, sys

def parse(path, options, status):
    text = pathlib.Path(path).read_text(errors='replace')
    def number(label):
        matches = re.findall(r'^\s*' + label + r'\s*[:=]\s*([-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?)\s*$', text, re.I | re.M)
        if len(matches) != 1:
            raise RuntimeError('Missing, invalid or ambiguous output field: ' + label)
        v = float(matches[0])
        if not math.isfinite(v):
            raise RuntimeError('Nonfinite output field: ' + label)
        return v
    for label, expected in [(r'Number of GPUs', 1), (r'Total number of options', options), (r'Number of paths', 262144)]:
        if number(label) != expected:
            raise RuntimeError('Printed configuration differs from command/environment: '+label)
    for label, expected in [('Parallelization method', 'streamed'), ('Problem scaling', 'strong')]:
        values = re.findall(r'^\s*' + label + r'\s*=\s*(\S+)\s*$', text, re.M)
        if values != [expected]:
            raise RuntimeError('Printed configuration differs from command/environment: '+label)
    reserve = number(r'Average reserve')
    l1 = number(r'L1 norm')
    ms = number(r'Total time\s*\(ms\.\)')
    if ms <= 0 or reserve < 0 or l1 < 0:
        raise RuntimeError('Invalid measured output')
    verdict = re.findall(r'Test (passed|failed!)', text)
    if len(verdict) != 1:
        raise RuntimeError('Missing or ambiguous sample verdict')
    passed = int(verdict[0] == 'passed')
    if (status == 0) != bool(passed):
        raise RuntimeError('Exit status disagrees with printed verdict')
    # The verdict retains the strict predicate at the six-decimal boundary.
    if reserve == 1.0:
        reserve = math.nextafter(reserve, math.inf if passed else -math.inf)
    return {'mc-bs-reserve':reserve,'sample-pass':passed,'average_reserve':reserve,
            'l1_norm':l1,'total_time_ms':ms,'time_s':ms/1000,'exit_status':status}

if __name__ == '__main__':
    result = parse(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
    pathlib.Path(sys.argv[4]).write_text(json.dumps(result, allow_nan=False)+'\n')
