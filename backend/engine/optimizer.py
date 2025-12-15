# backend/engine/optimizer.py
from __future__ import annotations
import math
from typing import List, Tuple, Any

def _grid_tiling(L: float, W: float, count: int, min_wall: float) -> List[Tuple[float, float]]:
    """Place `count` points on a near-uniform grid inside [0,L]×[0,W],
    respecting `min_wall` clearance from all walls."""
    if count <= 0:
        return []

    x0, x1 = min_wall, max(min_wall, L - min_wall)
    y0, y1 = min_wall, max(min_wall, W - min_wall)

    if x1 <= x0 or y1 <= y0:
        cx, cy = L * 0.5, W * 0.5
        return [(cx, cy) for _ in range(count)]

    # choose grid dims ~square
    nx = max(1, int(round(math.sqrt(count * (L / max(W, 1e-6))))))
    ny = max(1, int(math.ceil(count / nx)))
    while nx * ny < count:
        nx += 1

    xs = [x0 + (x1 - x0) * (i + 0.5) / nx for i in range(nx)]
    ys = [y0 + (y1 - y0) * (j + 0.5) / ny for j in range(ny)]

    pts: List[Tuple[float, float]] = []
    for j in range(ny):
        for i in range(nx):
            if len(pts) < count:
                pts.append((xs[i], ys[j]))
    return pts

def greedy_layout(G: Any, count: int, min_wall: float = 1.2) -> List[Tuple[float, float]]:
    """
    Returns `count` diffuser (x,y) positions inside the room described by `G`.
    Supports Grid2D with any of:
      - Lx/Ly (preferred)
      - x/y  (1-D axes)
      - xx/yy (2-D fields)
    """
    L_try = None
    W_try = None

    if hasattr(G, "Lx") and hasattr(G, "Ly"):
        L_try = float(G.Lx); W_try = float(G.Ly)

    if (L_try is None or W_try is None) and hasattr(G, "x") and hasattr(G, "y"):
        try:
            L_try = float(max(G.x) if len(G.x) else 0.0)
            W_try = float(max(G.y) if len(G.y) else 0.0)
        except Exception:
            pass

    if (L_try is None or W_try is None) and hasattr(G, "xx") and hasattr(G, "yy"):
        try:
            L_try = float(G.xx.max())
            W_try = float(G.yy.max())
        except Exception:
            pass

    if L_try is None or W_try is None:
        raise AttributeError(
            "optimizer.greedy_layout cannot infer room size from Grid2D. "
            "Ensure Grid2D exposes Lx/Ly or axes."
        )

    return _grid_tiling(L_try, W_try, int(count), float(min_wall))

