
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .routes.predict import router as predict_router
from .routes.report import router as report_router
from .routes.catalogs import router as catalogs_router
from .settings import settings

app = FastAPI(title="Classroom Air Distribution API", version="0.1.0")
app.include_router(predict_router)
app.include_router(report_router)
app.include_router(catalogs_router)

os.makedirs(settings.artifacts_dir, exist_ok=True)
app.mount("/artifacts", StaticFiles(directory=settings.artifacts_dir), name="artifacts")

@app.get("/health")
def health():
    return {"status": "ok"}
