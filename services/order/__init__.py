import sqlite3

DB_FILE = "zen7_payment.db"

def initialize_database():
    """Connects to the DB (creating it if necessary) and ensures tables exists."""

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            create table if not exists orders (
                order_number text primary key,
                user_id text not null,
                spend_amount real not null,
                budget real not null,
                currency text not null,
                deadline integer not null,
                status text not null,
                status_message text,
                creation_time integer not null)
        """)
initialize_database()