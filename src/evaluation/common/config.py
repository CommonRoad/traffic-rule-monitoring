import dataclasses

# Rule sets as in the paper's rule table (Tab. "Considered traffic rules"): all general rules (R-G1 to R-G4) plus the
# rules of the road type (R-IN1 to R-IN5 for intersections, R-I1 to R-I5 for interstates).
activated_intersection_rule_set = ["R_G1", "R_G2", "R_G3", "R_G4", "R_U1", "R_U2", "R_U3", "R_U4", "R_U5"]
activated_interstate_rule_set = ["R_G1", "R_G2", "R_G3", "R_G4", "R_I1", "R_I2", "R_I3", "R_I4", "R_I5"]

# Evaluation step sizes w of the paper (Tab. "Scenario and rule parameters").
trace_step_sizes = [10, 1]


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

    @property
    def latex_name(self) -> str:
        if self.name.startswith("Ours^"):
            return "\\textbf{Ours}$^\\text{" + self.name[-1] + "}$"
        return f"\\textbf{{{self.name}}}"


# The configurations are named as in the paper (Tab. "Configurations for our monitor evaluations").
# Earlier versions used C0 (no monitor) and C1-C6 for the planner baseline, Baseline, C1, C2, Ours, Ours^I, Ours^E.
configs = [
    EvalConfig(name="No monitor"),
    EvalConfig(name="Baseline", with_monitor=True),
    EvalConfig(name="C1", with_monitor=True, connected_eval=True),
    EvalConfig(name="C2", with_monitor=True, short_circuiting=True, connected_eval=True),
    EvalConfig(name="Ours", with_monitor=True, short_circuiting=True, connected_eval=True, reordering=True),
    EvalConfig(
        name="Ours^I",
        with_monitor=True,
        short_circuiting=True,
        connected_eval=True,
        iterative_eval=True,
        reordering=True,
    ),
    EvalConfig(
        name="Ours^E",
        with_monitor=True,
        short_circuiting=True,
        connected_eval=True,
        early_termination=True,
        iterative_eval=True,
        reordering=True,
    ),
]
