import concurrent.futures
import time
from pathlib import Path
from typing import Dict, List, Tuple

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


def remove_non_divisible_copy(expected_result: Dict[int, Dict[str, Dict[int, List[int]]]], divisor: float):
    result = {
        ego_id: {
            rule_id: {
                obs_id: [value for value in obs_result if value % divisor == 0]
                for obs_id, obs_result in rule_result.items()
            }
            for rule_id, rule_result in ego_result.items()
        }
        for ego_id, ego_result in expected_result.items()
    }
    return result


def check_result_empty_combined(res: dict[str, dict[int, list[int]]]) -> bool:
    for inner_map in res.values():
        for vec in inner_map.values():
            if vec:  # Return False if any list is not empty
                return False
    return True  # Return True if all lists are empty


def compare_result(
    exp_res: Dict[int, Dict[str, Dict[int, List[int]]]], actual_res: Dict[int, Dict[str, Dict[int, List[int]]]]
) -> bool:
    if len(exp_res) != len(actual_res):
        return False
    for ego_id, ego_result in exp_res.items():
        for rule_id, rule_result in ego_result.items():
            for obs_id, obs_result in rule_result.items():
                if (
                    actual_res[ego_id].get(rule_id) is not None
                    and actual_res[ego_id][rule_id].get(obs_id) is not None
                    and sorted(obs_result) != sorted(actual_res[ego_id][rule_id][obs_id])
                ):
                    return False
    return True


def evaluate(
    sc: Scenario, conf: EvalConfig, rule_set: List[str], exp_result: Dict[int, Dict[str, Dict[int, List[int]]]]
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

    if conf.reordering:
        with open(Path(__file__).parent / "configurations/predicates/predicate_costs.yaml", "r") as file:
            data = yaml.safe_load(file)
    else:
        with open(Path(__file__).parent / "configurations/predicates/predicate_costs_inverted.yaml", "r") as file:
            data = yaml.safe_load(file)
    predicate_cost = {
        key: [value["cost"], value["probability"], value["priority"]]
        for key, value in data.get("predicateCost", {}).items()
    }
    temporal_parameters = {}
    predicate_parameter = {}

    monitor_config = crmonitor.MonitorConfiguration()
    monitor_config.shortCircuiting = conf.short_circuiting
    monitor_config.hydraReordering = conf.reordering
    monitor_config.formulaEvaluationMode = (
        crmonitor.FormulaEvaluationMode.globally_early_termination
        if conf.early_termination
        else crmonitor.FormulaEvaluationMode.globally
    )
    monitor_config.hydraConnectedEvaluation = conf.connected_eval
    monitor_config.performanceMeasurement = False
    monitor = crmonitor.Monitor()
    monitor.set_config(sim_param, monitor_config, predicate_cost, predicate_parameter, temporal_parameters)
    monitor.activate_rule_sets(rule_set)

    exp_res = {}
    if conf.iterative_eval:
        for step in sim_param.trace_step:
            tmp = remove_non_divisible_copy(exp_result, step)
            for ego_id, ego_result in tmp.items():
                if not check_result_empty_combined(ego_result) and ego_id not in exp_res:
                    exp_res[ego_id] = tmp[ego_id]

        for ego_id, ego_result in exp_result.items():
            if exp_res.get(ego_id) is None:
                exp_res[ego_id] = exp_result[ego_id]
    else:
        exp_res = exp_result

    if conf.early_termination:
        expected_result_early_termination = {}
        for ego_id, ego_result in exp_res.items():
            min_rule = ""
            min_ego_time_step = float("inf")
            for rule_id, rule_result in ego_result.items():
                expected_result_early_termination.setdefault(ego_id, {})[rule_id] = {ego_id: []}
                for obs_id, obs_result in rule_result.items():
                    if obs_result and min_ego_time_step > min(obs_result):
                        min_rule = rule_id
                        min_ego_time_step = min(obs_result)
            if min_rule:
                expected_result_early_termination[ego_id][min_rule][ego_id] = [min_ego_time_step]
        exp_res = expected_result_early_termination

    computation_times = []
    for _ in range(5):
        start_time = time.time()
        try:
            actual_result = list(monitor.evaluate_scenarios_on_given_egos([crcpp.World(sc)], []).values())[0]
        except Exception as e:
            print(f"Error during evaluation: {e}")
            actual_result = "Error during evaluation."
            computation_times.append(0.0)
            break
        end_time = time.time()
        if not compare_result(exp_res, actual_result) and not conf.early_termination and not conf.iterative_eval:
            raise RuntimeError("Evaluation result does not match expected result.")
        elif not compare_result(exp_res, actual_result) and conf.early_termination and conf.iterative_eval:
            raise RuntimeError("Evaluation result does not match expected result.")
        elif not compare_result(exp_res, actual_result) and conf.iterative_eval and not conf.iterative_eval:
            raise RuntimeError("Evaluation result does not match expected result.")
        elif not compare_result(exp_res, actual_result) and not conf.early_termination and conf.iterative_eval:
            raise RuntimeError("Evaluation result does not match expected result.")
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
            sc = CommonRoadFileReader(
                filename_map=map_path,
                filename_dynamic=scenario_path,
            ).open_map_dynamic()
        else:
            sc, _ = CommonRoadFileReader(filename_2020a=scenario_path).open()
        res = np.append(
            res,
            np.array(
                [
                    str(sc.scenario_id),
                    len(sc.obstacles),
                    sum([obs.prediction.final_time_step - obs.initial_state.time_step for obs in sc.obstacles]),
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

        # compute default eval result
        monitor = crmonitor.Monitor()
        monitor_config = crmonitor.MonitorConfiguration()
        monitor_config.formulaEvaluationMode = crmonitor.FormulaEvaluationMode.globally
        monitor_config.shortCircuiting = True
        monitor_config.hydraConnectedEvaluation = False
        monitor_config.hydraReordering = True
        sim_param = crmonitor.MonitorSimulationParameters()
        sim_param.world_parameters = crcpp.WorldParameters(
            crcpp.RoadNetworkParameters(),
            crcpp.SensorParameters(250.0, 250.0),
            crcpp.ActuatorParameters.ego_defaults(),
            crcpp.TimeParameters(50, 0.3, 0.1),
            crcpp.ActuatorParameters.vehicle_defaults(),
        )
        with open(Path(__file__).parent / "configurations/predicates/predicate_costs.yaml", "r") as file:
            data = yaml.safe_load(file)
        predicate_cost = {
            key: [value["cost"], value["probability"], value["priority"]]
            for key, value in data.get("predicateCost", {}).items()
        }
        monitor.set_config(sim_param, monitor_config, predicate_cost, {}, {})
        monitor.activate_rule_sets(activated_traffic_rule_sets)
        result = monitor.evaluate_scenarios_on_given_egos([crcpp.World(sc)], [])

        for idx, eval_config in enumerate(configs[1:7]):
            evaluations.append((sc, activated_traffic_rule_sets, base_idx, eval_config, idx, list(result.values())[0]))

    with concurrent.futures.ProcessPoolExecutor(max_workers=24) as executor:
        future_to_conf = {executor.submit(evaluate, conf[0], conf[3], conf[1], conf[5]): conf for conf in evaluations}
        for future in concurrent.futures.as_completed(future_to_conf):
            conf = future_to_conf[future]
            res[conf[2] + 1, conf[4] + 3] = future.result()

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
        Path(__file__).parent / "scenarios/planning/DEU_TestRightBeforeLeft-1/" / "DEU_TestRightBeforeLeft-1_2_T-1.pb",
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
