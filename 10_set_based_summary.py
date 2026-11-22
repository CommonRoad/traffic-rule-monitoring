import argparse
import csv
import json
import math
import re
import subprocess
import sys
import traceback
from pathlib import Path

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.common.util import FileFormat, Interval
from commonroad.geometry.shape import Polygon, ShapeGroup
from commonroad.prediction.prediction import Occupancy, SetBasedPrediction
from commonroad_rp.reactive_planner import ReactivePlanner
from commonroad_rp.utility.config import ReactivePlannerConfiguration
from commonroad_rp.utility.utils_coordinate_system import create_coordinate_system, create_initial_ref_path
from shapely.geometry import Polygon as ShapelyPolygon

from evaluation.set_based.set_based_common import set_scenario_id

REPO_ROOT = Path(__file__).parent
# The 23 set-based CommonRoad benchmark scenarios (without the hand-made examples of 07_set_based.py).
SCENARIO_DIR = REPO_ROOT / "scenarios" / "set_based" / "cr_scenarios"
TEMPLATE_YAML = REPO_ROOT / "configurations" / "set_based" / "ZAM_Augmentation-1_1_S-1.yaml"
OUTPUT_DIR = REPO_ROOT / "output" / "set_based_scenario_eval"
CONVERTED_DIR = OUTPUT_DIR / "_converted"
REJECTION_RE = re.compile(r"Rejected (\d+) infeasible trajectories due to rule violations")


def _shape_parts(shape):
    return list(shape.shapes) if isinstance(shape, ShapeGroup) else [shape]


def _is_degenerate(shape) -> bool:
    """Zero-area polygons (e.g., collinear vertices) crash the triangulation of the collision checker."""
    return isinstance(shape, Polygon) and (len(shape.vertices) < 3 or not ShapelyPolygon(shape.vertices).area > 1e-6)


def _prepare_scenario(scenario_path: Path) -> Path:
    """Normalize a set-based scenario so that it can be loaded by crcpp.World and the collision checker:
    - occupancies with a time interval apply to every time step of the whole interval; occupancies of the same
      time step are merged into a shape group,
    - zero-area polygons are removed from the occupancy shapes,
    - interval-valued initial states use the lower bound (the set-based prediction only needs the current velocity).
    Returns the path to the normalized scenario."""
    converted = CONVERTED_DIR / scenario_path.name
    sc, pp = CommonRoadFileReader(str(scenario_path)).open()
    for o in sc.dynamic_obstacles:
        for attr, value in list(vars(o.initial_state).items()):
            if isinstance(value, Interval):
                setattr(o.initial_state, attr, value.start)
        if o.prediction is None or not hasattr(o.prediction, "occupancy_set"):
            continue
        per_step = {}
        for occ in o.prediction.occupancy_set:
            ts = occ.time_step
            steps = [ts] if not isinstance(ts, Interval) else range(math.ceil(ts.start), math.floor(ts.end) + 1)
            parts = [part for part in _shape_parts(occ.shape) if not _is_degenerate(part)]
            for step in steps:
                per_step.setdefault(int(step), []).extend(parts)
        occupancies = []
        for step in sorted(per_step):
            if not per_step[step]:
                continue
            shape = per_step[step][0] if len(per_step[step]) == 1 else ShapeGroup(per_step[step])
            occupancies.append(Occupancy(step, shape))
        o.prediction = SetBasedPrediction(o.prediction.initial_time_step, occupancies)
    CONVERTED_DIR.mkdir(parents=True, exist_ok=True)
    CommonRoadFileWriter(
        sc,
        pp,
        author="na",
        affiliation="na",
        source="na",
        tags=sc.tags or set(),
        file_format=FileFormat.XML,
    ).write_to_file(str(converted), OverwriteExistingFile.ALWAYS)
    return converted


def _read_latest_rejection_count(log_dir: Path) -> int:
    """Sum the rule-violation rejections over all sampling levels of the planning cycle (latest log)."""
    logs = list(log_dir.glob("*.log"))
    if not logs:
        return 0
    latest = max(logs, key=lambda p: p.stat().st_mtime)
    return sum(int(m.group(1)) for m in REJECTION_RE.finditer(latest.read_text()))


def run_once(scenario_path: Path, with_monitor: bool) -> dict:
    scenario_path = _prepare_scenario(scenario_path)
    rp_config = ReactivePlannerConfiguration.load(TEMPLATE_YAML, str(scenario_path))
    rp_config.general.path_output = str(OUTPUT_DIR)
    rp_config.update()

    rp_config.monitor.activated_traffic_rules = ["R_GS1"]
    rp_config.monitor.set_based = True
    rp_config.debug.complete_rule_eval = True
    rp_config.debug.draw_traj_set = False
    rp_config.debug.save_plots = False
    rp_config.debug.show_plots = False

    if not with_monitor:
        rp_config.scenario.scenario_id = set_scenario_id(rp_config)
        rp_config.monitor.with_rule_monitoring = False

    # Run a single planning step inline (instead of execute_rp from set_based_common)
    # so we don't pull in the unconditional visualization path.
    ref_path = create_initial_ref_path(rp_config.scenario.lanelet_network, rp_config.planning_problem)
    planner = ReactivePlanner(rp_config)
    planner.set_reference_path(coordinate_system=create_coordinate_system(ref_path))
    planner.record_state_and_input(planner.x_0)
    planner.set_desired_velocity(current_speed=planner.x_0.velocity)
    optimal = planner.plan()  # rejection counts are emitted to the log here

    solved = False
    if optimal is not None:
        # optimal[0] is a Trajectory; use CommonRoad's built-in goal check
        solved, _ = rp_config.planning_problem.goal_reached(optimal[0])

    log_dir = OUTPUT_DIR / str(rp_config.scenario.scenario_id) / "logs"
    return {
        "rejected": _read_latest_rejection_count(log_dir),
        "solved": bool(solved),
    }


def _render_github_table(rows, headers):
    widths = [max(len(h), *(len(str(r[h])) for r in rows)) for h in headers]
    sep = "| " + " | ".join("-" * w for w in widths) + " |"
    out = ["| " + " | ".join(h.ljust(w) for h, w in zip(headers, widths)) + " |", sep]
    out += ["| " + " | ".join(str(r[h]).ljust(w) for h, w in zip(headers, widths)) + " |" for r in rows]
    return "\n".join(out)


def _render_latex_booktabs(rows, headers):
    lines = [
        "\\begin{tabular}{" + "l" + "r" * (len(headers) - 1) + "}",
        "\\toprule",
        " & ".join(h.replace("_", "\\_") for h in headers) + " \\\\",
        "\\midrule",
    ]
    lines += [" & ".join(str(r[h]) for h in headers) + " \\\\" for r in rows]
    lines += ["\\bottomrule", "\\end{tabular}"]
    return "\n".join(lines)


def _write_summary(rows):
    headers = ["scenario", "rejected_with", "rejected_without", "diff_rejected", "solved_with", "solved_without"]
    with (OUTPUT_DIR / "summary.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    (OUTPUT_DIR / "summary.tex").write_text(_render_latex_booktabs(rows, headers))
    print(_render_github_table(rows, headers))


CHILD_RESULT_RE = re.compile(r"^CHILD_RESULT=(.*)$")


def _run_in_child(scenario_path: Path, with_monitor: bool) -> dict:
    """Run a single (scenario, monitor) pair in a subprocess so that C++ segfaults
    only kill the child. Returns a dict {rejected, solved} or {error: '...'} on failure."""
    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--child",
        "--scenario",
        str(scenario_path),
        "--monitor",
        "1" if with_monitor else "0",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return {"error": "timeout"}
    if proc.returncode != 0:
        sig = -proc.returncode if proc.returncode < 0 else None
        return {"error": f"exit{proc.returncode}{f'/sig{sig}' if sig else ''}"}
    for line in proc.stdout.splitlines():
        m = CHILD_RESULT_RE.match(line)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                return {"error": "bad_json"}
    return {"error": "no_result"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Process only the first N scenarios.")
    parser.add_argument(
        "--scenario",
        action="append",
        default=None,
        help="Restrict to specific scenario file (stem or full filename). Repeatable.",
    )
    parser.add_argument("--child", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--monitor", type=int, default=None, help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.child:
        scenario_path = Path(args.scenario[0])
        try:
            result = run_once(scenario_path, with_monitor=bool(args.monitor))
            print(f"CHILD_RESULT={json.dumps(result)}")
        except Exception as exc:
            traceback.print_exc()
            print(f"CHILD_RESULT={json.dumps({'error': type(exc).__name__})}")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    scenarios = sorted(SCENARIO_DIR.glob("*.xml"))
    if args.scenario:
        wanted = {Path(s).stem for s in args.scenario}
        scenarios = [p for p in scenarios if p.stem in wanted]
    if args.limit is not None:
        scenarios = scenarios[: args.limit]

    rows = []
    for sc_path in scenarios:
        print(f"--- {sc_path.stem} ---")
        r_with = _run_in_child(sc_path, with_monitor=True)
        r_without = _run_in_child(sc_path, with_monitor=False)

        def fmt(r, key):
            return r["error"] if "error" in r else r.get(key)

        rej_w, rej_wo = fmt(r_with, "rejected"), fmt(r_without, "rejected")
        try:
            diff = int(rej_w) - int(rej_wo)
        except (TypeError, ValueError):
            diff = "n/a"
        rows.append(
            {
                "scenario": sc_path.stem,
                "rejected_with": rej_w,
                "rejected_without": rej_wo,
                "diff_rejected": diff,
                "solved_with": fmt(r_with, "solved"),
                "solved_without": fmt(r_without, "solved"),
            }
        )
    _write_summary(rows)


if __name__ == "__main__":
    main()
