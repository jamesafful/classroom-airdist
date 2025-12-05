
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .routes.predict import router as predict_router

app = FastAPI(title="Classroom Air Distribution API", version="0.1.1")
app.include_router(predict_router)

os.makedirs("artifacts", exist_ok=True)
app.mount("/artifacts", StaticFiles(directory="artifacts"), name="artifacts")

@app.get("/health")
def health():
    return {"status": "ok"}
