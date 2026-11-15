from pathlib import Path

import yaml

from evaluation.monitor.formula_size_eval import formula_size_eval

# Evaluates the computation time of the monitor over the formula size. Not part of the paper.
with open(Path(__file__).parent.parent / "configurations/rv_monitor/evaluation_parameters.yaml", "r") as f:
    params = yaml.safe_load(f)

seed = params["general"]["seed"]
num_iters = params["general"]["num_iters"]
with_tex = params["general"]["with_tex"]

for fs_params in params["formula_size_eval"]:
    formula_size_eval(**fs_params, seed=seed, num_iters=num_iters, with_tex=with_tex)
