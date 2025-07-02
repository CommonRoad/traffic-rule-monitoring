import argparse
import concurrent.futures
import copy
import logging
from pathlib import Path
from typing import List, Tuple

import crmonitor
import numpy as np
from commonroad_rp.utility.config import ReactivePlannerConfiguration
from func_timeout import FunctionTimedOut, func_timeout
from tabulate import tabulate

from src.evaluation.common.config import (
    EvalConfig,
    activated_intersection_rule_set,
    activated_interstate_rule_set,
    configs,
)
from src.evaluation.common.scenario_eval import load_pred_costs
from src.evaluation.planning.rp_planner import run_planner_cr_scenario


def evaluate(
    sc_path: Path,
    conf: EvalConfig,
    rule_set: List[str],
    timeout: int = 600,
):
    print(f"Evaluating scenario {sc_path} - {conf}")

    computation_times = []
    for _ in range(1):
        config_path = Path(__file__).parent / f"configurations/planning/{sc_path.stem}.yaml"

        rp_config = ReactivePlannerConfiguration.load(config_path, str(sc_path))
        rp_config.monitor.activated_traffic_rules = rule_set
        rp_config.debug.complete_rule_eval = conf.complete_rule_eval
        rp_config.debug.complete_collision_eval = conf.complete_collision_eval
        rp_config.monitor.trace_step = [10, 1] if conf.iterative_eval else [1]
        rp_config.monitor.short_circuiting = conf.short_circuiting
        rp_config.monitor.hydra_reordering = (
            True  # we need to set this to True to also set a bad reordering for demonstration purposes
        )
        rp_config.monitor.formula_evaluation_mode = rp_config.monitor.formula_evaluation_mode_val = (
            crmonitor.FormulaEvaluationMode.globally_early_termination.value
            if conf.early_termination
            else crmonitor.FormulaEvaluationMode.globally.value
        )
        rp_config.monitor.hydra_connected_evaluation = conf.connected_eval
        rp_config.monitor.performance_measurement = False
        data = load_pred_costs(conf.reordering, rule_set, Path(__file__).parent)
        rp_config.monitor.predicate_cost = {
            key: [value["cost"], value["probability"]] for key, value in data.get("predicateCost", {}).items()
        }
        try:
            rp_config.update()
            res = func_timeout(
                timeout,
                run_planner_cr_scenario,
                args=(rp_config,),
            )
            computation_times.append(res if res is not None else 0.0)
        except FunctionTimedOut:
            logging.error(
                f"Timout during evaluating of scenario {str(rp_config.scenario.scenario_id)} with config {str(conf)}."
            )
            computation_times.append(0.0)
        except Exception:
            logging.error(f"Error evaluating predicate scenario from path {str(sc_path)} with config {str(conf)}.")
            computation_times.append(0.0)
    average_time = sum(computation_times) / len(computation_times)
    return np.round(average_time, 4)


def eval_scenario(config_settings: List[Tuple], max_workers: int = 24, timeout: int = 600) -> np.ndarray:
    res = np.array(["Scenario Name", "C1", "C2", "C3", "C4", "C5", "C6"]).reshape(1, -1)

    evaluations = []
    for base_idx, setting in enumerate(config_settings):
        scenario_path, activated_traffic_rule_sets = setting
        res = np.append(
            res,
            np.array(
                [
                    str(scenario_path.stem),
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
        res = np.append(
            res,
            np.array(
                [
                    str(scenario_path.stem) + "*",
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
        for idx, eval_config in enumerate(configs[6:7], start=5):
            if not any("_U" in rname for rname in activated_traffic_rule_sets) or idx > 1:
                # only show first case for simple scenario due to computation time
                if "ZAM_Augmentation" in str(scenario_path):
                    conf_copy = copy.deepcopy(eval_config)
                    conf_copy.complete_rule_eval = True
                    conf_copy.complete_collision_eval = True
                    evaluations.append(
                        (
                            scenario_path,
                            activated_traffic_rule_sets,
                            (base_idx + 1) * 2 - 1,
                            conf_copy,
                            idx,
                        )
                    )
                evaluations.append(
                    (
                        scenario_path,
                        activated_traffic_rule_sets,
                        (base_idx + 1) * 2,
                        eval_config,
                        idx,
                    )
                )

    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_conf = {executor.submit(evaluate, conf[0], conf[3], conf[1], timeout): conf for conf in evaluations}
        for future in concurrent.futures.as_completed(future_to_conf):
            conf = future_to_conf[future]
            res[conf[2], conf[4] + 1] = future.result()

    return res


scenario_configs = [
    (
        Path(__file__).parent / "scenarios/motivating_examples" / "ZAM_Augmentation-1_1_T-1.xml",
        activated_interstate_rule_set,
    ),
    (
        Path(__file__).parent / "scenarios/motivating_examples" / "USA_US101-22_5_T-1.xml",
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate predicates on scenarios.")
    parser.add_argument("--threads", type=int, default=24, help="Number of threads to use.")
    parser.add_argument("--timeout", type=int, default=600, help="Timeout in seconds.")
    args = parser.parse_args()

    comp_summary = eval_scenario(scenario_configs, max_workers=args.threads, timeout=args.timeout)

    path = Path(__file__).parent / "output/planning"
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    print("##### Overall Summary #######")
    with open(f"{path}/comp_summary.txt", "w") as f:
        f.write(tabulate(comp_summary, headers="firstrow", tablefmt="latex"))
