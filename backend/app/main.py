# backend/app/main.py
import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from .routes.predict import router as predict_router

app = FastAPI(title="Classroom Air Distribution API", version="0.3.0")
app.include_router(predict_router)

os.makedirs("artifacts", exist_ok=True)
app.mount("/artifacts", StaticFiles(directory="artifacts"), name="artifacts")
app.mount("/static", StaticFiles(directory="web/static"), name="static")

@app.get("/", response_class=HTMLResponse)
def root():
    return "<h3>Classroom Air Distribution</h3><p>Open <a href='/app'>/app</a> for the UI or <a href='/docs'>/docs</a> for the API.</p>"

@app.get("/app", response_class=HTMLResponse)
def app_page():
    with open("web/templates/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/health")
def health():
    return {"status": "ok"}

