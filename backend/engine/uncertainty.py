
def estimate(req, locs, stats):
    drivers = []
    level = "low"
    pp = 6.0
    if req.room.height_m <= 2.7:
        drivers.append("low ceiling"); level = "medium"; pp += 2.0
    if abs(req.loads.deltaT_C) >= 12.0:
        drivers.append("large |ΔT|"); level = "medium"; pp += 2.0
    if stats["pct_v_gt_0_25"] > 10.0:
        drivers.append("draft-prone pattern"); level = "high"; pp += 3.0
    return level, pp, drivers
