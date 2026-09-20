import shutil
import tempfile
import zipfile
from pathlib import Path

import geopandas as gpd
from geoalchemy2.shape import from_shape
from sqlalchemy.orm import Session

from app.models import Boundary, ShapefileUpload

# Common attribute names used for administrative-boundary shapefiles
# (GADM, Pakistan Bureau of Statistics, HDX/OCHA exports, etc.), checked
# in priority order so the most specific/local name wins.
NAME_FIELD_CANDIDATES = [
    "NAME_3", "ADM3_EN", "TEHSIL", "TEHSIL_NAM",
    "NAME_2", "ADM2_EN", "DISTRICT", "DISTRICT_N",
    "NAME_1", "ADM1_EN", "PROVINCE",
    "NAME", "NAME_EN",
]


class ShapefileError(ValueError):
    pass


def extract_zip(zip_bytes: bytes, dest_dir: Path) -> Path:
    zip_path = dest_dir / "upload.zip"
    zip_path.write_bytes(zip_bytes)
    try:
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(dest_dir)
    except zipfile.BadZipFile as exc:
        raise ShapefileError("Uploaded file is not a valid .zip archive") from exc

    shp_files = list(dest_dir.rglob("*.shp"))
    if not shp_files:
        raise ShapefileError("No .shp file found inside the uploaded zip")
    if len(shp_files) > 1:
        raise ShapefileError(
            f"Zip contains {len(shp_files)} .shp files; upload one layer at a time"
        )
    return shp_files[0]


def read_shapefile(shp_path: Path) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(shp_path)
    if gdf.empty:
        raise ShapefileError("Shapefile contains no features")
    if gdf.crs is None:
        raise ShapefileError(
            "Shapefile has no coordinate reference system (.prj) defined"
        )
    if gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)
    return gdf


def guess_name_field(gdf: gpd.GeoDataFrame) -> str | None:
    columns = {c.upper(): c for c in gdf.columns}
    for candidate in NAME_FIELD_CANDIDATES:
        if candidate in columns:
            return columns[candidate]
    return None


def load_shapefile_into_db(
    db: Session,
    zip_bytes: bytes,
    filename: str,
    name_field: str | None = None,
) -> dict:
    """Replace the boundaries table with features from the given zipped shapefile.

    If name_field is not provided, it is guessed from common admin-boundary
    field names. Raises ShapefileError if it can't be determined.
    """
    tmp_dir = Path(tempfile.mkdtemp(prefix="shp_upload_"))
    try:
        shp_path = extract_zip(zip_bytes, tmp_dir)
        gdf = read_shapefile(shp_path)

        if name_field is None:
            name_field = guess_name_field(gdf)
        if not name_field or name_field not in gdf.columns:
            raise ShapefileError(
                "Could not determine which field holds the place name. "
                f"Available fields: {list(gdf.columns)}. "
                "Re-upload with ?name_field=<field> to specify it explicitly."
            )

        rows = []
        for _, feature in gdf.iterrows():
            geom = feature.geometry
            if geom is None or geom.is_empty:
                continue
            if geom.geom_type == "Polygon":
                geom = gpd.GeoSeries([geom]).unary_union
                from shapely.geometry import MultiPolygon
                geom = MultiPolygon([geom]) if geom.geom_type == "Polygon" else geom
            elif geom.geom_type != "MultiPolygon":
                raise ShapefileError(
                    f"Unsupported geometry type '{geom.geom_type}'; "
                    "only Polygon/MultiPolygon boundaries are supported"
                )

            properties = {
                col: (None if gpd.pd.isna(feature[col]) else feature[col])
                for col in gdf.columns
                if col != gdf.geometry.name
            }
            rows.append(
                Boundary(
                    name=str(feature[name_field]),
                    properties=properties,
                    geom=from_shape(geom, srid=4326),
                )
            )

        if not rows:
            raise ShapefileError("No usable polygon features found in shapefile")

        db.query(Boundary).delete()
        db.add_all(rows)
        db.add(
            ShapefileUpload(
                filename=filename,
                name_field=name_field,
                feature_count=len(rows),
            )
        )
        db.commit()

        return {
            "filename": filename,
            "name_field": name_field,
            "feature_count": len(rows),
            "fields_available": list(gdf.columns),
        }
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
