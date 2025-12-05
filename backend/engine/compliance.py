
def vrp_classroom(Pz_people: int, area_m2: float, supply_cfm: float):
    Rp = 10.0
    Ra = 0.12
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
