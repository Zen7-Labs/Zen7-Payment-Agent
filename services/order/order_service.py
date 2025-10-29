from log import logger
import dao.app as pg_dao

def add_or_update_order_item(order_number: str, user_id: str, spend_amount: float, budget: float, currency: str, deadline: int, status: str, status_message: str = ""):
    pg_dao.add_or_update_order_item(order_number, user_id, spend_amount, budget, currency, deadline, status, status_message)
    logger.info(f"Successfully inserted order - order_number: {order_number}, spend_amount: {spend_amount}, budget: {budget}, currency: {currency}, deadline: {deadline}, status: {status}, status_message: {status_message}")

def get_order_item(order_number: str) -> dict[str, any]:
    return pg_dao.get_order_item(order_number)
    
def get_order_list_by_user(user_id: str) -> list[dict[str, any]]:
    return pg_dao.get_order_list_by_user(user_id)