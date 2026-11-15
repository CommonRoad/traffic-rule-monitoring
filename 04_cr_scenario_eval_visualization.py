from pathlib import Path

from evaluation.common.config import activated_intersection_rule_set, activated_interstate_rule_set
from evaluation.common.scenario_eval import vis_scenario

if __name__ == "__main__":
    scenario_configs = [
        (
            Path(__file__).parent / "scenarios/motivating_examples" / "USA_US101-22_5_T-1.xml",
            activated_interstate_rule_set,
            [0, 10, 20],
            [-50, 130, -15, 50],
            0.72,
        ),
        (
            Path(__file__).parent / "scenarios/motivating_examples" / "ZAM_Augmentation-1_1_T-1.xml",
            activated_interstate_rule_set,
            [0, 10, 20],
            [22, 117, -5, 10],
            0.0,
        ),
        (
            Path(__file__).parent / "scenarios/planning" / "USA_US101-14_7_T-1.xml",
            activated_interstate_rule_set,
            [0, 10, 20],
            [-40, 100, -15, 50],
            0.72,
        ),
        (
            Path(__file__).parent / "scenarios/planning/intersection/DEU_Salzwedel-107/" / "DEU_Salzwedel-107_1_T-7.pb",
            activated_intersection_rule_set,
            [0, 10, 20],
            [-200, 100, -150, 100],
            0.0,
        ),
        (
            Path(__file__).parent / "scenarios/planning/intersection/USA_Peach-4/" / "USA_Peach-4_9_T-1.pb",
            activated_intersection_rule_set,
            [0, 10, 20],
            [-150, 100, -150, 100],
            0.0,
        ),
    ]

    for sc in scenario_configs:
        vis_scenario(
            scenario_path=sc[0],
            time_steps=sc[2],
            activated_rules=sc[1],
            plot_limits=sc[3],
            rotation=sc[4],
        )
