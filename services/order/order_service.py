from log import logger
import sqlite3
from datetime import datetime, timezone
from services.order import DB_FILE

def _to_timestamp(dt: datetime):
    return int(dt.timestamp())

def _to_datetime_str(ts: int, tz: timezone = timezone.utc, pattern: str = "%Y-%m-%d") -> str:
    dt = datetime.fromtimestamp(ts, tz)
    return dt.strftime(pattern)

def add_or_update_order_item(order_number: str, user_id: str, spend_amount: float, budget: float, currency: str, deadline: int, status: str, status_message: str = ""):
    with sqlite3.connect(DB_FILE) as conn:
        
        creation_time = datetime.now()
        cursor = conn.cursor()
        cursor.execute("""
            insert or replace into orders (order_number, user_id, spend_amount, budget, currency, deadline, status, status_message, creation_time)
                values (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (order_number, user_id, spend_amount, budget, currency, deadline, status, status_message, _to_timestamp(creation_time)))
        conn.commit()
        logger.info(f"Successfully inserted order - order_number: {order_number}, spend_amount: {spend_amount}, budget: {budget}, currency: {currency}, deadline: {deadline}, status: {status}, status_message: {status_message}, creation_time: {creation_time}")

def get_order_item(order_number: str) -> dict[str, any]:
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        ptmt = cursor.execute("""
            select order_number, user_id, spend_amount, budget, deadline, currency, status, status_message, creation_time 
                from orders where order_number = ?
        """, (order_number,))
        res =ptmt.fetchone()
        if res:
            return {
                "order_number": res[0],
                "user_id": res[1],
                "spend_amount": res[2],
                "budget": res[3],
                "deadline": _to_datetime_str(res[4]),
                "currency": res[5],
                "status": res[6],
                "status_message": res[7],
                "creation_time": _to_datetime_str(res[8], pattern="%Y-%m-%d %H:%M:%S")
            }
        raise Exception(f"None of item found in orders by order_number: {order_number}")

def get_order_list_by_user(user_id: str) -> list[dict[str, any]]:
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        ptmt = cursor.execute("""
            select order_number, user_id, spend_amount, budget, deadline, currency, status, status_message, creation_time 
                from orders where user_id = ?
        """, (user_id,))
        res = ptmt.fetchall()
        if res:
            results = []
            for rs in res:
                item = {
                    "order_number": rs[0],
                    "user_id": rs[1],
                    "spend_amount": rs[2],
                    "budget": rs[3],
                    "deadline": _to_datetime_str(rs[4]),
                    "currency": rs[5],
                    "status": res[6],
                    "status_message": res[7],
                    "creation_time": _to_datetime_str(rs[8], pattern="%Y-%m-%d %H:%M:%S")
                }
                results.append(item)
            return results
        raise Exception(f"None of item found in orders by user_id: {user_id}")