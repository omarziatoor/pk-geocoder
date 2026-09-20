from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.geocode import reverse_geocode
from app.schemas import ReverseGeocodeResponse

router = APIRouter()


@router.get("/api/reverse-geocode", response_model=ReverseGeocodeResponse)
def get_place_name(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    db: Session = Depends(get_db),
):
    result = reverse_geocode(db, lat, lon)
    if result is None:
        raise HTTPException(status_code=404, detail="No boundary found for this location")
    return result


@router.get("/health")
def health():
    return {"status": "ok"}
