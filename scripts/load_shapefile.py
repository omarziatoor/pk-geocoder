"""CLI tool to (re)load the boundaries table from a local shapefile.

Usage:
    python scripts/load_shapefile.py path/to/boundaries.zip [--name-field DISTRICT]

The zip must contain a single .shp layer (plus .shx/.dbf/.prj).
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.shapefile_loader import ShapefileError, load_shapefile_into_db  # noqa: E402
from sqlalchemy import text  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip_path", type=Path, help="Path to a .zip containing the shapefile")
    parser.add_argument("--name-field", default=None, help="Attribute field to use as place name")
    args = parser.parse_args()

    if not args.zip_path.exists():
        print(f"File not found: {args.zip_path}", file=sys.stderr)
        sys.exit(1)

    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        result = load_shapefile_into_db(
            db,
            args.zip_path.read_bytes(),
            args.zip_path.name,
            args.name_field,
        )
    except ShapefileError as exc:
        print(f"Load failed: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()

    print(f"Loaded {result['feature_count']} features using name field '{result['name_field']}'")
    print(f"Available fields: {', '.join(result['fields_available'])}")


if __name__ == "__main__":
    main()
