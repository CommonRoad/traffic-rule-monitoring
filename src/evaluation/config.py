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


configs = [
    EvalConfig(),
    EvalConfig(with_monitor=True, visualization=True),
    EvalConfig(with_monitor=True, short_circuiting=True),
    EvalConfig(with_monitor=True, short_circuiting=True, reordering=True),
    EvalConfig(with_monitor=True, short_circuiting=True, connected_eval=True, reordering=True),
    EvalConfig(with_monitor=True, short_circuiting=True, connected_eval=True, early_termination=True, reordering=True),
    EvalConfig(
        with_monitor=True,
        short_circuiting=True,
        connected_eval=True,
        early_termination=True,
        iterative_eval=True,
        reordering=True,
    ),
    EvalConfig(
        with_monitor=True,
        short_circuiting=True,
        connected_eval=True,
        early_termination=True,
        iterative_eval=True,
        visualization=True,
        reordering=True,
    ),
]
