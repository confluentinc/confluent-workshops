import psycopg2
import random

def load_properties(filepath):
    props = {}
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                props[key.strip()] = value.strip()
    return props

# Load DB credentials
config = load_properties("psql_client.properties")

# PostgreSQL connection
conn = psycopg2.connect(
    host=config.get("host"),
    database=config.get("database"),
    user=config.get("user"),
    password=config.get("password"),
    port=int(config.get("port", 5432))
)
cursor = conn.cursor()

# Static product-price mapping
PRODUCTS = {
    "Samsung S25 Ultra 5G": 1299,
    "Apple iPhone 15 Pro Max": 1499,
    "OnePlus 12R": 549,
    "Google Pixel 9 Pro": 1099,
    "Xiaomi 14 Ultra": 999,
    "Vivo X100 Pro": 899,
    "Oppo Find X7": 849,
    "Motorola Edge 50": 499,
    "Realme GT 6": 429,
    "Nothing Phone 2a": 329,
    "Sony Xperia 1 VI": 1199,
    "Asus ROG Phone 8": 899,
    "Redmi Note 13 Pro": 279,
    "Poco F6": 329,
    "iQOO 12": 649,
    "Honor Magic 6": 799,
    "Nokia X30": 379,
    "Tecno Phantom X2": 449,
    "Infinix Zero Ultra": 399,
    "Lava Agni 2": 299,
    "RealMe 5 Pro": 150
}

def ensure_unique_constraint():
    try:
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'unique_product_name'
                ) THEN
                    ALTER TABLE products
                    ADD CONSTRAINT unique_product_name UNIQUE (name);
                END IF;
            END$$;
        """)
        conn.commit()
        print("✅ Ensured unique constraint on 'name'")
    except Exception as e:
        print(f"⚠️ Could not add unique constraint: {e}")

def insert_products_once():
    for name, price in PRODUCTS.items():
        quantity = random.randint(70, 100)
        cursor.execute("""
            INSERT INTO products (name, price, quantity)
            VALUES (%s, %s, %s)
            ON CONFLICT (name) DO NOTHING;
        """, (name, price, quantity))
    conn.commit()
    print("✅ Inserted all unique products")

if __name__ == "__main__":
    ensure_unique_constraint()
    insert_products_once()
    cursor.close()
    conn.close()
