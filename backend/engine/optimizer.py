# backend/engine/optimizer.py
from __future__ import annotations
import math
from typing import List, Tuple, Any

def _grid_tiling(l: float, w: float, count: int, min_wall: float) -> List[Tuple[float, float]]:
    """Place `count` points on a near-uniform grid inside a rectangle [0,l]x[0,w],
    respecting `min_wall` clearance from all walls."""
    if count <= 0:
        return []

    # usable rectangle after wall clearance
    x0, x1 = min_wall, l - min_wall
    y0, y1 = min_wall, w - min_wall

    # if constraints impossible, fall back to center placement
    if x1 <= x0 or y1 <= y0:
        cx, cy = l / 2.0, w / 2.0
        return [(cx, cy)] * count

    # choose rows x cols close to square that cover `count`
    rows = int(math.floor(math.sqrt(count)))
    cols = int(math.ceil(count / max(1, rows)))
    while rows * cols < count:
        rows += 1

    xs = [x0 + (i + 0.5) * (x1 - x0) / rows for i in range(rows)]
    ys = [y0 + (j + 0.5) * (y1 - y0) / cols for j in range(cols)]

    locs: List[Tuple[float, float]] = []
    for i in range(rows):
        for j in range(cols):
            if len(locs) == count:
                break
            locs.append((xs[i], ys[j]))
        if len(locs) == count:
            break
    return locs

def greedy_layout(
    G: Any,
    count: int,
    min_wall: float = 1.2,
    L: float | None = None,
    W: float | None = None,
) -> List[Tuple[float, float]]:
    """
    Public API compatible with existing calls.
    We optionally take L/W; if not provided, infer from Grid2D safely.
    """
    # Prefer explicit L/W from caller (most robust)
    if L is not None and W is not None:
        return _grid_tiling(float(L), float(W), int(count), float(min_wall))

    # Try to infer from common Grid2D attributes
    L_try = getattr(G, "length", None) or getattr(G, "L", None)
    W_try = getattr(G, "width", None) or getattr(G, "W", None)

    # As a last resort, infer from axis vectors if available
    if (L_try is None or W_try is None) and hasattr(G, "xs") and hasattr(G, "ys"):
        try:
            L_try = float(G.xs[-1])
            W_try = float(G.ys[-1])
        except Exception:
            pass

    if L_try is None or W_try is None:
        raise AttributeError(
            "optimizer.greedy_layout needs room length/width. "
            "Pass L=room.length_m, W=room.width_m from the route."
        )

    return _grid_tiling(float(L_try), float(W_try), int(count), float(min_wall))
