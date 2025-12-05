
from pydantic import BaseModel, Field, conlist
from typing import List, Optional, Literal, Dict, Any

class Room(BaseModel):
    length_m: float
    width_m: float
    height_m: float
    shape: Literal["rect", "l_preset"] = "rect"
    window_wall: Optional[Literal["north","south","east","west"]] = None

class People(BaseModel):
    students: int
    teachers: int
    seated_fraction: float = 0.9

class Loads(BaseModel):
    deltaT_C: float = -8.0
    mode: Literal["cooling", "heating"] = "cooling"

class Standard(BaseModel):
    type: Literal["ASHRAE_62_1","ASHRAE_241"] = "ASHRAE_62_1"
    edition: str = "2022"
    eca_target_cfm: Optional[float] = None

class Ventilation(BaseModel):
    supply_total_cfm: float
    infiltration_cfm: float = 0.0

class DiffuserSel(BaseModel):
    type: Literal["ceiling_4way","slot","plaque","2way","sidewall"]
    model_id: str = "example_square_cone"
    count: int
    neck_size_in: Optional[int] = 8
    existing_locations: Optional[List[Dict[str,float]]] = None

class DiffuserConstraints(BaseModel):
    min_from_walls_m: float = 1.2
    min_from_board_m: float = 1.2
    face_velocity_fpm_max: int = 700

class Diffusers(BaseModel):
    selection: conlist(DiffuserSel, min_length=1)
    constraints: DiffuserConstraints = DiffuserConstraints()

class Returns(BaseModel):
    locations: List[Dict[str,float]]

class Solver(BaseModel):
    optimize_layout: bool = True
    grid_spacing_m: float = 0.6
    time_budget_ms: int = 2000

class PredictRequest(BaseModel):
    room: Room
    people: People
    loads: Loads
    standard: Standard
    ventilation: Ventilation
    diffusers: Diffusers
    returns: Returns
    solver: Solver = Solver()

class PredictResponse(BaseModel):
    adpi: float
    adpi_uncertainty_pp: float
    velocity_stats: Dict[str, float]
    edt: Dict[str, Any]
    draft_risk_area_pct: float
    compliance: Dict[str, Any]
    layout: Dict[str, Any]
    warnings: List[str]
    uncertainty: Dict[str, Any]
    artifacts: Dict[str, str]
    provenance: Dict[str, str]
