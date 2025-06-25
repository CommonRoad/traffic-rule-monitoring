import copy
from pathlib import Path
from typing import Dict, List, Union

import crcpp
import crmonitor
import numpy as np
import yaml
from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.scenario.obstacle import ObstacleType
from commonroad.scenario.scenario import Scenario
from commonroad.visualization.draw_params import DynamicObstacleParams, MPDrawParams
from commonroad.visualization.mp_renderer import MPRenderer
from matplotlib import pyplot as plt


def create_ego_draw_params(time_begin: int):
    ego_params = DynamicObstacleParams()
    ego_params.time_begin = time_begin
    ego_params.time_end = 1000
    ego_params.draw_icon = True
    ego_params.vehicle_shape.occupancy.shape.facecolor = "#E37222"
    ego_params.vehicle_shape.occupancy.shape.edgecolor = "black"
    ego_params.vehicle_shape.occupancy.shape.zorder = 50
    ego_params.vehicle_shape.occupancy.shape.opacity = 1
    ego_params.trajectory.draw_trajectory = False

    return ego_params


def load_pred_costs(conf, rule_set: List[str], base_path: Path):
    if conf.reordering and any(["_U" in rule for rule in rule_set]):
        with open(base_path / "configurations/predicates/predicate_costs_intersection.yaml", "r") as file:
            data = yaml.safe_load(file)
    elif not conf.reordering and any(["_U" in rule for rule in rule_set]):
        with open(base_path / "configurations/predicates/predicate_costs_intersection_inverted.yaml", "r") as file:
            data = yaml.safe_load(file)
    elif conf.reordering and any(["_I" in rule for rule in rule_set]):
        with open(base_path / "configurations/predicates/predicate_costs_interstate.yaml", "r") as file:
            data = yaml.safe_load(file)
    elif not conf.reordering and any(["_I" in rule for rule in rule_set]):
        with open(base_path / "configurations/predicates/predicate_costs_interstate_inverted.yaml", "r") as file:
            data = yaml.safe_load(file)
    else:
        raise RuntimeError("No predicate costs found for the given rule set.")
    return data


def load_scenario(sc_path: Path):
    if sc_path.suffix == ".pb":
        map_path = sc_path.parent / f"{sc_path.stem.split('_')[0]}_{sc_path.stem.split('_')[1]}.pb"
        sc = CommonRoadFileReader(
            filename_map=map_path,
            filename_dynamic=sc_path,
        ).open_map_dynamic()
    else:
        sc, _ = CommonRoadFileReader(filename_2020a=sc_path).open()
    return sc


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
    path = Path(__file__).parent.parent.parent.parent / "output/planning"
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    rnd = MPRenderer(plot_limits=plot_limits)
    rnd.draw_params.time_begin = time_step
    rnd.draw_params.time_end = max_time_step
    rnd.draw_params.dynamic_obstacle.draw_icon = True
    rnd.draw_params.axis_visible = False
    rnd.draw_params.dynamic_obstacle.trajectory.draw_trajectory = False
    draw_params = MPDrawParams()
    draw_params.axis_visible = False
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
            draw_params.dynamic_obstacle.vehicle_shape.occupancy.shape.facecolor = "#ff0000"
            draw_params.dynamic_obstacle.vehicle_shape.occupancy.shape.edgecolor = "black"
        else:
            draw_params.dynamic_obstacle.vehicle_shape.occupancy.shape.facecolor = "#009933"
            draw_params.dynamic_obstacle.vehicle_shape.occupancy.shape.edgecolor = "black"
        obstacle = sc.obstacle_by_id(obs)
        obstacle.draw(rnd, draw_params=draw_params)
        scenario_copy.remove_obstacle(obstacle)
    scenario_copy.draw(rnd)
    rnd.render()

    plt.savefig(
        str(Path(__file__).parent.parent.parent.parent / "output/planning" / f"{sc.scenario_id}_{time_step}.svg"),
        bbox_inches="tight",
    )


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
    obstacle_ids = [
        obs.obstacle_id
        for obs in scenario.obstacles
        if obs.obstacle_type in [ObstacleType.CAR, ObstacleType.BUS, ObstacleType.TRUCK]
    ]

    monitor = crmonitor.Monitor()
    sim_param = crmonitor.MonitorSimulationParameters()
    sim_param.checkObstacleValid = False
    sim_param.checkEgoValid = False
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
