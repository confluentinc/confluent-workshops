from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from services.chart_loader import load_charts

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    charts = load_charts()
    return templates.TemplateResponse("query_editor.html", {"request": request, "charts": charts})