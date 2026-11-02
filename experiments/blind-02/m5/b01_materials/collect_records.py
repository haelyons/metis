"""Read the authorized blind-01 records; write only this materials directory."""
import csv
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
B01 = OUT.parent.parent.parent / "blind-01" / "m5"
HASHES = B01 / "intake_mirror/HASHES.tsv"
with HASHES.open(newline="") as f:
    hashes = {r["input"]: dict(r, source_record=f"blind-01/m5/intake_mirror/HASHES.tsv:{i}")
              for i, r in enumerate(csv.DictReader(f, delimiter="\t"), 2)}
with (B01 / "intake_check_codex/selected_cases.csv").open(newline="") as f:
    index = {r["id"]: dict(r, source_line=i) for i, r in enumerate(csv.DictReader(f), 2)}
units = json.loads((B01 / "run11/agent/harness/units.json").read_text())["units"]
probe = json.loads((B01 / "run11/agent/results/reproduce/out/concurrency/concurrency.json").read_text())
raw = (B01 / "run9/agent/results/reproduce/out/results/frodock_setup.csv").read_bytes().splitlines(keepends=True)
assert raw[0] == b"id,kind,receptor,ligand\n"
selected = [s["index"] for s in probe["sample"]]
assert selected == [3, 5, 9, 15]
unit_lines = [172, 284, 508, 844]
cases = []
needed = {"index.parquet", "metadata.parquet", "test_set_pdbs.zip",
          "pinder_source@ebeb28a2f8411363cef722b7d293c978f7442672",
          "frodock_distribution:unverified_mirror"}
roles = {k: ["run9 recorded source/environment material"] for k in needed}
for position, u in enumerate(selected):
    unit = units[u]
    pid, kind = unit["id"].rsplit(":", 1)
    row = next(csv.DictReader([raw[0].decode(), raw[u + 1].decode()]))
    assert row["id"] == pid and row["kind"] == kind == "apo"
    entry = index[pid]
    # These are the already-recorded entry paths, including default-API auxiliary
    # downloads. Auxiliary files are not additional docking cases or input choices.
    native = "pdbs/" + pid + ".pdb"
    primary = ["pdbs/" + entry["apo_R_pdb"], "pdbs/" + entry["apo_L_pdb"]]
    holo = ["test_set_pdbs/" + entry["holo_R_pdb"], "test_set_pdbs/" + entry["holo_L_pdb"]]
    names = {entry[k] for k in ("apo_R_pdb", "apo_L_pdb", "predicted_R_pdb", "predicted_L_pdb") if entry[k]}
    names.update(n for k in ("apo_R_pdbs", "apo_L_pdbs") for n in entry[k].split(";") if n)
    paths = {native, *holo, *("pdbs/" + n for n in names)}
    maps = {"mappings/" + n.replace(".pdb", ".parquet") for n in names if not n.startswith("af__")}
    maps.update("mappings/" + entry[k].replace(".pdb", ".parquet") for k in ("holo_R_pdb", "holo_L_pdb"))
    paths.update(maps)
    for p in sorted(paths):
        assert p in hashes, p
        needed.add(p)
        role = "reference native" if p == native else "primary apo source" if p in primary else "separated holo" if p in holo else "residue mapping" if p.startswith("mappings/") else "default-API auxiliary structure"
        roles.setdefault(p, []).append(f"{pid}: {role}")
    record = raw[0] + raw[u + 1]
    cases.append({"id": unit["id"], "system_id": pid, "kind": kind,
                  "manifest_index": u, "manifest_line": unit_lines[position],
                  "prepared_record_line": u + 2, "prepared_record": raw[u + 1].decode(),
                  "record_line_bytes": len(raw[u + 1]),
                  "record_line_sha256": hashlib.sha256(raw[u + 1]).hexdigest(),
                  "csv_bytes": len(record), "csv_sha256": hashlib.sha256(record).hexdigest(),
                  "index_record": entry, "native": native, "primary": primary,
                  "holo": holo, "entry_paths": sorted(paths)})
sample = raw[0] + b"".join(raw[u + 1] for u in selected)
assert len(sample) == 644
assert hashlib.sha256(sample).hexdigest() == "f34c87e11bc77f02997f41aaae17cf6958ce02976b9621886d96c03029b27af0"
reference = json.loads((B01 / "run11/agent/results/reproduce/units_reference.json").read_text())["sha256"]
assert set(reference) == {p for u in selected for p in units[u]["outputs"]}
assert len(reference) == 200
files = []
for key in sorted(needed):
    h = hashes[key]
    files.append({"input": key, "url": h["url"], "bytes": int(h["bytes"]),
                  "sha256": h["sha256"], "source_record": h["source_record"],
                  "provenance": "unverified_mirror" if key == "frodock_distribution:unverified_mirror" else "official_original_location",
                  "roles": roles[key]})
evidence = {"provenance_note": "FroDock distribution remains unverified_mirror.",
            "cases": cases, "files": files, "sample_csv": sample.decode(),
            "sample_csv_bytes": len(sample), "sample_csv_sha256": hashlib.sha256(sample).hexdigest(),
            "probe_reference_paths": len(reference),
            "probe_wrappers_match_origin": {name: (B01 / "run11/agent/harness" / name).read_bytes() == (B01 / "run10_harness3" / name).read_bytes()
                                            for name in ("units.json", "run_units.sh", "run_command.sh")}}
(OUT / "records.json").write_text(json.dumps(evidence, indent=2) + "\n")
print(json.dumps({"cases": [c["id"] for c in cases], "fetch_files": len(files), "sample_csv_sha256": evidence["sample_csv_sha256"], "wrapper_parity": evidence["probe_wrappers_match_origin"]}, indent=2))
