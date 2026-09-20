# Pakistan Reverse Geocoder

Given a latitude/longitude, returns the name of the Pakistani administrative
boundary (e.g. district) containing that point, using a PostGIS point-in-polygon
lookup against an uploadable shapefile.

## Stack

- **API**: FastAPI (Python), deployed on [Render](https://render.com) (free tier)
- **Database**: PostgreSQL + PostGIS, e.g. [Supabase](https://supabase.com) (free tier)
- **Boundary data**: uploaded via a password-protected web page, or the CLI script

## Local setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

copy .env.example .env          # then fill in DATABASE_URL / ADMIN_PASSWORD
```

Run the API:

```bash
uvicorn app.main:app --reload
```

## Loading the boundary shapefile

Two ways to load/replace the `boundaries` table. Both accept a **zip file**
containing one polygon layer (`.shp` + `.shx` + `.dbf` + ideally `.prj`).

**1. Web page** (requires `ADMIN_USERNAME`/`ADMIN_PASSWORD` to be set):

Visit `/admin/upload`, pick the zip, optionally specify which attribute field
holds the place name (e.g. `DISTRICT`, `NAME_2`) if auto-detection doesn't
find it, and submit. This **replaces all existing boundaries**.

**2. CLI script** (useful for the initial load or scripted deploys):

```bash
python scripts/load_shapefile.py path/to/boundaries.zip --name-field DISTRICT
```

If `--name-field` / the form field is left blank, the loader guesses from common
admin-boundary field names (`DISTRICT`, `NAME_2`, `ADM2_EN`, `PROVINCE`, `NAME`, ...).
If it can't guess, it lists the available fields in the shapefile so you can
specify the correct one.

## API

```
GET /api/reverse-geocode?lat=31.5204&lon=74.3587
```

```json
{
  "name": "Lahore",
  "properties": { "...": "all shapefile attributes for the matched feature" },
  "matched_exact": true
}
```

`matched_exact: false` means no polygon contained the point exactly, and the
nearest boundary within ~5km was returned instead (handles coastline/border
edge cases).

## Deploying

1. **Database**: create a free Supabase project, enable PostGIS
   (`create extension postgis;` in the SQL editor, or let the app do it on
   startup), and copy the connection string.
2. **API**: create a free Render web service from this GitHub repo. Render
   picks up `render.yaml` automatically. Set `DATABASE_URL`, `ADMIN_USERNAME`,
   and `ADMIN_PASSWORD` in the Render dashboard (not committed to git).
3. Load the initial shapefile via `/admin/upload` on the deployed URL, or run
   `scripts/load_shapefile.py` locally against the Supabase `DATABASE_URL`.

The GitHub repo itself is just source control — GitHub Pages is **not** used
to host this, since it can't run a Python process or reach a database.
