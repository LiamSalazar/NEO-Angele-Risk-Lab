from __future__ import annotations

from neo_ange.simulation.perturbation import PerturbationConfig, PerturbationEngine


def test_perturb_row_generates_rows_and_bounds() -> None:
    row = {
        "object_key": "A",
        "diameter": 1.0,
        "moid": 0.02,
        "min_close_approach_dist": 0.01,
        "sentry_ip": 1e-5,
        "n_obs_used": 20,
    }

    perturbed = PerturbationEngine().perturb_row(
        row,
        PerturbationConfig(n_simulations=25, random_state=7),
    )

    assert len(perturbed) == 25
    assert (perturbed["moid"] >= 0).all()
    assert (perturbed["min_close_approach_dist"] >= 0).all()
    assert perturbed["sentry_ip"].between(0, 1).all()
    assert set(perturbed["object_key"]) == {"A"}
