import os
from typing import List, Union

import numpy as np
from commonroad.geometry.shape import Circle
from commonroad.planning.planning_problem import PlanningProblem
from commonroad.scenario.obstacle import DynamicObstacle
from commonroad.scenario.scenario import Scenario
from commonroad.visualization.draw_params import ShapeParams
from commonroad.visualization.mp_renderer import MPRenderer
from commonroad_rp.trajectories import TrajectorySample
from commonroad_rp.utility.config import ReactivePlannerConfiguration
from matplotlib import pyplot as plt

from src.evaluation.common.scenario_eval import create_ego_draw_params


def draw_traffic_cone(rnd: MPRenderer, position: np.ndarray) -> None:
    orange = "#fc6716"
    white = "#ffffff"
    base = Circle(0.4, position)
    base.draw(rnd, draw_params=ShapeParams(facecolor=orange, edgecolor=orange, zorder=1000))
    base = Circle(0.3, position)
    base.draw(rnd, draw_params=ShapeParams(facecolor=white, edgecolor=white, zorder=1001))
    base = Circle(0.2, position)
    base.draw(rnd, draw_params=ShapeParams(facecolor=orange, edgecolor=orange, zorder=1002))


def draw_traffic_cones(rnd: MPRenderer) -> None:
    draw_traffic_cone(rnd, np.array([56, 67.9]))
    draw_traffic_cone(rnd, np.array([56, 66.6]))
    draw_traffic_cone(rnd, np.array([56, 65.3]))
    draw_traffic_cone(rnd, np.array([56, 63.9]))
    draw_traffic_cone(rnd, np.array([54, 65.5]))
    draw_traffic_cone(rnd, np.array([54.9, 64.65]))


def draw_figure(
    scenario: Scenario,
    planning_problem: PlanningProblem,
    ego: DynamicObstacle,
    timestep: int,
    config: ReactivePlannerConfiguration,
    traj_set: List[TrajectorySample],
    ref_path: np.ndarray,
    plot_limits: Union[List[Union[int, float]], None],
) -> None:
    rnd = MPRenderer(figsize=(20, 10), plot_limits=plot_limits)

    # set renderer draw params
    rnd.draw_params.time_begin = timestep
    rnd.draw_params.dynamic_obstacle.draw_icon = config.debug.draw_icons
    rnd.draw_params.dynamic_obstacle.trajectory.draw_trajectory = config.debug.draw_prediction_others
    rnd.draw_params.planning_problem.initial_state.state.draw_arrow = False
    rnd.draw_params.planning_problem.initial_state.state.radius = 0.5

    ego_params = create_ego_draw_params(timestep)

    # draw traffic cones
    draw_traffic_cones(rnd)

    # visualize scenario, planning problem, ego vehicle
    scenario.draw(rnd)
    if config.debug.draw_planning_problem:
        planning_problem.draw(rnd)
    ego.draw(rnd, draw_params=ego_params)
    rnd.render()

    # visualize optimal trajectory
    pos = np.asarray([state.position for state in ego.prediction.trajectory.state_list])
    rnd.ax.plot(
        pos[:, 0],
        pos[:, 1],
        color="k",
        marker="x",
        markersize=2.5,
        zorder=21,
        linewidth=2.0,
        label="optimal trajectory",
    )

    for i in range(0, len(traj_set)):
        if traj_set[i].feasibility_label.name in config.debug.traj_vis_filter:
            continue
        color = config.debug.traj_color[traj_set[i].feasibility_label.name]
        plt.plot(traj_set[i].cartesian.x, traj_set[i].cartesian.y, color=color, zorder=20, linewidth=0.1, alpha=1.0)

    # visualize reference path
    rnd.ax.plot(
        ref_path[:, 0],
        ref_path[:, 1],
        color="g",
        marker=".",
        markersize=1,
        zorder=19,
        linewidth=1.8,
        label="reference path",
    )

    plt.xlabel("x [m]", fontsize=22)
    plt.ylabel("y [m]", fontsize=22)
    plt.xticks(fontsize=22)
    plt.yticks(fontsize=22)

    os.makedirs(os.path.join(config.general.path_output, str(scenario.scenario_id)), exist_ok=True)
    plot_dir = os.path.join(config.general.path_output, str(scenario.scenario_id))
    plt.savefig(
        f"{plot_dir}/{scenario.scenario_id}_{timestep}.{config.debug.plots_file_format}",
        format=config.debug.plots_file_format,
        dpi=300,
        bbox_inches="tight",
    )
