from pathlib import Path
from typing import List

import crmonitor
from commonroad.common.file_writer import CommonRoadFileWriter
from commonroad.common.solution import VehicleType
from commonroad.common.util import FileFormat
from commonroad.common.writer.file_writer_interface import OverwriteExistingFile
from commonroad.planning.planning_problem import PlanningProblem, PlanningProblemSet
from commonroad.scenario.scenario import Scenario, Tag
from commonroad_rp.utility.config import ReactivePlannerConfiguration
from crcarla.carla_interface import CarlaInterface
from crcarla.controller.reactive_planner import ReactivePlannerInterface
from crcarla.helper.config import CarlaParams, CustomVis, SupportedCARLAVersion, TrajectoryVisualization
from crpred.basic_models.constant_velocity_predictor import ConstantVelocityCurvilinearPredictor

from evaluation.common.config import trace_step_sizes


def init_carla_params():
    param = CarlaParams()
    param.map = "Town10"
    param.use_docker = True
    param.carla_version = SupportedCARLAVersion.V_0_10_0
    param.ego.vehicle_ks_state = False
    param.vehicle.vehicle_ks_state = False
    param.offscreen_mode = True
    param.vis_type = CustomVis.THIRD_PERSON
    param.ego_view.record_video = True
    param.visualization.remove_tmp_files = False
    param.visualization.vis_activation.hud = False
    param.ego_view.video_path = Path(__file__).parent.parent.parent.parent
    param.simulation.max_time_step = 450
    param.simulation.number_walkers = 0
    param.simulation.number_vehicles = 0
    param.visualization.vis_activation.trajectory = TrajectoryVisualization.ONLY_FEASIBLE
    param.visualization.vis_activation.traj_color_mapping = {
        "optimal": "black",
        "feasible": "green",
        "infeasible": "purple",
        "collision": "red",
        "rule_violating": "red",
    }

    return param


def init_rp_config_carla(rules: List[str]):
    rp_config = ReactivePlannerConfiguration()
    rp_config.debug.multiproc = False
    rp_config.planning.replanning_frequency = 1
    rp_config.sampling.d_min = -1.5
    rp_config.sampling.d_max = 1.5
    rp_config.debug.complete_collision_eval = True
    rp_config.debug.complete_rule_eval = True
    rp_config.monitor.with_rule_monitoring = True
    rp_config.monitor.activated_traffic_rules = rules
    rp_config.monitor.trace_reset_option = "filter"
    rp_config.monitor.trace_reset_option_val = crmonitor.TraceResetOptions.filter
    rp_config.monitor.trace_step = list(trace_step_sizes)
    rp_config.monitor.field_of_view_front = 150
    rp_config.monitor.field_of_view_rear = 75
    rp_config.monitor.temporal_parameters = {"tIntersectionPassBefore": 5.0, "tIntersectionPassAfter": 5.0}

    return rp_config


def execute_simulation(
    rp_config: ReactivePlannerConfiguration,
    planning_problem: PlanningProblem,
    scenario: Scenario,
    carla_interface: CarlaInterface,
    use_scenario: bool,
):
    # execute simulation and planning
    rp_config.update(scenario, planning_problem)
    predictor = ConstantVelocityCurvilinearPredictor()
    carla_interface.plan(
        ReactivePlannerInterface(rp_config, draw_trajectories=True, store_failing_scenarios=False),
        predictor,
        scenario if use_scenario else None,
        planning_problem,
        VehicleType.BMW_320i,
    )

    # store resulting CommonRoad scenario
    sc = carla_interface.create_cr_scenario(scenario)
    CommonRoadFileWriter(
        sc,
        PlanningProblemSet([planning_problem]),
        author="TUM-CPS",
        affiliation="Technical University of Munich",
        source="CARLA",
        tags={Tag.URBAN},
        file_format=FileFormat.XML,
    ).write_to_file(None, OverwriteExistingFile.ALWAYS)
