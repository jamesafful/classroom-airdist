
import numpy as np
import yaml, os
from ..app.settings import settings

with open(settings.constants_file) as f:
    C = yaml.safe_load(f)

def local_temperature(Vmag, Tr=24.0, deltaT_C=-8.0):
    gamma = 2.0
    mix = np.exp(-gamma * np.clip(Vmag, 0, 1.0))
    Tx = Tr + deltaT_C * (1.0 - mix)
    return Tx

def edt_field(Tx, Tr, Vmag):
    return (Tx - Tr) - 8.0 * (Vmag - 0.15)

def compute_metrics(Vmag, Tx):
    Tr = 24.0
    edt = edt_field(Tx, Tr, Vmag)
    Tmin = C["edt"]["Tmin_C"]
    Tmax = C["edt"]["Tmax_C"]
    vmax = C["edt"]["vmax_mps"]
    pass_mask = (edt >= Tmin) & (edt <= Tmax) & (Vmag < vmax)
    adpi = float(np.mean(pass_mask))
    pct_low = 100.0 * float(np.mean(Vmag < C["occupied_zone"]["v_low_mps"]))
    pct_high = 100.0 * float(np.mean(Vmag > C["occupied_zone"]["v_high_mps"]))
    draft_area = pct_high
    hist, bin_edges = np.histogram(edt, bins=20, range=(-3.0, 2.0))
    hist_bins = [{"bin": float((bin_edges[i]+bin_edges[i+1])/2), "count": int(hist[i])} for i in range(len(hist))]
    warnings = []
    if pct_high > 10.0: warnings.append("High-velocity area >10% of occupied zone")
    if pct_low > 25.0: warnings.append("Large stagnation area (V<0.05 m/s)")
    return {
        "adpi": adpi,
        "pct_v_lt_0_05": pct_low,
        "pct_v_gt_0_25": pct_high,
        "draft_risk_area_pct": draft_area,
        "edt_pass_fraction": float(np.mean(pass_mask)),
        "edt_hist": hist_bins,
        "edt_values": edt.flatten().tolist(),
        "warnings": warnings,
    }
