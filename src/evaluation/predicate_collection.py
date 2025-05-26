import dataclasses
from typing import Dict, List


@dataclasses.dataclass
class Argument:
    lanelet_type: bool = False
    traffic_light_type: bool = False
    intersection_type: bool = False
    traffic_sign_type: bool = False
    obstacle_type: bool = False
    side: bool = False
    threshold: bool = False
    turning_direction: bool = False


predicate_collection_args: Dict[str, List[Argument]] = {
    "adjacent_lanelet_of_type_predicate": [Argument(lanelet_type=True)],
    # "approach_intersection_predicate",
    "at_intersection_type_predicate": [Argument(intersection_type=True)],
    # "at_same_intersection_predicate",
    "at_traffic_light_predicate": [Argument(traffic_light_type=True)],
    "at_traffic_sign_predicate": [Argument(traffic_sign_type=True)],
    "brakes_stronger_predicate": [Argument(threshold=True)],
    # "braking_at_intersection_possible_predicate",
    # "causes_braking_intersection_predicate",
    "close_to_intersection_predicate": [Argument(intersection_type=True)],
    "close_to_lane_border_predicate": [Argument(threshold=True)],
    # "close_to_stop_line_predicate",
    "completely_on_lanelet_type_predicate": [Argument(lanelet_type=True)],
    "decelerates_predicate": [Argument(threshold=True)],
    # "drives_faster_predicate",
    # "drives_with_slightly_higher_speed_predicate",
    "has_priority_predicate": [Argument(turning_direction=True), Argument(turning_direction=True)],
    # "high_computation_time_test_predicate",
    # "in_front_of_predicate",
    # "in_intersection_conflict_area_predicate",
    "in_neighboring_lane_predicate": [Argument(side=True)],
    "in_outermost_lane_predicate": [Argument(side=True)],
    # "in_projection_domain_predicate",
    # "in_same_lane_predicate",
    # "in_single_lane_predicate",
    # "in_standstill_predicate",
    # "interstate_broad_enough_predicate",
    "is_of_type_predicate": [Argument(obstacle_type=True)],
    # "keeps_braking_speed_limit_predicate",
    # "keeps_fov_speed_limit_predicate",
    # "keeps_lane_speed_limit_predicate",
    # "keeps_min_speed_limit_predicate",
    # "keeps_safe_distance_prec_predicate",
    # "keeps_type_speed_limit_predicate",
    "lane_based_orientation_side_predicate": [Argument(side=True)],
    # "lane_based_orientation_similar_predicate",
    "lateral_distance_to_obstacle_above_threshold_predicate": [Argument(threshold=True)],
    # "left_of_predicate",
    # "low_computation_time_test_predicate",
    # "makes_u_turn_predicate",
    # "narrow_road_predicate",
    "neighboring_lane_opp_driving_dir_predicate": [Argument(side=True)],
    # "on_incoming_left_of_predicate",
    "on_lanelet_with_successor_type_predicate": [Argument(lanelet_type=True)],
    "on_lanelet_with_type_predicate": [Argument(lanelet_type=True)],
    # "on_oncoming_of_predicate",
    # "on_road_predicate",
    # "on_same_road_predicate",
    "on_similar_oriented_lanelet_with_type_predicate": [Argument(lanelet_type=True)],
    "on_similar_oriented_lanelet_without_type_predicate": [Argument(lanelet_type=True)],
    # "orientation_towards_predicate",
    # "overtaking_allowed_predicate",
    "parallel_to_lane_marking_of_type_on_side_predicate": [Argument(side=True)],
    # "preserves_traffic_flow_predicate",
    # "relevant_traffic_light_predicate",
    # "reverses_predicate",
    # "right_of_predicate",
    # "signal_set_predicate",
    # "slow_other_vehicle_predicate",
    # "stop_line_in_front_predicate",
    "two_or_more_lanes_for_one_dir_predicate": [Argument(side=True)],
    # "unobstructed_intersection_view_predicate",
    "velocity_below_threshold_predicate": [Argument(threshold=True)],
}
