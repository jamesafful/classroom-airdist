
import numpy as np
from backend.engine.edt_adpi import local_temperature, compute_metrics

def test_edt_adpi_basic():
    V = np.full((10,10), 0.2)
    Tx = local_temperature(V, Tr=24.0, deltaT_C=-8.0)
    stats = compute_metrics(V, Tx)
    assert 0 <= stats["adpi"] <= 1
    assert "edt_hist" in stats
