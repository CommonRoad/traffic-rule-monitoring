import time
from pathlib import Path
from typing import List

import crcpp
import crmonitor
import numpy as np
from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.scenario.scenario import Scenario
from tabulate import tabulate

from src.evaluation.common.config import EvalConfig, configs

comp_summary = np.array(
    ["Scenario Name", "num_vehicles", "num_time_steps", "C1", "C2", "C3", "C4", "C5", "C6"]
).reshape(1, -1)


def evaluate(
    eval_name: str,
    sc: Scenario,
    conf: EvalConfig,
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
    sim_param.trace_step = [10, 1] if conf.iterative_eval else [1]
    # sim_param.log_level = "debug"
    predicate_cost = {}
    temporal_parameters = {}
    predicate_parameter = {}

    monitor_config = crmonitor.MonitorConfiguration()
    monitor_config.shortCircuiting = conf.short_circuiting
    monitor_config.hydraReordering = conf.reordering
    monitor_config.earlyTermination = conf.early_termination
    monitor_config.hydraConnectedEvaluation = conf.connected_eval
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


def eval_scenario(res, scenario_path, activated_traffic_rule_sets, base_idx):
    if scenario_path.suffix == ".pb":
        map_path = scenario_path.parent / f"{scenario_path.stem.split('_')[0]}_{scenario_path.stem.split('_')[1]}.pb"
        scenario = CommonRoadFileReader(
            filename_map=map_path,
            filename_dynamic=scenario_path,
        ).open_map_dynamic()
    else:
        scenario, _ = CommonRoadFileReader(filename_2020a=scenario_path).open()
    res = np.append(
        res,
        np.array(
            [
                str(scenario.scenario_id),
                len(scenario.obstacles),
                sum([obs.prediction.final_time_step - obs.initial_state.time_step for obs in scenario.obstacles]),
                None,
                None,
                None,
                None,
                None,
                None,
            ]
        ).reshape(1, -1),
        axis=0,
    )
    # C4: we use re-ordering to see concrete benefit of connected eval
    for idx, config in enumerate(configs[1:6]):
        res[base_idx, idx + 2] = evaluate(f"C{idx}", scenario, config, activated_traffic_rule_sets)

    return res


print("##### Interstate #######")
interstate_rule_set = ["R_G1", "R_G2", "R_G3", "R_G4", "R_G5", "R_I1", "R_I2", "R_I3", "R_I4", "R_I5"]
comp_summary = eval_scenario(
    comp_summary, Path(__file__).parent / "scenarios/planning" / "USA_US101-14_2_T-1.xml", interstate_rule_set, 1
)

comp_summary = eval_scenario(
    comp_summary,
    Path(__file__).parent / "scenarios/motivating_examples" / "USA_US101-22_3_T-1.xml",
    interstate_rule_set,
    2,
)

print("##### Intersection #######")
activated_traffic_rule_sets_1 = ["R_G1", "R_G2", "R_G3", "R_G4", "R_G5", "R_U1", "R_U2", "R_U3", "R_U4", "R_U5"]
activated_traffic_rule_sets_2 = ["R_G3", "R_G5", "R_U1", "R_U2", "R_U3", "R_U4", "R_U5"]

comp_summary = eval_scenario(
    comp_summary,
    Path(__file__).parent / "scenarios/planning/DEU_TestRightBeforeLeft-1/" / "DEU_TestRightBeforeLeft-1_2_T-1.pb",
    activated_traffic_rule_sets_2,
    3,
)


# comp_summary[2, 3] = evaluate("baseline", scenario, False, False, False, False, activated_traffic_rule_sets_2)
# comp_summary[2, 4] = evaluate(
#    "short-circuiting", scenario, True, True, False, False, activated_traffic_rule_sets_1
# )  # second True necessary otherwise ccs error
# comp_summary[2, 5] = evaluate("ours", scenario, True, True, True, False, activated_traffic_rule_sets_1)
# comp_summary[2, 6] = evaluate("ours_early", scenario, True, True, True, True, activated_traffic_rule_sets_1)
# we use re-ordering to see concrete benefit of connected eval

path = Path(__file__).parent / "output/planning"
if not path.exists():
    path.mkdir(parents=True, exist_ok=True)
print("##### Overall Summary #######")
with open(f"{path}/comp_summary.txt", "w") as f:
    f.write(tabulate(comp_summary, headers="firstrow", tablefmt="latex"))
