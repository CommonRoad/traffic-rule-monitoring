import argparse
import copy
import logging
import multiprocessing
import signal
from pathlib import Path
from typing import List, Tuple, Union

import crmonitor
import numpy as np
from commonroad_rp.utility.config import ReactivePlannerConfiguration
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
):
    print(f"Evaluating scenario {sc_path} - {conf}")

    computation_times = []
    for _ in range(1):
        config_path = Path(__file__).parent / "configurations/planning/planning_base_comp_time.yaml"

        rp_config = ReactivePlannerConfiguration.load(config_path, str(sc_path))
        rp_config.monitor.activated_traffic_rules = rule_set
        rp_config.debug.complete_rule_eval = conf.complete_rule_eval
        rp_config.debug.complete_collision_eval = conf.complete_collision_eval
        rp_config.monitor.trace_step = [10, 1] if conf.iterative_eval else [1]
        rp_config.monitor.short_circuiting = conf.short_circuiting
        rp_config.monitor.hydra_reordering = (
            True  # we need to set this to True to also set a bad reordering for demonstration purposes
        )
        rp_config.monitor.formula_evaluation_mode = (
            crmonitor.FormulaEvaluationMode.globally_early_termination.value
            if conf.early_termination
            else crmonitor.FormulaEvaluationMode.globally.value
        )
        rp_config.monitor.hydra_connected_evaluation = conf.connected_eval
        rp_config.monitor.performance_measurement = False
        data = load_pred_costs(conf, rule_set, Path(__file__).parent)
        rp_config.monitor.predicate_cost = {
            key: [value["cost"], value["probability"]] for key, value in data.get("predicateCost", {}).items()
        }
        try:
            rp_config.update()
            computation_times.append(
                run_planner_cr_scenario(
                    rp_config,
                )
            )
        except Exception:
            logging.error(f"Error evaluating predicate scenario from path {str(sc_path)} with config {str(conf)}.")
            computation_times.append(0.0)
    average_time = sum(computation_times) / len(computation_times)
    return np.round(average_time, 4)


def _evaluate_wrapper(arguments: List[Union[Path, List[str], int, EvalConfig, int]]) -> Tuple[int, int, float]:
    scenario_path, activated_traffic_rule_sets, res_idx, conf, idx = arguments
    try:
        return res_idx, idx + 1, evaluate(scenario_path, conf, activated_traffic_rule_sets)
    except Exception:
        logging.error(f"Error in scenario {scenario_path} with config {conf}")
        return res_idx, idx + 1, 0.0


def _timeout_handler(signum, frame):
    raise TimeoutError("Evaluation timed out")


def _evaluate_worker(arguments, queue, timeout=600):
    signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(timeout)
    try:
        res_idx, col_idx, value = _evaluate_wrapper(arguments)
        queue.put((res_idx, col_idx, value))
    except TimeoutError:
        queue.put((arguments[2], arguments[4] + 1, 0.0))
    except Exception:
        queue.put((arguments[2], arguments[4] + 1, 0.0))
    finally:
        signal.alarm(0)


def eval_scenario(config_settings: List[Tuple], max_workers: int = 24, timeout: int = 600) -> np.ndarray:
    res = np.array(["Scenario Name", "C1", "C2", "C3", "C4", "C5", "C6"]).reshape(1, -1)

    evaluations = []
    for base_idx, setting in enumerate(config_settings):
        scenario_path, activated_traffic_rule_sets = setting
        res = np.append(
            res,
            np.array([str(scenario_path.stem), None, None, None, None, None, None]).reshape(1, -1),
            axis=0,
        )
        res = np.append(
            res,
            np.array([str(scenario_path.stem) + "*", None, None, None, None, None, None]).reshape(1, -1),
            axis=0,
        )
        for idx, eval_config in enumerate(configs[1:7]):
            if not any("_U" in rname for rname in activated_traffic_rule_sets) or idx > 1:
                evaluations.append(
                    (scenario_path, activated_traffic_rule_sets, (base_idx + 1) * 2 - 1, eval_config, idx)
                )
                conf_copy = copy.deepcopy(eval_config)
                conf_copy.complete_rule_eval = False
                evaluations.append((scenario_path, activated_traffic_rule_sets, (base_idx + 1) * 2, conf_copy, idx))

    running = []
    queue = multiprocessing.Queue()
    i = 0
    while i < len(evaluations):
        # Start up to max_workers processes
        while len(running) < max_workers and i < len(evaluations):
            p = multiprocessing.Process(target=_evaluate_worker, args=(evaluations[i], queue, timeout))
            p.start()
            running.append((i, p))
            i += 1
        # Check for finished or timed out processes
        for idx, p in running:
            p.join(timeout)
            if p.is_alive():
                logging.error(f"Timeout in evaluation {idx}, killing process.")
                p.terminate()
                p.join()
                res_idx, col_idx = evaluations[idx][2], evaluations[idx][4] + 1
                res[res_idx, col_idx] = 0.0
            else:
                try:
                    res_idx, col_idx, value = queue.get_nowait()
                    res[res_idx, col_idx] = value
                except Exception:
                    res_idx, col_idx = evaluations[idx][2], evaluations[idx][4] + 1
                    res[res_idx, col_idx] = 0.0
        running = []
    # Drain any remaining results
    while not queue.empty():
        try:
            res_idx, col_idx, value = queue.get_nowait()
            res[res_idx, col_idx] = value
        except Exception:
            pass
    return res


scenario_configs = [
    (
        Path(__file__).parent / "scenarios/motivating_examples" / "ZAM_Augmentation-1_1_T-1.xml",
        activated_interstate_rule_set,
    ),
    (
        Path(__file__).parent / "scenarios/planning" / "USA_US101-14_7_T-1.xml",
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
    args = parser.parse_args()

    comp_summary = eval_scenario(scenario_configs, max_workers=args.threads)

    path = Path(__file__).parent / "output/planning"
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    print("##### Overall Summary #######")
    with open(f"{path}/comp_summary.txt", "w") as f:
        f.write(tabulate(comp_summary, headers="firstrow", tablefmt="latex"))
