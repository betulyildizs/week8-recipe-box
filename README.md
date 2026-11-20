# Starter — Recipe Box

A tiny FastAPI + SQLite service with a static frontend. Your playground for concurrent
agents and a generator–critic loop.

## Setup
```bash
pip install -r requirements.txt
pytest
uvicorn main:app --reload   # http://localhost:8000  (UI at /, docs at /docs)
```

## Endpoints
- `POST /recipes` `{ "title": ..., "ingredients": [...], "tags": [...] }`
- `GET /recipes`, `GET /recipes/{id}`
- `GET /recipes/{id}/scaled?factor=2` returns a recipe copy with leading numeric ingredient quantities scaled (for example, `200 g flour` to `400 g flour` and `200g flour` to `400g flour`). Decimal factors are supported, and ingredients without a leading quantity are unchanged. The factor must be finite and positive; a missing, malformed, zero, negative, or non-finite factor returns `422`, and an unknown recipe returns `404`.
- `GET /shopping-list?ids=1,2,3` merges recipe ingredients without duplicates

## Parallel work with git worktrees
```bash
git worktree add ../recipe-task-a -b task-a
git worktree add ../recipe-task-b -b task-b
```

## Files
- `main.py` — the app
- `static/index.html` — minimal UI
- `test_main.py` — pytest suite
- `docs/TASKS.md` — independent tasks (safe to run in parallel)
