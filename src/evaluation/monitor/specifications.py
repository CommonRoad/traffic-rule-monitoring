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

specs_lazy = [("S1", "G(low_comp_time('rand') | high_comp_time('rand'))")]

predicate_cost_1 = {
    "low_comp_time": [1.0, 1.0, 0.0],
    "high_comp_time": [100.0, 0.0, 0.0],
}

predicate_cost_2 = {
    "low_comp_time": [100.0, 0.0, 0.0],
    "high_comp_time": [1.0, 1.0, 0.0],
}
