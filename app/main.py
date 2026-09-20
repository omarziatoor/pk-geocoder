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
    with engine.begin() as conn:
        # Supabase exposes every table in the `public` schema through its
        # PostgREST API by default. These tables are only ever accessed via
        # this app's own DB connection (table owner, which bypasses RLS), so
        # enabling RLS with no policies blocks all access through PostgREST
        # without affecting the app.
        conn.execute(text("ALTER TABLE boundaries ENABLE ROW LEVEL SECURITY"))
        conn.execute(text("ALTER TABLE shapefile_uploads ENABLE ROW LEVEL SECURITY"))


app.include_router(api.router)
app.include_router(admin.router)
