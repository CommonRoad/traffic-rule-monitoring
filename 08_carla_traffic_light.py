import numpy as np
from commonroad.common.util import Interval
from commonroad.geometry.shape import Rectangle
from commonroad.planning.goal import GoalRegion
from commonroad.planning.planning_problem import PlanningProblem
from commonroad.scenario.state import InitialState, PMState
from crcarla.carla_interface import CarlaInterface

from evaluation.planning.carla import init_carla_params, init_rp_config_carla, execute_simulation

param = init_carla_params()
rp_config = init_rp_config_carla(["R_U2"])

carla_interface = CarlaInterface(param)
scenario = carla_interface.create_cr_map()

# set planning problem for previously specified map
planning_problem = PlanningProblem(
    planning_problem_id=0,
    initial_state=InitialState(
        time_step=0,
        position=np.array([-103, 17.0]),
        orientation=1.57,
        velocity=8,
        acceleration=0.0,
        yaw_rate=0.0,
        slip_angle=0.0,
    ),
    goal_region=GoalRegion(
        [
            PMState(
                time_step=Interval(0, 450),
                position=Rectangle(
                    3, 6, np.array([-53.5, 52]), -1.57
                ),  # goal region in front of the intersection end because somehow reactive planner rejects all trajectories
            )
        ]
    ),
)

execute_simulation(rp_config, planning_problem, scenario, carla_interface, False)