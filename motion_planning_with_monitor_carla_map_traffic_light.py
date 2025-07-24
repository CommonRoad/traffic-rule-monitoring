import numpy as np
from commonroad.common.solution import VehicleType
from commonroad.common.util import Interval
from commonroad.geometry.shape import Rectangle
from commonroad.planning.goal import GoalRegion
from commonroad.planning.planning_problem import PlanningProblem
from commonroad.scenario.state import InitialState, PMState
from crcarla.carla_interface import CarlaInterface
from crcarla.controller.reactive_planner import ReactivePlannerInterface
from crpred.basic_models.constant_velocity_predictor import ConstantVelocityCurvilinearPredictor
from evaluation.planning.carla import init_caral_params, init_rp_config_carla

param = init_caral_params()
rp_config = init_rp_config_carla(["R_U2"])

carla_interface = CarlaInterface(param)
scenario = carla_interface.create_cr_map()
planning_problem = PlanningProblem(
    planning_problem_id=0,
    initial_state=InitialState(
        time_step=0,
        position=np.array([275.0, -134.0]),
        orientation=0.0,
        velocity=8,
        acceleration=0.0,
        yaw_rate=0.0,
        slip_angle=0.0,
    ),
    goal_region=GoalRegion(
        [
            PMState(
                time_step=Interval(0, 350),
                position=Rectangle(10, 3, np.array([335, -165.0]), -1.57),
            )
        ]
    ),
)
rp_config.update(scenario, planning_problem)

predictor = ConstantVelocityCurvilinearPredictor()

# start planning
carla_interface.plan(
    ReactivePlannerInterface(rp_config, draw_trajectories=True, store_failing_scenarios=True),
    predictor,
    None,
    planning_problem,
    VehicleType.BMW_320i,
)
