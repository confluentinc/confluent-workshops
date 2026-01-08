from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import threading
import kafka_consumer

app = FastAPI()

# Serve static and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Start Kafka consumers in background threads
threading.Thread(target=kafka_consumer.consume_mobile_sales, daemon=True).start()
threading.Thread(target=kafka_consumer.consume_region_sales, daemon=True).start()
threading.Thread(target=kafka_consumer.consume_top_selling_products, daemon=True).start()
threading.Thread(target=kafka_consumer.consume_regional_sales_trend, daemon=True).start()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/data")
async def get_data():
    return {
        "mobile_sales": kafka_consumer.mobile_sales_data,
        "region_sales": kafka_consumer.region_sales_data,
        "top_selling_products": kafka_consumer.top_selling_product_data,
        "weekly_region_sales": kafka_consumer.weekly_region_sales_data
    }
