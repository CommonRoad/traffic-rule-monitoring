import dataclasses

activated_intersection_rule_set = [
    "R_G1",
    "R_G2",
    "R_G3",
 #   "R_G4",
 #   "R_G5",
  #  "R_U1",
    "R_U2",
 #   "R_U3",
 #   "R_U4",
    "R_U5",
    "R_U12",
]
activated_interstate_rule_set = ["R_G1", "R_G2", "R_G3", "R_G4", "R_G5", "R_I1", "R_I2", "R_I3", "R_I4", "R_I5"]


@dataclasses.dataclass
class EvalConfig:
    name: str = ""
    connected_eval: bool = False
    short_circuiting: bool = False
    reordering: bool = False
    iterative_eval: bool = False
    early_termination: bool = False
    check_results: bool = False
    with_monitor: bool = False
    complete_rule_eval: bool = False
    complete_collision_eval: bool = False


configs = [
    EvalConfig(name="C0"),
    EvalConfig(name="C1", with_monitor=True),  # C1: Baseline
    EvalConfig(name="C2", with_monitor=True, connected_eval=True),  # C2: connected evaluation
    EvalConfig(
        name="C3", with_monitor=True, short_circuiting=True, connected_eval=True
    ),  # C3: connected evaluation and short-circuiting
    EvalConfig(
        name="C4", with_monitor=True, short_circuiting=True, connected_eval=True, reordering=True
    ),  # C4: connected evaluation, short-circuiting, and reordering
    EvalConfig(
        name="C5", with_monitor=True, short_circuiting=True, connected_eval=True, iterative_eval=True, reordering=True
    ),  # C5: connected evaluation, short-circuiting, reordering, and iterative evaluation
    EvalConfig(
        name="C6",
        with_monitor=True,
        short_circuiting=True,
        connected_eval=True,
        early_termination=True,
        iterative_eval=True,
        reordering=True,
    ),  # C6: connected evaluation, short-circuiting, reordering, iterative evaluation, and early termination
]
