from log import logger
from dao.model import Intent
from dao.app import add_intent
from .constants import ChainID, AssetID, TokenDecimals
from datetime import datetime

def collect_intent(session_id: str, chain: str, payer_address: str, payee_address: str, amount: float, deadline: datetime = None, status: str = None) -> Intent | dict[str, any]:
    
    if not session_id:
        logger.error("Failed to get session_id")
        return {
            "status": "failed",
            "message": "Failed to get session_id"
        }

    intent_id = session_id
    logger.info(f"Collected intent_id: {intent_id} with session_id")

    chain_id = ChainID.get(chain.lower())
    if not chain_id:
        logger.error(f"Failed to get chain_id by chain: {chain}")
        return {
            "status": "failed",
            "message": f"Failed to get chain_id by chain: {chain}"
        }
    logger.info(f"Collected chain_id: {chain_id} by chain: {chain}")
    
    asset_id = AssetID.get(chain_id)
    if not asset_id:
        logger.error(f"Failed to get asset_id by chain_id: {chain_id}")
        return {
            "status": "failed",
            "message": f"Failed to get asset_id by chain_id: {chain_id}"
        }
    logger.info(f"Collected asset_id: {asset_id} by chain_id: {chain_id}")

    if not payer_address:
        logger.error("Failed to get payer_address")
        return {
            "status": "failed",
            "message": "Failed to get payer_address"
        }
    logger.info(f"Collected payer_address: {payer_address}")

    if not payee_address:
        logger.error("Failed to get payee_address")
        return {
            "status": "failed",
            "message": "Failed to get payee_address"
        }
    logger.info(f"Collected payee_address: {payee_address}")
    logger.info(f"Collected amount: {amount}")

    intent = Intent(intent_id=intent_id, chain_id=chain_id, asset_id=asset_id, 
                    payer_address=payer_address, payee_address=payee_address,
                    amount=amount)

    token_decimal = TokenDecimals.get(chain_id)
    if not token_decimal:
        logger.error(f"Failed to get token_decimal by chain_id: {chain_id}")
        return {
            "status": "failed",
            "message": f"Failed to get token_decimal by chain_id: {chain_id}"
        }
    logger.info(f"Collected token_decimal: {token_decimal} by chain_id: {chain_id}")
    
    intent.token_decimals = token_decimal

    if deadline:
        logger.info(f"Collected intent_deadline: {deadline}")
        intent.intent_deadline = deadline

    logger.info(f"Collected status: {status}")
    intent.status = status
    
    inserted_intent = add_intent(intent)
    logger.info(f"Added intent: {inserted_intent}")

    return intent
    