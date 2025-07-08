from evaluation.monitor.trace_length_eval import eval_trace_length

from src.evaluation.monitor.formula_size_eval import formula_size_eval
from src.evaluation.monitor.lazy_eval import lazy_eval
from src.evaluation.monitor.specifications import (
    specs1_atomic,
    specs1_pred,
    specs2_atomic,
    specs2_pred,
)

eval_trace_length(
    specs1_pred, "running_example_predicate", 2, 0.6, True, 10, range(500, 5500, 500), "Trace Length [x100]", 5
)
eval_trace_length(
    specs2_pred, "dissimilar_predicate", 6, 0.6, True, 10, range(500, 5500, 500), "Trace Length [x100]", 5
)

eval_trace_length(
    specs1_atomic, "running_example_atomic", 2, 1.1, False, 10, range(20000, 220000, 20000), "Trace Length [x10000]", 5
)
eval_trace_length(
    specs2_atomic, "dissimilar_atomic", 6, 1.1, False, 10, range(20000, 220000, 20000), "Trace Length [x10000]", 5
)


lazy_eval(50, 5, 10)


formula_size_eval("formula_size_atomic", 4, 1000, 50, 0.3, True, 10, 5)
formula_size_eval("formula_size_predicate", 4, 1000, 50, 0.3, False, 10, 5)
