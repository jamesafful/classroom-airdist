# backend/engine/jets.py
from __future__ import annotations
import json, os
import numpy as np
from typing import List, Tuple

# -----------------------------
# Catalog helpers
# -----------------------------
def _load_any_model(model_id: str) -> dict:
    """Load a simple diffuser model; fall back to example if missing."""
    path = os.path.join("data", "catalogs", "v0", f"{model_id}.json")
    if not os.path.exists(path):
        path = os.path.join("data", "catalogs", "v0", "example_square_cone.json")
    with open(path) as f:
        return json.load(f)

def _interpolate_throw(model: dict, cfm: float, key: str = "50") -> float:
    """Linear interpolate throw (in meters) for the given CFM at 'key' (e.g., '50' fpm)."""
    tab = model["throws_fpm"][key]
    xs = [p["cfm"] for p in tab]
    ys_ft = [p["throw_ft"] for p in tab]
    if cfm <= xs[0]:
        val_ft = ys_ft[0]
    elif cfm >= xs[-1]:
        val_ft = ys_ft[-1]
    else:
        val_ft = ys_ft[0]
        for i in range(len(xs) - 1):
            if xs[i] <= cfm <= xs[i + 1]:
                t = (cfm - xs[i]) / (xs[i + 1] - xs[i])
                val_ft = ys_ft[i] * (1 - t) + ys_ft[i + 1] * t
                break
    return val_ft * 0.3048  # ft -> m

# -----------------------------
# Jet surrogate
# -----------------------------
def _four_lobe(theta: np.ndarray, sharpness: float = 3.0) -> np.ndarray:
    """
    4-way directivity envelope, 0..1.
    Peaks along cardinal axes (0, 90, 180, 270 deg).
    """
    # abs(cos(2θ)) gives 4 lobes; raise to sharpen.
    return np.abs(np.cos(2.0 * theta)) ** sharpness

def velocity_field(
    G,
    diffuser_locs: List[Tuple[float, float]],
    per_cfm: float,
    model_id: str,
    use_lobes: bool = True,
) -> np.ndarray:
    """
    Build a horizontal velocity vector field from multiple diffusers.

    - Peaks slightly off the diffuser (core plateau), no zero hole at r=0.
    - Decays with distance roughly according to throw.
    - Optionally applies a 4-lobe pattern to mimic 4-way cones.
    """
    model = _load_any_model(model_id)
    T50_m = _interpolate_throw(model, per_cfm, key="50")

    # Core/decay are tied to throw, with reasonable floors.
    core = max(0.25, 0.20 * T50_m)   # [m] near-source region before decay
    lam  = max(1.00, 0.50 * T50_m)   # [m] e-folding decay length

    # Base amplitude scaling from per-outlet flow (tuned to comfort-ish speeds)
    # You can adjust these coefficients per model type.
    U0 = max(0.08, 0.00022 * per_cfm + 0.06)  # ~0.10–0.30 m/s for typical classroom flows

    # Mesh
    X = getattr(G, "xx")
    Y = getattr(G, "yy")
    ny, nx = X.shape
    field = np.zeros((ny, nx, 2), dtype=float)

    for (x0, y0) in diffuser_locs:
        dx = X - x0
        dy = Y - y0
        r  = np.hypot(dx, dy)
        eps = 1e-6

        # Unit direction (defined everywhere)
        r_eff = np.maximum(r, eps)
        ux_dir = dx / r_eff
        uy_dir = dy / r_eff

        # Core + decay:
        # - flat (≈1) inside 'core'
        # - exponential decay outside
        V_shape = np.exp(-(np.maximum(r - core, 0.0) / lam))

        if use_lobes:
            theta = np.arctan2(dy, dx)
            V_shape = V_shape * _four_lobe(theta, sharpness=3.0)

        V_local = U0 * V_shape

        field[:, :, 0] += ux_dir * V_local
        field[:, :, 1] += uy_dir * V_local

    # Soft cap to keep maps readable and stable across inputs
    Vmag = np.linalg.norm(field, axis=2)
    v95 = float(np.percentile(Vmag, 95))
    target_v95 = 0.30
    if v95 > target_v95 and v95 > 1e-6:
        field *= (target_v95 / v95)

    return field

# -----------------------------
# Return bias (weak inward pull)
# -----------------------------
def return_bias(G, returns: List[Tuple[float, float]], strength: float = 0.05) -> np.ndarray:
    """
    Add a gentle bias pointing toward each return location.
    """
    X = getattr(G, "xx")
    Y = getattr(G, "yy")
    ny, nx = X.shape
    fb = np.zeros((ny, nx, 2), dtype=float)
    for (xr, yr) in returns:
        dx = xr - X
        dy = yr - Y
        r = np.hypot(dx, dy) + 1e-6
        fb[:, :, 0] += strength * dx / r
        fb[:, :, 1] += strength * dy / r
    return fb
