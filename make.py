#!/usr/bin/env python3
"""Build everything: footprints, models, schematic, board, checks, fab package, docs.

    ./make.py              build and check everything
    ./make.py --stage sch  run one stage only (libs, sim, sch, pcb, out, docs)
    ./make.py --clean      delete everything the build generates
"""
import argparse, os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(ROOT, "scripts")
HW = os.path.join(ROOT, "hardware")
OUT = os.path.join(ROOT, "out")
BUILD = os.path.join(ROOT, "build")
sys.path.insert(0, SCRIPTS)
import kienv                                     # noqa: E402

STEM = "motorpid"
GENERATED = [
    f"hardware/{STEM}.kicad_sch", f"hardware/{STEM}.kicad_pcb", f"hardware/{STEM}.kicad_pro",
    "hardware/sym-lib-table", "hardware/fp-lib-table",
    "hardware/lib/motorpid.pretty/", "hardware/lib/motorpid.3dshapes/",
    "docs/images/", "docs/MANUFACTURING.md", "out/", "build/",
]
ALSO_TRANSIENT = [f"hardware/{STEM}.kicad_prl", "hardware/fp-info-cache"]


class Fail(Exception):
    pass


def banner(txt):
    print(f"\n=== {txt} " + "=" * max(0, 64 - len(txt)))


def sys_py(script, *args, env=None):
    e = dict(os.environ)
    e.update(env or {})
    r = subprocess.run([sys.executable, os.path.join(SCRIPTS, script), *args],
                       capture_output=True, text=True, env=e)
    sys.stdout.write(r.stdout)
    if r.returncode:
        sys.stdout.write(r.stderr)
        raise Fail(f"{script} failed")
    return r.stdout


def kicad_py(script, *args, env=None):
    e = dict(os.environ)
    e.update(env or {})
    run = kienv.runner()
    cmd = ([run, "python3.11", os.path.join(SCRIPTS, script), *args] if run
           else [sys.executable, os.path.join(SCRIPTS, script), *args])
    r = subprocess.run(cmd, capture_output=True, text=True, env=e)
    sys.stdout.write(r.stdout)
    if r.returncode:
        sys.stdout.write(r.stderr)
        raise Fail(f"{script} failed")
    return r.stdout


def count_violations(path):
    return sum(1 for line in open(path) if line.startswith("["))


def stage_libs():
    banner("footprints, models and project files")
    sys_py("gen_models.py")
    sys_py("gen_footprints.py")
    kienv.cli("fp", "upgrade", os.path.join(HW, "lib", "motorpid.pretty"), "--force")
    sys_py("gen_project.py")


def stage_sim():
    banner("simulation (ngspice)")
    # The simulation reads the netlist the schematic exports, and the sheet quotes
    # the simulation's numbers: so draw the sheet and export its netlist first (a
    # fresh clone has none: out/*.net is not committed), simulate, and let the
    # sch stage draw it again with the new numbers.
    sys_py("gen_sch.py")
    os.makedirs(OUT, exist_ok=True)
    kienv.cli("sch", "export", "netlist", "--format", "kicadsexpr", "-o",
              os.path.join(OUT, STEM + ".net"), os.path.join(HW, STEM + ".kicad_sch"))
    r = subprocess.run([sys.executable, os.path.join(ROOT, "sim", "pid_sim.py"), "--plots"],
                       capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    if r.returncode:
        sys.stdout.write(r.stderr)
        print("  !! simulation did not run (no libngspice?); the committed sim/results.json is used")


def stage_sch():
    banner("schematic")
    sys_py("gen_sch.py")
    sch = os.path.join(HW, STEM + ".kicad_sch")
    kienv.cli("sch", "upgrade", sch)
    os.makedirs(OUT, exist_ok=True)
    rpt = os.path.join(OUT, "erc.rpt")
    kienv.cli("sch", "erc", "--format", "report", "--severity-all", "-o", rpt, sch, check=False)
    n = count_violations(rpt)
    print(f"  ERC: {n} violation(s)")
    if n:
        raise Fail(f"ERC reported {n} violations -- see {os.path.relpath(rpt, ROOT)}")
    net = os.path.join(OUT, STEM + ".net")
    kienv.cli("sch", "export", "netlist", "--format", "kicadsexpr", "-o", net, sch)
    out = sys_py("check_circuit.py", net)
    if "all circuit checks passed" not in out:
        raise Fail("the netlist does not implement the Lab 10L loop")
    out = sys_py("check_schematic.py", sch)
    if "no text overlaps" not in out:
        raise Fail("the schematic sheet has overlapping or stray text")


def stage_pcb():
    banner("PCB")
    pcb = os.path.join(HW, STEM + ".kicad_pcb")
    net = os.path.join(OUT, STEM + ".net")
    out = kicad_py("gen_pcb.py", net, pcb)
    if "had nowhere to go" in out:
        raise Fail("some silkscreen could not be placed")
    sys_py("gen_project.py")
    rpt = os.path.join(OUT, f"drc-{STEM}.rpt")
    kienv.cli("pcb", "drc", "--format", "report", "--severity-all", "--schematic-parity",
              "-o", rpt, pcb, check=False)
    n = count_violations(rpt)
    print(f"  DRC: {n} violation(s)")
    if n:
        raise Fail(f"DRC reported {n} violations -- see {os.path.relpath(rpt, ROOT)}")
    # the push-pull's copper is its heatsink: the worst stall on the board as built
    r = subprocess.run([sys.executable, os.path.join(ROOT, "sim", "thermal.py"), "--board"],
                       capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    if r.returncode:
        sys.stdout.write(r.stderr)
        raise Fail("a transistor runs too hot in the worst stall (sim/thermal.py --board)")


def stage_out():
    banner("manufacturing outputs")
    sys_py("gen_outputs.py")
    out = sys_py("check_outputs.py")
    if "ALL FAB CHECKS PASSED" not in out:
        raise Fail("the fab package did not pass its checks")


def stage_docs():
    banner("documentation")
    sys_py("gen_docs.py")


def stage_project():
    banner("project files")
    sys_py("gen_project.py")


def clean():
    banner("clean")
    locked = any(n.startswith("~") and n.endswith(".lck") for n in os.listdir(HW)) if os.path.isdir(HW) else False
    for rel in GENERATED + ([] if locked else ALSO_TRANSIENT):
        path = os.path.join(ROOT, rel.rstrip("/"))
        if rel.endswith("/"):
            if os.path.isdir(path):
                shutil.rmtree(path)
                print(f"  removed {rel}")
        elif os.path.exists(path):
            os.remove(path)
            print(f"  removed {rel}")


STAGES = [("libs", stage_libs), ("sim", stage_sim), ("sch", stage_sch), ("pcb", stage_pcb),
          ("out", stage_out), ("docs", stage_docs), ("project", stage_project)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clean", action="store_true")
    ap.add_argument("--stage", action="append")
    a = ap.parse_args()
    if a.clean:
        clean()
        return 0
    print(kienv.describe())
    try:
        for name, fn in STAGES:
            if a.stage and name not in a.stage:
                continue
            fn()
    except Fail as e:
        print(f"\nBUILD FAILED: {e}")
        return 1
    print("\nBUILD OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
