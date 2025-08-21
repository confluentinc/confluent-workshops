from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.services.product_service import ProductService
from app.models.models import User

router = APIRouter()

@router.get("/products", response_class=HTMLResponse)
def get_products(request: Request, email: str, name: str = None, db: Session = Depends(get_db)):
    """Display products page"""
    from app.main import templates
    all_products = ProductService.get_all_products(db)
    
    # If name is not provided, try to get it from the database
    if not name:
        user = db.query(User).filter_by(email=email).first()
        name = user.name if user else "User"
    
    return templates.TemplateResponse("products.html", {
        "request": request,
        "products": all_products,
        "email": email,
        "name": name
    })

@router.post("/cart/add")
def add_to_cart(
    email: str = Form(...), 
    product_id: int = Form(...), 
    quantity: int = Form(...),
    name: str = Form(...),
    db: Session = Depends(get_db)
):
    """Add product to cart"""
    user = db.query(User).filter_by(email=email).first()
    if user and ProductService.add_to_cart(db, user.id, product_id, quantity):
        return RedirectResponse(f"/products?email={email}&name={name}", status_code=303)
    return RedirectResponse(f"/products?email={email}&name={name}", status_code=303)

@router.get("/cart", response_class=HTMLResponse)
def view_cart(request: Request, email: str, name: str = None, db: Session = Depends(get_db)):
    """View shopping cart"""
    from app.main import templates
    user = db.query(User).filter_by(email=email).first()
    if user:
        cart_data = ProductService.get_user_cart(db, user.id)
        # If name is not provided, use the user's name from database
        if not name:
            name = user.name
        return templates.TemplateResponse("cart.html", {
            "request": request,
            "cart": cart_data['items'],
            "cart_total": cart_data['total'],
            "email": email,
            "name": name
        })
    return RedirectResponse(f"/products?email={email}&name={name}", status_code=303)

@router.post("/cart/remove")
def remove_from_cart(
    email: str = Form(...), 
    cart_id: int = Form(...),
    name: str = Form(...),
    db: Session = Depends(get_db)
):
    """Remove item from cart"""
    ProductService.remove_from_cart(db, cart_id)
    return RedirectResponse(f"/cart?email={email}&name={name}", status_code=303)