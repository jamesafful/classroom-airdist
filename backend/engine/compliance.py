
import yaml
from ..app.settings import settings

with open(settings.constants_file) as f:
    C = yaml.safe_load(f)

def vrp_classroom(Pz_people: int, area_m2: float, supply_cfm: float):
    Rp = C["classroom_vrp"]["Rp_cfm_per_person"]
    Ra = C["classroom_vrp"]["Ra_cfm_per_ft2"]
    area_ft2 = area_m2 * 10.7639
    Vbz = Rp * Pz_people + Ra * area_ft2
    pass_ = supply_cfm >= Vbz
    return {
        "std": "62.1-2022",
        "pass": bool(pass_),
        "Pz_people": Pz_people,
        "Az_m2": round(area_m2, 2),
        "Vbz_cfm": round(Vbz, 1),
        "supplied_cfm": round(supply_cfm, 1),
        "notes": "Assumes classroom category; Ez~1.0 for ceiling supply/return (cooling)."
    }
