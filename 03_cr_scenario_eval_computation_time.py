import concurrent.futures
import time
from pathlib import Path
from typing import List, Tuple

import crcpp
import crmonitor
import numpy as np
import yaml
from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.scenario.scenario import Scenario

from src.evaluation.common.config import (
    EvalConfig,
    activated_intersection_rule_set,
    activated_interstate_rule_set,
    configs,
)


def evaluate(
    sc: Scenario,
    conf: EvalConfig,
    rule_set: List[str],
) -> float:
    print(f"Evaluating scenario {sc.scenario_id} - {conf}")
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
    if conf.reordering:
        with open(Path(__file__).parent / "configurations/predicates/predicate_costs.yaml", "r") as f:
            data = yaml.safe_load(f)
    else:
        with open(Path(__file__).parent / "configurations/predicates/predicate_costs_inverted.yaml", "r") as f:
            data = yaml.safe_load(f)
    predicate_cost = {
        key: [value["cost"], value["probability"], value["priority"]]
        for key, value in data.get("predicateCost", {}).items()
    }
    temporal_parameters = {}
    predicate_parameter = {}

    monitor_config = crmonitor.MonitorConfiguration()
    monitor_config.shortCircuiting = conf.short_circuiting
    monitor_config.hydraReordering = conf.reordering
    monitor_config.formulaEvaluationMode = crmonitor.FormulaEvaluationMode.globally_early_termination
    monitor_config.hydraConnectedEvaluation = conf.connected_eval
    monitor_config.performanceMeasurement = False
    monitor = crmonitor.Monitor()
    monitor.set_config(sim_param, monitor_config, predicate_cost, predicate_parameter, temporal_parameters)
    monitor.activate_rule_sets(rule_set)

    computation_times = []
    for _ in range(5):
        start_time = time.time()
        actual_result = monitor.evaluate_scenarios_on_given_egos([crcpp.World(sc)], [])
        end_time = time.time()
        computation_times.append(end_time - start_time)
    average_time = sum(computation_times) / len(computation_times)
    print(actual_result)
    print(
        f"Average computation time {conf.name}: {average_time:.6f} seconds / Num. vehicles: {len(sc.obstacles)} / Num. time steps: {sum([obs.prediction.final_time_step - obs.initial_state.time_step for obs in sc.obstacles])}"
    )
    return np.round(average_time, 4)


def eval_scenario(config_settings: List[Tuple]):
    res = np.array(["Scenario Name", "num_vehicles", "num_time_steps", "C1", "C2", "C3", "C4", "C5", "C6"]).reshape(
        1, -1
    )
    evaluations = []
    for base_idx, setting in enumerate(config_settings):
        scenario_path, activated_traffic_rule_sets = setting
        if scenario_path.suffix == ".pb":
            map_path = (
                scenario_path.parent / f"{scenario_path.stem.split('_')[0]}_{scenario_path.stem.split('_')[1]}.pb"
            )
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
        for idx, eval_config in enumerate(configs[1:7]):
            evaluations.append((scenario, activated_traffic_rule_sets, base_idx, eval_config, idx))

    with concurrent.futures.ProcessPoolExecutor(max_workers=24) as executor:
        future_to_conf = {executor.submit(evaluate, conf[0], conf[3], conf[1]): conf for conf in evaluations}
        for future in concurrent.futures.as_completed(future_to_conf):
            conf = future_to_conf[future]
            res[conf[2], conf[4] + 3] = future.result()

    return res


scenario_configs = [
    (
        Path(__file__).parent / "scenarios/planning" / "USA_US101-14_2_T-1.xml",
        activated_interstate_rule_set,
    ),
    (
        Path(__file__).parent / "scenarios/motivating_examples" / "USA_US101-22_3_T-1.xml",
        activated_interstate_rule_set,
    ),
    (
        Path(__file__).parent / "scenarios/planning/" / "DEU_TestRightBeforeLeft-1_2_T-1.xml",
        activated_intersection_rule_set,
    ),
]


comp_summary = eval_scenario(scenario_configs)


path = Path(__file__).parent / "output/planning"
if not path.exists():
    path.mkdir(parents=True, exist_ok=True)
with open(f"{path}/comp_summary.txt", "w") as f:
    f.write(r"""\begin{table*}[!t]
 \centering
 \caption{Computation times for different configurations from \cref{tab:configurations} for evaluating rule-compliance of complete scenarios.}
 \center
 \begin{tabular}{@{}lcccccccc@{}}
  \toprule
  \textbf{Scenario}                   &   \textbf{\#Vehicles} &   \textbf{\#Time Steps} &   \textbf{C1 [s]} &   \textbf{C2 [s]} &     \textbf{C3 [s]} &   \textbf{C4 [s]} &   \textbf{C5 [s]} & \textbf{C6 [s]} \\
  \midrule
""")
    # Skip header row (index 0)
    for row in comp_summary[1:]:
        # Format each value, keep floats with 4 decimals, others as int or str
        scenario = row[0].replace("_", "\_")
        num_vehicles = int(row[1])
        num_time_steps = int(row[2])
        c_values = [f"{float(x):.4f}" if x is not None else "" for x in row[3:]]
        f.write(
            f"  {scenario} & {num_vehicles:13d} & {num_time_steps:14d} &   {c_values[0]} &   {c_values[1]} &  {c_values[2]} &  {c_values[3]} & {c_values[4]} & {c_values[5]} \\\\\n"
        )
    f.write(r"""
  \bottomrule
 \end{tabular}
 \label{tab:artificial_examples_eval}
\end{table*}
""")
