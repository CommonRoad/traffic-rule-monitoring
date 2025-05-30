import copy
import dataclasses
import glob
import logging
import statistics
import csv
from typing import Dict, List
import concurrent.futures
import crcpp
import crmonitor
from commonroad.common.file_reader import CommonRoadFileReader

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

    def __str__(self):
        return f"num executions: {self.num_executions}\nnum satisfactions: {self.satisfactions}\ntotal comp time: {self.total_comp_time}\nmin.: {self.min_comp_time}\nmax.: {self.max_comp_time}\navg.: {self.avg_comp_time}\nmedian: {self.median_comp_time}"


pred_cost_collection: Dict[str, PredicateCost] = {}

def evaluate_predicate(pred_name, paths):
    pred = crcpp.predicates()[pred_name]
    logging.debug(f"-------------Evaluating predicate: {pred_name}---------------")
    pred_cost_collection[pred_name] = PredicateCost()
    timer = crcpp.Timer()
    pred_stat = crcpp.PredicateStatistics()
    additional_function_parameters = extract_arg_combinations(pred_name)

    for param_combi in additional_function_parameters:
        for sc_path in paths:
            evaluate_scenario(param_combi, pred, pred_name, pred_stat, sc_path, timer)

    pred_cost_collection[pred_name].num_executions = pred_stat.num_executions
    pred_cost_collection[pred_name].satisfactions = pred_stat.num_satisfaction
    pred_cost_collection[pred_name].total_comp_time = pred_stat.total_computation_time
    pred_cost_collection[pred_name].min_comp_time = min(pred_stat.computation_time)
    pred_cost_collection[pred_name].max_comp_time = max(pred_stat.computation_time)
    pred_cost_collection[pred_name].avg_comp_time = statistics.mean(pred_stat.computation_time)
    pred_cost_collection[pred_name].median_comp_time = statistics.median(pred_stat.computation_time)


def execute_dateset_eval(paths: List[str]):
    """
    Execute the dataset evaluation for all scenarios in the CommonRoad dataset.
    """
    rules = ["R_G1", "R_G2"]
    rel_predicates = []
    for elem in crmonitor.get_traffic_rules_complete():
        for rule in rules:
            if elem[0] != rule:
                continue
            for pred in crcpp.predicates().keys():
                if pred[:-10] in elem[1] and pred == "orientation_towards_predicate" or pred == "in_front_of_predicate":
                    rel_predicates.append(pred)

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(evaluate_predicate, pred_name, paths) for pred_name in rel_predicates]
        concurrent.futures.wait(futures)

    with open('predicate_costs.csv', 'w', newline='') as csvfile:
        fieldnames = [
            'predicate',
            'num_executions',
            'satisfactions',
            'total_comp_time',
            'min_comp_time',
            'max_comp_time',
            'avg_comp_time',
            'median_comp_time'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for pred_name, pred_cost in pred_cost_collection.items():
            writer.writerow({
                'predicate': pred_name,
                'num_executions': pred_cost.num_executions,
                'satisfactions': pred_cost.satisfactions,
                'total_comp_time': pred_cost.total_comp_time,
                'min_comp_time': pred_cost.min_comp_time,
                'max_comp_time': pred_cost.max_comp_time,
                'avg_comp_time': pred_cost.avg_comp_time,
                'median_comp_time': pred_cost.median_comp_time
            })
    for pred_name, pred_cost in pred_cost_collection.items():
        print(f"Predicate: {pred_name}")
        print(pred_cost)
        print("--------------------------------------------------")


def evaluate_scenario(additional_function_parameters, pred, pred_name, pred_stat, sc_path, timer):
    sc, _ = CommonRoadFileReader(sc_path).open()
    logging.debug(f"Evaluating scenario: {sc.scenario_id}")
    for ego in sc.dynamic_obstacles:
        logging.debug(f"Evaluating ego: {ego.obstacle_id}")
        sc_temp = copy.deepcopy(sc)
        sc_temp.remove_obstacle(ego)

        if pred.is_vehicle_dependent:
            for obs in sc_temp.dynamic_obstacles:
                try:
                    pred.statistic_boolean_evaluation(
                        0,
                        crcpp.World(sc_temp),
                        crcpp.Obstacle(ego),
                        timer,
                        pred_stat,
                        crcpp.Obstacle(obs),
                        additional_function_parameters,
                        False,
                    )
                except Exception as e:
                    logging.error(f"Error evaluating predicate {pred_name} for obstacle {ego.obstacle_id}: {e}")
        else:
            try:
                pred.statistic_boolean_evaluation(
                    0,
                    crcpp.World(sc_temp),
                    crcpp.Obstacle(ego),
                    timer,
                    pred_stat,
                    crcpp.Obstacle(sc.dynamic_obstacles[0]),
                    additional_function_parameters,
                    False,
                )
            except Exception as e:
                logging.error(f"Error evaluating predicate {pred_name} for obstacle {ego.obstacle_id}: {e}")


if __name__ == "__main__":
    scenario_paths = [
        path
        for path in glob.glob("/home/sebastian/03_code/commonroad-scenarios/scenarios_2020a/NGSIM/US101/*.xml")
        if "_S-" not in path
    ]
    execute_dateset_eval(scenario_paths[1:8])
