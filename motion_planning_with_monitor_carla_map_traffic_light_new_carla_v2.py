import numpy as np
from commonroad.common.solution import VehicleType
from commonroad.common.util import Interval
from commonroad.geometry.shape import Rectangle
from commonroad.planning.goal import GoalRegion
from commonroad.planning.planning_problem import PlanningProblem
from commonroad.scenario.state import InitialState, PMState
from crcarla.carla_interface import CarlaInterface
from crcarla.controller.reactive_planner import ReactivePlannerInterface
from evaluation.planning.carla import init_caral_params, init_rp_config_carla

param = init_caral_params()
rp_config = init_rp_config_carla(["R_U2"])

# init carla interface
carla_interface = CarlaInterface(param)
# get scenario from specified map
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
                position=Rectangle(10, 3, np.array([2, 58]), 0),
            )
        ]
    ),
)
rp_config.update(scenario, planning_problem)

predictor = None  # ConstantVelocityCurvilinearPredictor()

# start planning
carla_interface.plan(
    ReactivePlannerInterface(rp_config, draw_trajectories=False, store_failing_scenarios=False),
    predictor,
    None,
    planning_problem,
    VehicleType.BMW_320i,
)
