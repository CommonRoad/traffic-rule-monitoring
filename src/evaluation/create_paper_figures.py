import copy
from pathlib import Path
from typing import Dict, List, Union

import crcpp
import crmonitor
import numpy as np
from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.scenario.scenario import Scenario
from commonroad.visualization.draw_params import MPDrawParams
from commonroad.visualization.mp_renderer import MPRenderer
from matplotlib import pyplot as plt
from tests.python.test_utils import get_test_scenario_directory


def time_step_violated(
    rel_time_step: int, obs_id: int, res: Dict[str, Dict[int, Dict[str, Dict[int, List[int]]]]], sc: Scenario
) -> bool:
    if res[str(sc.scenario_id)].get(obs_id) is not None:
        for rule, rule_eval in res[str(sc.scenario_id)][obs_id].items():
            for obs, obs_eval in rule_eval.items():
                if rel_time_step in obs_eval:
                    return True
    return False


def visualize_time_step(
    sc: Scenario,
    sel_obstacle: List[int],
    time_step: int,
    max_time_step: int,
    obstacle_ids: List[int],
    result: Dict[str, Dict[int, Dict[str, Dict[int, List[int]]]]],
    plot_limits: Union[List[Union[int, float]], None] = None,
):
    if not (Path(__file__).parent / "cr_vis").exists():
        (Path(__file__).parent / "cr_vis").mkdir(parents=True, exist_ok=True)
    rnd = MPRenderer(plot_limits=plot_limits)
    rnd.draw_params.time_begin = time_step
    rnd.draw_params.time_end = max_time_step
    rnd.draw_params.dynamic_obstacle.draw_icon = True
    rnd.draw_params.axis_visible = False
    rnd.draw_params.dynamic_obstacle.trajectory.draw_trajectory = False
    draw_params = MPDrawParams()
    draw_params.time_begin = time_step
    draw_params.time_end = max_time_step
    draw_params.dynamic_obstacle.draw_icon = True
    draw_params.dynamic_obstacle.trajectory.draw_trajectory = False
    rnd.ax.spines["top"].set_visible(False)
    rnd.ax.spines["right"].set_visible(False)
    rnd.ax.spines["bottom"].set_visible(False)
    rnd.ax.spines["left"].set_visible(False)
    rnd.ax.axis("scaled")

    scenario_copy = copy.deepcopy(sc)
    if len(sel_obstacle) == 0:
        sel_obstacle = obstacle_ids
    for obs in sel_obstacle:
        if time_step_violated(time_step, obs, result, scenario_copy):
            draw_params.dynamic_obstacle.vehicle_shape.occupancy.shape.facecolor = "#f5abbb"
            draw_params.dynamic_obstacle.vehicle_shape.occupancy.shape.edgecolor = "#de0232"
        else:
            draw_params.dynamic_obstacle.vehicle_shape.occupancy.shape.facecolor = "#a8f0c6"
            draw_params.dynamic_obstacle.vehicle_shape.occupancy.shape.edgecolor = "#3a5e49"
        obstacle = sc.obstacle_by_id(obs)
        obstacle.draw(rnd, draw_params=draw_params)
        scenario_copy.remove_obstacle(obstacle)
    scenario_copy.draw(rnd)
    rnd.render()
    plt.savefig(str(Path(__file__).parent / "cr_vis" / f"{sc.scenario_id}_{time_step}.svg"), bbox_inches="tight")


def vis_scenario(
    scenario_path: Path,
    time_steps: List[int],
    activated_rules: List[str],
    rotation: float = 0.0,
    plot_limits: Union[List[Union[int, float]], None] = None,
):
    if scenario_path.suffix == ".xml":
        scenario, _ = CommonRoadFileReader(filename_2020a=scenario_path).open()
    else:
        map_path = scenario_path.parent / f"{scenario_path.stem.split('_')[0]}_{scenario_path.stem.split('_')[1]}.pb"
        scenario = CommonRoadFileReader(
            filename_map=map_path,
            filename_dynamic=scenario_path,
        ).open_map_dynamic()
    if rotation != 0.0:
        scenario.translate_rotate(np.array([np.array(0), np.array(0)]), rotation)
    world = crcpp.World(scenario)
    obstacle_ids = [obs.obstacle_id for obs in scenario.obstacles]

    monitor = crmonitor.Monitor()
    sim_param = crmonitor.MonitorSimulationParameters()
    sim_param.checkObstacleValid = False
    sim_param.trace_reset_option = crmonitor.TraceResetOptions.always
    sim_param.storeEvalResults = False
    sim_param.world_parameters = crcpp.WorldParameters(
        crcpp.RoadNetworkParameters(),
        crcpp.SensorParameters(250.0, 250.0),
        crcpp.ActuatorParameters.ego_defaults(),
        crcpp.TimeParameters(50, 0.3, scenario.dt),
        crcpp.ActuatorParameters.vehicle_defaults(),
    )
    monitor.set_simulation_parameters(sim_param)
    monitor.activate_rule_sets(activated_rules)
    result = monitor.evaluate_scenarios_on_given_egos([world], obstacle_ids)

    for time_step in time_steps:
        visualize_time_step(scenario, obstacle_ids, time_step, 20, obstacle_ids, result, plot_limits)


vis_scenario(
    Path(__file__).parent / "USA_US101-22_3_T-1.xml", [6], ["R_G1"], rotation=0.725
)  # alternatives: USA_Peach-4_5_T-1.xml DEU_TestSafeDistance-1_1_T-1.xml
vis_scenario(
    Path(__file__).parent / "USA_US101-14_2_T-1.xml",
    [0, 10, 20],
    ["R_G1", "R_G2", "R_G3", "R_G4", "R_G5", "R_I1", "R_I2", "R_I3", "R_I4", "R_I5"],
    rotation=0.72,
)
vis_scenario(
    Path(
        get_test_scenario_directory() + "/test_intersection_rules/ru3_right_before_left/DEU_TestRightBeforeLeft-1/"
        "DEU_TestRightBeforeLeft-1_2_T-1.pb"
    ),
    [0, 32, 38, 47],
    ["R_G1", "R_G2", "R_G3", "R_G4", "R_G5", "R_U1", "R_U2", "R_U3", "R_U4", "R_U5"],
    plot_limits=[0, 120, 0, 80],
)
