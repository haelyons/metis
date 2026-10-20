#!/usr/bin/env python3
"""Generate strict LOPLS-AA-style LAMMPS inputs from a SMILES string.

This is intentionally conservative. Unsupported atom environments or missing
bonded terms raise a ParameterError instead of falling back to guessed values.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

try:
    from rdkit import Chem
    from rdkit.Chem import AllChem, Descriptors
except ImportError as exc:  # pragma: no cover - exercised by users without RDKit
    raise SystemExit("RDKit is required. Install rdkit before running this script.") from exc


KJ_TO_KCAL = 0.23900573614
AVOGADRO = 6.02214076e23


class ParameterError(RuntimeError):
    """Raised when strict LOPLS-AA assignment cannot continue."""


@dataclass(frozen=True)
class AtomParam:
    key: str
    label: str
    element: str
    mass: float
    charge: float
    sigma: float
    epsilon: float
    source: str


@dataclass(frozen=True)
class BondParam:
    key: tuple[str, str]
    k: float
    r0: float
    source: str


@dataclass(frozen=True)
class AngleParam:
    key: tuple[str, str, str]
    k: float
    theta0: float
    source: str


@dataclass(frozen=True)
class DihedralParam:
    key: tuple[str, str, str, str]
    style: str
    coeffs: tuple[float, ...]
    source: str


@dataclass
class Topology:
    mol: Chem.Mol
    atom_types: list[str]
    atom_params: list[AtomParam]
    bonds: list[tuple[int, int, BondParam]]
    angles: list[tuple[int, int, int, AngleParam]]
    dihedrals: list[tuple[int, int, int, int, DihedralParam]]
    shake_bonds: list[tuple[int, int]]


ATOM_PARAMS: dict[str, AtomParam] = {
    # L-OPLS hydrocarbon nonbonded terms, sigma in A, epsilon in kcal/mol.
    "CT_CH3": AtomParam("CT_CH3", "ctt", "C", 12.011, -0.222, 3.50, 0.066000, "L-OPLS hydrocarbons"),
    "CT_CH2": AtomParam("CT_CH2", "ct", "C", 12.011, -0.148, 3.50, 0.066000, "L-OPLS hydrocarbons"),
    "CT_CH": AtomParam("CT_CH", "cth", "C", 12.011, -0.074, 3.50, 0.066000, "L-OPLS hydrocarbons"),
    "CT_C": AtomParam("CT_C", "ctq", "C", 12.011, 0.000, 3.50, 0.066000, "L-OPLS hydrocarbons"),
    "HC_CH3": AtomParam("HC_CH3", "hct", "H", 1.008, 0.074, 2.50, 0.030000, "L-OPLS hydrocarbons"),
    "HC_CH2": AtomParam("HC_CH2", "hc", "H", 1.008, 0.074, 2.50, 0.026303, "L-OPLS hydrocarbons"),
    "HC_CH": AtomParam("HC_CH", "hch", "H", 1.008, 0.074, 2.50, 0.026303, "L-OPLS hydrocarbons"),
    "CM_CH2": AtomParam("CM_CH2", "cm2", "C", 12.011, -0.230, 3.55, 0.076000, "OPLS/2020 alkene"),
    "CM_CH": AtomParam("CM_CH", "cm", "C", 12.011, -0.160, 3.55, 0.076000, "L-OPLS hydrocarbons"),
    "CM_C": AtomParam("CM_C", "cmq", "C", 12.011, 0.000, 3.55, 0.076000, "L-OPLS hydrocarbons"),
    "HC_ALKENE": AtomParam("HC_ALKENE", "hcm", "H", 1.008, 0.160, 2.42, 0.030000, "L-OPLS hydrocarbons"),
    "HC_ALKENE_TERMINAL": AtomParam("HC_ALKENE_TERMINAL", "hcm2", "H", 1.008, 0.115, 2.42, 0.030000, "OPLS/2020 alkene"),
    # Ester extension.
    "C_ESTER": AtomParam("C_ESTER", "c2", "C", 12.011, 0.750, 3.1875, 0.105000, "LOPLS ester extension"),
    "O_ESTER_CARBONYL": AtomParam("O_ESTER_CARBONYL", "o2", "O", 15.999, -0.550, 3.1080, 0.168000, "LOPLS ester extension"),
    "O_ESTER_ALKOXY": AtomParam("O_ESTER_ALKOXY", "os", "O", 15.999, -0.450, 2.5500, 0.170000, "LOPLS ester extension"),
    "CT_ALKOXY": AtomParam("CT_ALKOXY", "ctos", "C", 12.011, 0.190, 3.50, 0.066000, "LOPLS ester extension"),
    "CT_ALKOXY_METHYL": AtomParam("CT_ALKOXY_METHYL", "ctosm", "C", 12.011, 0.160, 3.50, 0.066000, "LOPLS ester extension methyl ester neutralization"),
    "HC_ALPHA_ETHER": AtomParam("HC_ALPHA_ETHER", "hos", "H", 1.008, 0.030, 2.42, 0.015000, "LOPLS ester extension"),
    # Aliphatic ether OPLS/2020 terms from BOSS oplsaa.par atom types 180-185.
    "OS_ETHER": AtomParam("OS_ETHER", "osr", "O", 15.999, -0.400, 2.900, 0.120000, "OPLS/2020 ether nonbonded"),
    "CT_ETHER_METHYL": AtomParam("CT_ETHER_METHYL", "ctom", "C", 12.011, 0.110, 3.50, 0.066000, "OPLS/2020 ether nonbonded"),
    "CT_ETHER_CH2": AtomParam("CT_ETHER_CH2", "cto2", "C", 12.011, 0.140, 3.50, 0.066000, "OPLS/2020 ether nonbonded"),
    "CT_ETHER_CH": AtomParam("CT_ETHER_CH", "cto1", "C", 12.011, 0.170, 3.50, 0.066000, "OPLS/2020 ether nonbonded"),
    "CT_ETHER_C": AtomParam("CT_ETHER_C", "cto0", "C", 12.011, 0.200, 3.50, 0.066000, "OPLS/2020 ether nonbonded"),
    "HC_ETHER_ALPHA": AtomParam("HC_ETHER_ALPHA", "hco", "H", 1.008, 0.030, 2.48, 0.026000, "OPLS/2020 ether nonbonded"),
    # Simple OPLS/2020 benzene-like aromatic terms.
    "CA_AROM": AtomParam("CA_AROM", "ca", "C", 12.011, -0.115, 3.55, 0.068000, "OPLS/2020 aromatics"),
    "CA_AROM_SUB": AtomParam("CA_AROM_SUB", "cas", "C", 12.011, 0.000, 3.55, 0.068000, "OPLS/2020 aromatics"),
    "HA_AROM": AtomParam("HA_AROM", "ha", "H", 1.008, 0.115, 2.42, 0.030000, "OPLS/2020 aromatics"),
}


def _sorted2(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted((a, b)))


def _angle_key(a: str, b: str, c: str) -> tuple[str, str, str]:
    return min((a, b, c), (c, b, a))


def _dihedral_key(a: str, b: str, c: str, d: str) -> tuple[str, str, str, str]:
    return min((a, b, c, d), (d, c, b, a))


def rb_to_multi_harmonic(c0: float, c1: float, c2: float, c3: float, c4: float = 0.0) -> tuple[float, ...]:
    """Convert RB kJ/mol coefficients to LAMMPS multi/harmonic kcal/mol.

    LAMMPS uses cos(phi) with a trans reference opposite to the RB convention
    used in the papers/GROMACS, so odd terms change sign. This reproduces the
    supplied Squalane CT-CT-CT-CT coefficient line.
    """

    return tuple(round(x * KJ_TO_KCAL, 8) for x in (c0, -c1, c2, -c3, c4))


BOND_PARAMS: dict[tuple[str, str], BondParam] = {}
ANGLE_PARAMS: dict[tuple[str, str, str], AngleParam] = {}
DIHEDRAL_PARAMS: dict[tuple[str, str, str, str], DihedralParam] = {}
LAMMPS_TYPE_ALIASES = {
    "CT_CH": "CT_CH2",
    "HC_CH": "HC_CH2",
}


def lammps_type_alias(type_key: str) -> str:
    return LAMMPS_TYPE_ALIASES.get(type_key, type_key)


def atom_type_record(param: AtomParam) -> tuple[str, str, float, float, float]:
    aliased = ATOM_PARAMS[lammps_type_alias(param.key)]
    return (aliased.label, aliased.element, aliased.mass, aliased.sigma, aliased.epsilon)


def bond_type_record(param: BondParam) -> tuple[tuple[str, str], float, float]:
    a, b = (lammps_type_alias(x) for x in param.key)
    return (_sorted2(a, b), param.k, param.r0)


def angle_type_record(type_keys: tuple[str, str, str], param: AngleParam) -> tuple[tuple[str, str, str], float, float]:
    a, b, c = (lammps_type_alias(x) for x in type_keys)
    return ((a, b, c), param.k, param.theta0)


def dihedral_type_record(type_keys: tuple[str, str, str, str], param: DihedralParam) -> tuple[tuple[str, str, str, str], str, tuple[float, ...]]:
    return (_dihedral_key(*type_keys), param.style, param.coeffs)


def _add_bond(a: str, b: str, k: float, r0: float, source: str = "OPLS-AA bonded") -> None:
    BOND_PARAMS[_sorted2(a, b)] = BondParam(_sorted2(a, b), k, r0, source)


def _add_angle(a: str, b: str, c: str, k: float, theta0: float, source: str = "OPLS-AA bonded") -> None:
    ANGLE_PARAMS[_angle_key(a, b, c)] = AngleParam(_angle_key(a, b, c), k, theta0, source)


def _add_dihedral(
    a: str,
    b: str,
    c: str,
    d: str,
    coeffs: Sequence[float],
    source: str,
    style: str = "multi/harmonic",
    overwrite: bool = True,
) -> None:
    key = _dihedral_key(a, b, c, d)
    if not overwrite and key in DIHEDRAL_PARAMS:
        return
    DIHEDRAL_PARAMS[key] = DihedralParam(key, style, tuple(coeffs), source)


def _init_params() -> None:
    ether_carbons = ["CT_ETHER_METHYL", "CT_ETHER_CH2", "CT_ETHER_CH", "CT_ETHER_C"]
    carbon_sp3 = [
        "CT_CH3",
        "CT_CH2",
        "CT_CH",
        "CT_C",
        "CT_ALKOXY",
        "CT_ALKOXY_METHYL",
    ] + ether_carbons
    carbon_sp2 = ["CM_CH2", "CM_CH", "CM_C"]
    hydrogens = ["HC_CH3", "HC_CH2", "HC_CH", "HC_ALPHA_ETHER", "HC_ETHER_ALPHA"]
    alkene_hydrogens = ["HC_ALKENE", "HC_ALKENE_TERMINAL"]
    aromatic_c = ["CA_AROM", "CA_AROM_SUB"]

    for c in carbon_sp3:
        for h in hydrogens:
            _add_bond(c, h, 340.0, 1.090)
        for c2 in carbon_sp3:
            _add_bond(c, c2, 268.0, 1.529)
    for c in carbon_sp2:
        for h in alkene_hydrogens:
            _add_bond(c, h, 340.0, 1.080, "OPLS/2020 bonded")
        for c2 in carbon_sp2:
            _add_bond(c, c2, 549.0, 1.340, "OPLS/2020 bonded")
        for c2 in carbon_sp3:
            _add_bond(c, c2, 317.0, 1.510, "OPLS/2020 bonded")
    for c in aromatic_c:
        _add_bond(c, "HA_AROM", 367.0, 1.080, "OPLS/2020 bonded")
        for c2 in aromatic_c:
            _add_bond(c, c2, 469.0, 1.400, "OPLS/2020 bonded")
        for c2 in carbon_sp3 + ["C_ESTER"]:
            _add_bond(c, c2, 317.0, 1.500, "OPLS/2020 bonded")

    _add_bond("C_ESTER", "O_ESTER_CARBONYL", 570.0, 1.229, "LOPLS ester bonded")
    _add_bond("C_ESTER", "O_ESTER_ALKOXY", 320.0, 1.335, "LOPLS ester bonded")
    for c in carbon_sp3 + aromatic_c:
        _add_bond("C_ESTER", c, 317.0, 1.510, "LOPLS ester bonded")
        _add_bond("O_ESTER_ALKOXY", c, 320.0, 1.410, "LOPLS ester bonded")
    for c in carbon_sp3:
        _add_bond("OS_ETHER", c, 320.0, 1.410, "OPLS-AA ether bonded")

    for c1 in carbon_sp3:
        for c2 in carbon_sp3:
            for h in hydrogens:
                _add_angle(c1, c2, h, 37.5, 110.7)
            for c3 in carbon_sp3:
                _add_angle(c1, c2, c3, 58.35, 112.7)
            for c3 in carbon_sp2:
                _add_angle(c1, c2, c3, 58.35, 112.7, "OPLS/2020 bonded")
        for c2 in carbon_sp2:
            for h in hydrogens:
                _add_angle(c2, c1, h, 37.5, 110.7, "OPLS/2020 bonded")
            for c3 in carbon_sp3:
                _add_angle(c2, c1, c3, 58.35, 112.7, "OPLS/2020 bonded")
        for h in hydrogens:
            _add_angle("C_ESTER", c1, h, 37.5, 110.7, "LOPLS ester bonded")
            _add_angle("O_ESTER_ALKOXY", c1, h, 37.5, 110.7, "LOPLS ester bonded")
            _add_angle("OS_ETHER", c1, h, 35.0, 109.5, "OPLS-AA ether bonded")
        for c3 in carbon_sp3:
            _add_angle("C_ESTER", c1, c3, 58.35, 112.7, "LOPLS ester bonded")
            _add_angle("O_ESTER_ALKOXY", c1, c3, 58.35, 112.7, "LOPLS ester bonded")
            _add_angle("OS_ETHER", c1, c3, 50.0, 109.5, "OPLS-AA ether bonded")
        for ar in aromatic_c:
            for h in hydrogens:
                _add_angle(ar, c1, h, 35.0, 109.5, "OPLS-AA aryl-alkyl bonded")
            for c3 in carbon_sp3:
                _add_angle(ar, c1, c3, 63.0, 114.0, "OPLS-AA aryl-alkyl bonded")
            for ar2 in aromatic_c:
                _add_angle(ar, c1, ar2, 40.0, 109.5, "OPLS-AA aryl-alkyl bonded")
        for h1 in hydrogens:
            for h2 in hydrogens:
                _add_angle(h1, c1, h2, 33.0, 107.8)
    for c in carbon_sp2:
        for h1 in alkene_hydrogens:
            for h2 in alkene_hydrogens:
                _add_angle(h1, c, h2, 35.0, 117.0, "OPLS/2020 bonded")
        for c2 in carbon_sp2 + carbon_sp3:
            for h in alkene_hydrogens:
                _add_angle(h, c, c2, 35.0, 119.0, "OPLS/2020 bonded")
            for c3 in carbon_sp2 + carbon_sp3:
                _add_angle(c2, c, c3, 63.0, 120.0, "OPLS/2020 bonded")
    for c in aromatic_c:
        _add_angle("HA_AROM", c, "HA_AROM", 35.0, 120.0, "OPLS/2020 bonded")
        for c2 in aromatic_c + carbon_sp3 + ["C_ESTER"]:
            _add_angle("HA_AROM", c, c2, 35.0, 120.0, "OPLS/2020 bonded")
            for c3 in aromatic_c + carbon_sp3 + ["C_ESTER"]:
                _add_angle(c2, c, c3, 63.0, 120.0, "OPLS/2020 bonded")

    _add_angle("O_ESTER_CARBONYL", "C_ESTER", "O_ESTER_ALKOXY", 80.0, 123.0, "LOPLS ester bonded")
    for c in carbon_sp3 + aromatic_c:
        _add_angle("O_ESTER_CARBONYL", "C_ESTER", c, 80.0, 123.0, "LOPLS ester bonded")
        _add_angle("O_ESTER_ALKOXY", "C_ESTER", c, 70.0, 111.0, "LOPLS ester bonded")
        _add_angle("C_ESTER", "O_ESTER_ALKOXY", c, 60.0, 116.0, "LOPLS ester bonded")
        _add_angle("O_ESTER_ALKOXY", c, "HC_ALPHA_ETHER", 37.5, 110.7, "LOPLS ester bonded")
    for c1 in carbon_sp3:
        for c2 in carbon_sp3:
            _add_angle(c1, "OS_ETHER", c2, 60.0, 109.5, "OPLS-AA ether bonded")

    # Hydrocarbon RB torsions from L-OPLS. The paper applies the CT-CT-CT-CT
    # term across terminal and internal alkane torsions.
    alkane_rb = rb_to_multi_harmonic(0.518787, -0.230192, 0.896807, -1.49134)
    for a in carbon_sp3:
        for b in carbon_sp3:
            for c in carbon_sp3:
                for d in carbon_sp3:
                    _add_dihedral(a, b, c, d, alkane_rb, "L-OPLS hydrocarbons")
    alkene_neighbor_rb = rb_to_multi_harmonic(-2.04906, 1.03592, -1.34679, 0.864221)
    alkene_second_neighbor_rb = rb_to_multi_harmonic(3.78614, 0.106793, -0.562197, -1.48738)
    for cm1 in carbon_sp2:
        for cm2 in carbon_sp2:
            for ct1 in carbon_sp3:
                for ct2 in carbon_sp3:
                    _add_dihedral(cm1, cm2, ct1, ct2, alkene_neighbor_rb, "L-OPLS hydrocarbons")
                    _add_dihedral(cm1, ct1, ct2, ct2, alkene_second_neighbor_rb, "L-OPLS hydrocarbons")
    # Ester extension RB torsions. Paper labels use generic CT/HC; expand them
    # over the supported LOPLS CT subtypes.
    ester_ct_c_os_ct = rb_to_multi_harmonic(32.59672, -6.52543, -24.00659, 0.0)
    ester_os_c_o = rb_to_multi_harmonic(22.82916, 0.0, -24.00662, 0.0)
    ester_hc_ct_c_os = rb_to_multi_harmonic(0.17512, 0.71721, -0.00911, -0.93557)
    ester_c_os_ct_ct = rb_to_multi_harmonic(-7.05897, 7.54603, 5.22349, -5.22077)
    ester_hc_ct_ct_os = rb_to_multi_harmonic(0.91475, 2.67338, -0.09883, -3.59612)
    ester_ct_ct_c_os = rb_to_multi_harmonic(-1.88531, -4.94762, 2.62297, 4.12830)
    ester_ct_ct_c_o = rb_to_multi_harmonic(3.05944, -3.63216, -5.17499, 5.61279)
    ester_c_ct_ct_hc = rb_to_multi_harmonic(-0.73096, -1.84830, -0.07261, 2.47030)
    ester_c_ct_ct_ct = rb_to_multi_harmonic(-6.01526, 8.73040, 2.62473, -5.20449)
    ester_ct_ct_ct_os = rb_to_multi_harmonic(2.67162, 1.59535, 4.28477, -8.42744)
    alkoxy_ct = ["CT_ALKOXY", "CT_ALKOXY_METHYL"]
    for ct in carbon_sp3 + aromatic_c:
        for oct in alkoxy_ct:
            _add_dihedral(ct, "C_ESTER", "O_ESTER_ALKOXY", oct, ester_ct_c_os_ct, "LOPLS ester extension")
            _add_dihedral(oct, "O_ESTER_ALKOXY", "C_ESTER", "O_ESTER_CARBONYL", ester_os_c_o, "LOPLS ester extension")
    for ct in carbon_sp3:
        for hc in hydrogens:
            _add_dihedral(hc, ct, "C_ESTER", "O_ESTER_ALKOXY", ester_hc_ct_c_os, "LOPLS ester extension")
            _add_dihedral("C_ESTER", ct, ct, hc, ester_c_ct_ct_hc, "LOPLS ester extension")
        for ct2 in carbon_sp3:
            for oct in alkoxy_ct:
                _add_dihedral("C_ESTER", "O_ESTER_ALKOXY", oct, ct2, ester_c_os_ct_ct, "LOPLS ester extension")
            _add_dihedral(ct, ct2, "C_ESTER", "O_ESTER_ALKOXY", ester_ct_ct_c_os, "LOPLS ester extension")
            _add_dihedral(ct, ct2, "C_ESTER", "O_ESTER_CARBONYL", ester_ct_ct_c_o, "LOPLS ester extension")
            for ct3 in carbon_sp3:
                _add_dihedral("C_ESTER", ct, ct2, ct3, ester_c_ct_ct_ct, "LOPLS ester extension")
                _add_dihedral(ct, ct2, ct3, "O_ESTER_ALKOXY", ester_ct_ct_ct_os, "LOPLS ester extension")
    for hc in hydrogens:
        for ct in carbon_sp3:
            for oct in alkoxy_ct:
                _add_dihedral(hc, ct, oct, "O_ESTER_ALKOXY", ester_hc_ct_ct_os, "LOPLS ester extension")

    # BOSS OPLS/2020 dialkyl ether torsions from oplsaa.par entries 001, 006, 012, 013, and 016.
    ether_hc_ct_os_ct = (0.0, 0.0, 0.760, 0.0)
    ether_ct_os_ct_ct = (0.250, -0.250, 0.500, 0.0)
    ether_ct_ct_ct_os = (1.300, -0.500, 0.0, 0.0)
    ether_os_ct_ct_os = (-0.550, 0.0, 0.0, 0.0)
    for ct1 in carbon_sp3:
        for ct2 in carbon_sp3:
            _add_dihedral("HC_ETHER_ALPHA", ct1, "OS_ETHER", ct2, ether_hc_ct_os_ct, "OPLS/2020 ether torsion", "opls")
            for ct3 in carbon_sp3:
                _add_dihedral(ct1, "OS_ETHER", ct2, ct3, ether_ct_os_ct_ct, "OPLS/2020 ether torsion", "opls")
                _add_dihedral(ct1, ct2, ct3, "OS_ETHER", ether_ct_ct_ct_os, "OPLS/2020 ether torsion", "opls")
            _add_dihedral("OS_ETHER", ct1, ct2, "OS_ETHER", ether_os_ct_ct_os, "OPLS/2020 ether torsion", "opls")

    # BOSS OPLS aryl-alkyl torsions for alkyl benzenes.
    for ct1 in carbon_sp3:
        for ct2 in carbon_sp3:
            for ct3 in carbon_sp3:
                for ar in aromatic_c:
                    _add_dihedral(ct1, ct2, ct3, ar, (0.0, 0.0, 0.0, 0.0), "OPLS-AA alkylbenzene torsion", "opls")
                    for hc in hydrogens:
                        _add_dihedral(hc, ct1, ct2, ar, (0.0, 0.0, 0.462, 0.0), "OPLS-AA alkylbenzene torsion", "opls")
            for ar1 in aromatic_c:
                for ar2 in aromatic_c:
                    _add_dihedral(ct1, ct2, ar1, ar2, (0.0, 0.150, 0.0, 0.0), "OPLS-AA ethylbenzene torsion", "opls")
                    _add_dihedral(ct1, ar1, ar2, ct2, (0.0, 7.250, 0.0, 0.0), "OPLS/2020 aromatic planarity", "opls")
                    for ar3 in aromatic_c:
                        # ct-ar-ar-ar planarity across the ar1-ar2 ring bond; the third aromatic
                        # position is independent (needed at fused-ring junctions, e.g. naphthalene,
                        # where the 4th atom is CA_AROM_SUB while the 3rd is CA_AROM).
                        _add_dihedral(ct1, ar1, ar2, ar3, (0.0, 7.250, 0.0, 0.0), "OPLS/2020 aromatic planarity", "opls")
                        _add_dihedral(ar1, ct1, ar2, ar3, (0.0, 0.0, 0.0, 0.0), "OPLS-AA alkylbenzene torsion", "opls")
                    for hc in hydrogens:
                        _add_dihedral(hc, ct1, ar1, ar2, (0.0, 0.0, 0.0, 0.0), "OPLS-AA alkylbenzene torsion", "opls")

    # Generic low-barrier terminal/H torsions used by OPLS-AA and visible in the Squalane data file.
    terminal_atoms = carbon_sp3 + carbon_sp2 + aromatic_c + ["C_ESTER", "O_ESTER_ALKOXY", "O_ESTER_CARBONYL", "OS_ETHER"]
    h_atoms = hydrogens + alkene_hydrogens + ["HA_AROM"]
    for a in terminal_atoms + h_atoms:
        for b in terminal_atoms:
            for c in terminal_atoms:
                for d in terminal_atoms + h_atoms:
                    if a in h_atoms or d in h_atoms:
                        _add_dihedral(
                            a,
                            b,
                            c,
                            d,
                            (0.0, 0.0, 0.300, 0.0),
                            "OPLS-AA generic X-heavy-heavy-H",
                            "opls",
                            overwrite=False,
                        )
    for a in aromatic_c + ["HA_AROM"]:
        for b in aromatic_c:
            for c in aromatic_c:
                for d in aromatic_c + ["HA_AROM"]:
                    _add_dihedral(a, b, c, d, (0.0, 7.25, 0.0, 0.0), "OPLS/2020 aromatic planarity", "opls")


_init_params()


def heavy_neighbors(mol: Chem.Mol, idx: int) -> list[Chem.Atom]:
    return [n for n in mol.GetAtomWithIdx(idx).GetNeighbors() if n.GetAtomicNum() > 1]


def hydrogen_neighbor_count(atom: Chem.Atom) -> int:
    return sum(1 for n in atom.GetNeighbors() if n.GetAtomicNum() == 1)


def is_ester_carbonyl_c(atom: Chem.Atom) -> bool:
    if atom.GetAtomicNum() != 6:
        return False
    has_double_o = False
    has_single_o = False
    for bond in atom.GetBonds():
        other = bond.GetOtherAtom(atom)
        if other.GetAtomicNum() != 8:
            continue
        if bond.GetBondType() == Chem.BondType.DOUBLE:
            has_double_o = True
        elif bond.GetBondType() == Chem.BondType.SINGLE:
            has_single_o = True
    return has_double_o and has_single_o


def atom_type_for(mol: Chem.Mol, idx: int) -> str:
    atom = mol.GetAtomWithIdx(idx)
    atomic_num = atom.GetAtomicNum()
    if atomic_num == 1:
        parent = atom.GetNeighbors()[0]
        parent_type = atom_type_for(mol, parent.GetIdx())
        if parent_type in {"CT_ALKOXY", "CT_ALKOXY_METHYL"}:
            return "HC_ALPHA_ETHER"
        if parent_type in {"CT_ETHER_METHYL", "CT_ETHER_CH2", "CT_ETHER_CH", "CT_ETHER_C"}:
            return "HC_ETHER_ALPHA"
        if parent_type == "CA_AROM":
            return "HA_AROM"
        if parent_type == "CM_CH2":
            return "HC_ALKENE_TERMINAL"
        if parent_type.startswith("CM_"):
            return "HC_ALKENE"
        if parent_type == "CT_CH3":
            return "HC_CH3"
        if parent_type == "CT_CH2":
            return "HC_CH2"
        if parent_type == "CT_CH":
            return "HC_CH"
        raise ParameterError(f"Unsupported hydrogen parent type {parent_type} at atom {idx + 1}")
    if atomic_num == 8:
        for bond in atom.GetBonds():
            other = bond.GetOtherAtom(atom)
            if is_ester_carbonyl_c(other):
                if bond.GetBondType() == Chem.BondType.DOUBLE:
                    return "O_ESTER_CARBONYL"
                if bond.GetBondType() == Chem.BondType.SINGLE:
                    return "O_ESTER_ALKOXY"
        carbon_neighbors = []
        for bond in atom.GetBonds():
            other = bond.GetOtherAtom(atom)
            if bond.GetBondType() == Chem.BondType.SINGLE and other.GetAtomicNum() == 6:
                carbon_neighbors.append(other)
        if (
            len(carbon_neighbors) == 2
            and atom.GetDegree() == 2
            and all(not n.GetIsAromatic() for n in carbon_neighbors)
        ):
            return "OS_ETHER"
        raise ParameterError(f"Unsupported oxygen environment at atom {idx + 1}; enabled oxygens are esters and dialkyl ethers")
    if atomic_num != 6:
        raise ParameterError(f"Unsupported element {atom.GetSymbol()} at atom {idx + 1}")
    if is_ester_carbonyl_c(atom):
        return "C_ESTER"
    if atom.GetIsAromatic():
        return "CA_AROM" if hydrogen_neighbor_count(atom) > 0 else "CA_AROM_SUB"
    if any(b.GetBondType() == Chem.BondType.DOUBLE and b.GetOtherAtom(atom).GetAtomicNum() == 6 for b in atom.GetBonds()):
        h_count = hydrogen_neighbor_count(atom)
        if h_count == 2:
            return "CM_CH2"
        if h_count == 1:
            return "CM_CH"
        return "CM_C"
    if atom.GetHybridization() == Chem.HybridizationType.SP3:
        h_count = hydrogen_neighbor_count(atom)
        oxygen_types = [atom_type_for(mol, n.GetIdx()) for n in atom.GetNeighbors() if n.GetAtomicNum() == 8]
        if "O_ESTER_ALKOXY" in oxygen_types:
            return "CT_ALKOXY_METHYL" if h_count == 3 else "CT_ALKOXY"
        if oxygen_types.count("OS_ETHER") == 1:
            if h_count == 3:
                return "CT_ETHER_METHYL"
            if h_count == 2:
                return "CT_ETHER_CH2"
            if h_count == 1:
                return "CT_ETHER_CH"
            if h_count == 0:
                return "CT_ETHER_C"
        if oxygen_types.count("OS_ETHER") > 1:
            raise ParameterError(f"Acetal carbon environment at atom {idx + 1} is not enabled")
        if h_count == 3:
            return "CT_CH3"
        if h_count == 2:
            return "CT_CH2"
        if h_count == 1:
            return "CT_CH"
        if h_count == 0:
            return "CT_C"
    raise ParameterError(f"Unsupported carbon environment at atom {idx + 1}")


def embed_molecule(smiles: str, seed: int) -> Chem.Mol:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ParameterError(f"Invalid SMILES: {smiles}")
    mol = Chem.AddHs(mol)
    params = AllChem.ETKDGv3()
    params.randomSeed = seed
    status = AllChem.EmbedMolecule(mol, params)
    if status != 0:
        raise ParameterError("RDKit could not generate a 3D conformer for the SMILES")
    try:
        AllChem.UFFOptimizeMolecule(mol, maxIters=500)
    except Exception:
        pass
    return mol


def enumerate_angles(mol: Chem.Mol) -> list[tuple[int, int, int]]:
    angles: list[tuple[int, int, int]] = []
    for center in mol.GetAtoms():
        neigh = [n.GetIdx() for n in center.GetNeighbors()]
        for i, a in enumerate(neigh):
            for c in neigh[i + 1 :]:
                angles.append((a, center.GetIdx(), c))
    return angles


def enumerate_dihedrals(mol: Chem.Mol) -> list[tuple[int, int, int, int]]:
    dihedrals: set[tuple[int, int, int, int]] = set()
    for bond in mol.GetBonds():
        b = bond.GetBeginAtomIdx()
        c = bond.GetEndAtomIdx()
        left = [n.GetIdx() for n in mol.GetAtomWithIdx(b).GetNeighbors() if n.GetIdx() != c]
        right = [n.GetIdx() for n in mol.GetAtomWithIdx(c).GetNeighbors() if n.GetIdx() != b]
        for a in left:
            for d in right:
                dihedrals.add(min((a, b, c, d), (d, c, b, a)))
    return sorted(dihedrals)


def assign_topology(smiles: str, seed: int = 61453) -> Topology:
    mol = embed_molecule(smiles, seed)
    atom_types = [atom_type_for(mol, i) for i in range(mol.GetNumAtoms())]
    atom_params = [ATOM_PARAMS[t] for t in atom_types]

    bonds = []
    shake_bonds = []
    for bond in mol.GetBonds():
        i, j = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
        key = _sorted2(atom_types[i], atom_types[j])
        param = BOND_PARAMS.get(key)
        if not param:
            raise ParameterError(f"Missing bond parameter for {atom_types[i]}-{atom_types[j]} at atoms {i + 1}-{j + 1}")
        bonds.append((i, j, param))
        if mol.GetAtomWithIdx(i).GetAtomicNum() == 1 or mol.GetAtomWithIdx(j).GetAtomicNum() == 1:
            shake_bonds.append((i, j))

    angles = []
    for i, j, k in enumerate_angles(mol):
        key = _angle_key(atom_types[i], atom_types[j], atom_types[k])
        param = ANGLE_PARAMS.get(key)
        if not param:
            raise ParameterError(
                f"Missing angle parameter for {atom_types[i]}-{atom_types[j]}-{atom_types[k]} at atoms {i + 1}-{j + 1}-{k + 1}"
            )
        angles.append((i, j, k, param))

    dihedrals = []
    for i, j, k, l in enumerate_dihedrals(mol):
        key = _dihedral_key(atom_types[i], atom_types[j], atom_types[k], atom_types[l])
        param = DIHEDRAL_PARAMS.get(key)
        if not param:
            raise ParameterError(
                "Missing dihedral parameter for "
                f"{atom_types[i]}-{atom_types[j]}-{atom_types[k]}-{atom_types[l]} at atoms {i + 1}-{j + 1}-{k + 1}-{l + 1}"
            )
        dihedrals.append((i, j, k, l, param))

    return Topology(mol, atom_types, atom_params, bonds, angles, dihedrals, shake_bonds)


def cubic_box_length_angstrom(mw_g_mol: float, n_molecules: int, density_g_cm3: float) -> float:
    volume_cm3 = (mw_g_mol * n_molecules) / (density_g_cm3 * AVOGADRO)
    return (volume_cm3 ** (1.0 / 3.0)) * 1.0e8


def write_xyz(mol: Chem.Mol, path: Path) -> None:
    conf = mol.GetConformer()
    with path.open("w") as handle:
        handle.write(f"{mol.GetNumAtoms()}\n")
        handle.write("generated by smiles2loplsaa\n")
        for atom in mol.GetAtoms():
            pos = conf.GetAtomPosition(atom.GetIdx())
            handle.write(f"{atom.GetSymbol()} {pos.x:.8f} {pos.y:.8f} {pos.z:.8f}\n")


def read_xyz_coords(path: Path) -> list[tuple[float, float, float]]:
    lines = path.read_text().splitlines()
    if len(lines) < 2:
        raise ParameterError(f"Invalid Packmol XYZ output: {path}")
    natoms = int(lines[0].strip())
    coords = []
    for line in lines[2 : 2 + natoms]:
        parts = line.split()
        coords.append((float(parts[1]), float(parts[2]), float(parts[3])))
    if len(coords) != natoms:
        raise ParameterError(f"Packmol XYZ output atom count mismatch in {path}")
    return coords


def run_packmol(topology: Topology, n_molecules: int, box_length: float, tolerance: float, seed: int, workdir: Path) -> list[tuple[float, float, float]]:
    packmol = shutil.which("packmol")
    if not packmol:
        raise ParameterError("Packmol is required but was not found on PATH")
    monomer_xyz = workdir / "monomer.xyz"
    packed_xyz = workdir / "packed.xyz"
    input_file = workdir / "packmol.inp"
    write_xyz(topology.mol, monomer_xyz)
    upper = box_length - tolerance
    input_file.write_text(
        "\n".join(
            [
                f"tolerance {tolerance:.4f}",
                "filetype xyz",
                f"seed {seed}",
                f"output {packed_xyz}",
                "",
                f"structure {monomer_xyz}",
                f"  number {n_molecules}",
                f"  inside box {tolerance:.4f} {tolerance:.4f} {tolerance:.4f} {upper:.4f} {upper:.4f} {upper:.4f}",
                "end structure",
                "",
            ]
        )
    )
    with input_file.open("r") as stdin:
        result = subprocess.run([packmol], cwd=workdir, stdin=stdin, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise ParameterError(f"Packmol failed with exit code {result.returncode}:\n{result.stderr or result.stdout}")
    return read_xyz_coords(packed_xyz)


def unique_ids(items: Iterable[object]) -> tuple[dict[object, int], list[object]]:
    ids: dict[object, int] = {}
    ordered: list[object] = []
    for item in items:
        if item not in ids:
            ids[item] = len(ids) + 1
            ordered.append(item)
    return ids, ordered


def write_lammps_data(topology: Topology, coords: Sequence[tuple[float, float, float]], n_molecules: int, box_length: float, path: Path) -> dict[str, int]:
    atoms_per_mol = topology.mol.GetNumAtoms()
    expected_atoms = atoms_per_mol * n_molecules
    if len(coords) != expected_atoms:
        raise ParameterError(f"Expected {expected_atoms} packed coordinates, got {len(coords)}")

    atom_type_ids, atom_type_order = unique_ids(atom_type_record(param) for param in topology.atom_params)
    bond_type_ids, bond_type_order = unique_ids(bond_type_record(b[2]) for b in topology.bonds)
    angle_type_ids, angle_type_order = unique_ids(
        angle_type_record((topology.atom_types[i], topology.atom_types[j], topology.atom_types[k]), param)
        for i, j, k, param in topology.angles
    )
    dihedral_type_ids, dihedral_type_order = unique_ids(
        dihedral_type_record(
            (topology.atom_types[i], topology.atom_types[j], topology.atom_types[k], topology.atom_types[l]), param
        )
        for i, j, k, l, param in topology.dihedrals
    )
    dihedral_styles = sorted({record[1] for record in dihedral_type_order})
    use_hybrid_dihedrals = len(dihedral_styles) > 1

    with path.open("w") as out:
        out.write("LAMMPS data file generated by smiles2loplsaa\n\n")
        out.write(f"{expected_atoms} atoms\n")
        out.write(f"{len(topology.bonds) * n_molecules} bonds\n")
        out.write(f"{len(topology.angles) * n_molecules} angles\n")
        out.write(f"{len(topology.dihedrals) * n_molecules} dihedrals\n")
        out.write("0 impropers\n\n")
        out.write(f"{len(atom_type_order)} atom types\n")
        out.write(f"{len(bond_type_order)} bond types\n")
        out.write(f"{len(angle_type_order)} angle types\n")
        out.write(f"{len(dihedral_type_order)} dihedral types\n")
        out.write("0 improper types\n\n")
        out.write(f"0.000000 {box_length:.6f} xlo xhi\n")
        out.write(f"0.000000 {box_length:.6f} ylo yhi\n")
        out.write(f"0.000000 {box_length:.6f} zlo zhi\n\n")

        out.write("Masses\n\n")
        for record in atom_type_order:
            label, _element, mass, _sigma, _epsilon = record
            out.write(f"{atom_type_ids[record]:5d} {mass:12.6f}   # {label}\n")

        out.write("\nAtoms\n\n")
        atom_id = 1
        for mol_id in range(1, n_molecules + 1):
            offset = (mol_id - 1) * atoms_per_mol
            for local_idx, param in enumerate(topology.atom_params):
                x, y, z = coords[offset + local_idx]
                atom_record = atom_type_record(param)
                out.write(
                    f"{atom_id:8d} {mol_id:6d} {atom_type_ids[atom_record]:5d} "
                    f"{param.charge: .12f} {x:14.9f} {y:14.9f} {z:14.9f}\n"
                )
                atom_id += 1

        out.write("\nBonds\n\n")
        row_id = 1
        for mol_idx in range(n_molecules):
            offset = mol_idx * atoms_per_mol
            for i, j, param in topology.bonds:
                record = bond_type_record(param)
                out.write(f"{row_id:8d} {bond_type_ids[record]:5d} {offset + i + 1:8d} {offset + j + 1:8d}\n")
                row_id += 1

        out.write("\nAngles\n\n")
        row_id = 1
        for mol_idx in range(n_molecules):
            offset = mol_idx * atoms_per_mol
            for i, j, k, param in topology.angles:
                record = angle_type_record((topology.atom_types[i], topology.atom_types[j], topology.atom_types[k]), param)
                out.write(
                    f"{row_id:8d} {angle_type_ids[record]:5d} {offset + i + 1:8d} {offset + j + 1:8d} {offset + k + 1:8d}\n"
                )
                row_id += 1

        out.write("\nDihedrals\n\n")
        row_id = 1
        for mol_idx in range(n_molecules):
            offset = mol_idx * atoms_per_mol
            for i, j, k, l, param in topology.dihedrals:
                record = dihedral_type_record(
                    (topology.atom_types[i], topology.atom_types[j], topology.atom_types[k], topology.atom_types[l]), param
                )
                out.write(
                    f"{row_id:8d} {dihedral_type_ids[record]:5d} {offset + i + 1:8d} {offset + j + 1:8d} "
                    f"{offset + k + 1:8d} {offset + l + 1:8d}\n"
                )
                row_id += 1

        out.write("\nPair Coeffs\n\n")
        for record in atom_type_order:
            label, _element, _mass, sigma, epsilon = record
            out.write(f"{atom_type_ids[record]:5d} {epsilon: .15f} {sigma:.6f}   # {label}\n")

        out.write("\nBond Coeffs\n\n")
        for record in bond_type_order:
            key, k, r0 = record
            out.write(f"{bond_type_ids[record]:5d} {k: .6f} {r0:.6f}   # {' '.join(key)}\n")

        out.write("\nAngle Coeffs\n\n")
        for record in angle_type_order:
            key, k, theta0 = record
            out.write(f"{angle_type_ids[record]:5d} {k: .6f} {theta0:.6f}   # {' '.join(key)}\n")

        out.write("\nDihedral Coeffs\n\n")
        for record in dihedral_type_order:
            key, style, coeffs = record
            coeff_text = " ".join(f"{c:.8f}" for c in coeffs)
            if use_hybrid_dihedrals:
                out.write(f"{dihedral_type_ids[record]:5d} {style} {coeff_text}   # {' '.join(key)}\n")
            else:
                out.write(f"{dihedral_type_ids[record]:5d} {coeff_text}   # {' '.join(key)}\n")

    if not dihedral_styles:
        dihedral_style = "opls"
    elif use_hybrid_dihedrals:
        dihedral_style = "hybrid " + " ".join(style for style in ("opls", "multi/harmonic") if style in dihedral_styles)
    else:
        dihedral_style = dihedral_styles[0]
    return {
        "atom_types": len(atom_type_order),
        "bond_types": len(bond_type_order),
        "angle_types": len(angle_type_order),
        "dihedral_types": len(dihedral_type_order),
        "dihedral_style": dihedral_style,
    }


def lammps_init_text(dihedral_style: str) -> str:
    return f"""units          real
atom_style     full
boundary       p p p

bond_style     harmonic
angle_style    harmonic
dihedral_style {dihedral_style}

pair_style     lj/cut/coul/long 12.0
pair_modify    mix geometric tail yes
kspace_style   pppm 1.0e-5
special_bonds  lj/coul 0.0 0.0 0.5
"""


def coefficient_command_text(topology: Topology) -> str:
    atom_type_ids, atom_type_order = unique_ids(atom_type_record(param) for param in topology.atom_params)
    bond_type_ids, bond_type_order = unique_ids(bond_type_record(b[2]) for b in topology.bonds)
    angle_type_ids, angle_type_order = unique_ids(
        angle_type_record((topology.atom_types[i], topology.atom_types[j], topology.atom_types[k]), param)
        for i, j, k, param in topology.angles
    )
    dihedral_type_ids, dihedral_type_order = unique_ids(
        dihedral_type_record(
            (topology.atom_types[i], topology.atom_types[j], topology.atom_types[k], topology.atom_types[l]), param
        )
        for i, j, k, l, param in topology.dihedrals
    )
    dihedral_styles = sorted({record[1] for record in dihedral_type_order})
    use_hybrid_dihedrals = len(dihedral_styles) > 1

    lines = ["# Generated coefficient commands; keep with in.data for restart/read_data workflows."]
    for record in atom_type_order:
        label, _element, _mass, sigma, epsilon = record
        lines.append(f"pair_coeff      {atom_type_ids[record]} {atom_type_ids[record]} {epsilon:.15f} {sigma:.6f}   # {label}")
    for record in bond_type_order:
        key, k, r0 = record
        lines.append(f"bond_coeff      {bond_type_ids[record]} {k:.6f} {r0:.6f}   # {' '.join(key)}")
    for record in angle_type_order:
        key, k, theta0 = record
        lines.append(f"angle_coeff     {angle_type_ids[record]} {k:.6f} {theta0:.6f}   # {' '.join(key)}")
    for record in dihedral_type_order:
        key, style, coeffs = record
        coeff_text = " ".join(f"{c:.8f}" for c in coeffs)
        if use_hybrid_dihedrals:
            lines.append(f"dihedral_coeff  {dihedral_type_ids[record]} {style} {coeff_text}   # {' '.join(key)}")
        else:
            lines.append(f"dihedral_coeff  {dihedral_type_ids[record]} {coeff_text}   # {' '.join(key)}")
    return "\n".join(lines) + "\n"


def lammps_settings_text(timestep: float, coeff_text: str = "") -> str:
    coeff_block = f"{coeff_text}\n" if coeff_text else ""
    return f"""{coeff_block}neighbor        2.0 bin
neigh_modify    every 1 delay 0 check yes
timestep        {timestep:.6g}
"""


def write_lammps_init(path: Path, dihedral_style: str) -> None:
    path.write_text(lammps_init_text(dihedral_style))


def write_lammps_settings(path: Path, timestep: float, coeff_text: str = "") -> None:
    path.write_text(lammps_settings_text(timestep, coeff_text))


def write_metadata(topology: Topology, path: Path, smiles: str, n_molecules: int, box_length: float, density: float | None, counts: dict[str, int]) -> None:
    net_charge = sum(p.charge for p in topology.atom_params)
    sources = sorted({p.source for p in topology.atom_params})
    path.write_text(
        json.dumps(
            {
                "smiles": smiles,
                "n_molecules": n_molecules,
                "atoms_per_molecule": topology.mol.GetNumAtoms(),
                "net_charge_per_molecule": round(net_charge, 10),
                "box_length_angstrom": box_length,
                "density_g_cm3": density,
                "type_counts": counts,
                "atom_types": topology.atom_types,
                "parameter_sources": sources,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def default_output_dir(smiles: str, n_molecules: int) -> Path:
    safe = re.sub(r"[^A-Za-z0-9._+-]+", "_", smiles).strip("._")
    if not safe:
        safe = "molecule"
    if safe != smiles or len(safe) > 80:
        digest = hashlib.sha1(smiles.encode("utf-8")).hexdigest()[:8]
        safe = f"{safe[:64]}_{digest}"
    return Path("output") / f"{n_molecules}x{safe}"


def build_system(args: argparse.Namespace) -> None:
    topology = assign_topology(args.smiles, args.seed)
    if args.n is None:
        atoms_per_mol = topology.mol.GetNumAtoms()
        args.n = max(1, round(args.target_atoms / atoms_per_mol))
        print(
            f"--target-atoms {args.target_atoms}: {atoms_per_mol} atoms/molecule "
            f"-> n = {args.n} ({args.n * atoms_per_mol} atoms)"
        )
    if args.box_length is not None:
        box_length = args.box_length
    else:
        mw = Descriptors.MolWt(topology.mol)
        box_length = cubic_box_length_angstrom(mw, args.n, args.density)

    out_dir = Path(args.out) if args.out else default_output_dir(args.smiles, args.n)
    out_dir.mkdir(parents=True, exist_ok=True)
    data_path = out_dir / "in.data"
    init_path = out_dir / "in.init"
    settings_path = out_dir / "in.settings"
    metadata_path = out_dir / "metadata.json"

    with tempfile.TemporaryDirectory(prefix="smiles2loplsaa_") as tmp:
        coords = run_packmol(topology, args.n, box_length, args.packmol_tolerance, args.seed, Path(tmp))
    counts = write_lammps_data(topology, coords, args.n, box_length, data_path)
    dihedral_style = str(counts["dihedral_style"])
    write_lammps_init(init_path, dihedral_style)
    write_lammps_settings(settings_path, args.timestep, coefficient_command_text(topology))
    write_metadata(topology, metadata_path, args.smiles, args.n, box_length, args.density if args.box_length is None else None, counts)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-smiles", "--smiles", required=True, help="Input SMILES string")
    parser.add_argument("-n", "--n", type=int, default=None, help="Number of molecules (or use --target-atoms)")
    parser.add_argument("--target-atoms", type=int, default=None, help="Target total atom count; N is computed from atoms/molecule (~15000 recommended)")
    parser.add_argument("--density", type=float, default=0.75, help="Target density in g/cm^3 when --box-length is absent")
    parser.add_argument("--box-length", type=float, help="Cubic box length in Angstrom")
    parser.add_argument("--out", help="Output directory. Defaults to output/<N>x<SMILES>")
    parser.add_argument("--timestep", type=float, default=1.0, help="LAMMPS timestep in fs")
    parser.add_argument("--seed", type=int, default=61453, help="Random seed for RDKit and Packmol")
    parser.add_argument("--packmol-tolerance", type=float, default=2.0, help="Packmol tolerance in Angstrom")
    args = parser.parse_args(argv)
    if args.n is None and args.target_atoms is None:
        parser.error("provide -n/--n or --target-atoms")
    if args.n is not None and args.n <= 0:
        parser.error("--n must be positive")
    if args.target_atoms is not None and args.target_atoms <= 0:
        parser.error("--target-atoms must be positive")
    if args.box_length is None and args.density <= 0:
        parser.error("--density must be positive")
    if args.box_length is not None and args.box_length <= 0:
        parser.error("--box-length must be positive")
    if args.timestep <= 0:
        parser.error("--timestep must be positive")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        build_system(args)
    except ParameterError as exc:
        print(f"ERROR: {exc}", file=os.sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
