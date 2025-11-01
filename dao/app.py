from log import logger
from sqlmodel import Session, select
from .database import engine
from .model import OrderItem, SettlementBatch, SettlementDetail, PayoutInstruction
from datetime import datetime

def add_settlement_batch(settlement_batch: SettlementBatch, settlement_detail: SettlementDetail):
    with Session(engine) as session:
        settlement_detail.settlement_batch = settlement_batch
        session.add(settlement_detail)
        session.commit()
        session.refresh(settlement_detail)
        logger.info(f"Added settlement batch: {settlement_batch} with details: {settlement_detail}")

def add_payout_instruction(settlement_batch: SettlementBatch, payout_instruction: PayoutInstruction):
    with Session(engine) as session:
        payout_instruction.settlement_batch = settlement_batch
        session.add(payout_instruction)
        session.commit()
        session.refresh(payout_instruction)
        logger.info(f"Added settlement batch: {settlement_batch} with payout instruction: {payout_instruction}")

def add_or_update_order_item(order_number: str, user_id: str, spend_amount: float, budget: float, currency: str, chain: str, deadline: int, status: str, status_message: str = "") -> dict[str, any]:
    with Session(engine) as session:
        order_item = OrderItem(
            order_number=order_number, user_id=user_id, spend_amount=spend_amount,
            budget=budget, currency=currency, chain=chain, deadline=deadline, 
            status=status.lower(), status_message=status_message
        )
        existing_order_item = session.exec(
            select(OrderItem).where(OrderItem.order_number == order_number)
        ).first()
        if existing_order_item:
            logger.info(f"Updating existing order: {existing_order_item} with order_number: {order_number}")
            existing_order_item.status = status.lower()
            existing_order_item.updated_at = datetime.now()
            session.add(existing_order_item)
            session.commit()
            session.refresh(existing_order_item)
            return existing_order_item.model_dump(mode="json", exclude_none=True)
        else:
            logger.info(f"Adding new order: {order_number}")
            session.add(order_item)
            session.commit()
            session.refresh(order_item)
            return order_item.model_dump(mode="json", exclude_none=True)
    return None

def get_order_item(order_number: str) -> dict[str, any]:
    with Session(engine) as session:
        order_item = session.exec(
            select(OrderItem).where(OrderItem.order_number == order_number)
        ).first()
        session.commit()
        session.refresh(order_item)
        if order_item:
            logger.info(f"Get order: {order_item.model_dump()} by order_number: {order_number}")
            return order_item.model_dump(mode="json")
        return None

def get_order_list_by_user(user_id: str) -> list[dict[str, any]]:
    with Session(engine) as session:
        order_list = session.exec(
            select(OrderItem).where(OrderItem.user_id == user_id)
        ).all()
        session.commit()
        session.refresh(order_list)
        if order_list:
            logger.info(f"Get order list: {order_list} by user_id: {user_id}")
            results = []
            for order in order_list:
                results.append(order.model_dump(mode="json"))
            return results
        return None