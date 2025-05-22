from pathlib import Path
from typing import List, Union

from commonroad_rp.utility.config import ReactivePlannerConfiguration

from src.evaluation.common.config import EvalConfig, configs
from src.evaluation.set_based.set_based_common import execute_rp, set_scenario_id


def set_based_safe_distance(scenario_path: str, conf_path: Path, eval_config: EvalConfig, pl: List[Union[int, float]]):
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

    if not eval_config.with_monitor:
        sc_id = set_scenario_id(rp_config)
        rp_config.scenario.scenario_id = sc_id
        rp_config.monitor.with_rule_monitoring = False

    execute_rp(rp_config, pl, False)


def eval_set_based_safe_dist():
    scenario = Path(__file__).parent.parent.parent.parent / "scenarios/set_based" / "ZAM_Augmentation-1_1_S-1.xml"
    config_path = Path(__file__).parent.parent.parent.parent / "configurations" / "ZAM_Augmentation-1_1_S-1.yaml"
    plot_limits = [0, 80, -5, 10]

    for config in configs:
        set_based_safe_distance(str(scenario), config_path, config, plot_limits)


if __name__ == "__main__":
    eval_set_based_safe_dist()
