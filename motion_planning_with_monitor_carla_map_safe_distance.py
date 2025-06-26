from pathlib import Path

import crmonitor
import numpy as np
from commonroad.common.solution import VehicleType
from commonroad.common.util import Interval
from commonroad.geometry.shape import Rectangle
from commonroad.planning.goal import GoalRegion
from commonroad.planning.planning_problem import PlanningProblem
from commonroad.scenario.state import InitialState, PMState
from commonroad_rp.utility.config import ReactivePlannerConfiguration
from crpred.basic_models.constant_velocity_predictor import ConstantVelocityCurvilinearPredictor

from crcarla.carla_interface import CarlaInterface
from crcarla.controller.reactive_planner import ReactivePlannerInterface
from crcarla.helper.config import CarlaParams, CustomVis, TrajectoryVisualization

# Carla params
param = CarlaParams()
param.map = "Town01"
param.ego.vehicle_ks_state = False
param.vehicle.vehicle_ks_state = False
param.offscreen_mode = True
param.vis_type = CustomVis.THIRD_PERSON
param.ego_view.video_path = Path(__file__).parent.parent
param.simulation.max_time_step = 200
param.simulation.number_walkers = 0
param.simulation.number_vehicles = 150
param.visualization.vis_activation.trajectory = TrajectoryVisualization.ONLY_FEASIBLE

# configure CommonRoad reactive planner
rp_config = ReactivePlannerConfiguration()
rp_config.debug.multiproc = False
rp_config.planning.replanning_frequency = 1
rp_config.sampling.v_max = 30
rp_config.sampling.d_min = -1
rp_config.sampling.d_max = 1
rp_config.debug.complete_collision_eval = True
rp_config.debug.complete_rule_eval = True
rp_config.debug.draw_traj_set = True
rp_config.monitor.with_rule_monitoring = True
rp_config.monitor.activated_traffic_rules = ["R_G1"]
rp_config.monitor.trace_reset_option_val = crmonitor.TraceResetOptions.always
rp_config.monitor.history_size = 0
rp_config.monitor.field_of_view_front = 150
rp_config.monitor.field_of_view_rear = 75

# init carla interface
carla_interface = CarlaInterface(param)
# get scenario from specified map
scenario = carla_interface.create_cr_map()
# set planning problem for previously specified map
planning_problem = PlanningProblem(
    planning_problem_id=0,
    initial_state=InitialState(
        time_step=0,
        position=np.array([339.0, -100.0]),
        orientation=1.57,
        velocity=8,
        acceleration=0.0,
        yaw_rate=0.0,
        slip_angle=0.0,
    ),
    goal_region=GoalRegion(
        [
            PMState(
                time_step=Interval(0, 250),
                position=Rectangle(10, 3, np.array([339.0, -15.0]), 1.57),
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
