import statistics
from copy import deepcopy
from typing import Tuple

from commonroad.visualization.mp_renderer import MPRenderer
from commonroad_rp.reactive_planner import ReactivePlanner
from commonroad_rp.utility.config import ReactivePlannerConfiguration
from commonroad_rp.utility.evaluation import (
    create_full_solution_ego_vehicle,
    evaluate_results,
)
from commonroad_rp.utility.logger import initialize_logger
from commonroad_rp.utility.utils_coordinate_system import (
    CoordinateSystem,
    create_coordinate_system,
    create_initial_ref_path,
)
from commonroad_rp.utility.visualization import plot_final_trajectory, visualize_planner_at_timestep

from src.evaluation.common.scenario_eval import create_ego_draw_params


def run_planner_cr_scenario(
    config: ReactivePlannerConfiguration, plot_limits: Tuple[float, float, float, float] | None = None
) -> float:
    # Initialization
    initialize_logger(config)
    ref_path_orig = create_initial_ref_path(config.scenario.lanelet_network, config.planning_problem)
    rp_cosys: CoordinateSystem = create_coordinate_system(ref_path_orig)
    planner = ReactivePlanner(config)
    planner.set_reference_path(coordinate_system=rp_cosys)

    comp_times = []

    # Run Planning
    planner.record_state_and_input(planner.x_0)
    sampling_iteration_in_planner = True
    while not planner.goal_reached():
        current_count = len(planner.record_state_list) - 1

        # check if planning cycle or not
        plan_new_trajectory = current_count % config.planning.replanning_frequency == 0
        if plan_new_trajectory:
            # new planning cycle -> plan a new optimal trajectory
            planner.set_desired_velocity(current_speed=planner.x_0.velocity)
            if sampling_iteration_in_planner:
                optimal = planner.plan()
            else:
                optimal = None
                i = 1
                while optimal is None and i <= planner.sampling_level:
                    optimal = planner.plan(i)
                    i += 1

            if not optimal:
                print("No optimal trajectory found, stopping planning.")
                exit()

            # record state and input
            comp_times.append(planner.journal["rule_check"])
            planner.record_state_and_input(optimal[0].state_list[1])

            # reset planner state for re-planning
            planner.reset(
                initial_state_cart=planner.record_state_list[-1],
                initial_state_curv=(optimal[1][1], optimal[2][1]),
                collision_checker=planner.collision_checker,
                coordinate_system=planner.coordinate_system,
            )

            # visualization: create ego Vehicle for planned trajectory and store sampled trajectory set
            if config.debug.show_plots or config.debug.save_plots:
                ego_vehicle = planner.convert_state_list_to_commonroad_object(optimal[0].state_list)
                sampled_trajectory_bundle = None
                if config.debug.draw_traj_set:
                    sampled_trajectory_bundle = deepcopy(planner.stored_trajectories)
        else:
            # simulate scenario one step forward with planned trajectory
            sampled_trajectory_bundle = None

            # continue on optimal trajectory
            temp = current_count % config.planning.replanning_frequency

            # record state and input
            planner.record_state_and_input(optimal[0].state_list[1 + temp])

            # reset planner state for re-planning
            planner.reset(
                initial_state_cart=planner.record_state_list[-1],
                initial_state_curv=(optimal[1][1 + temp], optimal[2][1 + temp]),
                collision_checker=planner.collision_checker,
                coordinate_system=planner.coordinate_system,
            )

        print(f"current time step: {current_count}")

        # visualize the current time step of the simulation
        if config.debug.show_plots or config.debug.save_plots:
            rnd = MPRenderer(figsize=(20, 10))
            rnd.draw_params.axis_visible = False
            rnd.draw_params.dynamic_obstacle.vehicle_shape.occupancy.shape.edgecolor = "black"
            visualize_planner_at_timestep(
                scenario=config.scenario,
                planning_problem=config.planning_problem,
                ego=ego_vehicle,
                traj_set=sampled_trajectory_bundle,
                ref_path=planner.reference_path,
                timestep=current_count,
                config=config,
                rnd=rnd,
                ego_params=create_ego_draw_params(current_count),
                plot_limits=plot_limits,
            )
        if config.monitor.with_rule_monitoring:
            planner.prepare_monitor()

    cleaned_times = [comp_times[0]]
    for idx in range(len(comp_times) - 1):
        cleaned_times.append(comp_times[idx + 1] - comp_times[idx])

    if config.debug.save_plots or config.debug.show_plots:
        ego_vehicle_solution = create_full_solution_ego_vehicle(config, planner.record_state_list)
        rnd = MPRenderer(figsize=(20, 10))
        rnd.draw_params.axis_visible = False
        rnd.draw_params.dynamic_obstacle.vehicle_shape.occupancy.shape.edgecolor = "black"
        plot_final_trajectory(
            config.scenario,
            config.planning_problem,
            ego_vehicle_solution.prediction.trajectory.state_list,
            config,
            ego_vehicle=ego_vehicle_solution,
            rnd=rnd,
            ego_params=create_ego_draw_params(0),
        )
        evaluate_results(config, ego_vehicle_solution.prediction.trajectory, planner.record_input_list)

    return statistics.median(cleaned_times)
