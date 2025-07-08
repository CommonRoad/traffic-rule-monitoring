from pathlib import Path

import yaml
from evaluation.monitor.trace_length_eval import eval_trace_length

from src.evaluation.monitor.formula_size_eval import formula_size_eval
from src.evaluation.monitor.lazy_eval import lazy_eval

with open(Path(__file__).parent / "configurations/rv_monitor/evaluation_parameters.yaml", "r") as f:
    params = yaml.safe_load(f)

# Use general parameters
seed = params["general"]["seed"]
num_iters = params["general"]["num_iters"]

# Run eval_trace_length with **kwargs
for eval_params in params["eval_trace_length"]:
    eval_trace_length(**eval_params, num_iters=num_iters, seed=seed)

# Run lazy_eval with **kwargs
lazy_eval(**params["lazy_eval"], num_iters=num_iters, seed=seed)

# Run formula_size_eval with **kwargs
for fs_params in params["formula_size_eval"]:
    formula_size_eval(**fs_params, seed=seed, num_iters=num_iters)
