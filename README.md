
# classroom-airdist

A fast, trustworthy mixing-mode air distribution design assistant for K-12 classrooms.

- Predicts ADPI, EDT histogram, draft-risk bands
- Computes ASHRAE 62.1 VRP breathing-zone airflow (classroom category defaults)
- Suggests diffuser layout + per-diffuser CFM
- Exports PNG heatmaps, CSV coordinates
- REST API via FastAPI (/predict, /report)

Scope (MVP): Overhead mixing ventilation in cooling mode, rectangular rooms. This is a design-assist tool; the engineer of record must review/approve.

## Quickstart (Codespaces / local)
```bash
pip install -U pip
pip install -e .
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
# http://localhost:8000/docs
```
