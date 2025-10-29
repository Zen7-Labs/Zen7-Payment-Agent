import asyncio
from services import CHAIN_ID

from log import logger

from pydantic import BaseModel
# Assuming 'create_sepolia_handler' is defined in this module path
from services.custodial.transfer_handler import create_sepolia_handler

from dao.model import (
    SettlementBatch, SettlementBatchStatus, SettlementDetail, SettlementDetailStatus,
    SourceEvent, FinalityStatus
)
from dao.app import add_settlement_batch

from datetime import datetime

class ExecutePermitRequest(BaseModel):
    owner: str
    spender: str
    value: int
    deadline: int
    v: int
    r: str
    s: str
    network: str = "sepolia"


class TransferFromRequest(BaseModel):
    owner: str
    amount: str
    network: str = "sepolia"

async def execute_permit(permit_request: ExecutePermitRequest):
    """Execute EIP-2612 permit authorization to establish USDC allowance relationship"""
    try:
        logger.info(" Executing permit authorization...")
        logger.info(f"Owner: {permit_request.owner}")
        logger.info(f"Spender: {permit_request.spender}")
        logger.info(f"Value: {permit_request.value}")
        logger.info(f"Deadline: {permit_request.deadline}")
        logger.info(f"Signature: v={permit_request.v}, r={permit_request.r}, s={permit_request.s}")
        
        # Get transfer handler
        handler = create_sepolia_handler()
        
        if not handler:
            raise Exception("Transfer handler not available")
        
        # Locally simulate permit call to catch errors in advance
        simulate_result = handler.simulate_permit(
            owner=permit_request.owner,
            spender=permit_request.spender,
            value=permit_request.value,
            deadline=permit_request.deadline,
            v=permit_request.v,
            r=permit_request.r,
            s=permit_request.s
        )
        if not simulate_result.get("success"):
            logger.error(f" Local permit simulation failed: {simulate_result.get('error')}")
            raise Exception(f"Permit simulation failed: {simulate_result.get('error')}")
        
        # Check spender address's ETH balance
        try:
            eth_balance = await handler.get_eth_balance(permit_request.spender)
            logger.info(f" Spender ETH Balance (Network: {permit_request.network}): {eth_balance} ETH")
            if eth_balance < 0.0001:
                logger.warning(f"  Warning: Spender ETH balance is too low ({eth_balance} ETH), may not be enough to pay for gas fees")
        except Exception as e:
            logger.warning(f"  Could not retrieve ETH balance: {e}")
        
        # Call the actual permit execution method
        result = await handler.execute_permit(
            owner=permit_request.owner,
            spender=permit_request.spender,
            value=permit_request.value,
            deadline=permit_request.deadline,
            v=permit_request.v,
            r=permit_request.r,
            s=permit_request.s,
            network=permit_request.network  # Pass network information
        )
        
        if result.get("success"):
            # Poll for transaction status until confirmed or timed out (every 2 seconds, max approx 60 seconds)
            tx_hash = result.get("tx_hash")
            max_attempts = 30
            interval_seconds = 2
            for _ in range(max_attempts):
                try:
                    poll = await handler.get_transaction_status(tx_hash)
                    if poll.get("success") and poll.get("status") == "confirmed":
                        return {
                            "success": True,
                            "txHash": tx_hash,
                            "status": "confirmed",
                            "message": "Permit confirmed",
                            "polling_required": False,
                            "details": result.get("details", {})
                        }
                    if not poll.get("success") and poll.get("status") == "failed":
                        return {
                            "success": False,
                            "txHash": tx_hash,
                            "status": "failed",
                            "message": poll.get("message", "Transaction failed"),
                            "details": poll.get("details", {})
                        }
                except Exception:
                    pass
                await asyncio.sleep(interval_seconds)
            # Timeout: remain pending for the upstream service to continue polling
            return {
                "success": True,
                "txHash": tx_hash,
                "status": "pending",
                "message": "Permit transaction submitted, waiting for confirmation...",
                "polling_required": True,
                "details": result.get("details", {})
            }
        else:
            raise Exception(result.get("error", "Permit execution failed"))
    except Exception as e:
        logger.error(f" Permit execution failed: {str(e)}")
        raise Exception(f"Permit execution failed: {str(e)}")

async def transfer_from(req: TransferFromRequest):
    """Use the established allowance to transfer USDC from owner to the backend wallet address (the spender itself)."""
    settlement_batch = SettlementBatch()
    settlement_batch_detail = SettlementDetail()
    try:
        logger.info(" Executing transferFrom...")
        logger.info(f"Owner: {req.owner}")
        logger.info(f"Amount: {req.amount}")
        logger.info(f"Network: {req.network}")

        
        handler = create_sepolia_handler()

        if not handler:
            raise Exception("Transfer handler not available")
        
        settlement_batch.chain_id = CHAIN_ID
        settlement_batch.merchant_id = "zen7"
        settlement_batch.tenant_id = req.owner
        settlement_batch.asset_id = f"ASSET_{CHAIN_ID}"
        
        current = datetime.now()
        settlement_batch.asset_id = f"ASSET_{int(current.timestamp())}"

        settlement_batch.check_date = current
        settlement_batch.period_start = current

        settlement_batch_detail.chain_id = CHAIN_ID
        settlement_batch_detail.intent_id = f"INTENT_{int(current.timestamp())}"
        
        # Locally simulate transferFrom call to catch errors in advance
        try:
            owner_checksum = handler.w3.to_checksum_address(req.owner)
            spender_checksum = handler.account.address
            
            settlement_batch.payee_address = spender_checksum
            settlement_batch.total_amount = req.amount
            settlement_batch.settlement_status = SettlementBatchStatus.pending_payout
            settlement_batch.finance_confirm_status = FinalityStatus.pending

            settlement_batch_detail.payer_address = owner_checksum
            settlement_batch_detail.payee_address = spender_checksum
            settlement_batch_detail.gross_amount = req.amount
            settlement_batch_detail.settlement_status = SettlementDetailStatus.pending

            # callStatic transferFrom
            handler.usdc_contract.functions.transferFrom(
                owner_checksum,
                spender_checksum,
                int(req.amount)
            ).call({'from': spender_checksum})
        except Exception as e:
            if hasattr(e, 'args') and len(e.args) > 0:
                error_msg = str(e.args[0])
            else:
                error_msg = str(e)
            logger.error(f" transferFrom local simulation failed: {error_msg}")
            raise Exception(f"transferFrom simulation failed: {error_msg}")

        result = await handler.execute_transfer_from(req.owner, req.amount)
        if result.get("success"):
            # Poll for transaction status until confirmed or timed out (every 2 seconds, max approx 60 seconds)
            tx_hash = result.get("tx_hash")

            settlement_batch_detail.tx_hash = tx_hash
            settlement_batch_detail.settlement_status = SettlementDetailStatus.pending
            settlement_batch_detail.source_event = SourceEvent.transfer_completed

            max_attempts = 30
            interval_seconds = 2
            for _ in range(max_attempts):
                try:
                    poll = await handler.get_transaction_status(tx_hash)
                    if poll.get("success") and poll.get("status") == "confirmed":
                        settlement_batch.settlement_status = SettlementBatchStatus.released
                        settlement_batch_detail.fee_amount = poll["details"]["gas_used"] / 10000
                        settlement_batch_detail.net_amount = settlement_batch_detail.gross_amount - settlement_batch_detail.fee_amount
                        settlement_batch_detail.settlement_status = SettlementDetailStatus.released
                        return {
                            "success": True,
                            "txHash": tx_hash,
                            "status": "confirmed",
                            "message": "TransferFrom confirmed",
                            "polling_required": False,
                            "details": result.get("details", {})
                        }
                    if not poll.get("success") and poll.get("status") == "failed":
                        settlement_batch.settlement_status = SettlementBatchStatus.failed
                        settlement_batch_detail.fee_amount = poll["details"]["gas_used"] / 10000
                        settlement_batch_detail.net_amount = settlement_batch_detail.gross_amount - settlement_batch_detail.fee_amount
                        settlement_batch_detail.settlement_status = SettlementDetailStatus.failed
                        return {
                            "success": False,
                            "txHash": tx_hash,
                            "status": "failed",
                            "message": poll.get("message", "Transaction failed"),
                            "details": poll.get("details", {})
                        }
                except Exception:
                    pass
                await asyncio.sleep(interval_seconds)
            # Timeout: remain pending for the upstream service to continue polling
            return {
                "success": True,
                "txHash": tx_hash,
                "status": "pending",
                "message": "TransferFrom transaction submitted, waiting for confirmation...",
                "polling_required": True,
                "details": result.get("details", {})
            }
        else:
            raise Exception(result.get("error", "transferFrom failed"))
    except Exception as e:
        logger.error(f" transferFrom execution failed: {str(e)}")
        raise Exception(f"transferFrom execution failed: {str(e)}")
    finally:
        current = datetime.now()
        settlement_batch.period_end = current
        settlement_batch.updated_at = current
        settlement_batch_detail.settled_at = current
        settlement_batch_detail.source_event = SourceEvent.settlement_completed
        add_settlement_batch(settlement_batch, settlement_batch_detail)

async def get_transaction_status(tx_hash: str):
    """Query transaction status"""
    try:
        logger.info(f" Querying transaction status: {tx_hash}")
    
        handler = create_sepolia_handler()
        
        if not handler:
            raise Exception("Transfer handler not available")
        
        result = await handler.get_transaction_status(tx_hash)
        
        if result.get("success"):
            return {
                "success": True,
                "txHash": tx_hash,
                "status": result.get("status"),
                "message": result.get("message"),
                "details": result.get("details", {})
            }
        else:
            return {
                "success": False,
                "txHash": tx_hash,
                "error": result.get("error"),
                "message": result.get("message")
            }
        
    except Exception as e:
        logger.error(f"Querying transaction status failed: {str(e)}")
        raise Exception(f"Failed to get transaction status: {str(e)}")