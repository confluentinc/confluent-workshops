from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.services.analytics_service import AnalyticsService
from app.services.user_service import UserService
from app.utils.chart_utils import create_click_trends_chart, create_product_type_chart, create_top_users_chart

router = APIRouter()

@router.get("/analytics", response_class=HTMLResponse)
def analytics_page(request: Request, email: str, name: str = None, db: Session = Depends(get_db)):
    """Analytics dashboard page - now just renders template with loaders"""
    from app.main import templates
    from app.models.models import User
    
    # If name is not provided, try to get it from the database
    if not name:
        user = db.query(User).filter_by(email=email).first()
        name = user.name if user else "User"
    
    return templates.TemplateResponse("analytics.html", {
        "request": request,
        "email": email,
        "name": name
    })

@router.get("/api/analytics/kpi")
def get_kpi_data(email: str, db: Session = Depends(get_db)):
    """API endpoint for KPI data"""
    try:
        analytics_service = AnalyticsService()
        if not analytics_service.athena_client:
            return JSONResponse({"success": False, "error": "Athena client not available"})
        
        total_clicks = analytics_service.get_total_clicks()
        return JSONResponse({"success": True, "total_clicks": total_clicks})
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting KPI data: {e}")
        return JSONResponse({"success": False, "error": str(e)})

@router.get("/api/analytics/click-trends")
def get_click_trends_data(email: str, db: Session = Depends(get_db)):
    """API endpoint for click trends chart data"""
    try:
        analytics_service = AnalyticsService()
        if not analytics_service.athena_client:
            return JSONResponse({"success": False, "error": "Athena client not available"})
        
        click_trends_df = analytics_service.get_click_trends_data()
        chart_data = create_click_trends_chart(click_trends_df)
        return JSONResponse({"success": True, "chart_data": chart_data})
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting click trends data: {e}")
        return JSONResponse({"success": False, "error": str(e)})

@router.get("/api/analytics/product-type")
def get_product_type_data(email: str, db: Session = Depends(get_db)):
    """API endpoint for product type chart data"""
    try:
        analytics_service = AnalyticsService()
        if not analytics_service.athena_client:
            return JSONResponse({"success": False, "error": "Athena client not available"})
        
        product_type_df = analytics_service.get_product_type_distribution()
        chart_data = create_product_type_chart(product_type_df)
        return JSONResponse({"success": True, "chart_data": chart_data})
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting product type data: {e}")
        return JSONResponse({"success": False, "error": str(e)})

@router.get("/api/analytics/top-users")
def get_top_users_chart_data(email: str, db: Session = Depends(get_db)):
    """API endpoint for top users chart data"""
    try:
        analytics_service = AnalyticsService()
        if not analytics_service.athena_client:
            return JSONResponse({"success": False, "error": "Athena client not available"})
        
        top_users_df = analytics_service.get_top_users()
        chart_data = create_top_users_chart(top_users_df)
        return JSONResponse({"success": True, "chart_data": chart_data})
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting top users chart data: {e}")
        return JSONResponse({"success": False, "error": str(e)})

@router.get("/api/query-data")
def custom_query(
    request: Request, 
    email: str, 
    query: str, 
    database: str = "default",
    db: Session = Depends(get_db)
):
    """API endpoint for custom Athena queries"""
    analytics_service = AnalyticsService()
    
    if not analytics_service.athena_client:
        return {"error": "Athena client not available"}
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Custom query from {email}: {query}")
    
    df = analytics_service.execute_athena_query(query, database)
    
    result = {
        "data": df.to_dict('records'), 
        "columns": df.columns.tolist(),
        "row_count": len(df)
    }
    logger.info(f"Returning {len(df)} rows to frontend")
    return result 