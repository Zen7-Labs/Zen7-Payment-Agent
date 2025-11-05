from log import logger
from dao.model import SettlementDetail, SourceEvent, SettlementDetailStatus
from .constants import ChainID, AssetID, TokenDecimals
from datetime import datetime

def collect_settlement_detail(chain: str, gross_amount: float = 0, 
    fee_amount: float = 0, net_amount: float = 0, source_event: SourceEvent = None, 
    settlement_detail_status: SettlementDetailStatus = None, session_id: str = None,
    tx_hash: str = None, payer_address: str = None, payee_address: str = None,
    settled_at: datetime = None) -> SettlementDetail:
    
    chain_id = ChainID.get(chain.lower())
    if not chain_id:
        logger.error(f"Failed to get chain_id by chain: {chain} for settlement_detail")
        return {
            "status": "failed",
            "message": f"Failed to get chain_id by chain: {chain} for settlement_detail"
        }
    logger.info(f"Collected chain_id: {chain_id} by chain: {chain} for settlement_detail")

    logger.info(f"Collected gross_amount: {gross_amount} for settlement_detail")
    logger.info(f"Collected fee_amount: {fee_amount} for settlement_detail")
    logger.info(f"Collected net_amount: {net_amount} for settlement_detail")

    if not source_event:
        source_event = SourceEvent.transfer_completed        
    logger.info(f"Collected source_event: {source_event} for settlement_detail")
    if not settlement_detail_status:
        settlement_detail_status = SettlementDetailStatus.void
    logger.info(f"Collected settlement_detail_status: {settlement_detail_status} for settlement_detail")

    settlement_detail = SettlementDetail(chain_id=chain_id, gross_amount=gross_amount,
                fee_amount=fee_amount, net_amount=net_amount, source_event=source_event,
                settlement_status=settlement_detail_status)

    if session_id:
        intent_id = session_id
        logger.info(f"Collected intent_id: {intent_id} for settlement_detail")
        settlement_detail.intent_id = intent_id
    if tx_hash:
        logger.info(f"Collected tx_hash: {tx_hash} for settlement_detail")
        settlement_detail.tx_hash = tx_hash
    if payer_address:
        logger.info(f"Collected payer_address: {payer_address} for settlement_detail")
        settlement_detail.payer_address = payer_address
    if payee_address:
        logger.info(f"Collected payee_address: {payee_address} for settlement_detail")
        settlement_detail.payee_address = payee_address
    if settled_at:
        logger.info(f"Collected settled_at: {settled_at} for settlement_detail")
        settlement_detail.settled_at = settled_at
    
    return settlement_detail