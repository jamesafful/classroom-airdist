
import os
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from ..schemas import PredictRequest, PredictResponse
from ...engine import grid as gridmod
from ...engine import jets, edt_adpi, compliance, optimizer, uncertainty as uncty
import numpy as np
from ...reports import figures

router = APIRouter(prefix="/predict", tags=["predict"])

@router.post("", response_model=PredictResponse)
def predict(req: PredictRequest):
    G = gridmod.Grid2D(req.room.length_m, req.room.width_m, spacing=req.solver.grid_spacing_m)

    sel = req.diffusers.selection[0]
    count = sel.count
    if req.solver.optimize_layout or not sel.existing_locations:
        locs = optimizer.greedy_layout(G, count=count, min_wall=req.diffusers.constraints.min_from_walls_m)
    else:
        locs = [(p["x"], p["y"]) for p in (sel.existing_locations or [])]

    total_cfm = float(req.ventilation.supply_total_cfm)
    per_cfm = total_cfm / max(1, len(locs))

    field = jets.velocity_field(G, locs, per_cfm, sel.model_id)

    returns = [(r["x"], r["y"]) for r in req.returns.locations]
    if returns:
        field += jets.return_bias(G, returns, strength=0.05)

    deltaT = req.loads.deltaT_C
    Vmag = np.linalg.norm(field, axis=2)
    Tx = edt_adpi.local_temperature(Vmag, Tr=24.0, deltaT_C=deltaT)
    stats = edt_adpi.compute_metrics(Vmag, Tx)
    adpi = stats["adpi"]
    draft_area = stats["draft_risk_area_pct"]

    comp = compliance.vrp_classroom(req.people.students + req.people.teachers,
                                    area_m2=req.room.length_m * req.room.width_m,
                                    supply_cfm=total_cfm)

    u_level, u_pp, drivers = uncty.estimate(req, locs, stats)

    os.makedirs("artifacts", exist_ok=True)
    figures.save_velocity_heatmap(G, Vmag, locs, returns, "artifacts/adpi_map.png")
    figures.save_edt_histogram(stats["edt_values"], "artifacts/edt_hist.png")
    figures.save_layout_csv(locs, per_cfm, "artifacts/layout.csv")

    resp = {
        "adpi": round(float(adpi), 3),
        "adpi_uncertainty_pp": float(u_pp),
        "velocity_stats": {
            "pct_v_lt_0_05": round(float(stats["pct_v_lt_0_05"]), 2),
            "pct_v_gt_0_25": round(float(stats["pct_v_gt_0_25"]), 2),
            "v50_mps": round(float(np.percentile(Vmag, 50)), 3),
            "v95_mps": round(float(np.percentile(Vmag, 95)), 3),
        },
        "edt": {"pass_fraction": round(float(stats["edt_pass_fraction"]), 3),
                "histogram_bins": stats["edt_hist"]},
        "draft_risk_area_pct": round(float(draft_area), 2),
        "compliance": comp,
        "layout": {
            "diffusers": [{"x": x, "y": y, "cfm": round(per_cfm,1)} for (x,y) in locs],
            "model": sel.model_id,
            "returns": [{"x": x, "y": y} for (x,y) in returns]
        },
        "warnings": stats["warnings"],
        "uncertainty": {"level": u_level, "drivers": drivers},
        "artifacts": {
            "heatmap_png_url": "/artifacts/adpi_map.png",
            "edt_hist_png_url": "/artifacts/edt_hist.png",
            "coordinates_csv_url": "/artifacts/layout.csv",
        },
        "provenance": {"engine_version": "0.1.1", "catalog_version": "v0", "assumption_preset": "K12_mixing_v1"}
    }
    return JSONResponse(resp)
