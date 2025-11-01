from log import logger

import asyncio

from asyncio import Task
from .payment_service import PaymentService

class TaskScopedServiceManager:
    _instances: dict[Task, PaymentService] = {}

    @classmethod
    async def execute_sign(cls, wallet_address: str, payload: dict[str, any]) -> PaymentService:
        current_task = asyncio.current_task()
        if current_task is None:
            raise RuntimeError("Must be called within an asyncio task.")
        instance = cls._instances.get(current_task)
        if instance is None:
            instance = PaymentService(wallet_address, payload)
            await instance.sign_for_payment()
            cls._instances[current_task] = instance
        return instance
    
    @classmethod
    async def execute_permit_and_transfer(cls, wallet_address: str):
        current_task = asyncio.current_task()
        if current_task is None:
            raise RuntimeError("Must be called within an asyncio task.")
        instance = cls._instances.get(current_task)
        if instance and instance.wallet_address == wallet_address:
            logger.info(f"Execute to permit and transfer with wallet address: {wallet_address} for payment service instance")
            await instance.do_permit_and_transfer()
        else:
            logger.error(f"No found payment service instance with wallet address: {wallet_address}")
            
    @classmethod
    async def release_instance(cls, wallet_address: str):
        current_task = asyncio.current_task()
        if current_task in cls._instances:
            instance = cls._instances.get(current_task)
            if instance and instance.wallet_address == wallet_address:
                instance = cls._instances.pop(current_task)
                await instance.cleanup()
                logger.info(f"Payment service instance for wallet_address: {instance.wallet_address} has cleaned up.")