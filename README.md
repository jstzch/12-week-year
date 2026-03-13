# 12-Week Year

A simple project to help achieve goals in 12 weeks.

## Quick Start

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Run the API
uvicorn main:app --reload

# Run tests
pytest
```

## Project Structure

```
12-week-year/
├── backend/          # FastAPI backend
│   ├── main.py       # API entry point
│   ├── tests/       # Unit tests
│   └── requirements.txt
├── frontend/         # Frontend (coming soon)
└── docker-compose.yml
```

## API Endpoints

- `GET /` - Root endpoint
- `GET /api/hello` - Hello endpoint
