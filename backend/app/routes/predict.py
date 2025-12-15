# backend/app/routes/predict.py
import os, io, csv, json
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from ..schemas import (
    PredictRequest, PredictResponse,
    PredictBatchRequest, PredictBatchResponse
)
from ...engine import grid as gridmod
from ...engine import jets, edt_adpi, compliance, optimizer, uncertainty as uncty
import numpy as np
from ...reports import figures

router = APIRouter(prefix="/predict", tags=["predict"])

def _clamp_grid_spacing(s: float) -> float:
    # prevent silly values: 0.02..1.0 m
    return float(min(1.0, max(0.02, s)))

def _compute_metrics_and_artifacts(req: PredictRequest) -> PredictResponse:
    # build grid
    G = gridmod.Grid2D(req.room.length_m, req.room.width_m, spacing=_clamp_grid_spacing(req.solver.grid_spacing_m))

    # diffuser locations
    sel = req.diffusers.selection[0]
    count = int(sel.count)
    if req.solver.optimize_layout or not sel.existing_locations:
        locs = optimizer.greedy_layout(G, count=count, min_wall=req.diffusers.constraints.min_from_walls_m)
        used_manual = False
    else:
        locs = [(p["x"], p["y"]) for p in (sel.existing_locations or [])]
        # if fewer coords than count, add auto-fill
        if len(locs) < count:
            locs += optimizer.greedy_layout(G, count=count-len(locs),
                                            min_wall=req.diffusers.constraints.min_from_walls_m)
        used_manual = True

    total_cfm = float(req.ventilation.supply_total_cfm)
    per_cfm = total_cfm / max(1, len(locs))

    # velocity field
    field = jets.velocity_field(
        G, locs, per_cfm, sel.model_id,
        v95_target=req.comfort.v95_target_mps,
        v95_blend=req.comfort.v95_blend
    )

    # returns
    returns = [(r["x"], r["y"]) for r in req.returns.locations]
    if returns:
        field += jets.return_bias(G, returns, strength=0.05)

    # diagnostics
    Vmag = np.linalg.norm(field, axis=2)
    Tx = edt_adpi.local_temperature(Vmag, Tr=24.0, deltaT_C=req.loads.deltaT_C)

    # comfort
    stats = edt_adpi.compute_metrics(
        Vmag, Tx,
        Tmin=req.comfort.edt_min_C,
        Tmax=req.comfort.edt_max_C,
        vmax=req.comfort.v_cap_mps
    )
    adpi = stats["adpi"]
    draft_area = stats["draft_risk_area_pct"]

    # code-compliance
    comp = compliance.vrp_classroom(req.people.students + req.people.teachers,
                                    area_m2=req.room.length_m * req.room.width_m,
                                    supply_cfm=total_cfm)

    # uncertainty (stub-aware)
    u_level, u_pp, drivers = uncty.estimate(req, locs, stats)

    # artifacts
    os.makedirs("artifacts", exist_ok=True)
    figures.save_velocity_heatmap(
        G, Vmag, locs, returns, "artifacts/adpi_map.png",
        extent=(0.0, float(req.room.length_m), 0.0, float(req.room.width_m))
    )
    figures.save_edt_histogram(stats["edt_values"], "artifacts/edt_hist.png")
    figures.save_layout_csv(locs, per_cfm, "artifacts/layout.csv")

    # response
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
        "provenance": {"engine_version": "0.1.1", "catalog_version": "v0", "assumption_preset": "K12_mixing_v1"},
        "debug": {
            "optimize_layout_received": bool(req.solver.optimize_layout),
            "used_diffusers": [{"x": x, "y": y} for (x,y) in locs],
            "used_returns": [{"x": x, "y": y} for (x,y) in returns],
            "grid_spacing_used_m": float(G.spacing) if hasattr(G, "spacing") else float(req.solver.grid_spacing_m),
            "n_cells": int(Vmag.size)
        }
    }
    return PredictResponse(**resp)

@router.post("", response_model=PredictResponse)
def predict(req: PredictRequest):
    try:
        return _compute_metrics_and_artifacts(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch", response_model=PredictBatchResponse)
def predict_batch(req: PredictBatchRequest):
    results = []
    for scen in req.scenarios:
        results.append(_compute_metrics_and_artifacts(scen))
    return PredictBatchResponse(results=results)

@router.get("/batch.csv")
def example_batch_csv():
    # small helper that streams a CSV example so users see the batch outputs
    rows = [
        ["scenario","adpi","v95_mps","draft_pct","pct_v_lt_0.05","pct_v_gt_0.25"],
        ["example", 0.42, 0.29, 2.1, 8.5, 1.2],
    ]
    sio = io.StringIO()
    w = csv.writer(sio)
    w.writerows(rows)
    sio.seek(0)
    return StreamingResponse(iter([sio.read()]), media_type="text/csv",
                             headers={"Content-Disposition":"attachment; filename=example_batch.csv"})

