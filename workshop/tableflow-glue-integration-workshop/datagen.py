from confluent_kafka import SerializingProducer
from confluent_kafka.serialization import StringSerializer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.json_schema import JSONSerializer
from faker import Faker
import random, datetime, time, uuid

def load_properties(file_path):
    props = {}
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                props[key.strip()] = value.strip()
    return props

props = load_properties("client.properties")

schema_registry_conf = {
    "url": props["schema.registry.url"],
    "basic.auth.user.info": props["basic.auth.user.info"]
}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)

with open("ecommerce_order.json", "r") as f:
    schema_str = f.read()

json_serializer = JSONSerializer(schema_str, schema_registry_client)

producer_conf = {
    "bootstrap.servers": props["bootstrap.servers"],
    "security.protocol": props["security.protocol"],
    "sasl.mechanisms": props["sasl.mechanisms"],
    "sasl.username": props["sasl.username"],
    "sasl.password": props["sasl.password"],
    "key.serializer": StringSerializer("utf_8"),
    "value.serializer": json_serializer
}

producer = SerializingProducer(producer_conf)

faker = Faker()

PRODUCTS = [
    {"id": "PROD1", "name": "iPhone 16", "category": "Electronics"},
    {"id": "PROD2", "name": "Samsung Galaxy S25", "category": "Electronics"},
    {"id": "PROD3", "name": "AirPods Pro", "category": "Electronics"},
    {"id": "PROD4", "name": "Nike Running Shoes", "category": "Fashion"},
    {"id": "PROD5", "name": "Levi's Jeans", "category": "Fashion"},
    {"id": "PROD6", "name": "Wooden Dining Table", "category": "Home"},
    {"id": "PROD7", "name": "Ceramic Vase", "category": "Home"},
    {"id": "PROD8", "name": "MacBook Pro", "category": "Electronics"},
    {"id": "PROD9", "name": "Samsung TV 55\"", "category": "Electronics"},
    {"id": "PROD10", "name": "Adidas Hoodie", "category": "Fashion"},
    {"id": "PROD11", "name": "Sony PlayStation 6", "category": "Electronics"},
    {"id": "PROD12", "name": "LG Refrigerator", "category": "Home"},
    {"id": "PROD13", "name": "Dell XPS 15", "category": "Electronics"},
    {"id": "PROD14", "name": "HP Spectre Laptop", "category": "Electronics"},
    {"id": "PROD15", "name": "Canon DSLR Camera", "category": "Electronics"},
    {"id": "PROD16", "name": "KitchenAid Mixer", "category": "Home"},
    {"id": "PROD17", "name": "Samsung Microwave", "category": "Home"},
    {"id": "PROD18", "name": "Puma Sneakers", "category": "Fashion"},
    {"id": "PROD19", "name": "Levi's Jacket", "category": "Fashion"},
    {"id": "PROD20", "name": "Apple Watch Series 10", "category": "Electronics"},
    {"id": "PROD21", "name": "Google Pixel 12", "category": "Electronics"},
    {"id": "PROD22", "name": "Bose Headphones", "category": "Electronics"},
    {"id": "PROD23", "name": "Wooden Coffee Table", "category": "Home"},
    {"id": "PROD24", "name": "Ikea Sofa", "category": "Home"},
    {"id": "PROD25", "name": "Ray-Ban Sunglasses", "category": "Fashion"},
    {"id": "PROD26", "name": "Samsung Smartwatch", "category": "Electronics"},
    {"id": "PROD27", "name": "Amazon Echo Dot", "category": "Electronics"},
    {"id": "PROD28", "name": "Nike T-Shirt", "category": "Fashion"},
    {"id": "PROD29", "name": "HP Printer", "category": "Electronics"},
    {"id": "PROD30", "name": "Dyson Vacuum Cleaner", "category": "Home"}
]

LOCATIONS = [
    "Bangalore", "Mumbai", "Delhi", "Hyderabad", "Gurgaon", "New York", "London", "Paris", "Tokyo", "Berlin", "Sydney", "Toronto", "Singapore", "Dubai"
]

SUPPLIERS = ["TechSource", "FashionHub", "HomeMart", "ElectroWorld", "UrbanStyles"]
WAREHOUSES = ["Bangalore Warehouse", "Mumbai Warehouse", "Delhi Warehouse", "Chennai Warehouse", "Global Warehouse"]
LOGISTICS_PARTNERS = ["BlueDart", "FedEx", "DHL", "EcomExpress", "Delhivery"]

def generate_order():
    order_date = faker.date_time_between(start_date="-30d", end_date="now")
    expected_days = random.randint(1, 10)
    delivery_shift = random.randint(-3, 5)
    delivery_date = order_date + datetime.timedelta(days=expected_days + delivery_shift)

    status = "Delivered" if delivery_date <= datetime.datetime.utcnow() else random.choice(["Pending", "Shipped"])
    return_flag = random.choice([True, False]) if status == "Delivered" else False
    return_reason = random.choice(["Damaged", "Wrong Item", "Late Delivery", "Quality Issue"]) if return_flag else None

    product = random.choice(PRODUCTS)
    
    return {
        "order_id": f"ORD{random.randint(1000,9999)}",
        "order_date": order_date.isoformat(),
        "delivery_date": delivery_date.isoformat(),
        "customer_id": f"CUST{random.randint(1,500)}",
        "customer_location": random.choice(LOCATIONS),
        "product_id": product["id"],
        "product_name": product["name"],
        "category": product["category"],
        "quantity": random.randint(1, 10),
        "unit_price": round(random.uniform(50, 500), 2),
        "supplier_id": f"SUP{random.randint(1,50)}",
        "supplier_name": random.choice(SUPPLIERS),
        "warehouse_id": f"WH{random.randint(1,10)}",
        "warehouse_location": random.choice(LOCATIONS),
        "status": status,
        "return_flag": return_flag,
        "return_reason": return_reason,
        "logistics_partner": random.choice(LOGISTICS_PARTNERS),
        "logistics_cost": round(random.uniform(10, 100), 2),
        "cogs": round(random.uniform(20, 200), 2),
        "total_order_value": round(random.uniform(200, 2000), 2),
        "profit_margin": round(random.uniform(50, 500), 2)
    }

print("Producing messages... Press Ctrl+C to stop.")
try:
    while True:
        order = generate_order()
        producer.produce(topic="ecommerce_orders", key=order["order_id"], value=order)
        print(f"Produced: {order}")
        producer.flush()
        time.sleep(1)  # adjust rate as needed
except KeyboardInterrupt:
    print("Stopped producing messages.")
