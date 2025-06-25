from copy import deepcopy
from typing import List, Union

from commonroad.common.common_scenario import ScenarioID
from commonroad.visualization.mp_renderer import MPRenderer
from commonroad_rp.reactive_planner import ReactivePlanner
from commonroad_rp.utility.config import ReactivePlannerConfiguration
from commonroad_rp.utility.utils_coordinate_system import (
    CoordinateSystem,
    create_coordinate_system,
    create_initial_ref_path,
)
from commonroad_rp.utility.visualization import visualize_planner_at_timestep

from src.evaluation.common.scenario_eval import create_ego_draw_params
from src.evaluation.set_based.set_based_vis import draw_figure


def execute_rp(rp_config: ReactivePlannerConfiguration, pl: List[Union[int, float]], left_turn: bool):
    ref_path_orig = create_initial_ref_path(rp_config.scenario.lanelet_network, rp_config.planning_problem)

    # pre-process reference path and create coordinate system
    rp_cosys: CoordinateSystem = create_coordinate_system(ref_path_orig)

    # initialize reactive planner
    planner = ReactivePlanner(rp_config)

    # set coordinate system in planner
    planner.set_reference_path(coordinate_system=rp_cosys)

    planner.record_state_and_input(planner.x_0)

    sampling_iteration_in_planner = True

    current_count = len(planner.record_state_list) - 1

    plan_new_trajectory = current_count % rp_config.planning.replanning_frequency == 0
    if plan_new_trajectory:
        planner.set_desired_velocity(current_speed=planner.x_0.velocity)
        if sampling_iteration_in_planner:
            optimal = planner.plan()
        else:
            optimal = None
            i = 1
            while optimal is None and i <= planner.sampling_level:
                optimal = planner.plan(i)

        planner.record_state_and_input(optimal[0].state_list[1])

        planner.reset(
            initial_state_cart=planner.record_state_list[-1],
            initial_state_curv=(optimal[1][1], optimal[2][1]),
            collision_checker=planner.collision_checker,
            coordinate_system=planner.coordinate_system,
        )

        if rp_config.debug.show_plots or rp_config.debug.save_plots:
            ego_vehicle = planner.convert_state_list_to_commonroad_object(optimal[0].state_list)
            sampled_trajectory_bundle = None
            if rp_config.debug.draw_traj_set:
                sampled_trajectory_bundle = deepcopy(planner.stored_trajectories)

    if left_turn:
        draw_figure(
            scenario=rp_config.scenario,
            planning_problem=rp_config.planning_problem,
            ego=ego_vehicle,
            traj_set=sampled_trajectory_bundle,
            ref_path=planner.reference_path,
            timestep=current_count,
            config=rp_config,
            plot_limits=pl,
        )
    else:
        rnd = MPRenderer(figsize=(20, 10), plot_limits=pl)
        rnd.draw_params.axis_visible = False
        visualize_planner_at_timestep(
            scenario=rp_config.scenario,
            planning_problem=rp_config.planning_problem,
            ego=ego_vehicle,
            traj_set=sampled_trajectory_bundle,
            ref_path=planner.reference_path,
            timestep=current_count,
            config=rp_config,
            plot_limits=pl,
            ego_params=create_ego_draw_params(current_count),
            rnd=rnd,
        )


def set_scenario_id(rp_config):
    sc_id = ScenarioID(
        country_id=rp_config.scenario.scenario_id.country_id,
        map_name=rp_config.scenario.scenario_id.map_name + "_no_monitor",
        map_id=rp_config.scenario.scenario_id.map_id,
        configuration_id=rp_config.scenario.scenario_id.configuration_id,
        obstacle_behavior=rp_config.scenario.scenario_id.obstacle_behavior,
        prediction_id=rp_config.scenario.scenario_id.prediction_id,
    )
    return sc_id
