from pathlib import Path
from typing import Dict, List, Union

from commonroad_rp.utility.config import ReactivePlannerConfiguration

from evaluation.set_based.set_based_common import execute_rp, set_scenario_id


def set_based_left_turn(
    scenario_path: str, conf_path: Path, pl: List[Union[int, float]], i_param: Dict[str, float], monitor: bool = True
) -> None:
    rp_config = ReactivePlannerConfiguration.load(conf_path, scenario_path)
    rp_config.debug.complete_rule_eval = True
    rp_config.general.path_output = str(Path(__file__).parent.parent.parent.parent / "output/set_based")
    rp_config.update()

    if monitor:
        rp_config.rule_monitor.update_rule_time_parameters(i_param)
    else:
        sc_id = set_scenario_id(rp_config)
        rp_config.scenario.scenario_id = sc_id
        rp_config.monitor.with_rule_monitoring = False

    execute_rp(rp_config, pl, True)


def eval_set_based_left_turn():
    scenario = Path(__file__).parent.parent.parent.parent / "scenarios/set_based" / "DEU_TestTurnLeft-1_1_T-1.xml"
    config_path = (
        Path(__file__).parent.parent.parent.parent / "configurations/set_based" / "DEU_TestTurnLeft-1_1_T-1.yaml"
    )
    plot_limits = [40, 70, 40, 90]
    intersection_params = {"tIntersectionPassBefore": 15.0, "tIntersectionPassAfter": 15.0}

    set_based_left_turn(str(scenario), config_path, plot_limits, intersection_params, True)
    set_based_left_turn(str(scenario), config_path, plot_limits, intersection_params, False)


if __name__ == "__main__":
    eval_set_based_left_turn()
