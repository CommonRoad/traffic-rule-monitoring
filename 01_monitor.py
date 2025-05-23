import rvm

from src.evaluation.monitor.formula_size_eval import formula_size_eval
from src.evaluation.monitor.lazy_eval import lazy_eval
from src.evaluation.monitor.specifications import (
    predicate_cost_1,
    predicate_cost_2,
    specs1_atomic,
    specs1_pred,
    specs2_atomic,
    specs2_pred,
    specs_lazy,
)
from src.evaluation.monitor.trace_length_eval import eval_trace_length_atomic
from src.evaluation.monitor.trace_length_eval_predicate import eval_trace_length_predicate

eval_trace_length_predicate(specs1_pred, "running_example_predicate", 2, 0.6)
eval_trace_length_predicate(specs2_pred, "dissimilar_predicate", 6, 0.6)


eval_trace_length_atomic(specs1_atomic, "running_example_atomic", 2, 1.1)
eval_trace_length_atomic(specs2_atomic, "dissimilar_atomic", 6, 1.1)


formulas = [rvm.Parser.parse(form[1], form[0]) for form in specs_lazy]
lazy_eval(rvm.Hydra2(formulas, predicateCosts=predicate_cost_1), 50)
lazy_eval(rvm.Hydra2(formulas, predicateCosts=predicate_cost_2), 50)


formula_size_eval("formula_size_atomic", 4, 1000, 50, 0.3)
