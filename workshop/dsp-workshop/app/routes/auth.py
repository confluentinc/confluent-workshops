from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.services.user_service import UserService

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    """Login page"""
    from app.main import templates
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login_user(
    name: str = Form(...), 
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle user login"""
    UserService.get_or_create_user(db, name, email)
    return RedirectResponse(f"/products?email={email}&name={name}", status_code=303)

@router.get("/logout")
def logout():
    """Handle user logout"""
    return RedirectResponse("/", status_code=303) 