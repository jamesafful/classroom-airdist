
import numpy as np
from dataclasses import dataclass

@dataclass
class Grid2D:
    Lx: float
    Ly: float
    spacing: float = 0.6

    def __post_init__(self):
        nx = max(3, int(self.Lx / self.spacing) + 1)
        ny = max(3, int(self.Ly / self.spacing) + 1)
        self.x = np.linspace(self.spacing/2, self.Lx - self.spacing/2, nx)
        self.y = np.linspace(self.spacing/2, self.Ly - self.spacing/2, ny)
        self.xx, self.yy = np.meshgrid(self.x, self.y, indexing="xy")
        self.shape = self.xx.shape
