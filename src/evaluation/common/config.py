import dataclasses


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
