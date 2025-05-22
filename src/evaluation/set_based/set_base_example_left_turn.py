from pathlib import Path
from typing import Dict, List, Union

from commonroad_rp.utility.config import ReactivePlannerConfiguration

from src.evaluation.config import EvalConfig, configs
from src.evaluation.set_based.set_based_common import execute_rp, set_scenario_id


def set_based_left_turn(
    scenario_path: str, conf_path: Path, eval_config: EvalConfig, pl: List[Union[int, float]], i_param: Dict[str, float]
) -> None:
    rp_config = ReactivePlannerConfiguration.load(conf_path, scenario_path)
    rp_config.monitor.short_circuiting = eval_config.short_circuiting
    rp_config.monitor.hydraReordering = eval_config.reordering
    rp_config.monitor.earlyTermination = eval_config.early_termination
    rp_config.monitor.hydraConnectedEvaluation = eval_config.connected_eval
    rp_config.monitor.trace_step = [1] if not eval_config.iterative_eval else [10, 1]
    rp_config.update()

    if eval_config.visualization:
        rp_config.debug.complete_rule_eval = True
    else:
        rp_config.debug.complete_rule_eval = False

    if eval_config.with_monitor:
        rp_config.rule_monitor.update_rule_time_parameters(i_param)
    else:
        sc_id = set_scenario_id(rp_config)
        rp_config.scenario.scenario_id = sc_id
        rp_config.monitor.with_rule_monitoring = False

    execute_rp(rp_config, pl, True)


def eval_set_based_left_turn():
    scenario = Path(__file__).parent.parent.parent.parent / "scenarios/set_based" / "ZAM_TestTurnLeft-2_1_S-1.xml"
    config_path = Path(__file__).parent.parent.parent.parent / "configurations" / "ZAM_TestTurnLeft-1_1_S-1.yaml"
    plot_limits = [40, 70, 40, 120]
    intersection_params = {"tIntersectionPassBefore": 15.0, "tIntersectionPassAfter": 15.0}

    for config in configs:
        set_based_left_turn(str(scenario), config_path, config, plot_limits, intersection_params)


if __name__ == "__main__":
    eval_set_based_left_turn()
