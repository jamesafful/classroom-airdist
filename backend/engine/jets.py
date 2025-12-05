
import json, os
import numpy as np

def _load_any_model(model_id: str):
    # Use shipped example catalog only (users can replace with vendor data)
    path = os.path.join("data", "catalogs", "v0", f"{model_id}.json")
    if not os.path.exists(path):
        path = os.path.join("data", "catalogs", "v0", "example_square_cone.json")
    with open(path) as f:
        return json.load(f)

def _interpolate_throw(model: dict, cfm: float, key: str="50") -> float:
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
    return val_ft * 0.3048

def velocity_field(G, diffuser_locs, per_cfm, model_id):
    model = _load_any_model(model_id)
    T50_m = _interpolate_throw(model, per_cfm, key="50")
    sigma = max(0.5, 0.35 * T50_m)
    U0 = max(0.1, per_cfm/1000.0)

    field = np.zeros((G.shape[0], G.shape[1], 2), dtype=float)
    for (x0,y0) in diffuser_locs:
        dx = G.xx - x0
        dy = G.yy - y0
        r2 = dx*dx + dy*dy
        amp = U0 * np.exp(-r2/(2*sigma*sigma))
        norm = np.sqrt(r2) + 1e-6
        field[:,:,0] += amp * dx / norm
        field[:,:,1] += amp * dy / norm
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
