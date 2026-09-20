from fastapi import FastAPI
from sqlalchemy import text

from app.database import Base, engine
from app.routers import admin, api

app = FastAPI(title="Pakistan Reverse Geocoder")


@app.on_event("startup")
def on_startup():
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
    Base.metadata.create_all(bind=engine)


app.include_router(api.router)
app.include_router(admin.router)
