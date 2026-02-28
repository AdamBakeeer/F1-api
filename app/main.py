from fastapi import FastAPI
from app.api.drivers import router as drivers_router

app = FastAPI(title="F1 Performance API")

@app.get("/")
def root():
    return {"message": "F1 API is running"}

# Register the /drivers routes
app.include_router(drivers_router)