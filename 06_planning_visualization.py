import concurrent.futures
from pathlib import Path
from typing import List, Tuple

import crmonitor
from commonroad_rp.trajectories import FeasibilityStatus
from commonroad_rp.utility.config import ReactivePlannerConfiguration

from evaluation.common.config import (
    activated_intersection_rule_set,
    activated_interstate_rule_set,
)
from evaluation.common.scenario_eval import load_pred_costs
from evaluation.planning.rp_planner import run_planner_cr_scenario


def evaluate(
    sc_path: Path,
    rule_set: List[str],
    with_monitor: bool,
    plot_limits: Tuple[float, float, float, float],
):
    print(f"Evaluating scenario {sc_path}")

    config_path = Path(__file__).parent / f"configurations/planning/{sc_path.stem}.yaml"

    rp_config = ReactivePlannerConfiguration.load(config_path, str(sc_path))
    rp_config.monitor.with_rule_monitoring = with_monitor
    rp_config.monitor.activated_traffic_rules = rule_set
    rp_config.debug.complete_rule_eval = True
    rp_config.debug.complete_collision_eval = True
    rp_config.monitor.trace_step = [10, 1]
    rp_config.monitor.short_circuiting = True
    rp_config.debug.draw_icons = True
    rp_config.debug.show_evaluation_plots = False
    rp_config.debug.draw_planning_problem = True
    rp_config.debug.plots_file_format = "svg"
    rp_config.debug.ref_path_color = "orange"
    rp_config.monitor.history_size = 30
    rp_config.debug.traj_vis_filter = ["INFEASIBLE_KINEMATIC"]
    rp_config.debug.traj_color = {
        FeasibilityStatus.FEASIBLE.name: "green",
        FeasibilityStatus.INFEASIBLE_KINEMATIC.name: "red",
        FeasibilityStatus.INFEASIBLE_COLLISION.name: "red",
        FeasibilityStatus.INFEASIBLE_RULE.name: "red",
    }
    rp_config.debug.draw_ref_path = True
    rp_config.debug.draw_traj_set = True
    rp_config.debug.draw_prediction_others = True
    rp_config.debug.save_plots = True
    rp_config.general.path_output = str(
        Path(__file__).parent / f"output/planning/{'with_monitor' if with_monitor else 'without_monitor'}"
    )
    rp_config.monitor.hydra_reordering = (
        True  # we need to set this to True to also set a bad reordering for demonstration purposes
    )

    rp_config.monitor.formula_evaluation_mode = crmonitor.FormulaEvaluationMode.globally_early_termination.name
    rp_config.monitor.formula_evaluation_mode_val = crmonitor.FormulaEvaluationMode[
        rp_config.monitor.formula_evaluation_mode
    ]
    rp_config.monitor.hydra_connected_evaluation = True
    rp_config.monitor.performance_measurement = False
    data = load_pred_costs(True, rule_set, Path(__file__).parent)
    rp_config.monitor.predicate_cost = {
        key: [value["cost"], value["probability"]] for key, value in data.get("predicateCost", {}).items()
    }
    rp_config.update()
    run_planner_cr_scenario(rp_config, plot_limits)


def eval_scenario(config_settings: List[Tuple], without_monitor: bool):
    with concurrent.futures.ProcessPoolExecutor(max_workers=12) as executor:
        futures = []
        for setting in config_settings:
            scenario_path, activated_traffic_rule_sets, plot_limits = setting
            futures.append(executor.submit(evaluate, scenario_path, activated_traffic_rule_sets, True, plot_limits))
            if without_monitor:
                futures.append(
                    executor.submit(evaluate, scenario_path, activated_traffic_rule_sets, False, plot_limits)
                )
        concurrent.futures.wait(futures)


scenario_configs = [
    (
        Path(__file__).parent / "scenarios/motivating_examples" / "USA_US101-22_5_T-1.xml",
        activated_interstate_rule_set,
        [-20, 58.22154813195135, -52.18761429753197, 20],
    ),
    (
        Path(__file__).parent / "scenarios/planning/intersection/DEU_Salzwedel-107/" / "DEU_Salzwedel-107_1_T-7.pb",
        activated_intersection_rule_set,
        [-26.31180869192808, 27.792619041001938, -31.0, 20.061873788838348],
    ),
    (
        Path(__file__).parent / "scenarios/planning/intersection/USA_Peach-4/" / "USA_Peach-4_9_T-1.pb",
        activated_intersection_rule_set,
        [-34.82384098144091, 20.0, -69.2432711302175, 20],
    ),
]

if __name__ == "__main__":
    eval_scenario(scenario_configs, False)

    path = Path(__file__).parent / "output/planning"
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
