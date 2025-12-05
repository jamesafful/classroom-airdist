
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def save_velocity_heatmap(G, Vmag, diffusers, returns, path):
    plt.figure()
    plt.imshow(Vmag.T, origin="lower", extent=(0, G.Lx, 0, G.Ly), aspect="equal")
    if diffusers:
        xs, ys = zip(*diffusers)
        plt.scatter(xs, ys, marker="o")
    if returns:
        rx, ry = zip(*returns)
        plt.scatter(rx, ry, marker="x")
    plt.colorbar(label="Velocity (m/s)")
    plt.title("Velocity magnitude at occupied height")
    plt.xlabel("m"); plt.ylabel("m")
    plt.tight_layout()
    plt.savefig(path, dpi=160)
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
