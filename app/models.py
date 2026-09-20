from geoalchemy2 import Geometry
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class Boundary(Base):
    __tablename__ = "boundaries"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, index=True)
    properties = Column(JSONB, nullable=False, default=dict)
    geom = Column(Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=False)


class ShapefileUpload(Base):
    __tablename__ = "shapefile_uploads"

    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    name_field = Column(String, nullable=False)
    feature_count = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
