import dataclasses

activated_intersection_rule_set = [
    "R_G1",
    "R_G2",
    "R_G3",
    "R_G4",
    "R_G5",
    "R_U1",
    "R_U2",
    "R_U3",
    "R_U4",
    "R_U5",
]
activated_interstate_rule_set = ["R_G1", "R_G2", "R_G3", "R_G4", "R_G5", "R_I1", "R_I2", "R_I3", "R_I4", "R_I5"]


@dataclasses.dataclass
class EvalConfig:
    name: str = ""
    with_monitor: bool = False
    reordering: bool = False
    short_circuiting: bool = False
    connected_eval: bool = False
    iterative_eval: bool = False
    early_termination: bool = False
    visualization: bool = False


configs = [
    EvalConfig(name="C0"),
    EvalConfig(name="C1", with_monitor=True, visualization=True, reordering=False),  # C1: Baseline
    EvalConfig(
        name="C2", with_monitor=True, short_circuiting=True, reordering=False
    ),  # C2: Baseline with short-circuiting
    EvalConfig(
        name="C3", with_monitor=True, short_circuiting=True, reordering=True
    ),  # C3: Ours without connected evaluation, iterative evaluation, and early termination
    EvalConfig(
        name="C4", with_monitor=True, short_circuiting=True, connected_eval=True, reordering=True
    ),  # C4: Ours without iterative evaluation and early termination
    EvalConfig(
        name="C5", with_monitor=True, short_circuiting=True, connected_eval=True, iterative_eval=True, reordering=True
    ),  # C5: Ours without iterative evaluation
    EvalConfig(
        name="C6",
        with_monitor=True,
        short_circuiting=True,
        connected_eval=True,
        early_termination=True,
        iterative_eval=True,
        reordering=True,
    ),  # C6: Our approach
    EvalConfig(
        name="C7",
        with_monitor=True,
        short_circuiting=True,
        connected_eval=True,
        early_termination=True,
        iterative_eval=True,
        visualization=True,
        reordering=True,
    ),
]
