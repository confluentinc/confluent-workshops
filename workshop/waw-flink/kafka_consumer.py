from confluent_kafka import Consumer
import json, uuid, logging
from datetime import datetime, timezone, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Kafka Topics
MOBILE_TOPIC = "mobile_phones_sales"
REGION_TOPIC = "region_sales"
PRODUCTS_TOPIC = "units_sold_last_5m_window"
REGIONAL_SALES_TOPIC = "regional_sales_trend"

# Global data stores
mobile_sales_data = {}
region_sales_data = {}
top_selling_product_data = {}
weekly_region_sales_data = {}

def load_properties(file_path):
    props = {}
    with open(file_path, 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                props[key.strip()] = value.strip()
    return props


def create_consumer(props, group_id_prefix):
    """Create a Kafka consumer with a random group.id suffix."""
    return Consumer({
        'bootstrap.servers': props.get("bootstrap.servers"),
        'security.protocol': props.get("security.protocol"),
        'sasl.mechanisms': props.get("sasl.mechanisms"),
        'sasl.username': props.get("sasl.username"),
        'sasl.password': props.get("sasl.password"),
        'group.id': f"{group_id_prefix}-{uuid.uuid4()}",
        'auto.offset.reset': 'earliest'
    })


def safe_json_loads(raw_bytes):
    """Safely decode and parse JSON payloads, accounting for schema prefix."""
    if raw_bytes is None:
        return None
    try:
        # Handle Schema Registry 5-byte prefix (if present)
        payload = raw_bytes[5:] if len(raw_bytes) > 5 else raw_bytes
        return json.loads(payload.decode("utf-8"))
    except Exception:
        return None
    
def parse_window_end(window_end):
    # window_end is epoch milliseconds (13 digits)
    return datetime.fromtimestamp(window_end / 1000, tz=timezone.utc)
    
def last_completed_5min_window_end():
    now = datetime.now(timezone.utc)

    floored = now.replace(second=0, microsecond=0)

    last_5min = floored.minute - (floored.minute % 5)

    return floored.replace(minute=last_5min)

def is_last_completed_5min_window(window_end_raw):
    window_end = parse_window_end(window_end_raw)
    return window_end == last_completed_5min_window_end()


def consume_mobile_sales():
    props = load_properties("client.properties")
    consumer = create_consumer(props, "mobile-sales-group")
    consumer.subscribe([MOBILE_TOPIC])
    logging.info("📱 Started consumer for mobile_phones_sales...")

    while True:
        msg = consumer.poll(1.0)
        if msg is None or msg.error():
            continue

        try:
            key = safe_json_loads(msg.key())
            value = safe_json_loads(msg.value())
            if not key or not value:
                continue

            product = key.get("product_name")
            sales = value.get("total_sales")
            if product and sales is not None:
                mobile_sales_data[product] = sales

        except Exception as e:
            logging.error(f"Error in mobile consumer: {e}")


def consume_region_sales():
    props = load_properties("client.properties")
    consumer = create_consumer(props, "region-sales-group")
    consumer.subscribe([REGION_TOPIC])
    logging.info("🌍 Started consumer for region_sales...")

    while True:
        msg = consumer.poll(1.0)
        if msg is None or msg.error():
            continue

        try:
            key = safe_json_loads(msg.key())
            value = safe_json_loads(msg.value())
            if not key or not value:
                continue  

            region = key.get("region")
            total_units = value.get("total_units")
            total_revenue = value.get("total_revenue")

            if region:
                region_sales_data[region] = {
                    "total_units": total_units or 0,
                    "total_revenue": total_revenue or 0
                }

        except Exception as e:
            logging.error(f"Error in region consumer: {e}")

def consume_top_selling_products():
    props = load_properties("client.properties")
    consumer = create_consumer(props, "top-selling-products-group")
    consumer.subscribe([PRODUCTS_TOPIC])
    logging.info("🌍 Started consumer for top_selling_products...")

    while True:
        msg = consumer.poll(1.0)
        if msg is None or msg.error():
            continue

        try:
            key = safe_json_loads(msg.key())
            value = safe_json_loads(msg.value())

            if not key or not value:
                continue

            window_end = value.get("window_end")
            if not window_end:
                continue
            if not is_last_completed_5min_window(window_end):
                continue

            product_name = key.get("product_name")
            total_units = value.get("total_units")

            if product_name and total_units is not None:
                top_selling_product_data[product_name] = total_units

        except Exception as e:
            logging.error(f"Error in top selling products consumer: {e}")


def consume_regional_sales_trend():
    props = load_properties("client.properties")
    consumer = create_consumer(props, "weekly-region-sales-group")
    consumer.subscribe([REGIONAL_SALES_TOPIC])
    logging.info("🌍 Started consumer for weekly_region_sales...")

    global weekly_region_sales_data
    temp_data = {}  # {region: {date: units}}

    while True:
        msg = consumer.poll(1.0)
        if msg is None or msg.error():
            continue

        try:
            key = safe_json_loads(msg.key())
            value = safe_json_loads(msg.value())
            if not key or not value:
                continue  

            sale_date = key.get("sale_date")
            region = key.get("region")
            units = value.get("total_units_sold")

            if not (region and sale_date):
                continue  # skip invalid entries

            if region not in temp_data:
                temp_data[region] = {}

            temp_data[region][sale_date] = units or 0

            sorted_times = sorted({d for r in temp_data for d in temp_data[r]})

            # last 10 timestamps
            last_10 = sorted_times[-10:]

            # Prepare chart output
            weekly_region_sales_data["times"] = last_10

            weekly_region_sales_data["sales"] = {
                region: [temp_data[region].get(t, 0) for t in last_10]
                for region in temp_data
            }

        except Exception as e:
            logging.error(f"Weekly region consumer error: {e}")
