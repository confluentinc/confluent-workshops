from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.services.kafka_service import KafkaService
from app.models.models import Product, TrendingProduct, UserSuggestion
import asyncio
import time

router = APIRouter()

@router.get("/trending")
def get_trending_api(email: str, db: Session = Depends(get_db)):
    """Get trending products API"""
    import logging
    logger = logging.getLogger(__name__)
    
    trending_rows = db.query(TrendingProduct).order_by(TrendingProduct.view_count.desc()).limit(6).all()
    logger.info(f"Found {len(trending_rows)} trending products in database")
    
    product_ids = [row.product_id for row in trending_rows]
    logger.info(f"Product IDs: {product_ids}")
    
    products = db.query(Product).filter(Product.id.in_(product_ids)).all()
    logger.info(f"Found {len(products)} products in product table")
    
    product_map = {p.id: p for p in products}
    logger.info(f"Product map keys: {list(product_map.keys())}")
    
    final_data = []
    for row in trending_rows:
        logger.info(f"Processing trending row: product_id={row.product_id}, view_count={row.view_count}")
        product = product_map.get(row.product_id)
        if product:
            final_data.append({
                "product_id": row.product_id,
                "view_count": row.view_count,
                "name": product.name,
                "image": product.image,
                "type": product.type,
                "price": product.price,
                "quantity": product.quantity
            })
            logger.info(f"Added product: {product.name} with view_count: {row.view_count}")
        else:
            logger.warning(f"Product {row.product_id} not found in product table")
    
    logger.info(f"Returning {len(final_data)} trending products")
    return final_data

@router.get("/suggestions")
def get_suggestions_api(email: str, db: Session = Depends(get_db)):
    """Get personalized suggestions API"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Fetching suggestions for user: {email}")
    
    # Get all suggestions for the user
    suggestions = db.query(UserSuggestion).filter_by(user_email=email).all()
    logger.info(f"Found {len(suggestions)} suggestions in database for user {email}")
    
    if not suggestions:
        logger.warning(f"No suggestions found for user {email}")
        return []
    
    # Get product IDs from suggestions
    product_ids = [s.product_id for s in suggestions]
    logger.info(f"Product IDs from suggestions: {product_ids}")
    
    # Get products for these IDs
    products = db.query(Product).filter(Product.id.in_(product_ids)).all()
    logger.info(f"Found {len(products)} products for suggestion IDs")
    
    # Create product map
    product_map = {p.id: p for p in products}
    logger.info(f"Product map keys: {list(product_map.keys())}")
    
    # Build suggestions data
    suggestions_data = []
    for s in suggestions:
        if s.product_id in product_map:
            product = product_map[s.product_id]
            suggestion_item = {
                "product_id": s.product_id,
                "name": product.name,
                "image": product.image,
                "type": product.type,
                "price": product.price,
                "quantity": product.quantity
            }
            suggestions_data.append(suggestion_item)
            logger.info(f"Added suggestion: {product.name} (ID: {s.product_id})")
        else:
            logger.warning(f"Product {s.product_id} not found in product table")
    
    logger.info(f"Returning {len(suggestions_data)} suggestions for user {email}")
    return suggestions_data

@router.get("/trending/long-poll")
async def get_trending_long_poll(email: str, last_update: str = None, db: Session = Depends(get_db)):
    """Long polling endpoint for trending products updates"""
    max_wait = 30  # Maximum wait time in seconds
    check_interval = 1  # Check every second
    
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        trending_rows = db.query(TrendingProduct).order_by(TrendingProduct.view_count.desc()).limit(6).all()
        
        # Check if there are any updates since last check
        if last_update:
            recent_updates = [row for row in trending_rows if row.updated_at > last_update]
            if recent_updates:
                # Return updated data immediately
                product_ids = [row.product_id for row in trending_rows]
                products = db.query(Product).filter(Product.id.in_(product_ids)).all()
                product_map = {p.id: p for p in products}
                final_data = []
                for row in trending_rows:
                    product = product_map.get(row.product_id)
                    if product:
                        final_data.append({
                            "product_id": row.product_id,
                            "view_count": row.view_count,
                            "name": product.name,
                            "image": product.image,
                            "type": product.type,
                            "price": product.price,
                            "quantity": product.quantity
                        })
                return {"updated": True, "data": final_data, "timestamp": time.time()}
        
        # Wait before next check
        await asyncio.sleep(check_interval)
    
    # Return current data if no updates within timeout
    trending_rows = db.query(TrendingProduct).order_by(TrendingProduct.view_count.desc()).limit(6).all()
    product_ids = [row.product_id for row in trending_rows]
    products = db.query(Product).filter(Product.id.in_(product_ids)).all()
    product_map = {p.id: p for p in products}
    final_data = []
    for row in trending_rows:
        product = product_map.get(row.product_id)
        if product:
            final_data.append({
                "product_id": row.product_id,
                "view_count": row.view_count,
                "name": product.name,
                "image": product.image,
                "type": product.type,
                "price": product.price,
                "quantity": product.quantity
            })
    return {"updated": False, "data": final_data, "timestamp": time.time()}

@router.get("/suggestions/long-poll")
async def get_suggestions_long_poll(email: str, last_update: str = None, db: Session = Depends(get_db)):
    """Long polling endpoint for suggestions updates"""
    max_wait = 30  # Maximum wait time in seconds
    check_interval = 1  # Check every second
    
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        suggestions = db.query(UserSuggestion).filter_by(user_email=email).all()
        
        # Check if there are any updates since last check
        if last_update:
            recent_updates = [s for s in suggestions if s.updated_at > last_update]
            if recent_updates:
                # Return updated data immediately
                products = db.query(Product).filter(Product.id.in_([s.product_id for s in suggestions])).all()
                product_map = {p.id: p for p in products}
                suggestions_data = [{
                    "product_id": s.product_id,
                    "name": product_map[s.product_id].name if s.product_id in product_map else None,
                    "image": product_map[s.product_id].image if s.product_id in product_map else None,
                    "type": product_map[s.product_id].type if s.product_id in product_map else None,
                    "price": product_map[s.product_id].price if s.product_id in product_map else None,
                    "quantity": product_map[s.product_id].quantity if s.product_id in product_map else None
                } for s in suggestions if s.product_id in product_map]
                return {"updated": True, "data": suggestions_data, "timestamp": time.time()}
        
        # Wait before next check
        await asyncio.sleep(check_interval)
    
    # Return current data if no updates within timeout
    suggestions = db.query(UserSuggestion).filter_by(user_email=email).all()
    products = db.query(Product).filter(Product.id.in_([s.product_id for s in suggestions])).all()
    product_map = {p.id: p for p in products}
    suggestions_data = [{
        "product_id": s.product_id,
        "name": product_map[s.product_id].name if s.product_id in product_map else None,
        "image": product_map[s.product_id].image if s.product_id in product_map else None,
        "type": product_map[s.product_id].type if s.product_id in product_map else None,
        "price": product_map[s.product_id].price if s.product_id in product_map else None,
        "quantity": product_map[s.product_id].quantity if s.product_id in product_map else None
    } for s in suggestions if s.product_id in product_map]
    return {"updated": False, "data": suggestions_data, "timestamp": time.time()}

@router.post("/track-click")
async def track_click(request: Request):
    """Track product click events"""
    import json
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        data = await request.json()
        logger.info(f"Clickstream received: {data}")
        
        # Produce to Kafka
        kafka_service = KafkaService()
        kafka_service.produce_message("datagen_product_view", data)
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error tracking click: {e}")
        return {"status": "error", "message": str(e)} 