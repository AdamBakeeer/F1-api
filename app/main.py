import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import drivers, constructors, circuits, races, analytics, auth, favorites
from app.db.database import Base, engine
from app.models import models

app = FastAPI(title="F1 API")

Base.metadata.create_all(bind=engine)

# Configure CORS based on environment
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(drivers.router)
app.include_router(constructors.router)
app.include_router(circuits.router)
app.include_router(races.router)
app.include_router(analytics.router)
app.include_router(favorites.router)


@app.get("/")
def root():
    return {"message": "F1 API is running"}