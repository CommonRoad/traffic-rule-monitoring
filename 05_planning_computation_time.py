import concurrent.futures
from pathlib import Path
from typing import List

import crmonitor
import numpy as np
import yaml
from commonroad_rp.utility.config import ReactivePlannerConfiguration
from tabulate import tabulate

from src.evaluation.common.config import (
    EvalConfig,
    activated_intersection_rule_set,
    activated_interstate_rule_set,
    configs,
)
from src.evaluation.planning.rp_planner import run_planner_cr_scenario

comp_summary = np.array(["Scenario Name", "C1", "C2", "C3", "C4", "C5", "C6"]).reshape(1, -1)


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
        rp_config.monitor.trace_step = [10, 1] if conf.iterative_eval else [1]
        rp_config.monitor.short_circuiting = conf.short_circuiting
        rp_config.monitor.hydra_reordering = (
            True  # we need to set this to True to also set a bad reordering for demonstration purposes
        )
        rp_config.monitor.formula_evaluation_mode = (
            crmonitor.FormulaEvaluationMode.globally_early_termination
            if conf.early_termination
            else crmonitor.FormulaEvaluationMode.globally
        )
        rp_config.monitor.hydra_connected_evaluation = conf.connected_eval
        rp_config.monitor.performance_measurement = False
        if conf.reordering:
            with open(Path(__file__).parent / "configurations/predicates/predicate_costs.yaml", "r") as file:
                data = yaml.safe_load(file)
        else:
            with open(Path(__file__).parent / "configurations/predicates/predicate_costs_inverted.yaml", "r") as file:
                data = yaml.safe_load(file)
        rp_config.monitor.predicate_cost = {
            key: [value["cost"], value["probability"]] for key, value in data.get("predicateCost", {}).items()
        }
        rp_config.update()
        computation_times.append(run_planner_cr_scenario(rp_config))
    average_time = sum(computation_times) / len(computation_times)
    return np.round(average_time, 4)


def eval_scenario(res, scenario_path: Path, activated_traffic_rule_sets: List[str], base_idx: int):
    res = np.append(
        res,
        np.array(
            [
                str(scenario_path.stem),
                # len(scenario.obstacles),
                # sum([obs.prediction.final_time_step - obs.initial_state.time_step for obs in scenario.obstacles]),
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

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        futures = []
        for idx, config in enumerate(configs[1:7]):
            futures.append((idx, executor.submit(evaluate, scenario_path, config, activated_traffic_rule_sets)))
        for idx, future in futures:
            res[base_idx, idx + 1] = future.result()

    return res


# print("##### Interstate #######")
# this scenario does not work as goal region time interval not reachable
# eval_scenario(
#     comp_summary,
#     Path(__file__).parent / "scenarios/planning" / "USA_US101-14_2_T-1.xml",
#     activated_interstate_rule_set,
#     1,
# )

eval_scenario(
    comp_summary,
    Path(__file__).parent / "scenarios/motivating_examples" / "USA_US101-22_3_T-1.xml",
    activated_interstate_rule_set,
    1,
)

print("##### Intersection #######")
comp_summary = eval_scenario(
    comp_summary,
    Path(__file__).parent / "scenarios/planning/DEU_TestRightBeforeLeft-1/" / "DEU_TestRightBeforeLeft-1_2_T-1.pb",
    activated_intersection_rule_set,
    1,
)

path = Path(__file__).parent / "output/planning"
if not path.exists():
    path.mkdir(parents=True, exist_ok=True)
print("##### Overall Summary #######")
with open(f"{path}/comp_summary.txt", "w") as f:
    f.write(tabulate(comp_summary, headers="firstrow", tablefmt="latex"))
