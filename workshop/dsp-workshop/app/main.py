from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging
import os
import threading
import time
import json
from app.models.database import SessionLocal, engine
from app.models.models import Base, TrendingProduct, UserSuggestion, Product
from app.services.kafka_service import KafkaService
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="DSP Workshop", description="Data Streaming Platform Workshop Application")

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Mount static files and templates
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Import and include routers
from app.routes import auth, products, analytics, api

app.include_router(auth.router, tags=["Authentication"])
app.include_router(products.router, tags=["Products"])
app.include_router(analytics.router, tags=["Analytics"])
app.include_router(api.router, tags=["API"])

def db_update_callback(topic, key_data, value_data):
    session = SessionLocal()
    try:
        logger.info(f"DB update callback called for topic: {topic}")
        logger.info(f"Key data: {key_data}")
        logger.info(f"Value data: {value_data}")
        
        if topic == "datagen_trending_products":
            # Update trending products table
            product_id = key_data.get("product_id")
            view_count = value_data.get("view_count")
            
            # Handle different data formats
            if not product_id and "raw_value" in value_data:
                # Try to extract product_id from raw value
                raw_val = value_data["raw_value"]
                if isinstance(raw_val, str):
                    try:
                        parsed = json.loads(raw_val)
                        product_id = parsed.get("product_id")
                        view_count = parsed.get("view_count")
                    except:
                        pass
            
            # Convert product_id to integer if it's a string
            if product_id:
                try:
                    product_id = int(product_id)
                except (ValueError, TypeError):
                    logger.error(f"Invalid product_id format: {product_id}")
                    product_id = None
            
            # Convert view_count to integer if it's a string
            if view_count is not None:
                try:
                    view_count = int(view_count)
                except (ValueError, TypeError):
                    logger.error(f"Invalid view_count format: {view_count}")
                    view_count = None
            
            logger.info(f"Trending product received: {product_id} with view count {view_count}")
            if product_id and view_count is not None:
                existing = session.query(TrendingProduct).filter_by(product_id=product_id).first()
                if existing:
                    existing.view_count = view_count
                    existing.updated_at = datetime.now(timezone.utc).isoformat()
                else:
                    session.add(TrendingProduct(
                        product_id=product_id,
                        view_count=view_count,
                        updated_at=datetime.now(timezone.utc).isoformat()
                    ))
                session.commit()
                logger.info(f"Trending product updated in database: {product_id}")
                
        elif topic == "personalized_suggestions":
            user_email = key_data.get("user_email")
            product_ids = value_data.get("suggested_products", [])
            
            # Handle different data formats
            if not user_email and "raw_value" in value_data:
                raw_val = value_data["raw_value"]
                if isinstance(raw_val, str):
                    try:
                        parsed = json.loads(raw_val)
                        user_email = parsed.get("user_email")
                        product_ids = parsed.get("suggested_products", [])
                    except:
                        pass
            
            # Convert product_ids to integers if they're strings
            if product_ids:
                try:
                    product_ids = [int(pid) if isinstance(pid, str) else pid for pid in product_ids]
                except (ValueError, TypeError) as e:
                    logger.error(f"Error converting product_ids: {e}")
                    product_ids = []
            
            if user_email and product_ids:
                session.query(UserSuggestion).filter_by(user_email=user_email).delete()
                for pid in product_ids:
                    session.add(UserSuggestion(
                        user_email=user_email,
                        product_id=pid,
                        updated_at=datetime.now(timezone.utc).isoformat()
                    ))
                session.commit()
                logger.info(f"Suggestions updated for user: {user_email}")
                
    except Exception as e:
        logger.error(f"DB update callback error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        session.rollback()
    finally:
        session.close()

@app.on_event("startup")
async def startup_event():
    """Create database tables and start the single Kafka consumer worker on startup"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
    # Start the single Kafka consumer worker
    kafka_service = KafkaService()
    kafka_service.start_consumer(
        trending_topic="datagen_trending_products",
        suggestions_topic="personalized_suggestions",
        db_update_callback=db_update_callback
    )

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "DSP Workshop application is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True) 