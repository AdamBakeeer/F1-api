from fastapi import FastAPI
from app.api import drivers, constructors, circuits, races, analytics, auth

app = FastAPI(title="F1 API")

app.include_router(auth.router)
app.include_router(drivers.router)
app.include_router(constructors.router)
app.include_router(circuits.router)
app.include_router(races.router)
app.include_router(analytics.router)


@app.get("/")
def root():
    return {"message": "F1 API is running"}