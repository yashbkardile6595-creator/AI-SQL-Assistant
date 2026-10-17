"""Create and seed a small SQLite database for local testing."""
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "sales.db"

def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript("""
        DROP TABLE IF EXISTS sales;
        DROP TABLE IF EXISTS products;
        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            unit_price REAL NOT NULL,
            stock_quantity INTEGER NOT NULL
        );
        CREATE TABLE sales (
            sale_id INTEGER PRIMARY KEY,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            sale_date TEXT NOT NULL,
            revenue REAL NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        );
        """)
        products = [
            (1, "Laptop", "Electronics", 1200.0, 14),
            (2, "Widget A", "Accessories", 25.0, 120),
            (3, "Monitor", "Electronics", 280.0, 22),
            (4, "Keyboard", "Accessories", 55.0, 9),
            (5, "Office Chair", "Furniture", 180.0, 16),
        ]
        sales = [
            (1, 1, 1, "2025-01-12", 1200.0),
            (2, 2, 20, "2025-01-18", 500.0),
            (3, 3, 3, "2025-02-03", 840.0),
            (4, 1, 2, "2025-02-14", 2400.0),
            (5, 4, 10, "2025-03-08", 550.0),
            (6, 5, 4, "2025-03-19", 720.0),
            (7, 2, 35, "2025-04-01", 875.0),
            (8, 3, 5, "2025-04-20", 1400.0),
            (9, 1, 1, "2025-05-11", 1200.0),
            (10, 5, 6, "2025-05-23", 1080.0),
        ]
        conn.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?)", products)
        conn.executemany("INSERT INTO sales VALUES (?, ?, ?, ?, ?)", sales)
    print(f"Created sample database: {DB_PATH}")
    print("Tables: products, sales")

if __name__ == "__main__":
    main()
