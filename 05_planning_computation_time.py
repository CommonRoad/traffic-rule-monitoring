from pathlib import Path
from typing import List

import crcpp
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

comp_summary = np.array(
    ["Scenario Name", "num_vehicles", "num_time_steps", "C1", "C2", "C3", "C4", "C5", "C6"]
).reshape(1, -1)


def evaluate(
    eval_name: str,
    sc_path: Path,
    conf: EvalConfig,
    rule_set: List[str],
):
    print(f"Evaluating scenario {eval_name} - {conf}")

    config_path = Path(__file__).parent / "configurations/planning/planning_base_comp_time.yaml"

    rp_config = ReactivePlannerConfiguration.load(config_path, str(sc_path))
    rp_config.update()

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

    rp_config.rule_monitor.set_config(
        sim_param, monitor_config, predicate_cost, predicate_parameter, temporal_parameters
    )
    rp_config.rule_monitor.activate_rule_sets(rule_set)

    run_planner_cr_scenario(rp_config)

    # computation_times = []
    # for _ in range(5):
    #     start_time = time.time()
    #     actual_result = monitor.evaluate_scenarios_on_given_egos([crcpp.World(sc)], [])
    #     end_time = time.time()
    #     computation_times.append(end_time - start_time)
    # average_time = sum(computation_times) / len(computation_times)
    # print(actual_result)
    # print(
    #     f"Average computation time {eval_name}: {average_time:.6f} seconds / Num. vehicles: {len(sc.obstacles)} / Num. time steps: {sum([obs.prediction.final_time_step - obs.initial_state.time_step for obs in sc.obstacles])}"
    # )
    # return np.round(average_time, 4)


def eval_scenario(res, scenario_path, activated_traffic_rule_sets, base_idx):
    # res = np.append(
    #     res,
    #     np.array(
    #         [
    #             str(scenario.scenario_id),
    #             len(scenario.obstacles),
    #             sum([obs.prediction.final_time_step - obs.initial_state.time_step for obs in scenario.obstacles]),
    #             None,
    #             None,
    #             None,
    #             None,
    #             None,
    #             None,
    #         ]
    #     ).reshape(1, -1),
    #     axis=0,
    # )

    for idx, config in enumerate(configs[1:7]):
        evaluate(f"C{idx}", scenario_path, config, activated_traffic_rule_sets)


print("##### Interstate #######")
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
eval_scenario(
    comp_summary,
    Path(__file__).parent / "scenarios/planning/DEU_TestRightBeforeLeft-1_2_T-1.xml",
    activated_intersection_rule_set,
    2,
)

path = Path(__file__).parent / "output/planning"
if not path.exists():
    path.mkdir(parents=True, exist_ok=True)
print("##### Overall Summary #######")
with open(f"{path}/comp_summary.txt", "w") as f:
    f.write(tabulate(comp_summary, headers="firstrow", tablefmt="latex"))
