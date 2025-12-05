
import json, os
from fastapi import APIRouter
from ..settings import settings

router = APIRouter(prefix="/catalogs", tags=["catalogs"])

@router.get("")
def list_catalogs():
    files = []
    for fn in os.listdir(settings.catalog_dir):
        if fn.endswith(".json"):
            files.append(fn)
    return {"catalog_version": "v0", "files": files}

@router.get("/{model_id}")
def get_model(model_id: str):
    path = os.path.join(settings.catalog_dir, model_id)
    if not os.path.exists(path):
        path_json = os.path.join(settings.catalog_dir, f"{model_id}.json")
        path = path_json if os.path.exists(path_json) else path
    with open(path) as f:
        return json.load(f)
