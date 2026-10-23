#!/usr/bin/env python3
"""Build and run one short explicit-solvent segment, and report its speed."""
import argparse, json, os, sys, time

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["build", "run"], required=True)
    ap.add_argument("--pdb")
    ap.add_argument("--work", required=True)
    ap.add_argument("--padding-nm", type=float, default=1.2)
    ap.add_argument("--steps", type=int, default=250000)
    ap.add_argument("--timestep-fs", type=float, default=2.0)
    ap.add_argument("--equil-steps", type=int, default=2000)
    ap.add_argument("--report-interval", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    from openmm import app, unit, Platform, LangevinMiddleIntegrator, XmlSerializer
    os.makedirs(args.work, exist_ok=True)
    system_xml = os.path.join(args.work, "system.xml")
    solvated_pdb = os.path.join(args.work, "solvated.pdb")
    forcefield = app.ForceField("amber14-all.xml", "amber14/tip3pfb.xml")

    if args.mode == "build":
        pdb = app.PDBFile(args.pdb)
        modeller = app.Modeller(pdb.topology, pdb.positions)
        modeller.deleteWater()
        modeller.addHydrogens(forcefield)
        modeller.addSolvent(forcefield, model="tip3p",
                            padding=args.padding_nm * unit.nanometer,
                            neutralize=True)
        system = forcefield.createSystem(
            modeller.topology, nonbondedMethod=app.PME,
            nonbondedCutoff=1.0 * unit.nanometer,
            constraints=app.HBonds, rigidWater=True)
        with open(system_xml, "w") as fh:
            fh.write(XmlSerializer.serialize(system))
        with open(solvated_pdb, "w") as fh:
            app.PDBFile.writeFile(modeller.topology, modeller.positions, fh)
        n_atoms = modeller.topology.getNumAtoms()
        n_water = sum(1 for r in modeller.topology.residues()
                      if r.name in ("HOH", "WAT"))
        json.dump({"mode": "build", "atoms": n_atoms, "waters": n_water,
                   "padding_nm": args.padding_nm, "system_xml": system_xml,
                   "solvated_pdb": solvated_pdb}, open(args.out, "w"), indent=2)
        return 0

    pdb = app.PDBFile(solvated_pdb)
    with open(system_xml) as fh:
        system = XmlSerializer.deserialize(fh.read())
    integrator = LangevinMiddleIntegrator(
        300 * unit.kelvin, 1.0 / unit.picosecond,
        args.timestep_fs * unit.femtosecond)
    integrator.setRandomNumberSeed(args.seed)
    platform = Platform.getPlatformByName("CUDA")
    properties = {"Precision": "mixed"}
    sim = app.Simulation(pdb.topology, system, integrator, platform, properties)
    sim.context.setPositions(pdb.positions)

    t_min = time.time()
    sim.minimizeEnergy(maxIterations=500)
    minimise_s = time.time() - t_min

    sim.context.setVelocitiesToTemperature(300 * unit.kelvin, args.seed)
    t_eq = time.time()
    sim.step(args.equil_steps)
    equilibrate_s = time.time() - t_eq

    reporter_path = os.path.join(args.work, "md_reporter.csv")
    sim.reporters.append(app.StateDataReporter(
        reporter_path, args.report_interval, step=True, potentialEnergy=True,
        temperature=True, speed=True, elapsedTime=True, totalSteps=args.steps))
    trajectory_path = os.path.join(args.work, "md_trajectory.dcd")
    sim.reporters.append(app.DCDReporter(trajectory_path, args.report_interval))
    t_prod = time.time()
    sim.step(args.steps)
    production_s = time.time() - t_prod

    json.dump({
        "mode": "run", "atoms": pdb.topology.getNumAtoms(),
        "steps": args.steps, "timestep_fs": args.timestep_fs,
        "production_s": production_s, "minimise_s": minimise_s,
        "equilibrate_s": equilibrate_s, "reporter_path": reporter_path,
        "trajectory_path": trajectory_path,
        "report_interval_steps": args.report_interval,
        "frame_interval_ps": args.report_interval * args.timestep_fs / 1000.0,
        "platform": platform.getName(), "precision": "mixed",
        "openmm_version": __import__("openmm").version.version,
        "seed": args.seed}, open(args.out, "w"), indent=2)
    return 0

if __name__ == "__main__":
    sys.exit(main())
