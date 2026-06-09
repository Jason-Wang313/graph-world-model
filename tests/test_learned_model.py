import numpy as np
import pandas as pd

from graph_physics_best_of_n.learned_model import candidate_row, fit_ridge, predict


def test_learned_lite_ridge_outputs_finite_predictions():
    rows = []
    rows.extend(candidate_row(1, 2, "ring_chord", "omitted_edges", "mild"))
    rows.extend(candidate_row(3, 4, "chain", "shifted_rest_lengths", "medium"))
    df = pd.DataFrame(rows)
    model = fit_ridge(df, "real_utility")
    pred = predict(model, df)
    assert pred.shape[0] == df.shape[0]
    assert np.all(np.isfinite(pred))
