# backend/engine/jets.py
import json, os
import numpy as np

def _load_any_model(model_id: str):
    path = os.path.join("data", "catalogs", "v0", f"{model_id}.json")
    if not os.path.exists(path):
        path = os.path.join("data", "catalogs", "v0", "example_square_cone.json")
    with open(path) as f:
        return json.load(f)

def _interp_throw(model: dict, cfm: float, key: str="50") -> float:
    tab = model["throws_fpm"][key]
    xs = [p["cfm"] for p in tab]
    ys_ft = [p["throw_ft"] for p in tab]
    if cfm <= xs[0]: val_ft = ys_ft[0]
    elif cfm >= xs[-1]: val_ft = ys_ft[-1]
    else:
        val_ft = ys_ft[0]
        for i in range(len(xs)-1):
            if xs[i] <= cfm <= xs[i+1]:
                t = (cfm - xs[i])/(xs[i+1]-xs[i])
                val_ft = ys_ft[i]*(1-t) + ys_ft[i+1]*t
                break
    return val_ft * 0.3048  # ft → m

def velocity_field(G, diffuser_locs, per_cfm, model_id, v95_target=None, v95_blend=1.0):
    """
    Build a 2-D horizontal velocity field at occupied height from N ceiling diffusers.

    Parameters
    ----------
    per_cfm : float   per-diffuser airflow [cfm]
    v95_target : Optional[float]  If provided (e.g., 0.30), scale the field so that v95≈target.
    v95_blend : float in [0..1]   1.0=full normalization; 0.5=halfway; 0.0=disabled.
    """
    model = _load_any_model(model_id)
    T50_m = _interp_throw(model, float(per_cfm), key="50")

    # crude Gaussian jet spread & amplitude
    sigma = max(0.6, 0.50 * T50_m)
    U0 = max(0.08, 0.00025 * float(per_cfm) + 0.05)

    field = np.zeros((G.shape[0], G.shape[1], 2), dtype=float)
    for (x0,y0) in diffuser_locs:
        dx = G.xx - x0
        dy = G.yy - y0
        r2 = dx*dx + dy*dy
        amp = U0 * np.exp(-r2/(2*sigma*sigma))
        norm = np.sqrt(r2) + 1e-6
        field[:,:,0] += amp * dx / norm
        field[:,:,1] += amp * dy / norm

    # optional: add one or more returns as sinks in the route via return_bias()

    # normalize velocities so v95 ≈ v95_target (if provided)
    if v95_target is not None and 0.0 <= v95_blend <= 1.0:
        Vmag = np.linalg.norm(field, axis=2)
        v95 = float(np.percentile(Vmag, 95))
        if v95 > 1e-6:
            scale = (v95_target / v95)
            field *= ( (1.0 - v95_blend) + v95_blend * scale )

    return field

def return_bias(G, returns, strength=0.05):
    fb = np.zeros((G.shape[0], G.shape[1], 2), dtype=float)
    for (xr, yr) in returns:
        dx = xr - G.xx
        dy = yr - G.yy
        r = np.sqrt(dx*dx + dy*dy) + 1e-6
        fb[:,:,0] += strength * dx / r
        fb[:,:,1] += strength * dy / r
    return fb

