from fastapi import FastAPI
from sqlalchemy import create_engine, text
import os

app = FastAPI(title="F1 Performance API")

DATABASE_URL = "postgresql+psycopg2://adambakeer@localhost/f1db"
engine = create_engine(DATABASE_URL)


@app.get("/")
def root():
    return {"message": "F1 API is running"}


@app.get("/drivers")
def get_drivers():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM drivers LIMIT 50"))
        drivers = [dict(row._mapping) for row in result]
    return drivers