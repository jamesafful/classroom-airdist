
# classroom-airdist 

Same project, with packaging configured for install on GitHub Codespaces.

## Quickstart
```bash
pip install -U pip
pip install -e .
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
# http://localhost:8000/docs
```
  