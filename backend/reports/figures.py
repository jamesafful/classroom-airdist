
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def save_velocity_heatmap(G, Vmag, diffusers, returns, path):
    """
    Save a velocity magnitude heatmap aligned to physical coordinates.

    Assumptions:
    - Vmag has shape (ny, nx) with first index along +y and second along +x.
    - Grid2D exposes either .length/.width or .xs/.ys (monotonic).
    """
    import numpy as np
    import matplotlib.pyplot as plt

    # Resolve room extents from Grid2D
    if hasattr(G, "length") and hasattr(G, "width"):
        L, W = float(G.length), float(G.width)
    elif hasattr(G, "xs") and hasattr(G, "ys"):
        L, W = float(G.xs[-1]), float(G.ys[-1])
    else:
        raise AttributeError("Grid2D must expose (length,width) or (xs,ys)")

    plt.figure(figsize=(8, 6), dpi=120)

    # IMPORTANT: do not transpose; set origin+extent to map array -> world
    im = plt.imshow(
        Vmag,                       # shape (ny, nx)
        origin="lower",             # y=0 at bottom
        extent=[0, L, 0, W],        # x from 0..L, y from 0..W
        aspect="equal",
        cmap="viridis",
        vmin=0.0, vmax=1.0
    )
    plt.colorbar(im, label="Velocity (m/s)")

    # Overlay diffuser and return markers in the SAME coordinate system
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
    plt.hist(edt_values, bins=20, range=(-3,2))
    plt.xlabel("EDT (C)"); plt.ylabel("Count")
    plt.title("EDT distribution")
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()

def save_layout_csv(locs, per_cfm, path):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["x_m","y_m","per_diffuser_cfm"])
        for (x,y) in locs:
            w.writerow([round(x,3), round(y,3), round(per_cfm,1)])
