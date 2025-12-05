
from backend.engine.compliance import vrp_classroom

def test_vrp_classroom_basic():
    r = vrp_classroom(Pz_people=30, area_m2=70.0, supply_cfm=1200.0)
    assert r["Vbz_cfm"] > 0
    assert isinstance(r["pass"], bool)
