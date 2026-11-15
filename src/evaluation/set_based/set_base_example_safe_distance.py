from pathlib import Path
from typing import List, Union

from commonroad_rp.utility.config import ReactivePlannerConfiguration

from evaluation.set_based.set_based_common import execute_rp, set_scenario_id


def set_based_safe_distance(
    scenario_path: str, conf_path: Path, pl: List[Union[int, float]], with_monitor: bool
) -> None:
    rp_config = ReactivePlannerConfiguration.load(conf_path, scenario_path)
    rp_config.general.path_output = str(Path(__file__).parent.parent.parent.parent / "output/set_based")
    rp_config.update()

    rp_config.debug.complete_rule_eval = True

    if not with_monitor:
        sc_id = set_scenario_id(rp_config)
        rp_config.scenario.scenario_id = sc_id
        rp_config.monitor.with_rule_monitoring = False

    execute_rp(rp_config, pl, False)


def eval_set_based_safe_dist():
    scenario = Path(__file__).parent.parent.parent.parent / "scenarios/set_based" / "ZAM_Augmentation-1_1_S-1.xml"
    config_path = (
        Path(__file__).parent.parent.parent.parent / "configurations/set_based" / "ZAM_Augmentation-1_1_S-1.yaml"
    )
    plot_limits = [0, 80, -5, 10]

    set_based_safe_distance(str(scenario), config_path, plot_limits, True)
    set_based_safe_distance(str(scenario), config_path, plot_limits, False)


if __name__ == "__main__":
    eval_set_based_safe_dist()
