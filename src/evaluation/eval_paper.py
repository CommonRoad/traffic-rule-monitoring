import time
from pathlib import Path
from typing import List

import crcpp
import crmonitor
import numpy as np
from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.scenario.scenario import Scenario
from tabulate import tabulate
from tests.python.test_utils import get_test_scenario_directory

comp_summary = np.array(
    ["Scenario Name", "num_vehicles", "num_time_steps", "baseline", "short-circuiting", "ours", "ours_early"]
).reshape(1, -1)


def evaluate(
    eval_name: str,
    sc: Scenario,
    short_circuiting: bool,
    hydra_reordering: bool,
    hydra_connected_evaluation: bool,
    early_termination: bool,
    rule_set: List[str],
) -> float:
    sim_param = crmonitor.MonitorSimulationParameters()
    sim_param.world_parameters = crcpp.WorldParameters(
        crcpp.RoadNetworkParameters(),
        crcpp.SensorParameters(250.0, 250.0),
        crcpp.ActuatorParameters.ego_defaults(),
        crcpp.TimeParameters(50, 0.3, 0.1),
        crcpp.ActuatorParameters.vehicle_defaults(),
    )
    # sim_param.log_level = "debug"
    predicate_cost = {}
    temporal_parameters = {}
    predicate_parameter = {}

    monitor_config = crmonitor.MonitorConfiguration()
    monitor_config.shortCircuiting = short_circuiting
    monitor_config.hydraReordering = hydra_reordering
    monitor_config.earlyTermination = early_termination
    monitor_config.hydraConnectedEvaluation = hydra_connected_evaluation
    monitor_config.performanceMeasurement = False
    monitor = crmonitor.Monitor()
    monitor.activate_rule_sets(rule_set)
    monitor.set_config(sim_param, monitor_config, predicate_cost, predicate_parameter, temporal_parameters)

    computation_times = []
    for _ in range(5):
        start_time = time.time()
        actual_result = monitor.evaluate_scenarios_on_given_egos([crcpp.World(sc)], [])
        end_time = time.time()
        computation_times.append(end_time - start_time)
    average_time = sum(computation_times) / len(computation_times)
    print(actual_result)
    print(
        f"Average computation time {eval_name}: {average_time:.6f} seconds / Num. vehicles: {len(sc.obstacles)} / Num. time steps: {sum([obs.prediction.final_time_step - obs.initial_state.time_step for obs in sc.obstacles])}"
    )
    return np.round(average_time, 4)


print("##### Interstate #######")
activated_traffic_rule_sets_1 = ["R_G1", "R_G2", "R_G3", "R_G4", "R_G5", "R_I1", "R_I2", "R_I3", "R_I4", "R_I5"]
scenario_path = Path(__file__).parent / "USA_US101-14_2_T-1.xml"

scenario, _ = CommonRoadFileReader(filename_2020a=scenario_path).open()

comp_summary = np.append(
    comp_summary,
    np.array(
        [
            str(scenario.scenario_id),
            len(scenario.obstacles),
            sum([obs.prediction.final_time_step - obs.initial_state.time_step for obs in scenario.obstacles]),
            None,
            None,
            None,
            None,
        ]
    ).reshape(1, -1),
    axis=0,
)
comp_summary[1, 3] = evaluate("baseline", scenario, False, False, False, False, activated_traffic_rule_sets_1)
comp_summary[1, 4] = evaluate("short-circuiting", scenario, True, True, False, False, activated_traffic_rule_sets_1)
comp_summary[1, 5] = evaluate("ours", scenario, True, True, True, False, activated_traffic_rule_sets_1)
comp_summary[1, 6] = evaluate("ours_early", scenario, True, True, True, True, activated_traffic_rule_sets_1)
# we use re-ordering to see concrete benefit of connected eval


print("##### Intersection #######")
activated_traffic_rule_sets_1 = ["R_G1", "R_G2", "R_G3", "R_G4", "R_G5", "R_U1", "R_U2", "R_U3", "R_U4", "R_U5"]
activated_traffic_rule_sets_2 = ["R_G3", "R_G5", "R_U1", "R_U2", "R_U3", "R_U4", "R_U5"]
scenario_path = Path(
    get_test_scenario_directory() + "/test_intersection_rules/ru3_right_before_left/DEU_TestRightBeforeLeft-1/"
    "DEU_TestRightBeforeLeft-1_2_T-1.pb"
)
map_path = scenario_path.parent / f"{scenario_path.stem.split('_')[0]}_{scenario_path.stem.split('_')[1]}.pb"
scenario = CommonRoadFileReader(
    filename_map=map_path,
    filename_dynamic=scenario_path,
).open_map_dynamic()

comp_summary = np.append(
    comp_summary,
    np.array(
        [
            str(scenario.scenario_id),
            len(scenario.obstacles),
            sum([obs.prediction.final_time_step - obs.initial_state.time_step for obs in scenario.obstacles]),
            None,
            None,
            None,
            None,
        ]
    ).reshape(1, -1),
    axis=0,
)
comp_summary[2, 3] = evaluate("baseline", scenario, False, False, False, False, activated_traffic_rule_sets_2)
comp_summary[2, 4] = evaluate(
    "short-circuiting", scenario, True, True, False, False, activated_traffic_rule_sets_1
)  # second True necessary otherwise ccs error
comp_summary[2, 5] = evaluate("ours", scenario, True, True, True, False, activated_traffic_rule_sets_1)
comp_summary[2, 6] = evaluate("ours_early", scenario, True, True, True, True, activated_traffic_rule_sets_1)
# we use re-ordering to see concrete benefit of connected eval


print("##### Overall Summary #######")
print(tabulate(comp_summary, headers="firstrow", tablefmt="latex"))
