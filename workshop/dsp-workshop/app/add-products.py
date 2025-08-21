import psycopg2
<<<<<<< HEAD
=======
import os
>>>>>>> PLGCEE-322

def load_db_config(file_path):
    config = {}
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, value = line.split("=", 1)
            config[key.strip()] = value.strip()
    return config

products = [
<<<<<<< HEAD
    ("IPhone", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQhWKgWvIGp-C3ZsNYNCmoySyt6VLS456wTdg&s", "Mobile", 290, 30, 2),
    ("MI Tablet", "https://ss7.vzw.com/is/image/VerizonWireless/tcl-tab-10-nxtpaper-5g-front-left?wid=465&hei=465&fmt=webp", "Tablet", 250, 9, 2),
    ("Samsung Mobile", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQaGKIyT4KvMOwvaNHEv9vg1qc0evcKk6I7Zg&s", "Mobile", 160, 18, 2),
    ("Sony Headphones", "https://m.media-amazon.com/images/I/41tp0JPPlmL.jpg", "Headphones", 150, 17, 2),
    ("Lenovo Laptop", "https://png.pngtree.com/png-vector/20191026/ourmid/pngtree-laptop-icon-png-image_1871608.jpg", "Laptop", 350, 7, 2),
    ("DELL Laptop", "https://tslab.in/wp-content/uploads/2021/01/dell-studio-14-1458-laptop-531x531-1.jpg", "Laptop", 250, 30, 2),
    ("ACER Laptop", "https://i.gadgets360cdn.com/products/large/1554980432_635_acer_aspire_3.jpg", "Laptop", 320, 25, 2),
    ("MI Mobile", "https://i03.appmifile.com/154_item_in/11/04/2025/50f7e9d6090496422a43f1c5647f2e9c.png", "Mobile", 120, 20, 2),
    ("JBL Headphones", "https://dakauf.eu/wp-content/uploads/2025/03/JBL-JR320BT-Bluetooth-Wireless-On-Ear-Headphones-for-Kids-Green.png", "Headphones", 90, 20, 2),
    ("BOAT Headphones", "https://media.croma.com/image/upload/v1674053346/Croma%20Assets/Communication/Headphones%20and%20Earphones/Images/246220_0_nnlgdz.png", "Headphones", 75, 15, 2)
]

user = ("admin", "admin-1@gmail.com", "admin")

def main():
    config_path = "psqlclient.properties"
=======
    ("IPhone", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQhWKgWvIGp-C3ZsNYNCmoySyt6VLS456wTdg&s", "Mobile", 290, 30),
    ("MI Tablet", "https://ss7.vzw.com/is/image/VerizonWireless/tcl-tab-10-nxtpaper-5g-front-left?wid=465&hei=465&fmt=webp", "Tablet", 250, 9),
    ("Samsung Mobile", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQaGKIyT4KvMOwvaNHEv9vg1qc0evcKk6I7Zg&s", "Mobile", 160, 18),
    ("Sony Headphones", "https://m.media-amazon.com/images/I/41tp0JPPlmL.jpg", "Headphones", 150, 17),
    ("Lenovo Laptop", "https://png.pngtree.com/png-vector/20191026/ourmid/pngtree-laptop-icon-png-image_1871608.jpg", "Laptop", 350, 7),
    ("DELL Laptop", "https://tslab.in/wp-content/uploads/2021/01/dell-studio-14-1458-laptop-531x531-1.jpg", "Laptop", 250, 30),
    ("ACER Laptop", "https://i.gadgets360cdn.com/products/large/1554980432_635_acer_aspire_3.jpg", "Laptop", 320, 25),
    ("MI Mobile", "https://i03.appmifile.com/154_item_in/11/04/2025/50f7e9d6090496422a43f1c5647f2e9c.png", "Mobile", 120, 20),
    ("JBL Headphones", "https://dakauf.eu/wp-content/uploads/2025/03/JBL-JR320BT-Bluetooth-Wireless-On-Ear-Headphones-for-Kids-Green.png", "Headphones", 90, 20),
    ("BOAT Headphones", "https://prod4-sprcdn-assets.sprinklr.com/200052/5b5b94f9-3bab-4e6b-ac8f-2183c4218a27-361538681/370.png", "Headphones", 75, 15)
]


def main():
    # Get the base directory (dsp-workshop)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "psqlclient.properties")
>>>>>>> PLGCEE-322
    config = load_db_config(config_path)

    conn = psycopg2.connect(
        host=config["postgres.host"],
        database=config["postgres.db"],
        user=config["postgres.user"],
        password=config["postgres.password"]
    )

    cursor = conn.cursor()

<<<<<<< HEAD
    insert_user_query = '''
        INSERT INTO USERS (name, email, role)
        VALUES (%s, %s, %s)
        ON CONFLICT (email) DO NOTHING
    '''
    cursor.execute(insert_user_query, user)

    insert_products_query = '''
        INSERT INTO PRODUCTS (name, image, type, price, quantity, owner_id)
        VALUES (%s, %s, %s, %s, %s, %s)
=======
    insert_products_query = '''
        INSERT INTO PRODUCTS (name, image, type, price, quantity)
        VALUES (%s, %s, %s, %s, %s)
>>>>>>> PLGCEE-322
    '''
    cursor.executemany(insert_products_query, products)

    conn.commit()
<<<<<<< HEAD
    print("Products and admin user inserted successfully.")
=======
    print("Products inserted successfully.")
>>>>>>> PLGCEE-322
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
