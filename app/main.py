from fastapi import FastAPI
from app.api import drivers, constructors, circuits, races, analytics, auth
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="F1 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
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


@app.get("/")
def root():
    return {"message": "F1 API is running"}