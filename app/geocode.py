from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Boundary

# Nearest-match fallback radius in degrees (~5.5km at Pakistan's latitude),
# for points that fall just outside every polygon (coastline/border artifacts).
NEAREST_FALLBACK_DEGREES = 0.05


def reverse_geocode(db: Session, lat: float, lon: float) -> dict | None:
    """Return the boundary containing (lat, lon). If no polygon contains the
    point exactly, fall back to the nearest boundary within a small radius.
    """
    point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)

    match = (
        db.query(Boundary)
        .filter(func.ST_Contains(Boundary.geom, point))
        .first()
    )
    if match is not None:
        return {"name": match.name, "properties": match.properties, "matched_exact": True}

    nearest = (
        db.query(Boundary)
        .filter(func.ST_DWithin(Boundary.geom, point, NEAREST_FALLBACK_DEGREES))
        .order_by(func.ST_Distance(Boundary.geom, point))
        .first()
    )
    if nearest is not None:
        return {"name": nearest.name, "properties": nearest.properties, "matched_exact": False}

    return None
