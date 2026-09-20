import secrets

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import ADMIN_PASSWORD, ADMIN_USERNAME, MAX_UPLOAD_BYTES
from app.database import get_db
from app.shapefile_loader import ShapefileError, load_shapefile_into_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
security = HTTPBasic()


def require_admin(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    if not ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin upload is disabled: ADMIN_PASSWORD is not configured",
        )
    valid_user = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    valid_pass = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (valid_user and valid_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@router.get("/admin/upload", response_class=HTMLResponse)
def upload_page(request: Request, _: str = Depends(require_admin)):
    return templates.TemplateResponse(
        request, "upload.html", {"result": None, "error": None}
    )


@router.post("/admin/upload", response_class=HTMLResponse)
async def upload_shapefile(
    request: Request,
    file: UploadFile,
    name_field: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: str = Depends(require_admin),
):
    error = None
    result = None
    try:
        contents = await file.read(MAX_UPLOAD_BYTES + 1)
        if len(contents) > MAX_UPLOAD_BYTES:
            raise ShapefileError(
                f"File exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)}MB upload limit"
            )
        result = load_shapefile_into_db(db, contents, file.filename, name_field)
    except ShapefileError as exc:
        error = str(exc)

    return templates.TemplateResponse(
        request, "upload.html", {"result": result, "error": error}
    )
