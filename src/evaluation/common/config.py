import dataclasses

activated_intersection_rule_set = [
    "R_G1",
]
activated_interstate_rule_set = ["R_G1"]  # , "R_G2", "R_G3", "R_G4", "R_G5", "R_I1", "R_I2", "R_I3", "R_I4", "R_I5"]


@dataclasses.dataclass
class EvalConfig:
    with_monitor: bool = False
    reordering: bool = False
    short_circuiting: bool = True
    connected_eval: bool = False
    iterative_eval: bool = False
    early_termination: bool = False
    visualization: bool = False


# TODO change re-ordering Boolean values; temporary change to get better re-ordering results
configs = [
    EvalConfig(),
    EvalConfig(with_monitor=True, visualization=True, reordering=True),  # C1: Baseline
    EvalConfig(with_monitor=True, short_circuiting=True, reordering=True),  # C2: Baseline with short-circuiting
    EvalConfig(
        with_monitor=True, short_circuiting=True, reordering=False
    ),  # C3: Ours without connected evaluation, iterative evaluation, and early termination
    EvalConfig(
        with_monitor=True, short_circuiting=True, connected_eval=True, reordering=False
    ),  # C4: Ours without iterative evaluation and early termination
    EvalConfig(
        with_monitor=True, short_circuiting=True, connected_eval=True, iterative_eval=True, reordering=False
    ),  # C5: Ours without iterative evaluation
    EvalConfig(
        with_monitor=True,
        short_circuiting=True,
        connected_eval=True,
        early_termination=True,
        iterative_eval=True,
        reordering=False,
    ),  # C6: Our approach
    EvalConfig(
        with_monitor=True,
        short_circuiting=True,
        connected_eval=True,
        early_termination=True,
        iterative_eval=True,
        visualization=True,
        reordering=False,
    ),
]
