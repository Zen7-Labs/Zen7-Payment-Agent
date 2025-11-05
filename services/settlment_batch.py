from log import logger
from dao.model import SettlementBatch, SettlementDetail, SettlementBatchStatus
from dao.app import add_settlement_batch
from .constants import ChainID, AssetID, TokenDecimals
from datetime import datetime

def collect_settlement_batch(settlement_detail: SettlementDetail, chain: str, tenant_id: str,
    period_start: datetime, period_end: datetime, total_count: int = 0, total_amount: float = 0,
    payee_address: str = None, merchant_id: str = None, check_date: datetime = None, 
    fee_total: float = 0, net_total: float = 0, settlement_status: SettlementBatchStatus = None) -> dict[str, any]:
    chain_id = ChainID.get(chain.lower())
    if not chain_id:
        logger.error(f"Failed to get chain_id by chain: {chain} for settlement_batch")
        return {
            "status": "failed",
            "message": f"Failed to get chain_id by chain: {chain} for settlement_batch"
        }
    logger.info(f"Collected chain_id: {chain_id} by chain: {chain} for settlement_batch")

    asset_id = AssetID.get(chain_id)
    if not asset_id:
        logger.error(f"Failed to get asset_id by chain_id: {chain_id} for settlement_batch")
        return {
            "status": "failed",
            "message": f"Failed to get asset_id by chain_id: {chain_id} for settlement_batch"
        }
    logger.info(f"Collected asset_id: {asset_id} by chain_id: {chain_id} for settlement_batch")

    logger.info(f"Collected total_count: {total_count} for settlement_batch")
    logger.info(f"Collected total_amount: {total_amount} for settlement_batch")
    logger.info(f"Collected fee_total: {fee_total} for settlement_batch")
    logger.info(f"Collected net_total: {net_total} for settlement_batch")

    if not settlement_status:
        settlement_status = SettlementBatchStatus.created
    logger.info(f"Collected settlement_batch_status: {settlement_status} for settlement_batch")

    settlement_batch = SettlementBatch(tenant_id=tenant_id, chain_id=chain_id, asset_id=asset_id,
                                       total_count=total_count, total_amount=total_amount, 
                                       fee_total=fee_total, net_total=net_total, 
                                       settlement_status=settlement_status)
    if merchant_id:
        logger.info(f"Collected merchant_id: {merchant_id} for settlement_batch")
        settlement_batch.merchant_id = merchant_id
    if payee_address:
        logger.info(f"Collected payee_address: {payee_address} for settlement_batch")
        settlement_batch.payee_address = payee_address
    if check_date:
        logger.info(f"Collected check_date: {check_date} for settlement_batch")
        settlement_batch.check_date = check_date
    if period_start:
        logger.info(f"Collected period_start: {period_start} for settlement_batch")
        settlement_batch.period_start = period_start
    if period_end:
        logger.info(f"Collected period_end: {period_end} for settlement_batch")
        settlement_batch.period_end = period_end

    inserted_batch = add_settlement_batch(settlement_batch, settlement_detail)
    logger.info(f"Added settlement batch: {inserted_batch}")

    return {
        "status": "success",
        "message": f"Successfully collected settlement batch: {inserted_batch}"
    }
