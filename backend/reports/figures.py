# backend/reports/figures.py
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def _infer_extent_from_grid(G, Vmag_shape):
    if hasattr(G, "Lx") and hasattr(G, "Ly"):
        return (0.0, float(G.Lx), 0.0, float(G.Ly))
    if hasattr(G, "x") and hasattr(G, "y"):
        x = np.asarray(G.x); y = np.asarray(G.y)
        return (float(x.min()), float(x.max()), float(y.min()), float(y.max()))
    if hasattr(G, "xx") and hasattr(G, "yy"):
        xx = np.asarray(G.xx); yy = np.asarray(G.yy)
        return (float(xx.min()), float(xx.max()), float(yy.min()), float(yy.max()))
    ny, nx = Vmag_shape
    return (0.0, float(nx), 0.0, float(ny))

def save_velocity_heatmap(G, Vmag, diffusers, returns, path, extent=None):
    if extent is None:
        xmin, xmax, ymin, ymax = _infer_extent_from_grid(G, Vmag.shape)
    else:
        xmin, xmax, ymin, ymax = extent
    print(f"[figures] saving heatmap extent=({xmin},{xmax},{ymin},{ymax})")

    plt.figure(figsize=(8, 6), dpi=120)
    im = plt.imshow(
        Vmag, origin="lower", extent=[xmin, xmax, ymin, ymax],
        aspect="equal", cmap="viridis", vmin=0.0, vmax=1.0
    )
    plt.colorbar(im, label="Velocity (m/s)")

    if diffusers:
        dx = [x for (x, _) in diffusers]; dy = [y for (_, y) in diffusers]
        plt.scatter(dx, dy, s=40, c="#1f77b4", edgecolors="white", zorder=3)
    if returns:
        rx = [x for (x, _) in returns]; ry = [y for (_, y) in returns]
        plt.scatter(rx, ry, s=60, marker="x", c="#ff7f0e", zorder=3)

    plt.xlabel("m"); plt.ylabel("m")
    plt.title("Velocity magnitude @ occupied height")
    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight")
    plt.close()

def save_edt_histogram(edt_values, path):
    plt.figure()
    plt.hist(edt_values, bins=20, range=(-3, 2))
    plt.xlabel("EDT (°C)"); plt.ylabel("Count")
    plt.title("EDT distribution")
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()

def save_layout_csv(locs, per_cfm, path):
    import csv
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["x_m","y_m","per_diffuser_cfm"])
        for (x,y) in locs:
            w.writerow([round(x,3), round(y,3), round(per_cfm,1)])

