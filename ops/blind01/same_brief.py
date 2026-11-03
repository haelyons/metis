import hashlib, json, sys
X = "/home/hal/dev/interp/metis/experiments/blind-" + sys.argv[1] + "/science"
h = lambda st: hashlib.sha256(open(f"{X}/{st}/" + json.load(open(f"{X}/{st}/NEXT.json"))["brief"], "rb").read()).hexdigest()
a, b = h(sys.argv[2]), h(sys.argv[3])
print("identical", a == b, a[:12], b[:12])
