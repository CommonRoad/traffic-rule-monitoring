from copy import deepcopy
from pathlib import Path

from commonroad_rp.reactive_planner import ReactivePlanner
from commonroad_rp.utility.config import ReactivePlannerConfiguration
from commonroad_rp.utility.utils_coordinate_system import (
    CoordinateSystem,
    create_coordinate_system,
    create_initial_ref_path,
)
from commonroad_rp.utility.visualization import visualize_planner_at_timestep


def main(config: ReactivePlannerConfiguration) -> None:
    ref_path_orig = create_initial_ref_path(config.scenario.lanelet_network, config.planning_problem)

    # pre-process reference path and create coordinate system
    rp_cosys: CoordinateSystem = create_coordinate_system(ref_path_orig)

    # initialize reactive planner
    planner = ReactivePlanner(config)

    # set coordinate system in planner
    planner.set_reference_path(coordinate_system=rp_cosys)

    # **************************
    # Run Planning
    # **************************
    # Add first state to recorded state and input list
    planner.record_state_and_input(planner.x_0)

    current_count = len(planner.record_state_list) - 1

    # new planning cycle -> plan a new optimal trajectory
    planner.set_desired_velocity(current_speed=planner.x_0.velocity)
    optimal = planner.plan()

    # record state and input
    planner.record_state_and_input(optimal[0].state_list[1])

    # reset planner state for re-planning
    planner.reset(
        initial_state_cart=planner.record_state_list[-1],
        initial_state_curv=(optimal[1][1], optimal[2][1]),
        collision_checker=planner.collision_checker,
        coordinate_system=planner.coordinate_system,
    )

    # visualization: create ego Vehicle for planned trajectory and store sampled trajectory set
    ego_vehicle = planner.convert_state_list_to_commonroad_object(optimal[0].state_list)
    sampled_trajectory_bundle = deepcopy(planner.stored_trajectories)
    visualize_planner_at_timestep(
        scenario=config.scenario,
        planning_problem=config.planning_problem,
        ego=ego_vehicle,
        traj_set=sampled_trajectory_bundle,
        ref_path=planner.reference_path,
        timestep=current_count,
        config=config,
        plot_limits=[22, 117, -5, 10],
    )


if __name__ == "__main__":
    scenario_path = Path(__file__).parent / "scenarios/motivating_examples" / "ZAM_Augmentation-1_1_T-1.xml"
    config_path = Path(__file__).parent / "configurations/motivating_examples" / "ZAM_Augmentation-1_1_T-1.yaml"

    # Build config object
    rp_config = ReactivePlannerConfiguration.load(config_path, str(scenario_path))
    rp_config.update()

    main(config=rp_config)
