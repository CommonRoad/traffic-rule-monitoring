from pathlib import Path
from typing import List

import crmonitor
from commonroad_rp.utility.config import ReactivePlannerConfiguration
from crcarla.helper.config import CarlaParams, CustomVis, SupportedCARLAVersion, TrajectoryVisualization


def init_caral_params():
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
    param.ego_view.video_path = Path(__file__).parent.parent
    param.simulation.max_time_step = 450
    param.simulation.number_walkers = 0
    param.simulation.number_vehicles = 0
    param.start_carla_server = False
    param.visualization.vis_activation.trajectory = TrajectoryVisualization.ONLY_FEASIBLE


def init_rp_config_carla(rules: List[str]):
    rp_config = ReactivePlannerConfiguration()
    rp_config.debug.multiproc = False
    rp_config.planning.replanning_frequency = 1
    rp_config.sampling.v_max = 30
    rp_config.sampling.d_min = -1
    rp_config.sampling.d_max = 1
    rp_config.debug.complete_collision_eval = False
    rp_config.debug.complete_rule_eval = False
    rp_config.debug.draw_traj_set = False
    rp_config.monitor.with_rule_monitoring = True
    rp_config.monitor.activated_traffic_rules = rules
    rp_config.monitor.trace_reset_option_val = crmonitor.TraceResetOptions.always
    rp_config.monitor.history_size = 100
    rp_config.monitor.field_of_view_front = 150
    rp_config.monitor.field_of_view_rear = 75

    return rp_config
