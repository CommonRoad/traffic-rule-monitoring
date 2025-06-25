from pathlib import Path
from typing import List, Tuple

import crmonitor
import numpy as np
from commonroad_rp.utility.config import ReactivePlannerConfiguration

from src.evaluation.common.config import (
    EvalConfig,
    activated_intersection_rule_set,
    activated_interstate_rule_set,
    configs,
)
from src.evaluation.common.scenario_eval import load_pred_costs
from src.evaluation.planning.rp_planner import run_planner_cr_scenario


def evaluate(
    sc_path: Path,
    conf: EvalConfig,
    rule_set: List[str],
):
    print(f"Evaluating scenario {sc_path} - {conf}")

    config_path = Path(__file__).parent / "configurations/planning/planning_base_comp_time.yaml"

    rp_config = ReactivePlannerConfiguration.load(config_path, str(sc_path))
    rp_config.monitor.activated_traffic_rules = rule_set
    rp_config.debug.complete_rule_eval = conf.complete_rule_eval
    rp_config.debug.complete_collision_eval = conf.complete_collision_eval
    rp_config.monitor.trace_step = [10, 1] if conf.iterative_eval else [1]
    rp_config.monitor.short_circuiting = conf.short_circuiting
    rp_config.debug.draw_icons = True
    rp_config.debug.draw_planning_problem = True
    rp_config.debug.plots_file_format = "svg"
    rp_config.debug.draw_ref_path = True
    rp_config.debug.draw_traj_set = True
    rp_config.debug.draw_prediction_others = True
    rp_config.debug.save_plots = True
    rp_config.general.path_output = str(Path(__file__).parent / "output/planning")
    rp_config.monitor.hydra_reordering = (
        True  # we need to set this to True to also set a bad reordering for demonstration purposes
    )
    rp_config.monitor.formula_evaluation_mode = (
        crmonitor.FormulaEvaluationMode.globally_early_termination.value
        if conf.early_termination
        else crmonitor.FormulaEvaluationMode.globally.value
    )
    rp_config.monitor.hydra_connected_evaluation = conf.connected_eval
    rp_config.monitor.performance_measurement = False
    data = load_pred_costs(conf, rule_set, Path(__file__).parent)
    rp_config.monitor.predicate_cost = {
        key: [value["cost"], value["probability"]] for key, value in data.get("predicateCost", {}).items()
    }

    rp_config.update()
    run_planner_cr_scenario(rp_config)


def eval_scenario(config_settings: List[Tuple]) -> np.ndarray:
    for setting in config_settings:
        scenario_path, activated_traffic_rule_sets = setting
        evaluate(scenario_path, configs[-1], activated_traffic_rule_sets)


scenario_configs = [
    (
        Path(__file__).parent / "scenarios/motivating_examples" / "ZAM_Augmentation-1_1_T-1.xml",
        activated_interstate_rule_set,
    ),
    # (
    #     Path(__file__).parent / "scenarios/planning" / "USA_US101-14_7_T-1.xml",
    #     activated_interstate_rule_set,
    # ),
    (
        Path(__file__).parent / "scenarios/motivating_examples" / "USA_US101-22_5_T-1.xml",
        activated_interstate_rule_set,
    ),
    (
        Path(__file__).parent / "scenarios/planning/intersection/DEU_Salzwedel-107/" / "DEU_Salzwedel-107_1_T-7.pb",
        activated_intersection_rule_set,
    ),
    (
        Path(__file__).parent / "scenarios/planning/intersection/USA_Peach-4/" / "USA_Peach-4_9_T-1.pb",
        activated_intersection_rule_set,
    ),
]

if __name__ == "__main__":
    eval_scenario(scenario_configs)

    path = Path(__file__).parent / "output/planning"
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
