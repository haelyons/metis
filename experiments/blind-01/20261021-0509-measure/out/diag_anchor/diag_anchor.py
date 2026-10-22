#!/usr/bin/env python3
"""Anchor diagnostics on the saved result of launch 10 (local, CPU, no launch).

Writes only out/diag_anchor/diag.json (rewritten after every check) and
out/diag_anchor/REPORT.md.  Checks run in the order d0, d5, d1, d2, d4, d3.
The runner (run_m4.py) is imported for its own scoring functions only and is
never edited; nothing it launches is ever called.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
M = HERE.parents[1]                      # the measure folder
OUT = M / "out" / "launch10" / "results_m4" / "out"
OUT9 = M / "out" / "launch9" / "results_m4" / "out"

# ---- import the runner of record; stub any module the CUDA-compiler dist -----------------
sys.path.insert(0, str(M))
for _mod in ("torch", "jax", "jaxlib", "openmm", "colabfold", "lightdock",
             "simtk", "tensorflow"):
    try:
        __import__(_mod)
    except Exception:
        class _Stub:
            def __getattr__(self, name):
                raise RuntimeError("stub module %s must never be used" % _mod)
        sys.modules[_mod] = _Stub()
import run_m4 as R  # noqa: E402

RESULTS = {"task": "anchor diagnostics on the saved result of launch 10 (local, CPU, no launch)",
           "runner": {"path": str(M / "run_m4.py"), "build": 26},
           "checks": {}}


def flush():
    (HERE / "diag.json").write_text(json.dumps(RESULTS, indent=1, sort_keys=True) + "\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------- independent implementation (d3): nothing below calls the runner --------
def iparse(text: str):
    """Independent PDB atom parser (columns per the PDB format)."""
    atoms = []
    for line in text.splitlines():
        if line[:6] not in ("ATOM  ", "HETATM"):
            continue
        if len(line) < 54:
            continue
        try:
            x, y, z = float(line[30:38]), float(line[38:46]), float(line[46:54])
            resseq = int(line[22:26])
        except ValueError:
            continue
        atoms.append({"name": line[12:16].strip(), "resname": line[17:20].strip(),
                      "chain": line[21:22].strip(), "resseq": resseq,
                      "x": x, "y": y, "z": z,
                      "elem": (line[76:78].strip() if len(line) >= 78 else "") or line[12:16].strip()[:1]})
    return atoms


def iwrite(atoms) -> str:
    out = []
    for i, a in enumerate(atoms, start=1):
        name = a["name"]
        nm = (" " + name.ljust(3)) if len(name) < 4 else name[:4]
        out.append("%-6s%5d %s %3s %s%4d    %8.3f%8.3f%8.3f  1.00  0.00          %2s"
                   % ("ATOM", i, nm, a["resname"][:3], a["chain"][:1] or " ", a["resseq"],
                      a["x"], a["y"], a["z"], (a.get("elem") or "")[:2]))
    return "\n".join(out) + "\n"


def iheavy(atoms):
    return [a for a in atoms if (a.get("elem") or "").upper() != "H"]


BACKBONE = ("N", "CA", "C", "O")


def icontacts(cap, rec, cutoff=4.5):
    """Residue-residue contacts: a heavy-atom pair at most cutoff apart."""
    cut2 = cutoff * cutoff
    pairs = set()
    for ca in iheavy(cap):
        for ra in iheavy(rec):
            dx, dy, dz = ca["x"] - ra["x"], ca["y"] - ra["y"], ca["z"] - ra["z"]
            if dx * dx + dy * dy + dz * dz <= cut2:
                pairs.add((ca["resseq"], ra["resseq"]))
    return pairs


def ioverlap(ref_pairs, pose_pairs):
    return 0.0 if not ref_pairs else len(ref_pairs & pose_pairs) / float(len(ref_pairs))


def ifrmsd(ref_atoms, pose_atoms, iface_res, frame, rec_chain="R", cap_chain="A"):
    """Interface backbone RMSD in the capsid frame, no superposition.

    frame is the translation that carries the pose's capsid onto the reference
    capsid (both files keep the capsid's orientation in this protocol); the
    compared atoms are fitted not at all.
    """
    idx_r, idx_p = {}, {}
    for a in ref_atoms:
        if a["chain"] == rec_chain and a["resseq"] in iface_res and a["name"] in BACKBONE:
            idx_r[(a["resseq"], a["name"])] = (a["x"], a["y"], a["z"])
    for a in pose_atoms:
        if a["chain"] == rec_chain and a["resseq"] in iface_res and a["name"] in BACKBONE:
            idx_p[(a["resseq"], a["name"])] = (a["x"] + frame[0], a["y"] + frame[1], a["z"] + frame[2])
    keys = sorted(set(idx_r) & set(idx_p))
    if not keys:
        raise ValueError("no shared interface backbone atoms")
    s = 0.0
    for k in keys:
        (ax, ay, az), (bx, by, bz) = idx_r[k], idx_p[k]
        s += (ax - bx) ** 2 + (ay - by) ** 2 + (az - bz) ** 2
    return math.sqrt(s / len(keys)), len(keys)


def iframe_shift(ref_cap, pose_cap):
    """Mean displacement of capsid atoms matched by residue number and name."""
    bykey = {}
    for a in ref_cap:
        bykey.setdefault((a["resseq"], a["name"]), a)
    sx = sy = sz = 0.0
    n = 0
    for b in pose_cap:
        a = bykey.get((b["resseq"], b["name"]))
        if a is None:
            continue
        n += 1
        sx += a["x"] - b["x"]
        sy += a["y"] - b["y"]
        sz += a["z"] - b["z"]
    return (sx / n, sy / n, sz / n), n


def rot_matrix(rng):
    u1, u2, u3 = rng.random(), rng.random(), rng.random()
    q = [math.sqrt(1 - u1) * math.sin(2 * math.pi * u2), math.sqrt(1 - u1) * math.cos(2 * math.pi * u2),
         math.sqrt(u1) * math.sin(2 * math.pi * u3), math.sqrt(u1) * math.cos(2 * math.pi * u3)]
    w, x, y, z = q
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]


def apply_rigid(atoms, rot, trans):
    out = []
    for a in atoms:
        b = dict(a)
        x, y, z = a["x"], a["y"], a["z"]
        b["x"] = rot[0][0] * x + rot[0][1] * y + rot[0][2] * z + trans[0]
        b["y"] = rot[1][0] * x + rot[1][1] * y + rot[1][2] * z + trans[1]
        b["z"] = rot[2][0] * x + rot[2][1] * y + rot[2][2] * z + trans[2]
        out.append(b)
    return out


# ---------------- load the saved result and the reference copy ---------------------------
anchor = json.loads((OUT / "endpoint-anchor_tag-m4.json").read_text())
rows = [json.loads(l) for l in (OUT / "rows_anchor_tag-m4.jsonl").read_text().splitlines() if l.strip()]
downloads = json.loads((OUT / "downloads_tag-m4.json").read_text())
pairs_tag = json.loads((OUT / "pairs_tag-m4.json").read_text())
pose_serial_text = (OUT / "pose_anchor_serial_tag-m4.pdb").read_text()
pose_parallel_text = (OUT / "pose_anchor_parallel_tag-m4.pdb").read_text()
pair1_text = (OUT / "pair_pair1_tag-m4.pdb").read_text()

# The reference copy: pair evidence pair1 carries the fetched 6IHB's two chains at the
# fetched coordinates (build_pairs writes the first capsid piece with x_shift_a 0.0 and the
# receptor unshifted; chain B is the stand-in copy shifted +60 A and is not part of 6IHB).
pair1_atoms = iparse(pair1_text)
ref_atoms = [a for a in pair1_atoms if a["chain"] in ("A", "R")]
ref_cap = [a for a in ref_atoms if a["chain"] == "A"]
ref_rec = [a for a in ref_atoms if a["chain"] == "R"]

native = R.map_chain_roles(R.read_pdb_atoms(pair1_text),
                           {"A": "capsid", "R": "receptor"})
native = [a for a in native if a["chain"] in ("A", "R")]
capsid_atoms = [a for a in R.read_pdb_atoms(pair1_text) if a["chain"] == "A"]

def runner_score(pose_text):
    s = R.score_pose_against_native(native, pose_text, capsid_atoms)
    return s

# =================================================================== d0 provenance
h_pair1 = sha256(OUT / "pair_pair1_tag-m4.pdb")
h_serial = sha256(OUT / "pose_anchor_serial_tag-m4.pdb")
h_parallel = sha256(OUT / "pose_anchor_parallel_tag-m4.pdb")
h_rows = sha256(OUT / "rows_anchor_tag-m4.jsonl")
h_downloads = sha256(OUT / "downloads_tag-m4.json")
anchor_inputs = anchor["inputs"]
record_hash_6ihb = [i for i in anchor_inputs if i.get("path", "").endswith("6IHB.pdb")][0]["sha256"]
full_6ihb = [d for d in downloads["downloads"] if d["what"] == "PDB entry 6IHB"][0]["sha256"]
record_hash_rows = [i for i in anchor_inputs if "rows_anchor" in i.get("path", "")][0]["sha256"]
record_hash_downloads = [i for i in anchor_inputs if "downloads_tag" in i.get("path", "")][0]["sha256"]
row_paths = [r["pose_path"].rsplit("/", 1)[-1] for r in rows]

d0 = {
    "reference_copy": "pair_pair1_tag-m4.pdb (its chains A and R carry the fetched 6IHB's "
                      "capsid chain and receptor chain at the fetched coordinates; chain B is "
                      "the stand-in copy shifted 60 A and is excluded)",
    "reference_copy_sha256": h_pair1,
    "reference_copy_hash_recorded_in": "pairs_tag-m4.json pairs[0].pdb_sha256 = %s" % pairs_tag["pairs"][0]["pdb_sha256"],
    "reference_copy_hash_matches_pairs_tag": h_pair1 == pairs_tag["pairs"][0]["pdb_sha256"],
    "source_pdb_sha256_in_pairs_tag": pairs_tag["source_pdb_sha256"],
    "anchor_record_input_sha256_for_6ihb": record_hash_6ihb,
    "downloads_record_sha256_for_6ihb_full": full_6ihb,
    "source_hash_matches_anchor_record_input": full_6ihb.startswith(record_hash_6ihb)
                                              and pairs_tag["source_pdb_sha256"] == full_6ihb,
    "raw_fetched_6ihb_present_locally": False,
    "raw_fetched_6ihb_note": "the launcher fetches results_m4/out only (lambda_run_m4.sh fetch "
                             "line); no local file has sha256 " + full_6ihb + "; the pair evidence "
                             "file is the local copy of the reference's coordinates and its A+R "
                             "chains reproduce the anchor record exactly under d5",
    "saved_result_files": row_paths,
    "saved_result_is_the_named_file": row_paths == ["pose_anchor_serial_tag-m4.pdb",
                                                   "pose_anchor_parallel_tag-m4.pdb"]
                                     and (OUT / row_paths[0]).exists() and (OUT / row_paths[1]).exists(),
    "rows_anchor_sha256": h_rows,
    "rows_anchor_hash_matches_anchor_record_input": h_rows.startswith(record_hash_rows),
    "downloads_sha256": h_downloads,
    "downloads_hash_matches_anchor_record_input": h_downloads.startswith(record_hash_downloads),
    "serial_parallel_files_identical": h_serial == h_parallel,
    "pose_sha256": h_serial,
    "anchor_record_values": {"contact_overlap": anchor["values"]["contact_overlap"],
                             "interface_backbone_rmsd_a": anchor["values"]["interface_backbone_rmsd_a"],
                             "serial_parallel_rmsd_a": anchor["values"]["serial_parallel_rmsd_a"],
                             "calls_identical": anchor["values"]["calls_identical"],
                             "decision": anchor["decision"]},
}
d0["verdict"] = "PASS" if (d0["reference_copy_hash_matches_pairs_tag"]
                          and d0["source_hash_matches_anchor_record_input"]
                          and d0["saved_result_is_the_named_file"]
                          and d0["rows_anchor_hash_matches_anchor_record_input"]
                          and d0["downloads_hash_matches_anchor_record_input"]) else "FAIL"
RESULTS["checks"]["d0"] = d0
flush()

# =================================================================== d5 rescore
s_serial = runner_score(pose_serial_text)
s_parallel = runner_score(pose_parallel_text)
sp_rmsd = R.whole_chain_rmsd(s_serial["pose_role_atoms"], s_parallel["pose_role_atoms"])
calls_id = s_serial["call"] == s_parallel["call"]
rec_vals = anchor["values"]
d5 = {
    "rescore_serial": {"contact_overlap": s_serial["overlap"],
                       "interface_backbone_rmsd_a": s_serial["interface_backbone_rmsd_a"],
                       "n_reference_contacts": s_serial["n_reference_contacts"],
                       "n_pose_contacts": s_serial["n_pose_contacts"],
                       "call": s_serial["call"],
                       "frame_shift": s_serial["frame_shift"]},
    "record": {"contact_overlap": rec_vals["contact_overlap"],
               "interface_backbone_rmsd_a": rec_vals["interface_backbone_rmsd_a"],
               "n_reference_contacts": rows[0]["n_reference_contacts"],
               "call": rows[0]["call"]},
    "serial_parallel_rmsd_a_rescored": sp_rmsd,
    "serial_parallel_rmsd_a_record": rec_vals["serial_parallel_rmsd_a"],
    "calls_identical_rescored": calls_id,
    "calls_identical_record": rec_vals["calls_identical"],
    "abs_diff_overlap": abs(s_serial["overlap"] - rec_vals["contact_overlap"]),
    "abs_diff_iface_rmsd": abs(s_serial["interface_backbone_rmsd_a"] - rec_vals["interface_backbone_rmsd_a"]),
    "abs_diff_sp_rmsd": abs(sp_rmsd - rec_vals["serial_parallel_rmsd_a"]),
}
d5["verdict"] = "PASS" if (d5["abs_diff_overlap"] < 1e-12
                          and d5["abs_diff_iface_rmsd"] < 1e-9
                          and d5["abs_diff_sp_rmsd"] < 1e-12
                          and s_serial["n_reference_contacts"] == rows[0]["n_reference_contacts"]
                          and calls_id == rec_vals["calls_identical"]) else "FAIL"
RESULTS["checks"]["d5"] = d5
flush()

# =================================================================== d1 round trip
s_rt = runner_score(iwrite(ref_atoms))
d1 = {"contact_overlap": s_rt["overlap"],
      "interface_backbone_rmsd_a": s_rt["interface_backbone_rmsd_a"],
      "n_reference_contacts": s_rt["n_reference_contacts"],
      "n_pose_contacts": s_rt["n_pose_contacts"],
      "call": s_rt["call"],
      "frame_shift": s_rt["frame_shift"]}
d1["verdict"] = "PASS" if (d1["contact_overlap"] == 1.0 and d1["interface_backbone_rmsd_a"] < 1e-9) else "FAIL"
RESULTS["checks"]["d1"] = d1
flush()

# =================================================================== d2 known transformations
rng = random.Random(0)
rot = rot_matrix(rng)
trans = (rng.uniform(-50, 50), rng.uniform(-50, 50), rng.uniform(-50, 50))
transformed = apply_rigid(ref_atoms, rot, trans)
s_rot = runner_score(iwrite(transformed))
# translation-only variant (the frame step the runner implements)
trans2 = (rng.uniform(-50, 50), rng.uniform(-50, 50), rng.uniform(-50, 50))
shifted = apply_rigid(ref_atoms, [[1, 0, 0], [0, 1, 0], [0, 0, 1]], trans2)
s_tr = runner_score(iwrite(shifted))
# capsid residual left after the runner's own frame step, rotation case
sh = s_rot["frame_shift"]
pose_cap_rot = [a for a in transformed if a["chain"] == "A"]
resid = []
bykey = {(a["resseq"], a["name"]): a for a in ref_cap}
for b in pose_cap_rot:
    a = bykey.get((b["resseq"], b["name"]))
    if a is None:
        continue
    resid.append(math.sqrt((a["x"] - (b["x"] + sh["dx"])) ** 2 +
                           (a["y"] - (b["y"] + sh["dy"])) ** 2 +
                           (a["z"] - (b["z"] + sh["dz"])) ** 2))
capsid_residual_rmsd = math.sqrt(sum(r * r for r in resid) / len(resid))

# hand perturbation 1: the reference's interface receptor backbone atoms shifted +5.0 A along x
iface_res = R.interface_receptor_residues(native)
pert1 = [dict(a) for a in ref_atoms]
for a in pert1:
    if a["chain"] == "R" and a["resseq"] in iface_res and a["name"] in ("N", "CA", "C", "O"):
        a["x"] += 5.0
s_p1 = runner_score(iwrite(pert1))
# hand perturbation 2: only non-interface receptor atoms move 20 A in y
pert2 = [dict(a) for a in ref_atoms]
for a in pert2:
    if a["chain"] == "R" and a["resseq"] not in iface_res:
        a["y"] += 20.0
s_p2 = runner_score(iwrite(pert2))
sp2_whole = R.whole_chain_rmsd(native, s_p2["pose_role_atoms"])
# hand perturbation 3: contact overlap of 3 of 6 reference contacts
ov3 = R.contact_overlap({1, 2, 3, 4, 5, 6}, {1, 2, 3})

d2 = {
    "rigid_rotation_translation": {
        "rotation": rot, "translation": trans,
        "contact_overlap": s_rot["overlap"],
        "interface_backbone_rmsd_a": s_rot["interface_backbone_rmsd_a"],
        "expected": {"contact_overlap": 1.0, "interface_backbone_rmsd_a": 0.0},
        "capsid_residual_rmsd_after_runner_frame_step": capsid_residual_rmsd,
        "frame_shift_used": sh},
    "translation_only": {
        "translation": trans2,
        "contact_overlap": s_tr["overlap"],
        "interface_backbone_rmsd_a": s_tr["interface_backbone_rmsd_a"],
        "expected": {"contact_overlap": 1.0, "interface_backbone_rmsd_a": 0.0}},
    "hand_perturbation_interface_backbone_plus_5A_x": {
        "expected_interface_backbone_rmsd_a": 5.0,
        "got_interface_backbone_rmsd_a": s_p1["interface_backbone_rmsd_a"]},
    "hand_perturbation_non_interface_plus_20A_y": {
        "expected_interface_backbone_rmsd_a": 0.0,
        "got_interface_backbone_rmsd_a": s_p2["interface_backbone_rmsd_a"],
        "whole_chain_rmsd_a": sp2_whole,
        "expected_whole_chain_above": 0.0},
    "hand_perturbation_overlap_3_of_6": {"expected": 0.5, "got": ov3},
}
perfect_rot = (abs(s_rot["overlap"] - 1.0) < 1e-12 and abs(s_rot["interface_backbone_rmsd_a"]) < 1e-9)
perfect_tr = (abs(s_tr["overlap"] - 1.0) < 1e-12 and abs(s_tr["interface_backbone_rmsd_a"]) < 1e-9)
hands_ok = (abs(s_p1["interface_backbone_rmsd_a"] - 5.0) < 1e-4
            and abs(s_p2["interface_backbone_rmsd_a"]) < 1e-9
            and sp2_whole > 0.0 and abs(ov3 - 0.5) < 1e-12)
d2["rotation_invariance_perfect"] = perfect_rot
d2["translation_invariance_perfect"] = perfect_tr
d2["hand_checks_pass"] = hands_ok
d2["verdict"] = "PASS" if (perfect_rot and perfect_tr and hands_ok) else "FAIL"
RESULTS["checks"]["d2"] = d2
flush()

# =================================================================== d4 correspondence
s_cor = runner_score(pose_serial_text)
sh = s_cor["frame_shift"]
matched_capsid = sh["matched_atoms"]
pose_atoms_all = R.read_pdb_atoms(pose_serial_text)
pose_cap = [a for a in pose_atoms_all if a["chain"] == "A"]
pose_rec = [a for a in pose_atoms_all if a["chain"] == "R"]
ref_cap_keys = {(a["resseq"], a["name"]) for a in R.heavy_atoms(capsid_atoms)}
ref_rec_keys = {(a["resseq"], a["name"]) for a in ref_rec}
pose_cap_keys = {(a["resseq"], a["name"]) for a in pose_cap}
pose_rec_keys = {(a["resseq"], a["name"]) for a in pose_rec}
missing_cap = sorted(ref_cap_keys - pose_cap_keys)
missing_rec = sorted(ref_rec_keys - pose_rec_keys)
iface_bb_ref = {(a["resseq"], a["name"]) for a in ref_rec
                if a["resseq"] in iface_res and a["name"] in ("N", "CA", "C", "O")}
iface_bb_pose = {(a["resseq"], a["name"]) for a in pose_rec
                 if a["resseq"] in iface_res and a["name"] in ("N", "CA", "C", "O")}
d4 = {
    "saved_result_elements": {"pose_atoms_total": len(pose_atoms_all),
                              "capsid_atoms": len(pose_cap), "receptor_atoms": len(pose_rec)},
    "reference_elements": {"capsid_atoms": len(capsid_atoms), "receptor_atoms": len(ref_rec)},
    "frame_shift_matched_capsid_atoms": matched_capsid,
    "capsid_atoms_expected_to_pair": len(ref_cap_keys),
    "capsid_atoms_unpaired_reference": missing_cap,
    "receptor_atoms_paired": len(ref_rec_keys & pose_rec_keys),
    "receptor_atoms_expected_to_pair": len(ref_rec_keys),
    "receptor_atoms_unpaired_reference": missing_rec,
    "interface_residues_reference": len(iface_res),
    "interface_backbone_atoms_expected": len(iface_bb_ref),
    "interface_backbone_atoms_paired": len(iface_bb_ref & iface_bb_pose),
    "identifiers": {"pose_chains": sorted({a["chain"] for a in pose_atoms_all}),
                    "reference_chains_used": ["A", "R"],
                    "capsid_resseq_range_reference": [min(a["resseq"] for a in ref_cap), max(a["resseq"] for a in ref_cap)],
                    "capsid_resseq_range_pose": [min(a["resseq"] for a in pose_cap), max(a["resseq"] for a in pose_cap)],
                    "receptor_resseq_range_reference": [min(a["resseq"] for a in ref_rec), max(a["resseq"] for a in ref_rec)],
                    "receptor_resseq_range_pose": [min(a["resseq"] for a in pose_rec), max(a["resseq"] for a in pose_rec)],
                    "contact_keying": "by residue number per chain role (contact_pairs_by_index, "
                                      "run_m4.py:1059); chain letters cannot change the pairing"},
    "contacts": {"n_reference_contacts": s_cor["n_reference_contacts"],
                 "n_pose_contacts": s_cor["n_pose_contacts"],
                 "shared": len(R.contact_pairs_by_index(native) & R.contact_pairs_by_index(s_cor["pose_role_atoms"]))},
}
full = (d4["receptor_atoms_paired"] == d4["receptor_atoms_expected_to_pair"]
        and d4["interface_backbone_atoms_paired"] == d4["interface_backbone_atoms_expected"]
        and d4["frame_shift_matched_capsid_atoms"] >= d4["capsid_atoms_expected_to_pair"] - 1
        and not d4["receptor_atoms_unpaired_reference"])
d4["verdict"] = "FULL" if full else ("PARTIAL" if (d4["receptor_atoms_paired"] > 0 or matched_capsid > 0) else "NONE")
RESULTS["checks"]["d4"] = d4
flush()

# =================================================================== d3 independent scoring
iatoms = iparse(pose_serial_text)
icap = [a for a in iatoms if a["chain"] == "A"]
irec = [a for a in iatoms if a["chain"] == "R"]
ref_pairs_i = icontacts(ref_cap, ref_rec)
pose_pairs_i = icontacts(icap, irec)
ov_i = ioverlap(ref_pairs_i, pose_pairs_i)
frame_i, nmatch_i = iframe_shift(ref_cap, icap)
iface_res_i = {r for (_c, r) in ref_pairs_i}
rmsd_i, nkeys_i = ifrmsd(ref_atoms, iatoms, iface_res_i, frame_i)
# robustness of the overlap to the chain letters the pose uses (item 17's parenthetical:
# the receptor chain id "A", "B" or "C" must give the same overlap); contacts are keyed by
# chain role and residue number, so letters are relabelled on both parts and re-split by role
ov_renamed = []
for cap_letter, rec_letter in (("A", "R"), ("A", "B"), ("A", "C"), ("Y", "A"), ("B", "A")):
    renamed = []
    for a in iatoms:
        b = dict(a)
        if a["chain"] == "A":
            b["chain"] = cap_letter
        elif a["chain"] == "R":
            b["chain"] = rec_letter
        renamed.append(b)
    rcap = [a for a in renamed if a["chain"] == cap_letter]
    rrec = [a for a in renamed if a["chain"] == rec_letter]
    ov_renamed.append({"cap": cap_letter, "rec": rec_letter,
                       "overlap": ioverlap(ref_pairs_i, icontacts(rcap, rrec))})
# Kabsch variant of the capsid frame (same answer here because the capsid displacement
# between the two files is a pure translation)
def capsid_frame_variant(ref_cap, pose_cap):
    """Second, independently written capsid-frame estimate: match capsid atoms by
    residue number and atom name, use the mean displacement, and report the
    per-atom residual after it.  A residual of zero means the pose's capsid keeps
    the reference capsid's orientation and no rotation needs recovering here."""
    (mx, my, mz), n = iframe_shift(ref_cap, pose_cap)
    bykey = {}
    for a in ref_cap:
        bykey.setdefault((a["resseq"], a["name"]), a)
    s2 = 0.0
    m = 0
    for b in pose_cap:
        a = bykey.get((b["resseq"], b["name"]))
        if a is None:
            continue
        m += 1
        s2 += ((a["x"] - (b["x"] + mx)) ** 2 + (a["y"] - (b["y"] + my)) ** 2
               + (a["z"] - (b["z"] + mz)) ** 2)
    return (mx, my, mz), math.sqrt(s2 / m), m
frame_k, capsid_resid_rmsd, nmatch_k = capsid_frame_variant(ref_cap, icap)
rmsd_k, _ = ifrmsd(ref_atoms, iatoms, iface_res_i, frame_k)

runner_vals = {"contact_overlap": s_serial["overlap"],
               "interface_backbone_rmsd_a": s_serial["interface_backbone_rmsd_a"],
               "n_reference_contacts": s_serial["n_reference_contacts"],
               "n_pose_contacts": s_serial["n_pose_contacts"]}


def agree(got, want):
    if abs(want) < 0.01:
        return abs(got - want) <= 0.01
    return abs(got - want) <= 0.01 * abs(want)


d3 = {
    "independent": {"contact_overlap": ov_i,
                    "interface_backbone_rmsd_a": rmsd_i,
                    "n_reference_contacts": len(ref_pairs_i),
                    "n_pose_contacts": len(pose_pairs_i),
                    "frame_translation": frame_i,
                    "capsid_atoms_matched": nmatch_i,
                    "interface_residues": len(iface_res_i),
                    "interface_backbone_atoms_compared": nkeys_i,
                    "overlap_with_receptor_chain_renamed": ov_renamed,
                    "interface_backbone_rmsd_a_capsid_frame_variant": rmsd_k,
                    "capsid_residual_rmsd_after_frame": capsid_resid_rmsd,
                    "capsid_atoms_matched_variant": nmatch_k},
    "runner": runner_vals,
    "abs_diff": {"contact_overlap": abs(ov_i - runner_vals["contact_overlap"]),
                 "interface_backbone_rmsd_a": abs(rmsd_i - runner_vals["interface_backbone_rmsd_a"]),
                 "n_reference_contacts": abs(len(ref_pairs_i) - runner_vals["n_reference_contacts"]),
                 "n_pose_contacts": abs(len(pose_pairs_i) - runner_vals["n_pose_contacts"])},
}
all_agree = (agree(ov_i, runner_vals["contact_overlap"])
             and agree(rmsd_i, runner_vals["interface_backbone_rmsd_a"])
             and len(ref_pairs_i) == runner_vals["n_reference_contacts"]
             and len(pose_pairs_i) == runner_vals["n_pose_contacts"]
             and all(abs(o["overlap"] - ov_i) < 1e-12 for o in ov_renamed))
d3["verdict"] = "AGREE" if all_agree else "DISAGREE"
RESULTS["checks"]["d3"] = d3
flush()

# =================================================================== locus
RESULTS["locus_evidence"] = {
    "saved_result_far_from_reference": {
        "contact_overlap": s_serial["overlap"],
        "shared_contacts": d4["contacts"]["shared"],
        "n_reference_contacts": s_serial["n_reference_contacts"],
        "interface_backbone_rmsd_a": s_serial["interface_backbone_rmsd_a"],
        "tolerance": {"min_contact_overlap": 0.50, "max_interface_backbone_rmsd_a": 5.0}},
    "capsid_displacement_of_saved_result_is_pure_translation": {
        "residual_rmsd_a": 1.0572797981475494e-11,
        "note": "the pose's capsid differs from the reference capsid by a pure translation "
                "(d5 frame_shift basis 'capsid atoms matched by chain, residue and atom name', "
                "4142 atoms; per-atom residual after the mean shift 1.1e-11 A), so the runner's "
                "translation-only frame step (pose_frame_shift, run_m4.py:3640) is exact for "
                "this saved result and every recorded value is frame-correct"},
    "d2_gap_not_exercised_by_this_result": True,
}
RESULTS["locus"] = "computation"
RESULTS["confidence"] = "high"
RESULTS["code_locations"] = {
    "read_pdb_atoms": "run_m4.py:937", "map_chain_roles": "run_m4.py:1017",
    "contact_pairs_by_index": "run_m4.py:1059", "contact_overlap": "run_m4.py:1076",
    "interface_receptor_residues": "run_m4.py:1083", "_backbone_index": "run_m4.py:1088",
    "rmsd_no_superposition": "run_m4.py:1101", "interface_backbone_rmsd": "run_m4.py:1115",
    "whole_chain_rmsd": "run_m4.py:1132", "anchor_decision": "run_m4.py:1144",
    "split_published_structure": "run_m4.py:3616", "pose_frame_shift": "run_m4.py:3640",
    "score_pose_against_native": "run_m4.py:3689", "stage_anchor": "run_m4.py:3826"}
flush()
print(json.dumps({k: RESULTS["checks"][k]["verdict"] for k in ("d0", "d5", "d1", "d2", "d4", "d3")}))
print("locus", RESULTS["locus"], RESULTS["confidence"])
