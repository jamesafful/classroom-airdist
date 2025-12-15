# backend/reports/figures.py
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _infer_extent_from_grid(G, Vmag_shape):
    """
    Infer (xmin, xmax, ymin, ymax) from a grid-like object G.

    Supported attributes (in order of preference):
      - length/width
      - Lx/Ly
      - xs/ys (1D axes)
      - x/y   (1D axes)
      - xx/yy (2D coordinate fields)
      - fallback to array shape with unit spacing
    """
    # 1) explicit length/width
    if hasattr(G, "length") and hasattr(G, "width"):
        L, W = float(getattr(G, "length")), float(getattr(G, "width"))
        return (0.0, L, 0.0, W)

    # 2) explicit Lx/Ly
    if hasattr(G, "Lx") and hasattr(G, "Ly"):
        return (0.0, float(getattr(G, "Lx")), 0.0, float(getattr(G, "Ly")))

    # 3) 1D axes xs/ys
    if hasattr(G, "xs") and hasattr(G, "ys"):
        xs = np.asarray(getattr(G, "xs"))
        ys = np.asarray(getattr(G, "ys"))
        return (float(xs.min()), float(xs.max()), float(ys.min()), float(ys.max()))

    # 4) 1D axes x/y
    if hasattr(G, "x") and hasattr(G, "y"):
        x = np.asarray(getattr(G, "x"))
        y = np.asarray(getattr(G, "y"))
        return (float(x.min()), float(x.max()), float(y.min()), float(y.max()))

    # 5) 2D coordinate fields xx/yy
    if hasattr(G, "xx") and hasattr(G, "yy"):
        xx = np.asarray(getattr(G, "xx"))
        yy = np.asarray(getattr(G, "yy"))
        return (float(xx.min()), float(xx.max()), float(yy.min()), float(yy.max()))

    # 6) fallback: array shape (unit spacing)
    ny, nx = Vmag_shape
    return (0.0, float(nx), 0.0, float(ny))


def save_velocity_heatmap(G, Vmag, diffusers, returns, path, extent=None):
    """
    Save a velocity magnitude heatmap aligned to physical coordinates.

    Parameters
    ----------
    G : grid-like object (only used if extent is None)
    Vmag : (ny, nx) ndarray
    diffusers : list[(x, y)]
    returns : list[(x, y)]
    path : output PNG path
    extent : tuple(xmin, xmax, ymin, ymax)  # if provided, used directly
    """
    if extent is None:
        xmin, xmax, ymin, ymax = _infer_extent_from_grid(G, Vmag.shape)
    else:
        xmin, xmax, ymin, ymax = extent

    print(f"[figures] saving heatmap with extent=({xmin},{xmax},{ymin},{ymax})")

    plt.figure(figsize=(8, 6), dpi=120)
    im = plt.imshow(
        Vmag,
        origin="lower",
        extent=[xmin, xmax, ymin, ymax],
        aspect="equal",
        cmap="viridis",
        vmin=0.0, vmax=1.0,
    )
    plt.colorbar(im, label="Velocity (m/s)")

    if diffusers:
        xs = [x for (x, _) in diffusers]
        ys = [y for (_, y) in diffusers]
        plt.scatter(xs, ys, s=40, c="#1f77b4", edgecolors="white", zorder=3)

    if returns:
        xr = [x for (x, _) in returns]
        yr = [y for (_, y) in returns]
        plt.scatter(xr, yr, s=60, marker="x", c="#ff7f0e", zorder=3)

    plt.xlabel("m")
    plt.ylabel("m")
    plt.title("Velocity magnitude at occupied height")
    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight")
    plt.close()


def save_edt_histogram(edt_values, path):
    plt.figure()
    plt.hist(edt_values, bins=20, range=(-3, 2))
    plt.xlabel("EDT (°C)")
    plt.ylabel("Count")
    plt.title("EDT distribution")
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()

