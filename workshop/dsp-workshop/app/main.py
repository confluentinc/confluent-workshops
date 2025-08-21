<<<<<<< HEAD
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from confluent_kafka import Producer, Consumer
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
import json
import random
import logging
from typing import List, Dict, Any
# AWS Athena setup
import boto3
import pandas as pd
import plotly
import plotly.graph_objs as go
import plotly.express as px

# Add AWS configuration function after your existing config functions
def read_aws_config():
    config = {}
    try:
        with open("aws.properties") as fh:
            for line in fh:
                line = line.strip()
                if len(line) != 0 and line[0] != "#":
                    parameter, value = line.strip().split('=', 1)
                    config[parameter] = value.strip()
    except FileNotFoundError:
        logger.warning("aws.properties file not found, using default AWS config")
    return config

# Add AWS Athena setup after your existing configurations
try:
    aws_config = read_aws_config()
    athena_client = boto3.client(
        'athena',
        region_name=aws_config.get('aws.region', 'us-east-1'),
        aws_access_key_id=aws_config.get('aws.access_key_id'),
        aws_secret_access_key=aws_config.get('aws.secret_access_key'),
        aws_session_token=aws_config.get('aws.session_token')
    )
except Exception as e:
    logger.warning(f"AWS Athena client initialization failed: {e}")
    athena_client = None
=======
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
>>>>>>> PLGCEE-322

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

<<<<<<< HEAD
# FastAPI and Templates setup
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Read config from client.properties
def read_psql_config():
    config = {}
    with open("psqlclient.properties") as fh:
        for line in fh:
            line = line.strip()
            if len(line) != 0 and line[0] != "#":
                parameter, value = line.strip().split('=', 1)
                config[parameter] = value.strip()
    return config

# Read config from client.properties
def read_kafka_config():
    config = {}
    with open("client.properties") as fh:
        for line in fh:
            line = line.strip()
            if len(line) != 0 and line[0] != "#":
                parameter, value = line.strip().split('=', 1)
                config[parameter] = value.strip()
    return config

def get_kafka_config():
    full_config = read_kafka_config()
    kafka_keys = {
        "bootstrap.servers",
        "security.protocol",
        "sasl.mechanisms",
        "sasl.username",
        "sasl.password"
    }
    return {k: v for k, v in full_config.items() if k in kafka_keys}

config = read_psql_config()

# PostgreSQL setup
DATABASE_URL = (
    f"postgresql://{config['postgres.user']}:{config['postgres.password']}"
    f"@{config['postgres.host']}/{config['postgres.db']}"
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    role = Column(String, default="user")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    image = Column(String)
    type = Column(String)
    price = Column(Float)
    quantity = Column(Integer)
    owner_id = Column(Integer, ForeignKey("users.id"))

class CartItem(Base):
    __tablename__ = "cart"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    price = Column(Float)

# Create tables
Base.metadata.create_all(bind=engine)

# Kafka Producer
producer = Producer(get_kafka_config())

def get_suggestions_from_kafka(
    topic: str,
    kafka_config: Dict[str, str],
    user_email: str,
    db,
    limit: int = None
) -> List[Product]:
    from confluent_kafka import Consumer
    import json
    import random
    import logging
    from collections import OrderedDict

    logger = logging.getLogger("suggestions")

    consumer_config = kafka_config.copy()
    consumer_config["group.id"] = f"suggestions-consumer-{random.randint(1000, 9999)}"
    consumer_config["auto.offset.reset"] = "earliest"
    consumer_config["enable.auto.commit"] = False

    consumer = Consumer(consumer_config)
    consumer.subscribe([topic])

    seen_ids = OrderedDict()

    try:
        timeout_count = 0
        max_timeout = 10
        while timeout_count < max_timeout:
            msg = consumer.poll(1.0)
            if msg is None:
                timeout_count += 1
                continue
            if msg.error():
                logger.error(f"Consumer error: {msg.error()}")
                continue

            raw_key = msg.key()
            raw_value = msg.value()
            if not raw_key or not raw_value:
                continue

            try:
                key_str = raw_key[5:].decode("utf-8")
                value_str = raw_value[5:].decode("utf-8")

                key_data = json.loads(key_str)
                value_data = json.loads(value_str)

                if key_data.get("user_email") == user_email:
                    product_ids = value_data.get("suggested_products", [])
                    for pid in product_ids:
                        seen_ids[pid] = True  # ordered set behavior

            except Exception as e:
                logger.warning(f"Suggestion decoding error: {e}")
                continue

    except Exception as e:
        logger.error(f"Kafka consumption failed: {e}")
    finally:
        consumer.close()

    final_ids = list(seen_ids.keys())
    logger.info(f"Collected suggested product IDs: {final_ids}")

    if limit:
        final_ids = final_ids[:limit]

    products = db.query(Product).filter(Product.id.in_(final_ids)).all()
    id_to_product = {p.id: p for p in products}
    matched_products = [id_to_product[pid] for pid in final_ids if pid in id_to_product]

    logger.info(f"Final matched products from DB: {[p.id for p in matched_products]}")
    return matched_products

def get_trending_products_from_kafka(topic: str, kafka_config: Dict[str, str], limit: int = 6) -> List[Dict[str, Any]]:
    from confluent_kafka import Consumer
    import json
    import random
    import logging

    logger = logging.getLogger("main")

    consumer_config = kafka_config.copy()
    consumer_config["group.id"] = f"trending-consumer-{random.randint(1000, 9999)}"
    consumer_config["auto.offset.reset"] = "earliest"
    consumer_config["enable.auto.commit"] = False

    consumer = Consumer(consumer_config)
    consumer.subscribe([topic])

    product_views = {}
    timeout_count = 0
    max_timeout = 10

    try:
        while timeout_count < max_timeout:
            msg = consumer.poll(1.0)
            if msg is None:
                timeout_count += 1
                continue
            if msg.error():
                logger.error(f"Consumer error: {msg.error()}")
                continue

            raw_key = msg.key()
            raw_value = msg.value()

            if not raw_key or not raw_value:
                continue

            try:
                # Decode Confluent 5-byte schema prefix
                key_str = raw_key[5:].decode("utf-8")
                value_str = raw_value[5:].decode("utf-8")

                key_data = json.loads(key_str)
                value_data = json.loads(value_str)

                if "product_id" not in key_data or "view_count" not in value_data:
                    logger.warning(f"Incomplete data: key={key_str}, value={value_str}")
                    continue

                product_id = key_data["product_id"]
                view_count = value_data["view_count"]

                if product_id not in product_views or view_count > product_views[product_id]["view_count"]:
                    product_views[product_id] = {
                        "product_id": product_id,
                        "view_count": view_count
                    }
                logger.info(f"Accepted trending record: {product_views[product_id]}")

            except Exception as e:
                logger.warning(f"Error decoding Kafka message. Error: {e}")
                continue

    except Exception as e:
        logger.error(f"Kafka consumption failed: {e}")
    finally:
        consumer.close()

    trending = list(product_views.values())
    trending.sort(key=lambda x: x["view_count"], reverse=True)
    return trending[:limit]

# Utility
def is_admin(db, email):
    user = db.query(User).filter_by(email=email).first()
    return user and user.role == "admin"

# Routes
@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login_user(name: str = Form(...), email: str = Form(...)):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(email=email).first()
        if not user:
            db.add(User(name=name, email=email))
            db.commit()
    finally:
        db.close()
    return RedirectResponse(f"/products?email={email}", status_code=303)

@app.get("/products", response_class=HTMLResponse)
def get_products(request: Request, email: str):
    db = SessionLocal()
    try:
        all_products = db.query(Product).all()
        return templates.TemplateResponse("products.html", {
            "request": request,
            "products": all_products,
            "email": email,
            "is_admin": is_admin(db, email)
        })
    finally:
        db.close()

@app.post("/cart/add")
def add_to_cart(email: str = Form(...), product_id: int = Form(...), quantity: int = Form(...)):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(email=email).first()
        product = db.query(Product).filter_by(id=product_id).first()
        if product and quantity <= product.quantity:
            db.add(CartItem(user_id=user.id, product_id=product.id, quantity=quantity, price=product.price))
            product.quantity -= quantity
            db.commit()
    finally:
        db.close()
    return RedirectResponse(f"/products?email={email}", status_code=303)

@app.get("/cart", response_class=HTMLResponse)
def view_cart(request: Request, email: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(email=email).first()
        cart_items = db.query(CartItem).filter_by(user_id=user.id).all()
        products = {p.id: p for p in db.query(Product).all()}
        for item in cart_items:
            item.product_name = products[item.product_id].name
        return templates.TemplateResponse("cart.html", {
            "request": request,
            "cart": cart_items,
            "email": email
        })
    finally:
        db.close()

@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request, email: str):
    db = SessionLocal()
    try:
        if not is_admin(db, email):
            return RedirectResponse(f"/products?email={email}", status_code=303)
        return templates.TemplateResponse("admin.html", {"request": request, "email": email})
    finally:
        db.close()

@app.post("/admin/upload")
def upload_product(email: str = Form(...), name: str = Form(...), image: str = Form(...),
                   type: str = Form(...), price: float = Form(...), quantity: int = Form(...)):
    db = SessionLocal()
    try:
        if not is_admin(db, email):
            return {"error": "Unauthorized"}
        owner = db.query(User).filter_by(email=email).first()
        db.add(Product(name=name, image=image, type=type, price=price, quantity=quantity, owner_id=owner.id))
        db.commit()
    finally:
        db.close()
    return RedirectResponse(f"/admin?email={email}", status_code=303)

@app.post("/admin/delete")
def delete_product(email: str = Form(...), product_id: int = Form(...)):
    db = SessionLocal()
    try:
        if not is_admin(db, email):
            return {"error": "Unauthorized"}
        db.query(Product).filter_by(id=product_id).delete()
        db.commit()
    finally:
        db.close()
    return RedirectResponse(f"/products?email={email}", status_code=303)

@app.get("/admin/edit", response_class=HTMLResponse)
def edit_product(request: Request, email: str, product_id: int):
    db = SessionLocal()
    try:
        if not is_admin(db, email):
            return RedirectResponse(f"/products?email={email}", status_code=303)
        product = db.query(Product).filter_by(id=product_id).first()
        return templates.TemplateResponse("edit_product.html", {
            "request": request,
            "email": email,
            "product": product
        })
    finally:
        db.close()

@app.post("/admin/update")
def update_product(email: str = Form(...), product_id: int = Form(...),
                   name: str = Form(...), image: str = Form(...),
                   type: str = Form(...), price: float = Form(...), quantity: int = Form(...)):
    db = SessionLocal()
    try:
        if not is_admin(db, email):
            return {"error": "Unauthorized"}
        product = db.query(Product).filter_by(id=product_id).first()
        if product:
            product.name = name
            product.image = image
            product.type = type
            product.price = price
            product.quantity = quantity
            db.commit()
    finally:
        db.close()
    return RedirectResponse(f"/products?email={email}", status_code=303)

@app.post("/track-click")
async def track_click(request: Request):
    try:
        data = await request.json()
        logger.info(f"Clickstream received: {data}")
        
        # Produce to Kafka
        message = json.dumps(data).encode("utf-8")
        producer.produce("datagen_product_view", value=message)
        producer.flush()
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error tracking click: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/logout")
def logout():
    return RedirectResponse("/", status_code=303)

@app.get("/delete-account")
def delete_account(email: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(email=email).first()
        if user and user.role != "admin":
            db.query(CartItem).filter_by(user_id=user.id).delete()
            db.query(Product).filter_by(owner_id=user.id).delete()
            db.query(User).filter_by(id=user.id).delete()
            db.commit()
            return RedirectResponse("/", status_code=303)
    finally:
        db.close()
    return RedirectResponse(f"/products?email={email}", status_code=303)

@app.post("/cart/remove")
def remove_from_cart(email: str = Form(...), cart_id: int = Form(...)):
    db = SessionLocal()
    try:
        cart_item = db.query(CartItem).filter_by(id=cart_id).first()
        if cart_item:
            product = db.query(Product).filter_by(id=cart_item.product_id).first()
            if product:
                product.quantity += cart_item.quantity  # restore the quantity
            db.delete(cart_item)
            db.commit()
    finally:
        db.close()
    return RedirectResponse(f"/cart?email={email}", status_code=303)

@app.get("/trending")
def get_trending_api(email: str):
    db = SessionLocal()
    try:
        topic = "datagen_trending_products"
        trending_data = get_trending_products_from_kafka(topic, get_kafka_config(), limit=6)

        product_ids = [int(item["product_id"]) for item in trending_data if "product_id" in item]
        products = db.query(Product).filter(Product.id.in_(product_ids)).all()
        product_map = {p.id: p for p in products}

        final_data = []
        for item in trending_data:
            pid = int(item["product_id"])
            product = product_map.get(pid)
            if product:
                final_data.append({
                    "product_id": pid,
                    "view_count": item["view_count"],
                    "name": product.name,
                    "image": product.image,
                    "type": product.type,
                    "price": product.price,
                    "quantity": product.quantity
                })

        return final_data
    finally:
        db.close()

@app.get("/suggestions")
def get_suggestions_api(email: str):
    db = SessionLocal()
    try:
        suggestions = get_suggestions_from_kafka("personalized_suggestions", get_kafka_config(), email, db)
        return [{
            "product_id": p.id,
            "name": p.name,
            "image": p.image,
            "type": p.type,
            "price": p.price,
            "quantity": p.quantity
        } for p in suggestions]
    finally:
        db.close()

# Add the execute_athena_query function
def execute_athena_query(query: str, database: str = "default"):
    """Execute Athena query and return results as DataFrame"""
    if not athena_client:
        logger.error("Athena client not initialized")
        return pd.DataFrame()
    
    try:
        logger.info(f"Executing Athena query: {query}")
        logger.info(f"Database: {database}")
        logger.info(f"Output location: {aws_config.get('athena.output_location')}")
        
        # Start query execution
        response = athena_client.start_query_execution(
            QueryString=query,
            QueryExecutionContext={'Database': database},
            ResultConfiguration={
                'OutputLocation': aws_config.get('athena.output_location', 's3://dspathenaworkshopqueries/')
            }
        )
        
        query_execution_id = response['QueryExecutionId']
        logger.info(f"Query execution ID: {query_execution_id}")
        
        # Wait for query to complete
        import time
        max_wait_time = 60  # Maximum wait time in seconds
        wait_time = 0
        
        while wait_time < max_wait_time:
            result = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
            status = result['QueryExecution']['Status']['State']
            logger.info(f"Query status: {status}, waited {wait_time}s")
            
            if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                break
            time.sleep(2)
            wait_time += 2
        
        if status == 'SUCCEEDED':
            logger.info("Query succeeded, fetching results...")
            # Get query results
            results = athena_client.get_query_results(QueryExecutionId=query_execution_id)
            
            # Debug: Log the raw results structure
            logger.info(f"Results metadata: {results.get('ResultSet', {}).get('ResultSetMetadata', {})}")
            logger.info(f"Number of rows returned: {len(results.get('ResultSet', {}).get('Rows', []))}")
            
            # Convert to DataFrame
            if 'ResultSet' in results and 'Rows' in results['ResultSet']:
                if len(results['ResultSet']['Rows']) > 0:
                    columns = [col['Label'] for col in results['ResultSet']['ResultSetMetadata']['ColumnInfo']]
                    logger.info(f"Columns: {columns}")
                    
                    rows = []
                    for i, row in enumerate(results['ResultSet']['Rows'][1:]):  # Skip header row
                        row_data = []
                        for field in row['Data']:
                            # Handle different data types
                            value = field.get('VarCharValue', field.get('BigIntValue', field.get('DoubleValue', '')))
                            row_data.append(value)
                        rows.append(row_data)
                        if i < 3:  # Log first 3 rows for debugging
                            logger.info(f"Row {i}: {row_data}")
                    
                    df = pd.DataFrame(rows, columns=columns)
                    logger.info(f"DataFrame created with shape: {df.shape}")
                    return df
                else:
                    logger.warning("No data rows returned from query")
                    return pd.DataFrame()
            else:
                logger.error("Invalid results structure")
                return pd.DataFrame()
        elif status == 'FAILED':
            # Get failure reason
            failure_reason = result['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
            logger.error(f"Query failed: {failure_reason}")
            return pd.DataFrame()
        else:
            logger.error(f"Query timed out or was cancelled. Final status: {status}")
            return pd.DataFrame()
            
    except Exception as e:
        logger.error(f"Error executing Athena query: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return pd.DataFrame()

# Add these routes BEFORE your existing @app.get("/logout") route
@app.get("/analytics", response_class=HTMLResponse)
def analytics_page(request: Request, email: str):
    db = SessionLocal()
    athena_db = aws_config.get('athena.database')
    athena_table = aws_config.get('athena.table')
    qualified_table = f'"{athena_db}"."{athena_table}"'

    try:
        charts = {}
        total_clicks = 0
        top_users_data = []
        
        if athena_client:
            try:
                # 1. Product click trends over 5-minute spans
                click_trends_query = f"""
                SELECT 
                    DATE_TRUNC('minute', CAST("$$timestamp" AS timestamp)) - 
                    INTERVAL '1' MINUTE * (MINUTE(CAST("$$timestamp" AS timestamp)) % 5) as time_bucket,
                    COUNT(*) as click_count
                FROM {qualified_table}
                WHERE CAST("$$timestamp" AS timestamp) >= CURRENT_TIMESTAMP - INTERVAL '24' HOUR
                GROUP BY 1
                ORDER BY time_bucket
                """

                # 2. Product type distribution
                product_type_query = f"""
                SELECT type as product_type, COUNT(*) as click_count
                FROM {qualified_table}
                WHERE CAST("$$timestamp" AS timestamp) >= CURRENT_TIMESTAMP - INTERVAL '24' HOUR
                GROUP BY type
                ORDER BY click_count DESC
                """

                # 3. Total clicks KPI
                total_clicks_query = f"""
                SELECT COUNT(*) as total_clicks
                FROM {qualified_table}
                WHERE CAST("$$timestamp" AS timestamp) >= CURRENT_TIMESTAMP - INTERVAL '24' HOUR
                """

                # 4. Top 5 Active Users
                top_users_query = f"""
                SELECT email, COUNT(*) as click_count
                FROM {qualified_table}
                WHERE CAST("$$timestamp" AS timestamp) >= CURRENT_TIMESTAMP - INTERVAL '24' HOUR
                GROUP BY email
                ORDER BY click_count DESC
                LIMIT 5
                """

                # Execute queries
                click_trends_df = execute_athena_query(click_trends_query)
                product_type_df = execute_athena_query(product_type_query)
                total_clicks_df = execute_athena_query(total_clicks_query)
                top_users_df = execute_athena_query(top_users_query)
                
                logger.info(f"Click trends DataFrame shape: {click_trends_df.shape}")
                logger.info(f"Product type DataFrame shape: {product_type_df.shape}")
                logger.info(f"Total clicks DataFrame shape: {total_clicks_df.shape}")
                logger.info(f"Top users DataFrame shape: {top_users_df.shape}")
                
                # Create Chart 1: Click Trends Line Chart
                if not click_trends_df.empty:
                    click_trends_df['click_count'] = pd.to_numeric(click_trends_df['click_count'], errors='coerce')
                    
                    # Convert timestamps to string format for better display
                    time_labels = [str(ts) for ts in click_trends_df['time_bucket']]
                    click_values = click_trends_df['click_count'].tolist()
                    
                    charts['click_trends'] = {
                        'data': [{
                            'type': 'scatter',
                            'mode': 'lines+markers',
                            'x': time_labels,
                            'y': click_values,
                            'line': {'color': '#667eea', 'width': 3},
                            'marker': {'size': 6, 'color': '#667eea'},
                            'hovertemplate': '<b>Time:</b> %{x}<br><b>Clicks:</b> %{y}<extra></extra>'
                        }],
                        'layout': {
                            'title': 'Product Click Trends (5-Minute Intervals - Last 24 Hours)',
                            'height': 400,
                            'xaxis': {'title': 'Time', 'tickangle': -45},
                            'yaxis': {'title': 'Clicks'}
                        }
                    }

                # Create Chart 2: Product Type Distribution Pie Chart
                if not product_type_df.empty:
                    # Ensure proper data types and clean data
                    product_type_df['click_count'] = pd.to_numeric(product_type_df['click_count'], errors='coerce')
                    product_type_df = product_type_df.dropna()  # Remove any NaN values
                    
                    # Debug logging
                    logger.info(f"Product type data: {product_type_df.to_dict('records')}")
                    
                    labels = product_type_df['product_type'].tolist()
                    values = product_type_df['click_count'].tolist()
                    
                    # Create chart data structure manually
                    charts['product_type'] = {
                        'data': [{
                            'type': 'pie',
                            'labels': labels,
                            'values': values,
                            'hovertemplate': '<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>',
                            'textinfo': 'percent+label',
                            'textposition': 'inside'
                        }],
                        'layout': {
                            'title': 'Product Type Distribution (Last 24 Hours)',
                            'height': 400
                        }
                    }

                # Get Total Clicks KPI
                if not total_clicks_df.empty:
                    total_clicks = int(total_clicks_df['total_clicks'].iloc[0])

                # Create Chart 3: Top Users Bar Chart
                if not top_users_df.empty:
                    top_users_df['click_count'] = pd.to_numeric(top_users_df['click_count'], errors='coerce')
                    
                    user_emails = top_users_df['email'].tolist()
                    user_clicks = top_users_df['click_count'].tolist()
                    
                    charts['top_users'] = {
                        'data': [{
                            'type': 'bar',
                            'orientation': 'h',
                            'x': user_clicks,
                            'y': user_emails,
                            'marker': {'color': '#764ba2'},
                            'hovertemplate': '<b>User:</b> %{y}<br><b>Clicks:</b> %{x}<extra></extra>'
                        }],
                        'layout': {
                            'title': 'Top 5 Active Users (Last 24 Hours)',
                            'height': 400,
                            'xaxis': {'title': 'Clicks'},
                            'yaxis': {'title': 'User Email'},
                            'margin': {'l': 200}  # Add left margin for long email addresses
                        }
                    }
                    
                    # Prepare data for table
                    top_users_data = top_users_df.to_dict('records')

            except Exception as e:
                logger.error(f"Error creating analytics charts: {e}")
        
        return templates.TemplateResponse("analytics.html", {
            "request": request,
            "email": email,
            "charts": charts,
            "total_clicks": total_clicks,
            "top_users_data": top_users_data
        })
    finally:
        db.close()

@app.get("/api/query-data")
def custom_query(request: Request, email: str, query: str, database: str = "default"):
    """API endpoint for custom Athena queries"""
    db = SessionLocal()
    try:
        if not athena_client:
            return {"error": "Athena client not available"}
        
        logger.info(f"Custom query from {email}: {query}")
        df = execute_athena_query(query, database)
        
        result = {
            "data": df.to_dict('records'), 
            "columns": df.columns.tolist(),
            "row_count": len(df)
        }
        logger.info(f"Returning {len(df)} rows to frontend")
        return result
        
    except Exception as e:
        logger.error(f"Error in custom query: {e}")
        return {"error": str(e)}
    finally:
        db.close()
=======
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
>>>>>>> PLGCEE-322
