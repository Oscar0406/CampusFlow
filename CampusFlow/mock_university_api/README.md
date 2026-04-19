# Mock University API

A standalone FastAPI server that simulates a real university's SIS, Finance,
and Housing backends for local development and testing.

## Start the mock server

```bash
# From CampusFlow_v4 root:
uvicorn mock_university_api.server:app --port 8001 --reload
```

Visit http://localhost:8001/docs for the interactive API explorer.

## Connect CampusFlow to it

In `main.py`, change the university_id to `"utm_mock"`:

```python
result = asyncio.run(run("Your message", university_id="utm_mock"))
```

Or via the API, send `X-University-Id: utm_mock`.

`utm_mock.yaml` already points all adapter URLs to `http://localhost:8001`.
Set `MOCK_API_KEY=anything` in your `.env` — any non-empty string is accepted.

## Seed data

Edit `mock_university_api/data.py` to add more students, rooms, courses, or
financial records without changing any other code.
