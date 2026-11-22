import argparse
import concurrent.futures
import statistics
import time
from pathlib import Path
from typing import Dict, List, Tuple

import crcpp
import crmonitor
import numpy as np
from commonroad.scenario.scenario import Scenario

from evaluation.common.config import (
    EvalConfig,
    activated_intersection_rule_set,
    activated_interstate_rule_set,
    configs,
    trace_step_sizes,
)
from evaluation.common.cutoff import CUTOFF_SECONDS, format_cell, run_with_cutoff
from evaluation.common.scenario_eval import load_pred_costs, load_scenario


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
    sc: Scenario,
    conf: EvalConfig,
    rule_set: List[str],
    exp_result: Dict[int, Dict[str, Dict[int, List[int]]]],
) -> float:
    """Single timed run; raises if the evaluation fails."""
    print(f"Evaluating scenario {sc.scenario_id} - {conf}")
    sim_param = crmonitor.MonitorSimulationParameters()
    sim_param.world_parameters = crcpp.WorldParameters(
        crcpp.RoadNetworkParameters(),
        crcpp.SensorParameters(250.0, 250.0),
        crcpp.ActuatorParameters.ego_defaults(),
        crcpp.TimeParameters(50, 0.3, 0.1),
        crcpp.ActuatorParameters.vehicle_defaults(),
    )
    sim_param.trace_step = list(trace_step_sizes) if conf.iterative_eval else [1]

    data = load_pred_costs(conf.reordering, rule_set, Path(__file__).parent)
    predicate_cost = {
        key: [value["cost"], value["probability"]] for key, value in data.get("predicateCost", {}).items()
    }
    temporal_parameters = {}
    predicate_parameter = {}

    monitor_config = crmonitor.MonitorConfiguration()
    monitor_config.shortCircuiting = conf.short_circuiting
    monitor_config.hydraReordering = (
        True  # we need to set this to True to also set a bad reordering for demonstration purposes
    )
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

    if conf.check_results:
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

    world = crcpp.World(sc)
    start_time = time.perf_counter()
    actual_result = list(monitor.evaluate_scenarios_on_given_egos([world], []).values())[0]
    end_time = time.perf_counter()
    if conf.check_results:
        if not compare_result(exp_res, actual_result) and not conf.early_termination and not conf.iterative_eval:
            raise RuntimeError("Evaluation result does not match expected result.")
        elif not compare_result(exp_res, actual_result) and conf.early_termination and conf.iterative_eval:
            raise RuntimeError("Evaluation result does not match expected result.")
        elif not compare_result(exp_res, actual_result) and conf.iterative_eval and not conf.iterative_eval:
            raise RuntimeError("Evaluation result does not match expected result.")
        elif not compare_result(exp_res, actual_result) and not conf.early_termination and conf.iterative_eval:
            raise RuntimeError("Evaluation result does not match expected result.")
    print(
        f"Computation time {conf.name}: {end_time - start_time:.6f} seconds / Num. vehicles: {len(sc.obstacles)} / Num. time steps: {sum([obs.prediction.final_time_step - obs.initial_state.time_step for obs in sc.obstacles])}"
    )
    return end_time - start_time


def evaluate_with_cutoff(
    sc: Scenario,
    conf: EvalConfig,
    rule_set: List[str],
    exp_result: Dict[int, Dict[str, Dict[int, List[int]]]],
    repetitions: int,
    cutoff: float,
) -> str:
    """Median computation time over the successful repetitions as table cell.

    Repetitions that fail or exceed the cut-off are kept out of the median; "x" if none succeeded."""
    computation_times = []
    for _ in range(repetitions):
        status, value = run_with_cutoff(evaluate, (sc, conf, rule_set, exp_result), cutoff)
        if status != "ok":
            print(f"Evaluation of scenario {sc.scenario_id} with {conf.name} failed ({status}): {value}")
            if status == "timeout":
                break  # a repeated run would exceed the cut-off again
            continue
        computation_times.append(value)
    return format_cell(statistics.median(computation_times) if computation_times else None)


def eval_scenario(
    config_settings: List[Tuple], max_workers: int = 24, repetitions: int = 5, cutoff: float = CUTOFF_SECONDS
) -> np.ndarray:
    header = ["Scenario Name", "num_vehicles", "num_time_steps"] + [conf.name for conf in configs[1:7]]
    res = np.array(header, dtype=object).reshape(1, -1)
    evaluations = []
    for base_idx, setting in enumerate(config_settings):
        scenario_path, activated_traffic_rule_sets = setting
        sc = load_scenario(scenario_path)
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

        if any([conf.check_results for conf in configs]):
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
            data = load_pred_costs(True, activated_traffic_rule_sets, Path(__file__).parent)
            predicate_cost = {
                key: [value["cost"], value["probability"]] for key, value in data.get("predicateCost", {}).items()
            }
            monitor.set_config(sim_param, monitor_config, predicate_cost, {}, {})
            monitor.activate_rule_sets(activated_traffic_rule_sets)
            result = monitor.evaluate_scenarios_on_given_egos([crcpp.World(sc)], [])

        for idx, eval_config in enumerate(configs[1:7]):
            evaluations.append(
                (
                    sc,
                    activated_traffic_rule_sets,
                    base_idx,
                    eval_config,
                    idx,
                    list(result.values())[0] if eval_config.check_results else {},
                    repetitions,
                )
            )

    # each evaluation runs in its own process, which is killed when the cut-off is exceeded
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_conf = {
            executor.submit(evaluate_with_cutoff, conf[0], conf[3], conf[1], conf[5], conf[6], cutoff): conf
            for conf in evaluations
        }
        for future in concurrent.futures.as_completed(future_to_conf):
            conf = future_to_conf[future]
            res[conf[2] + 1, conf[4] + 3] = future.result()

    return res


scenario_configs = [
    (
        Path(__file__).parent / "scenarios/motivating_examples" / "USA_US101-22_5_T-1.xml",
        activated_interstate_rule_set,
    ),
    (
        Path(__file__).parent / "scenarios/motivating_examples" / "ZAM_Augmentation-1_1_T-1.xml",
        activated_interstate_rule_set,
    ),
    (
        Path(__file__).parent / "scenarios/planning" / "USA_US101-14_7_T-1.xml",
        activated_interstate_rule_set,
    ),
    (
        Path(__file__).parent / "scenarios/planning/intersection/DEU_Salzwedel-107/" / "DEU_Salzwedel-107_1_T-7.pb",
        activated_intersection_rule_set,
    ),
    (
        Path(__file__).parent / "scenarios/planning/intersection/USA_Peach-4/" / "USA_Peach-4_9_T-1.pb",
        activated_intersection_rule_set,
    ),
]


def store_summary_table():
    path = Path(__file__).parent / "output/planning"
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    conf_names = [conf.latex_name for conf in configs[1:7]]
    with open(f"{path}/comp_summary.txt", "w") as f:
        f.write(
            r"""\begin{table*}[!t]
     \centering
     \caption{Computation times (in seconds) for different configurations from \cref{tab:configurations} for evaluating the rule-compliance of complete scenarios.}
     \begin{tabular}{@{}lrrrrrrrr@{}}
      \toprule
      \textbf{Scenario}                   &   \textbf{\#Vehicles} &   \textbf{\#Time Steps} &   """
            + " &   ".join(conf_names)
            + r""" \\
      \midrule
"""
        )
        # Skip header row (index 0)
        for row in comp_summary[1:]:
            scenario = row[0].replace("_", r"\_")
            num_vehicles = int(row[1])
            num_time_steps = int(row[2])
            # None (not computed) is left empty; "x" marks cut-off or failed evaluations
            c_values = [str(x) if x is not None else "" for x in row[3:]]
            f.write(f"  {scenario} & {num_vehicles:13d} & {num_time_steps:14d} &   " + " & ".join(c_values) + " \\\\\n")
        f.write(
            r"""
      \bottomrule
     \end{tabular}
     \label{tab:comp_time_scenario_evaluation}
    \end{table*}
    """
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate predicates on scenarios.")
    parser.add_argument("--threads", type=int, default=1, help="Number of parallel workers.")
    parser.add_argument("--repetitions", type=int, default=5, help="Number of timed repetitions per configuration.")
    parser.add_argument(
        "--cutoff",
        type=float,
        default=CUTOFF_SECONDS,
        help="Cut-off time in seconds per evaluation (default: 20 min); exceeded evaluations are reported as x.",
    )
    args = parser.parse_args()
    comp_summary = eval_scenario(
        scenario_configs, max_workers=args.threads, repetitions=args.repetitions, cutoff=args.cutoff
    )

    store_summary_table()
