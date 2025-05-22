from src.evaluation.monitor.trace_length_eval import eval_trace_length_atomic
from src.evaluation.monitor.trace_length_eval_predicate import eval_trace_length_predicate

specs1_pred = [
    ("S1", "G((a('rand')) S[0, 4] (b('rand')))"),
    (
        "S2",
        "G((a('rand')) U[0, 4] (b('rand')))",
    ),
    ("S3", "G((a('rand')) U[0, 4] (b('rand')) & (a('rand')) S[0, 4] (b('rand')))"),
]

specs2_pred = [
    ("S1", "G(P[0, 4] (a('rand')))"),
    (
        "S2",
        "G(X[0, 4] (b('rand')))",
    ),
    ("S3", "G((c('rand')) U[0, 4] (d('rand')) & (e('rand')) S[0, 4] (f('rand')))"),
]


specs1_atomic = [
    ("S1", "G((a) S[0, 4] (b))"),
    (
        "S2",
        "G((a) U[0, 4] (b))",
    ),
    ("S3", "G((a) U[0, 4] (b) & (a) S[0, 4] (b))"),
]

specs2_atomic = [
    ("S1", "G(P[0, 4] a)"),
    (
        "S2",
        "G(X[0, 4] b)",
    ),
    ("S3", "G((c) U[0, 4] (d) & (e) S[0, 4] (f))"),
]


eval_trace_length_predicate(specs1_pred, "running_example_predicate", 2, 0.6)
eval_trace_length_predicate(specs2_pred, "dissimilar_predicate", 6, 0.6)


eval_trace_length_atomic(specs1_atomic, "running_example_atomic", 2, 1.1)
eval_trace_length_atomic(specs2_atomic, "dissimilar_atomic", 6, 1.1)

