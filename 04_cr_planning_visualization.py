from pathlib import Path

from src.evaluation.common.scenario_eval import vis_scenario

if __name__ == "__main__":
    vis_scenario(
        Path(__file__).parent / "scenarios/planning" / "USA_US101-14_2_T-1.xml",
        [0, 10, 20],
        ["R_G1", "R_G2", "R_G3", "R_G4", "R_G5", "R_I1", "R_I2", "R_I3", "R_I4", "R_I5"],
        rotation=0.72,
    )
    vis_scenario(
        Path(
            Path(__file__).parent
            / "scenarios/planning/DEU_TestRightBeforeLeft-1/"
            / "DEU_TestRightBeforeLeft-1_2_T-1.pb"
        ),
        [0, 32, 38, 47],
        ["R_G1", "R_G2", "R_G3", "R_G4", "R_G5", "R_U1", "R_U2", "R_U3", "R_U4", "R_U5"],
        plot_limits=[0, 120, 0, 80],
    )
