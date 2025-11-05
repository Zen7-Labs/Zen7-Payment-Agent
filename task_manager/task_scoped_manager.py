from log import logger

from .payment_service import PaymentService

class TaskScopedServiceManager:
    _instances: dict[str, PaymentService] = {}

    @classmethod
    async def execute_sign(cls, session_id: str, wallet_address: str, payload: dict[str, any]) -> dict[str, any]:
        logger.info(f"current session_id: {session_id} in execute_sign.")
        instance = cls._instances.get(session_id)
        result = {}
        if instance is None:
            instance = PaymentService(session_id, wallet_address, payload)
            result = await instance.sign_for_payment()
            cls._instances[session_id] = instance
        return result
    
    @classmethod
    async def execute_permit_and_transfer(cls, session_id: str, chain: str, wallet_address: str) -> dict[str, any]:
        logger.info(f"current session_id: {session_id} in execute_permit_and_transfer.")
        result = {}
        instance = cls._instances.get(session_id)
        logger.info(f"Instance for wallet_address: {instance.wallet_address}")
        if instance and instance.wallet_address == wallet_address:
            logger.info(f"Execute to permit and transfer with wallet address: {wallet_address} for payment service instance")
            result = await instance.do_permit_and_transfer(session_id, chain)
        return result
            
    @classmethod
    async def release_instance(cls, session_id: str, wallet_address: str):
        if cls._instances:
            instance = cls._instances.get(session_id)
            if instance and instance.wallet_address == wallet_address:
                instance = cls._instances.pop(session_id)
                await instance.cleanup()
                logger.info(f"Payment service instance for wallet_address: {instance.wallet_address} has cleaned up.")