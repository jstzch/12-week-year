"""12-Week Year - Backend API"""
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    """Root endpoint - Hello API"""
    return {"message": "Hello from 12-Week Year API!", "status": "ok"}


@app.get("/api/hello")
def hello():
    """Hello endpoint"""
    return {"message": "Hello, World!"}
