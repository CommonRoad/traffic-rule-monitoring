import argparse
import concurrent.futures
import copy
import csv
import dataclasses
import enum
import logging
import statistics
from pathlib import Path
from typing import Dict, List

import crcpp
import crmonitor
import yaml
from func_timeout import FunctionTimedOut, func_timeout

from src.evaluation.common.config import activated_intersection_rule_set, activated_interstate_rule_set
from src.evaluation.common.scenario_eval import load_scenario
from src.evaluation.predicate_collection import extract_arg_combinations


@dataclasses.dataclass
class PredicateCost:
    num_executions: int = 0
    satisfactions: int = 0
    total_comp_time: float = 0.0
    min_comp_time: float = 0.0
    max_comp_time: float = 0.0
    avg_comp_time: float = 0.0
    median_comp_time: float = 0.0
    satisfaction_probability: float = 0.0
    cost_total: float = 0.0
    cost_avg: float = 0.0
    cost_median: float = 0.0
    cost_max: float = 0.0

    def __str__(self):
        return (
            f"num executions: {self.num_executions}\n"
            f"num satisfactions: {self.satisfactions}\n"
            f"total comp time: {self.total_comp_time}\n"
            f"min.: {self.min_comp_time}\n"
            f"max.: {self.max_comp_time}\n"
            f"avg.: {self.avg_comp_time}\n"
            f"median: {self.median_comp_time}\n"
            f"satisfaction probability: {self.satisfaction_probability}\n"
            f"cost total: {self.cost_total}\n"
            f"cost avg: {self.cost_avg}\n"
            f"cost median: {self.cost_median}\n"
            f"cost max: {self.cost_max}\n"
        )


pred_cost_collection: Dict[str, PredicateCost] = {}


def evaluate_predicate(pred_name: str, paths: List[Path], step_size: int):
    pred = crcpp.predicates()[pred_name]
    logging.info(f"-------------Evaluating predicate: {pred_name}---------------")
    pred_cost_collection[pred_name] = PredicateCost()
    timer = crcpp.Timer()
    pred_stat = crcpp.PredicateStatistics()
    additional_function_parameters = extract_arg_combinations(pred_name)

    for param_combi in additional_function_parameters:
        for sc_path in paths:
            evaluate_scenario(param_combi, pred, pred_name, pred_stat, sc_path, timer, step_size)

    pred_cost_collection[pred_name].num_executions = pred_stat.num_executions
    pred_cost_collection[pred_name].satisfactions = pred_stat.num_satisfaction
    pred_cost_collection[pred_name].total_comp_time = pred_stat.total_computation_time
    pred_cost_collection[pred_name].min_comp_time = min(pred_stat.computation_time)
    pred_cost_collection[pred_name].max_comp_time = max(pred_stat.computation_time)
    pred_cost_collection[pred_name].avg_comp_time = statistics.mean(pred_stat.computation_time)
    pred_cost_collection[pred_name].median_comp_time = statistics.median(pred_stat.computation_time)
    if pred_stat.num_executions > 0:
        pred_cost_collection[pred_name].satisfaction_probability = pred_stat.num_satisfaction / pred_stat.num_executions


class ScenarioType(enum.Enum):
    INTERSTATE = "interstate"
    INTERSECTION = "intersection"


def execute_dateset_eval(paths: List[Path], scenario_type: ScenarioType, max_workers: int = 24, step_size: int = 4):
    """
    Execute the dataset evaluation for all scenarios in the CommonRoad dataset.
    """
    if scenario_type == ScenarioType.INTERSTATE:
        rel_predicates = extract_relevant_predicates(activated_interstate_rule_set)
    else:
        rel_predicates = extract_relevant_predicates(activated_intersection_rule_set)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(evaluate_predicate, pred_name, paths, step_size) for pred_name in rel_predicates]
        concurrent.futures.wait(futures)

    max_cost_total = max(pred_eval.total_comp_time for pred_eval in pred_cost_collection.values())
    max_cost_avg = max(pred_eval.avg_comp_time for pred_eval in pred_cost_collection.values())
    max_cost_median = max(pred_eval.median_comp_time for pred_eval in pred_cost_collection.values())
    max_cost_max = max(pred_eval.max_comp_time for pred_eval in pred_cost_collection.values())

    for pred_name in pred_cost_collection.keys():
        pred_cost_collection[pred_name].cost_total = (
            100 * pred_cost_collection[pred_name].total_comp_time / max_cost_total
        )
        pred_cost_collection[pred_name].cost_avg = 100 * pred_cost_collection[pred_name].avg_comp_time / max_cost_avg
        pred_cost_collection[pred_name].cost_median = (
            100 * pred_cost_collection[pred_name].median_comp_time / max_cost_median
        )
        pred_cost_collection[pred_name].cost_max = 100 * pred_cost_collection[pred_name].max_comp_time / max_cost_max

    path = Path(__file__).parent / "output/predicates/"
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    store_result(scenario_type)
    store_result_yaml(scenario_type)
    store_selected_results_tex(scenario_type)
    for pred_name, pred_eval in pred_cost_collection.items():
        print(f"Predicate: {pred_name}")
        print(pred_eval)
        print("--------------------------------------------------")


def extract_relevant_predicates(rules: List[str]) -> List[str]:
    rel_predicates = []
    for elem in crmonitor.get_traffic_rules_complete():
        for rule in rules:
            if elem[0] != rule:
                continue
            for pred in crcpp.predicates().keys():
                if pred[:-10] in elem[1]:
                    rel_predicates.append(pred)
    return rel_predicates


def store_result(scenario_type: ScenarioType):
    with open(
        Path(__file__).parent / f"output/predicates/predicate_{scenario_type.value}_costs.csv", "w", newline=""
    ) as csvfile:
        fieldnames = [
            "predicate",
            "num_executions",
            "satisfactions",
            "total_comp_time",
            "min_comp_time",
            "max_comp_time",
            "avg_comp_time",
            "median_comp_time",
            "satisfaction_probability",
            "cost_total",
            "cost_avg",
            "cost_median",
            "cost_max",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        for pred_name, pred_cost in pred_cost_collection.items():
            writer.writerow(
                {
                    "predicate": pred_name[:-10],
                    "num_executions": pred_cost.num_executions,
                    "satisfactions": pred_cost.satisfactions,
                    "total_comp_time": pred_cost.total_comp_time,
                    "min_comp_time": pred_cost.min_comp_time,
                    "max_comp_time": pred_cost.max_comp_time,
                    "avg_comp_time": pred_cost.avg_comp_time,
                    "median_comp_time": pred_cost.median_comp_time,
                    "satisfaction_probability": pred_cost.satisfaction_probability,
                    "cost_total": pred_cost.cost_total,
                    "cost_avg": pred_cost.cost_avg,
                    "cost_median": pred_cost.cost_median,
                    "cost_max": pred_cost.cost_max,
                }
            )


def store_selected_results_tex(scenario_type: ScenarioType):
    hardcoded = {
        "a": (1.0, 100.0),
        "b": (1.0, 100.0),
        "c": (100.0, 0.0),
        "d": (100.0, 0.0),
    }

    selected = [
        ("a", *hardcoded["a"]),
        ("b", *hardcoded["b"]),
        ("c", *hardcoded["c"]),
        ("d", *hardcoded["d"]),
        ("velocity_below_threshold_predicate", None, None),
        ("in_front_of_predicate", None, None),
        ("in_same_lane_predicate", None, None),
        ("lane_based_orientation_similar_predicate", None, None),
        ("in_neighboring_lane_predicate", None, None),
        ("in_single_lane_predicate", None, None),
        ("on_similar_oriented_lanelet_with_type_predicate", None, None),
        ("drives_faster_predicate", None, None),
        ("keeps_safe_distance_prec_predicate", None, None),
        ("velocity_below_threshold_predicate", None, None),
        ("orientation_towards_predicate", None, None),
    ]

    def to_latex_macro(pred_name: str) -> str:
        if pred_name in hardcoded:
            return f"${pred_name}$"
        parts = pred_name.split("_")
        return f"$\\{parts[0]}" + "".join([p.capitalize() for p in parts[1:]]) + "$"

    # Fill in cost/probability for non-hardcoded predicates from pred_cost_collection
    rows = []
    for name, cost, prob in selected:
        if cost is None:
            if name in pred_cost_collection:
                cost = pred_cost_collection[name].cost_median
                prob = pred_cost_collection[name].satisfaction_probability * 100
            else:
                cost = ""
                prob = ""
        rows.append((to_latex_macro(name), f"{cost:.4f}" if cost != "" else "", f"{prob:.1f}\\%" if prob != "" else ""))

    # Write table, 3 predicates per row
    output_path = Path(__file__).parent / f"output/predicates/predicate_costs_{scenario_type.value}_selected.tex"
    with open(output_path, "w") as f:
        f.write("\\begin{table*}[!tb]\n")
        f.write("\t\\centering\n")
        f.write("\t\\caption{Predicate costs and probabilities.}\n")
        f.write("\t\\center\n")
        f.write("\t\\begin{tabular}{@{}lcccccccc@{}} \\toprule\n")
        f.write("\t\t\\textbf{Name} & \\textbf{$\\costPredicate$} & \\textbf{$\\probabilityPredicate$} & ")
        f.write("\\textbf{Name} & \\textbf{$\\costPredicate$} & \\textbf{$\\probabilityPredicate$} & ")
        f.write("\\textbf{Name} & \\textbf{$\\costPredicate$} & \\textbf{$\\probabilityPredicate$}  \\\\ \\midrule\t\n")
        for i in range(0, len(rows), 3):
            row = []
            for j in range(3):
                if i + j < len(rows):
                    row.extend(rows[i + j])
                else:
                    row.extend(["", "", ""])
            f.write("\t\t" + " & ".join(row) + " \\\\\n")
        f.write("\t\\bottomrule\n")
        f.write("\t\\end{tabular}\n")
        f.write("\t\\label{tab:predicate_cost_overview}\n")
        f.write("\\end{table*}\n")


def store_result_yaml(scenario_type: ScenarioType):
    data = {"predicateCost": {}}
    for pred_name, pred_cost in pred_cost_collection.items():
        data["predicateCost"][pred_name[:-10]] = {
            "cost": float(f"{pred_cost.cost_median:.4f}"),
            "probability": float(f"{pred_cost.satisfaction_probability:.4f}"),
        }
    with open(Path(__file__).parent / f"output/predicates/predicate_costs_{scenario_type.value}.yaml", "w") as f:
        yaml.safe_dump(data, f, sort_keys=False)

    data = {"predicateCost": {}}
    for pred_name, pred_cost in pred_cost_collection.items():
        data["predicateCost"][pred_name[:-10]] = {
            "cost": float(f"{(100 - pred_cost.cost_median):.4f}"),
            "probability": float(f"{(1 - pred_cost.satisfaction_probability):.4f}"),
        }
    with open(
        Path(__file__).parent / f"output/predicates/predicate_costs_{scenario_type.value}_inverted.yaml", "w"
    ) as f:
        yaml.safe_dump(data, f, sort_keys=False)


def evaluate_scenario(
    additional_function_parameters: List[str],
    pred: crcpp.CommonRoadPredicate,
    pred_name: str,
    pred_stat: crcpp.PredicateStatistics,
    sc_path: Path,
    timer: crcpp.Timer,
    step_size: int,
):
    sc = load_scenario(sc_path)
    logging.debug(f"Evaluating scenario: {sc.scenario_id}")
    for ego in sc.dynamic_obstacles:
        logging.debug(f"Evaluating ego: {ego.obstacle_id}")
        sc_temp = copy.deepcopy(sc)
        sc_temp.remove_obstacle(ego)

        for time_step in range(ego.initial_state.time_step, ego.prediction.final_time_step, step_size):
            if pred.is_vehicle_dependent:
                for obs in sc_temp.dynamic_obstacles:
                    if obs.state_at_time(time_step) is None:
                        continue
                    try:
                        func_timeout(
                            0.1,
                            pred.statistic_boolean_evaluation,
                            args=(
                                time_step,
                                crcpp.World(sc_temp),
                                crcpp.Obstacle(ego),
                                timer,
                                pred_stat,
                                crcpp.Obstacle(obs),
                                additional_function_parameters,
                                False,
                            ),
                        )
                    except FunctionTimedOut:
                        logging.error(
                            f"Timout during evaluating predicate {pred_name} for ego vehicle {ego.obstacle_id} at time step {time_step}."
                        )
                    except Exception as e:
                        logging.error(
                            f"Error evaluating predicate {pred_name} for ego {ego.obstacle_id} and obstacle {obs.obstacle_id} at time step {time_step}: {e}"
                        )
            else:
                try:
                    func_timeout(
                        0.1,
                        pred.statistic_boolean_evaluation,
                        args=(
                            time_step,
                            crcpp.World(sc_temp),
                            crcpp.Obstacle(ego),
                            timer,
                            pred_stat,
                            crcpp.Obstacle(sc.dynamic_obstacles[0]),  # use random obstacle as it won't be used
                            additional_function_parameters,
                            False,
                        ),
                    )
                except FunctionTimedOut:
                    logging.error(
                        f"Timout during evaluating predicate {pred_name} for ego vehicle {ego.obstacle_id} at time step {time_step}."
                    )
                except Exception as e:
                    logging.error(
                        f"Error evaluating predicate {pred_name} for ego vehicle {ego.obstacle_id} at time step {time_step}: {e}"
                    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate predicates on scenarios.")
    parser.add_argument("--threads", type=int, default=24, help="Number of threads to use.")
    parser.add_argument("--step_size", type=int, default=10, help="Time step step size.")
    args = parser.parse_args()

    intersection_paths = [
        path
        for ext in ("xml", "pb")
        for path in (Path(__file__).parent / "scenarios/planning/DEU_TestRightBeforeLeft-1").rglob(f"*.{ext}")
        if "_S-" not in str(path) and ("_T-" in str(path) and "-SC" not in str(path))
    ]
    #  execute_dateset_eval(intersection_paths, ScenarioType.INTERSECTION, max_workers=args.threads)

    interstate_paths = [
        path
        for ext in ("xml", "pb")
        for path in (Path(__file__).parent / "scenarios/").rglob(f"*.{ext}")
        if "_S-" not in str(path) and ("_T-" in str(path) and "-SC" not in str(path)) and path not in intersection_paths
    ]
    execute_dateset_eval(interstate_paths, ScenarioType.INTERSTATE, max_workers=args.threads, step_size=args.step_size)
