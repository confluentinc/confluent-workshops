from confluent_kafka import SerializingProducer, KafkaException, KafkaError
from confluent_kafka.serialization import StringSerializer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.json_schema import JSONSerializer
from confluent_kafka.admin import AdminClient, NewTopic
from faker import Faker
import random, datetime, time, uuid

def load_properties(file_path):
    """Loads properties from a file."""
    props = {}
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                props[key.strip()] = value.strip()
    return props

def ensure_topic(props, topic_name, num_partitions=6, replication_factor=3, topic_configs=None, timeout=30):
    admin_conf = {
        "bootstrap.servers": props["bootstrap.servers"],
        "security.protocol": props["security.protocol"],
        "sasl.mechanisms": props["sasl.mechanisms"],
        "sasl.username": props["sasl.username"],
        "sasl.password": props["sasl.password"],
    }
    admin = AdminClient(admin_conf)
    md = admin.list_topics(timeout=10)
    if topic_name in md.topics and not md.topics[topic_name].error:
        print(f"Topic '{topic_name}' already exists.")
        return
    if topic_configs is None:
        topic_configs = {}
    new_topic = NewTopic(topic=topic_name, num_partitions=num_partitions, replication_factor=replication_factor, config=topic_configs)
    futures = admin.create_topics([new_topic])
    try:
        futures[topic_name].result(timeout=timeout)
        print(f"Created topic '{topic_name}' with {num_partitions} partitions.")
    except KafkaException as e:
        err = e.args[0]
        if isinstance(err, KafkaError) and err.code() == KafkaError.TOPIC_ALREADY_EXISTS:
            print(f"Topic '{topic_name}' already exists.")
        else:
            raise

# --- Configuration ---



# Load Kafka and Schema Registry properties
props = load_properties("client.properties")
ensure_topic(
    props=props,
    topic_name="sales_event",
    num_partitions=6,
    replication_factor=3,
    topic_configs={"retention.ms": "604800000", "cleanup.policy": "delete"}
)
# Configure Schema Registry client
schema_registry_conf = {
    "url": props["schema.registry.url"],
    "basic.auth.user.info": props["basic.auth.user.info"]
}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)

# Load the new sales event schema
with open("sales_event.json", "r") as f:
    schema_str = f.read()

# Create a JSONSerializer for the message value
json_serializer = JSONSerializer(schema_str, schema_registry_client)

# Configure the SerializingProducer
producer_conf = {
    "bootstrap.servers": props["bootstrap.servers"],
    "security.protocol": props["security.protocol"],
    "sasl.mechanisms": props["sasl.mechanisms"],
    "sasl.username": props["sasl.username"],
    "sasl.password": props["sasl.password"],
    "key.serializer": StringSerializer("utf_8"),  # Key is a simple string (product name)
    "value.serializer": json_serializer           # Value is serialized JSON
}

producer = SerializingProducer(producer_conf)

# --- Data Generation Constants ---

faker = Faker()

# Your provided product names
PRODUCT_NAMES = [
    "Samsung S25 Ultra 5G", "Apple iPhone 15 Pro Max", "OnePlus 12R",
    "Google Pixel 9 Pro", "Xiaomi 14 Ultra", "Vivo X100 Pro",
    "Oppo Find X7", "Motorola Edge 50", "Realme GT 6",
    "Nothing Phone 2a", "Sony Xperia 1 VI", "Asus ROG Phone 8",
    "Redmi Note 13 Pro", "Poco F6", "iQOO 12", "Honor Magic 6",
    "Nokia X30", "RealMe 5 Pro","Tecno Phantom X2", "Infinix Zero Ultra", "Lava Agni 2"
]

# Regions for data generation
REGIONS = [
    "North America", "Europe", "Asia-Pacific", "Latin America", "Middle East & Africa"
]

def generate_sales_event():
    """Generates a single fake sales event with a random timestamp from the past week."""
    product_name = random.choice(PRODUCT_NAMES)

    # Generate a random timestamp within the past 7 days
    now = datetime.datetime.now(datetime.timezone.utc)
    random_offset = datetime.timedelta(seconds=random.randint(0, 7 * 24 * 60 * 60))
    # random_timestamp = now - random_offset
    random_timestamp = now 

    return {
        "event_id": str(uuid.uuid4()),
        "event_timestamp": random_timestamp.isoformat(),
        "product_name": product_name,
        "units_sold": random.randint(1, 15),
        "region": random.choice(REGIONS)
    }

# --- Main Production Loop ---

print("Producing messages to topic 'sales_event'... Press Ctrl+C to stop.")
try:
    while True:
        sale_event = generate_sales_event()
        
        producer.produce(
            topic="sales_event",
            key=sale_event["product_name"],  # Use product_name as the message key
            value=sale_event
        )
        
        print(f"Produced: {sale_event}")
        
        # producer.flush() is inefficient in a loop.
        # For high throughput, it's better to poll().
        # But keeping flush() for simplicity to match your original script.
        producer.flush() 
        
        time.sleep(random.uniform(0.5, 2.0)) # Random sleep
        
except KeyboardInterrupt:
    print("Stopped producing messages.")
finally:
    # Ensure all outstanding messages are sent before exiting
    producer.flush()
    print("Producer flushed.")

