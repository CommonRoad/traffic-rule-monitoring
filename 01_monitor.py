from pathlib import Path

import yaml
from evaluation.monitor.formula_size_eval import formula_size_eval
from evaluation.monitor.lazy_eval import eval_lazy
from evaluation.monitor.trace_length_eval import eval_trace_length

with open(Path(__file__).parent / "configurations/rv_monitor/evaluation_parameters.yaml", "r") as f:
    params = yaml.safe_load(f)

# Use general parameters
seed = params["general"]["seed"]
num_iters = params["general"]["num_iters"]
with_tex = params["general"]["with_tex"]

for eval_params in params["eval_trace_length"]:
    eval_trace_length(**eval_params, num_iters=num_iters, seed=seed, with_tex=with_tex)

for eval_params in params["lazy_eval"]:
    eval_lazy(**eval_params, num_iters=num_iters, seed=seed, with_tex=with_tex)

for fs_params in params["formula_size_eval"]:
    formula_size_eval(**fs_params, seed=seed, num_iters=num_iters, with_tex=with_tex)
