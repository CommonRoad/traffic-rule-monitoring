import copy
import dataclasses
import glob
import statistics
from typing import Dict, List

import crcpp
from commonroad.common.file_reader import CommonRoadFileReader

from src.evaluation.predicate_collection import predicate_collection_args


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


def execute_dateset_eval(paths: List[str]):
    """
    Execute the dataset evaluation for all scenarios in the CommonRoad dataset.
    """
    for pred_name, pred in crcpp.predicates().items():
        if pred_name in predicate_collection_args.keys():
            continue
        print(f"-------------Evaluating predicate: {pred_name}---------------")
        pred_cost_collection[pred_name] = PredicateCost()
        timer = crcpp.Timer()
        pred_stat = crcpp.PredicateStatistics()
        # if predicate_collection_args.get(pred_name) is not None:
        #    for arg in predicate_collection_args.get(pred_name):
        #        additional_function_parameters.append()
        # else
        #     additional_function_parameters = ["0.0"]

        for sc_path in paths:
            sc, _ = CommonRoadFileReader(sc_path).open()
            print(f"Evaluating scenario: {sc.scenario_id}")
            for ego in sc.dynamic_obstacles:
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
                            print(f"Error evaluating predicate {pred_name} for obstacle {ego.obstacle_id}: {e}")
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
                        print(f"Error evaluating predicate {pred_name} for obstacle {ego.obstacle_id}: {e}")

        pred_cost_collection[pred_name].num_executions = pred_stat.num_executions
        pred_cost_collection[pred_name].satisfactions = pred_stat.num_satisfaction
        pred_cost_collection[pred_name].total_comp_time = pred_stat.total_computation_time
        pred_cost_collection[pred_name].min_comp_time = min(pred_stat.computation_time)
        pred_cost_collection[pred_name].max_comp_time = max(pred_stat.computation_time)
        pred_cost_collection[pred_name].avg_comp_time = statistics.mean(pred_stat.computation_time)
        pred_cost_collection[pred_name].median_comp_time = statistics.median(pred_stat.computation_time)
        print(pred_cost_collection[pred_name])


if __name__ == "__main__":
    scenario_paths = [
        path
        for path in glob.glob("/home/sebastian/03_code/commonroad-scenarios/scenarios_2020a/NGSIM/US101/*.xml")
        if "_S-" not in path
    ]
    execute_dateset_eval(scenario_paths)
