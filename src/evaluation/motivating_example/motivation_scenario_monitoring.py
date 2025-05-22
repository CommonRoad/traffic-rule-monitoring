from pathlib import Path

from src.evaluation.common.scenario_eval import vis_scenario


def motivation_scenario_eval_example():
    vis_scenario(
        Path(__file__).parent.parent.parent.parent / "scenarios/motivating_examples" / "USA_US101-22_3_T-1.xml",
        [6],
        ["R_G1"],
        rotation=0.725,
    )  # alternatives: USA_Peach-4_5_T-1.xml DEU_TestSafeDistance-1_1_T-1.xml


if __name__ == "__main__":
    motivation_scenario_eval_example()
