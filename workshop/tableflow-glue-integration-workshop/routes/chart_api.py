from fastapi import APIRouter
from services.chart_loader import load_charts

router = APIRouter()

@router.get("/api/chart-data")
def get_chart_data(chart: str):
    charts = load_charts()
    return charts.get(chart, {"data": [], "layout": {}})
