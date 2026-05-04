# shared/

Pydantic schemas shared between `backend/` and `program-builder/`.

## models/

| File | Purpose |
|------|---------|
| `plan_request.py` | Request sent from backend to program-builder (Lambda or HTTP) |
| `plan_response.py` | Generated plan returned by program-builder |

Install locally in each service via pip editable install or copy — no published package required in dev.
