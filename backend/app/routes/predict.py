# backend/app/routes/predict.py  (only the function body changed)
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from ..schemas import PredictRequest, PredictResponse
from ...engine import grid as gridmod
from ...engine import jets, edt_adpi, compliance, optimizer, uncertainty as uncty
import numpy as np
from ...reports import figures

router = APIRouter(prefix="/predict", tags=["predict"])

@router.post("", response_model=PredictResponse)
def predict(req: PredictRequest):
    # --- Grid creation with a safe lower bound on spacing ---
    # Allow < 0.1 m from UI, but prevent pathological resolutions
    spacing = max(0.05, float(req.solver.grid_spacing_m))  # floor at 5 cm
    G = gridmod.Grid2D(req.room.length_m, req.room.width_m, spacing=spacing)

    sel = req.diffusers.selection[0]
    count = int(sel.count)

    # --- Diffuser placement: MANUAL beats AUTO if provided ---
    manual = getattr(sel, "existing_locations", None)
    if manual and len(manual) > 0:
        try:
            locs = [(float(p["x"]), float(p["y"])) for p in manual]
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid diffuser existing_locations JSON; expected [{\"x\":..,\"y\":..}, ...].")
        # Optionally sync count to manual list
        if count != len(locs):
            count = len(locs)
    else:
        locs = optimizer.greedy_layout(
            G,
            count=count,
            min_wall=req.diffusers.constraints.min_from_walls_m,
            L=req.room.length_m,
            W=req.room.width_m,
        )

    # Bounds check for diffusers
    for i, (x, y) in enumerate(locs):
        if not (0.0 <= x <= req.room.length_m and 0.0 <= y <= req.room.width_m):
            raise HTTPException(status_code=400, detail=f"Diffuser {i} out of bounds: ({x},{y})")

    # --- Even CFM split for now ---
    total_cfm = float(req.ventilation.supply_total_cfm)
    per_cfm = total_cfm / max(1, len(locs))

    # --- Velocity field (supply + optional return bias) ---
    field = jets.velocity_field(G, locs, per_cfm, sel.model_id)

    # Returns: accept multiple; validate bounds
    try:
        returns = [(float(r["x"]), float(r["y"])) for r in req.returns.locations]
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid returns.locations JSON; expected [{\"x\":..,\"y\":..}, ...].")
    for i, (x, y) in enumerate(returns):
        if not (0.0 <= x <= req.room.length_m and 0.0 <= y <= req.room.width_m):
            raise HTTPException(status_code=400, detail=f"Return {i} out of bounds: ({x},{y})")

    if returns:
        field += jets.return_bias(G, returns, strength=0.05)

    # --- Metrics ---
    deltaT = float(req.loads.deltaT_C)
    Vmag = np.linalg.norm(field, axis=2)
    Tx = edt_adpi.local_temperature(Vmag, Tr=24.0, deltaT_C=deltaT)
    stats = edt_adpi.compute_metrics(Vmag, Tx)
    adpi = stats["adpi"]
    draft_area = stats["draft_risk_area_pct"]

    comp = compliance.vrp_classroom(
        req.people.students + req.people.teachers,
        area_m2=req.room.length_m * req.room.width_m,
        supply_cfm=total_cfm,
    )

    u_level, u_pp, drivers = uncty.estimate(req, locs, stats)

    # --- Artifacts ---
    os.makedirs("artifacts", exist_ok=True)
    figures.save_velocity_heatmap(G, Vmag, locs, returns, "artifacts/adpi_map.png")
    figures.save_edt_histogram(stats["edt_values"], "artifacts/edt_hist.png")
    figures.save_layout_csv(locs, per_cfm, "artifacts/layout.csv")

    # --- Response ---
    resp = {
        "adpi": round(float(adpi), 3),
        "adpi_uncertainty_pp": float(u_pp),
        "velocity_stats": {
            "pct_v_lt_0_05": round(float(stats["pct_v_lt_0_05"]), 2),
            "pct_v_gt_0_25": round(float(stats["pct_v_gt_0_25"]), 2),
            "v50_mps": round(float(np.percentile(Vmag, 50)), 3),
            "v95_mps": round(float(np.percentile(Vmag, 95)), 3),
        },
        "edt": {
            "pass_fraction": round(float(stats["edt_pass_fraction"]), 3),
            "histogram_bins": stats["edt_hist"],
        },
        "draft_risk_area_pct": round(float(draft_area), 2),
        "compliance": comp,
        "layout": {
            "diffusers": [{"x": x, "y": y, "cfm": round(per_cfm, 1)} for (x, y) in locs],
            "model": sel.model_id,
            "returns": [{"x": x, "y": y} for (x, y) in returns],
        },
        "warnings": stats["warnings"],
        "uncertainty": {"level": u_level, "drivers": drivers},
        "artifacts": {
            "heatmap_png_url": "/artifacts/adpi_map.png",
            "edt_hist_png_url": "/artifacts/edt_hist.png",
            "coordinates_csv_url": "/artifacts/layout.csv",
        },
        "provenance": {
            "engine_version": "0.1.1",
            "catalog_version": "v0",
            "assumption_preset": "K12_mixing_v1",
        },
        # Debug echo: know exactly what was used
        "debug": {
            "optimize_layout_received": bool(req.solver.optimize_layout),
            "used_diffusers": [{"x": x, "y": y} for (x, y) in locs],
            "used_returns": [{"x": x, "y": y} for (x, y) in returns],
            "grid_spacing_used_m": float(spacing),
            "n_cells": int(Vmag.size),
        },
    }
    return JSONResponse(resp)
