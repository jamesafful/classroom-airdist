
def greedy_layout(G, count=4, min_wall=1.2):
    # Basic 2x2 for count==4; else center + near-quadrants.
    if count == 4:
        return [(G.Lx*0.3, G.Ly*0.3), (G.Lx*0.3, G.Ly*0.7),
                (G.Lx*0.7, G.Ly*0.3), (G.Lx*0.7, G.Ly*0.7)]
    pts = [(G.Lx/2.0, G.Ly/2.0)]
    for a,b in [(0.3,0.3),(0.3,0.7),(0.7,0.3),(0.7,0.7)]:
        if len(pts) >= count: break
        pts.append((G.Lx*a, G.Ly*b))
    return pts
