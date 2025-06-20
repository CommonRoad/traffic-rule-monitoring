import itertools
from enum import Enum
from typing import Dict, List

import crcpp


class Argument(Enum):
    LANELET_TYPE = 1
    TRAFFIC_LIGHT_TYPE = 2
    INTERSECTION_TYPE = 3
    TRAFFIC_SIGN_TYPE = 4
    OBSTACLE_TYPE = 5
    SIDE = 6
    THRESHOLD = 7
    TURNING_DIRECTION = 8
    LINE_MARKING_TYPE = 9


class Side(Enum):
    LEFT = "left"
    RIGHT = "right"


predicate_collection_args: Dict[str, List[Argument]] = {
    "adjacent_lanelet_of_type_predicate": [Argument.SIDE, Argument.LANELET_TYPE],
    # "approach_intersection_predicate",
    "at_intersection_type_predicate": [Argument.INTERSECTION_TYPE],
    # "at_same_intersection_predicate",
    "at_traffic_light_predicate": [Argument.TURNING_DIRECTION, Argument.TRAFFIC_LIGHT_TYPE],
    "at_traffic_sign_predicate": [Argument.TRAFFIC_SIGN_TYPE],
    "brakes_stronger_predicate": [Argument.THRESHOLD],
    # "braking_at_intersection_possible_predicate",
    # "causes_braking_intersection_predicate",
    "close_to_intersection_predicate": [Argument.INTERSECTION_TYPE],
    "close_to_lane_border_predicate": [Argument.SIDE],
    # "close_to_stop_line_predicate",
    "completely_on_lanelet_type_predicate": [Argument.LANELET_TYPE],
    "decelerates_predicate": [Argument.THRESHOLD],
    # "drives_faster_predicate",
    # "drives_with_slightly_higher_speed_predicate",
    "has_priority_predicate": [Argument.TURNING_DIRECTION, Argument.TURNING_DIRECTION],
    # "high_computation_time_test_predicate",
    # "in_front_of_predicate",
    # "in_intersection_conflict_area_predicate",
    "in_neighboring_lane_predicate": [Argument.SIDE],
    "in_outermost_lane_predicate": [Argument.SIDE],
    # "in_projection_domain_predicate",
    # "in_same_lane_predicate",
    # "in_single_lane_predicate",
    # "in_standstill_predicate",
    # "interstate_broad_enough_predicate",
    "is_of_type_predicate": [Argument.OBSTACLE_TYPE],
    # "keeps_braking_speed_limit_predicate",
    # "keeps_fov_speed_limit_predicate",
    # "keeps_lane_speed_limit_predicate",
    # "keeps_min_speed_limit_predicate",
    # "keeps_safe_distance_prec_predicate",
    # "keeps_type_speed_limit_predicate",
    "lane_based_orientation_side_predicate": [Argument.SIDE],
    # "lane_based_orientation_similar_predicate",
    "lateral_distance_to_obstacle_above_threshold_predicate": [Argument.THRESHOLD],
    # "left_of_predicate",
    # "low_computation_time_test_predicate",
    # "makes_u_turn_predicate",
    # "narrow_road_predicate",
    "neighboring_lane_opp_driving_dir_predicate": [Argument.SIDE],
    # "on_incoming_left_of_predicate",
    "on_lanelet_with_successor_type_predicate": [Argument.LANELET_TYPE],
    "on_lanelet_with_type_predicate": [Argument.LANELET_TYPE],
    # "on_oncoming_of_predicate",
    # "on_road_predicate",
    # "on_same_road_predicate",
    "on_similar_oriented_lanelet_with_type_predicate": [Argument.LANELET_TYPE],
    "on_similar_oriented_lanelet_without_type_predicate": [Argument.LANELET_TYPE],
    # "orientation_towards_predicate",
    # "overtaking_allowed_predicate",
    "parallel_to_lane_marking_of_type_on_side_predicate": [Argument.SIDE, Argument.LINE_MARKING_TYPE],
    # "preserves_traffic_flow_predicate",
    # "relevant_traffic_light_predicate",
    # "reverses_predicate",
    # "right_of_predicate",
    # "signal_set_predicate",
    # "slow_other_vehicle_predicate",
    # "stop_line_in_front_predicate",
    "two_or_more_lanes_for_one_dir_predicate": [Argument.SIDE],
    # "unobstructed_intersection_view_predicate",
    "velocity_below_threshold_predicate": [Argument.THRESHOLD],
}

param_values: Dict[str, List[str]] = {
    "brakes_stronger_predicate": ["-2.0"],
    "decelerates_predicate": ["-2.0"],
    "lateral_distance_to_obstacle_above_threshold_predicate": ["1.5"],  # d_min_urban 1.5 d_min_non_urban 2.0
    "velocity_below_threshold_predicate": [
        "8.33"
    ],  # max_congestion_velocity: 2.78, max_slow_moving_traffic_velocity: 8.33, max_queue_of_vehicles_velocity: 3.0
}


rel_obs_types = [
    crcpp.ObstacleType.vehicle,
    crcpp.ObstacleType.car,
    crcpp.ObstacleType.truck,
    crcpp.ObstacleType.bus,
    crcpp.ObstacleType.bicycle,
    crcpp.ObstacleType.motorcycle,
    crcpp.ObstacleType.pedestrian,
]

rel_lanelet_types = [
    crcpp.LaneletType.accessRamp,
    crcpp.LaneletType.exitRamp,
    crcpp.LaneletType.highway,
    crcpp.LaneletType.intersection,
    crcpp.LaneletType.interstate,
    crcpp.LaneletType.incoming,
    crcpp.LaneletType.mainCarriageWay,
    crcpp.LaneletType.shoulder,
]

rel_traffic_light_states = [crcpp.TrafficLightState.red, crcpp.TrafficLightState.green, crcpp.TrafficLightState.yellow]

rel_intersection_types = [crcpp.IntersectionType.FOUR_WAY_INTERSECTION, crcpp.IntersectionType.T_INTERSECTION]

rel_line_markings = [crcpp.LineMarking.solid, crcpp.LineMarking.dashed]


def extract_arg_combinations(pred_name: str) -> List[List[str]]:
    """
    Extract argument combinations for a given predicate name.
    """
    args = []
    if pred_name in predicate_collection_args:
        for idx, arg in enumerate(predicate_collection_args[pred_name]):
            if arg is Argument.LANELET_TYPE:
                args.append([lt.name for lt in rel_lanelet_types])
            if arg is Argument.TRAFFIC_LIGHT_TYPE:
                args.append([tl.name for tl in rel_traffic_light_states])
            if arg is Argument.INTERSECTION_TYPE:
                args.append([it.name for it in rel_intersection_types])
            if arg is Argument.TRAFFIC_SIGN_TYPE:
                args.append(["stop", "yield", "priority", "max_speed"])
            if arg is Argument.OBSTACLE_TYPE:
                args.append([ot.name for ot in rel_obs_types])
            if arg is Argument.SIDE:
                args.append([side.value for side in Side])
            if arg is Argument.THRESHOLD:
                args.append([param_values[pred_name][idx]])
            if arg is Argument.TURNING_DIRECTION:
                args.append([side.value for side in Side])
            if arg is Argument.LINE_MARKING_TYPE:
                args.append([lt.name for lt in rel_line_markings])

        return [list(comb) for comb in itertools.product(*args)]
    return [["0.0"]]
