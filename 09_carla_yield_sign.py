import numpy as np
from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.util import Interval
from commonroad.geometry.shape import Rectangle
from commonroad.planning.goal import GoalRegion
from commonroad.planning.planning_problem import PlanningProblem
from commonroad.scenario.state import InitialState, PMState
from crcarla.carla_interface import CarlaInterface

from evaluation.planning.carla import execute_simulation, init_carla_params, init_rp_config_carla

param = init_carla_params()
rp_config = init_rp_config_carla(["R_U2", "R_U4", "R_U12", "R_G1"])

# init carla interface
carla_interface = CarlaInterface(param)
# get scenario from specified map
scenario = CommonRoadFileReader(
    filename_map="scenarios/planning/ZAM_CARLAReactivePlannerError-10/ZAM_CARLAReactivePlannerError-10.pb",
    filename_dynamic="scenarios/planning/ZAM_CARLAReactivePlannerError-10/ZAM_CARLAReactivePlannerError-10_1_T-1.pb",
).open_map_dynamic()
scenario.remove_obstacle(scenario.obstacle_by_id(596))
scenario.remove_obstacle(scenario.obstacle_by_id(595))

carla_interface.set_tm_agent_via_instructions(
    InitialState(
        position=np.array([24.0, -28.0]), velocity=4.0, orientation=0.0, slip_angle=0.0, yaw_rate=0.0, time_step=0
    ),
    6,
    ["Straight", "Right", "Straight"],
    4,
    2,
)

# set planning problem for previously specified map
planning_problem = PlanningProblem(
    planning_problem_id=0,
    initial_state=InitialState(
        time_step=0,
        position=np.array([44, -50.0]),
        orientation=1.57,
        velocity=4,
        acceleration=0.0,
        yaw_rate=0.0,
        slip_angle=0.0,
    ),
    goal_region=GoalRegion(
        [
            PMState(
                time_step=Interval(0, 150),
                position=Rectangle(10, 3, np.array([60, -28]), 0),
            )
        ]
    ),
)

execute_simulation(rp_config, planning_problem, scenario, carla_interface, True)
