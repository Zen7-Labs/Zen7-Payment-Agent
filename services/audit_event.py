from log import logger
from dao.model import AuditEventType, AuditEvent, Intent
from dao.app import add_audit_event
from .constants import ChainID, AssetID, TokenDecimals

def collect_audit_event(session_id: str, chain: str, event_type: AuditEventType, owner_address: str, spender_address: str, amount: float, tx_hash: str = None, signature: str = None, nonce: str = None, intent: Intent = None) -> dict[str, any]:
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

    if not owner_address:
        logger.error("Failed to get owner_address")
        return {
            "status": "failed",
            "message": "Failed to get owner_address"
        }
    logger.info(f"Collected owner_address: {owner_address}")

    if not spender_address:
        logger.error("Failed to get spender_address")
        return {
            "status": "failed",
            "message": "Failed to get spender_address"
        }
    logger.info(f"Collected spender_address: {spender_address}")

    token_decimal = TokenDecimals.get(chain_id)
    if not token_decimal:
        logger.error(f"Failed to get token_decimal by chain_id: {chain_id}")
        return {
            "status": "failed",
            "message": f"Failed to get token_decimal by chain_id: {chain_id}"
        }
    logger.info(f"Collected token_decimal: {token_decimal} by chain_id: {chain_id}")
    logger.info(f"Collected amount: {amount}")

    audit_event = AuditEvent(intent_id=intent_id, chain_id=chain_id, asset_id=asset_id,
                             owner_address=owner_address, spender_address=spender_address,
                             event_type=event_type, token_decimals=token_decimal, amount=amount)
    if tx_hash:
        logger.info(f"Collected tx_hash: {tx_hash}")
        audit_event.tx_hash = tx_hash
    if nonce:
        logger.info(f"Collected permit_nonce: {nonce}")
        audit_event.permit_nonce = nonce

    if signature:
        logger.info(f"Collected signature_hash: {signature}")
        audit_event.signature_hash = signature

    inserted_audit = add_audit_event(audit_event=audit_event, intent=intent)
    logger.info(f"Added audit event: {inserted_audit}")

    return {
        "status": "success",
        "message": f"Successfully collected audit event: {inserted_audit}"
    }