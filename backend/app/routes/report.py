
import os
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from ..settings import settings

router = APIRouter(prefix="/report", tags=["report"])

@router.post("")
def generate_report_stub():
    os.makedirs(settings.artifacts_dir, exist_ok=True)
    report_path = os.path.join(settings.artifacts_dir, "submittal.txt")
    with open(report_path, "w") as f:
        f.write("Report placeholder. Use /predict artifacts for figures and CSVs.\n")
    return JSONResponse({"report_pdf_url": f"/artifacts/submittal.txt"})
