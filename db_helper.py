import os

import mysql.connector
from dotenv import load_dotenv

# Load configuration from a local .env file (see .env.example).
load_dotenv()

# Database configuration is read from environment variables so that no
# credentials are ever committed to source control.
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "")
DB_NAME = os.getenv("DB_NAME", "beanbuddy")

def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME
    )

def init_db():
    # MySQL doesn't use 'sqlite3.Row', it uses dictionaries if requested
    # We will handle table creation manually or assume it persists.
    # For this resume project, we run this once to create tables.
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS menu (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            price DECIMAL(10, 2) NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INT AUTO_INCREMENT PRIMARY KEY,
            session_id VARCHAR(255), 
            status VARCHAR(50) DEFAULT 'IN_PROGRESS'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            order_id INT,
            item_name VARCHAR(255),
            size VARCHAR(50),
            quantity INT,
            total_price DECIMAL(10, 2),
            FOREIGN KEY (order_id) REFERENCES orders(order_id)
        )
    ''')

    # Check if menu is empty
    cursor.execute('SELECT count(*) FROM menu')
    if cursor.fetchone()[0] == 0:
        val = [
            ('latte', 5.00),
            ('cappuccino', 6.00),
            ('espresso', 3.00),
            ('americano', 4.00)
        ]
        cursor.executemany("INSERT INTO menu (name, price) VALUES (%s, %s)", val)
        conn.commit()
        print("Database initialized with dummy data.")
    
    conn.close()

def get_formatted_menu():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True) # returns results as dicts
    cursor.execute("SELECT name, price FROM menu")
    items = cursor.fetchall()
    conn.close()
    
    if not items:
        return "Our menu is currently empty."
        
    response = "Here is our menu:\n"
    for item in items:
        response += f"{item['name'].capitalize()}: ${item['price']}\n"
    return response

def get_or_create_order(session_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT order_id FROM orders WHERE session_id = %s AND status = 'IN_PROGRESS'", (session_id,))
    order = cursor.fetchone()
    
    if order:
        order_id = order['order_id']
        conn.close()
        return order_id
    else:
        cursor.execute("INSERT INTO orders (session_id, status) VALUES (%s, 'IN_PROGRESS')", (session_id,))
        conn.commit()
        order_id = cursor.lastrowid
        conn.close()
        return order_id

def add_item_to_order(session_id, item_name, size, quantity):
    order_id = get_or_create_order(session_id)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT price FROM menu WHERE LOWER(name) = LOWER(%s)", (item_name,))
    result = cursor.fetchone()
    
    if result is None:
        conn.close()
        return -1 
        
    price = float(result['price'])
    
    if size.lower() == "large":
        price += 1.00
    elif size.lower() == "medium":
        price += 0.50
        
    total_price = price * quantity
    
    cursor.execute("INSERT INTO order_items (order_id, item_name, size, quantity, total_price) VALUES (%s, %s, %s, %s, %s)", 
                   (order_id, item_name, size, quantity, total_price))
    
    conn.commit()
    conn.close()
    return 1 

def get_current_order_items(session_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = """
    SELECT item_name, size, quantity, total_price 
    FROM order_items 
    JOIN orders ON order_items.order_id = orders.order_id 
    WHERE orders.session_id = %s AND orders.status = 'IN_PROGRESS'
    """
    cursor.execute(query, (session_id,))
    items = cursor.fetchall()
    conn.close()
    
    if not items:
        return ""
        
    response = "So far you have:\n"
    for item in items:
        response += f"- {item['size']} {item['item_name']} (${item['total_price']})\n"
    return response

def complete_order(session_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT order_id FROM orders WHERE session_id = %s AND status = 'IN_PROGRESS'", (session_id,))
    result = cursor.fetchone()
    
    if result is None:
        conn.close()
        return None 
        
    order_id = result['order_id']
    
    cursor.execute("SELECT SUM(total_price) as total FROM order_items WHERE order_id = %s", (order_id,))
    total_result = cursor.fetchone()
    total_amount = total_result['total']
    
    if total_amount is None:
        total_amount = 0.0
    else:
        total_amount = float(total_amount)
        
    cursor.execute("UPDATE orders SET status = 'PREPARING' WHERE order_id = %s", (order_id,))
    conn.commit()
    conn.close()
    return order_id, total_amount

def get_order_status(order_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT status FROM orders WHERE order_id = %s", (order_id,))
    result = cursor.fetchone()
    conn.close()
    if result is None:
        return None
    return result['status']

def remove_item_from_order(session_id, item_name):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT order_id FROM orders WHERE session_id = %s AND status = 'IN_PROGRESS'", (session_id,))
    result = cursor.fetchone()
    
    if result is None:
        conn.close()
        return -1
        
    order_id = result['order_id']
    
    cursor.execute("SELECT * FROM order_items WHERE order_id = %s AND LOWER(item_name) = LOWER(%s)", (order_id, item_name))
    item_check = cursor.fetchone()
    
    if item_check is None:
        conn.close()
        return 0 
        
    cursor.execute("DELETE FROM order_items WHERE order_id = %s AND LOWER(item_name) = LOWER(%s)", (order_id, item_name))
    
    conn.commit()
    conn.close()
    return 1

# Run initialization
if __name__ == "__main__":
    init_db()