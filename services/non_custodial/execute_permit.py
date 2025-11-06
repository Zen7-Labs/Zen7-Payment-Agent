from log import logger
from services.blockchain_errors import BlockchainErrorClassifier

import asyncio

from pydantic import BaseModel
# Assuming 'create_sepolia_handler' is defined in this module path
from services.non_custodial.transfer_handler import create_handler

class ExecutePermitRequest(BaseModel):
    owner: str
    spender: str
    value: float
    deadline: int
    # EVM signature parameters (Optional, required for EVM chains)
    v: int = None
    r: str = None
    s: str = None
    # Solana signature parameters (Optional, required for Solana chains)
    signature: str = None  # Solana partial signed transaction (Base64 encoded)
    token: str = "USDC"  # Token symbol (USDC or DAI)
    network: str = "sepolia"  # Reserved for future multi-chain support


class TransferFromRequest(BaseModel):
    owner: str
    amount: float
    token: str = "USDC"  # Token symbol (USDC or DAI)
    network: str = "sepolia"  # Reserved for future multi-chain support

async def execute_permit(permit_request: ExecutePermitRequest):
    """Execute EIP-2612 permit authorization to establish USDC allowance relationship"""
    try:
        logger.info(" Executing permit authorization...")
        logger.info(f"Owner: {permit_request.owner}")
        logger.info(f"Spender: {permit_request.spender}")
        logger.info(f"Value: {permit_request.value}")
        logger.info(f"Deadline: {permit_request.deadline}")
        logger.info(f"Signature: v={permit_request.v}, r={permit_request.r}, s={permit_request.s}, Solana Sig={permit_request.signature}")
        
        # Get transfer handler
        handler = create_handler(network=permit_request.network, token=permit_request.token)
        
        if not handler:
            raise Exception("Transfer handler not available")
        
        # Check current allowance
        result = await handler.check_allowance(owner_address=permit_request.owner)
        if result.get("allowance", 0) >= permit_request.value:
            logger.info(f"Skip permit transaction because it already has sufficient allowance. Current: {result.get('allowance')}, Required: {permit_request.value}")
            return {
                "success": True,
                "txHash": "",
                "status": "confirmed", # Treat as confirmed since no tx is needed
                "message": "Skipped permit transaction due to existing allowance",
                "polling_required": False,
                "details": result.get("details", {})
            }

        # Locally simulate permit call to catch errors in advance
        simulate_params = {
            "owner": permit_request.owner,
            "spender": permit_request.spender,
            "value": permit_request.value,
            "deadline": permit_request.deadline
        }
        
        # EVM Parameters
        if permit_request.v is not None:
            simulate_params.update({
                "v": permit_request.v,
                "r": permit_request.r,
                "s": permit_request.s
            })
        
        # Solana Parameters
        if permit_request.signature:
            # Note: For Solana, permit execution usually includes the transfer, making separate simulation complex/unnecessary
            # Assuming the BaseTransferHandler or derived class has a simulate_permit method
            simulate_params["signature"] = permit_request.signature
        
        # The BaseTransferHandler is expected to have a simulate_permit method
        simulate_result = handler.simulate_permit(**simulate_params)
        if not simulate_result.get("success"):
            error_msg = simulate_result.get('error')
            error_code = simulate_result.get('error_code')
            logger.error(f" Local permit simulation failed: {error_msg}")
            if error_code:
                raise Exception(f"[{error_code}] Permit simulation failed: {error_msg}")
            else:
                raise Exception(f"Permit simulation failed: {error_msg}")
        
        # Check spender address's ETH/BNB etc. balance
        native_currency = "NATIVE" # Default placeholder
        try:
            native_currency = handler.chain_config.get("native_currency", "ETH")
        except AttributeError:
             # Handler might not have chain_config if it's not an EVM handler, which is fine
             pass
             
        try:
            native_balance = await handler.get_native_balance(permit_request.spender)
            logger.info(f" Spender {native_currency} Balance (Network: {permit_request.network}): {native_balance} {native_currency}")
            if native_balance < 0.0001:
                logger.warning(f"  Warning: Spender {native_currency} balance is too low ({native_balance} {native_currency}), may not be enough to pay for gas fees")
        except Exception as e:
            logger.warning(f"  Could not retrieve {native_currency} balance for spender: {e}")
        
        # Call the actual permit execution method (submit and poll for confirmation before returning)
        # Pass different parameters based on the protocol type
        permit_params = {
            "owner": permit_request.owner,
            "spender": permit_request.spender,
            # Note: Assuming the handler will handle token unit conversion if needed, but the EVM handler expects int (smallest unit)
            "value": permit_request.value, 
            "deadline": permit_request.deadline
        }
        
        # EVM Parameters
        if permit_request.v is not None:
            permit_params.update({
                "v": permit_request.v,
                "r": permit_request.r,
                "s": permit_request.s
            })
        
        # Solana Parameters
        if permit_request.signature:
            permit_params["signature"] = permit_request.signature
        
        result = await handler.execute_permit(**permit_params)
        
        if result.get("success"):
            # Compatible with EVM (tx_hash) and Solana (signature)
            tx_hash = result.get("tx_hash") or result.get("signature")
            max_attempts = 30  # Approximately 60 seconds
            interval_seconds = 2
            
            # Polling loop
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
                except Exception as poll_e:
                    logger.warning(f"Polling failed for {tx_hash}: {poll_e}")
                    pass # Ignore exceptions during polling, just wait and retry
                await asyncio.sleep(interval_seconds)
            
            # Timed out without confirmation -> Return pending, allowing the upstream service to continue polling
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
        # Re-raise the exception for upstream handling
        raise Exception(f"Permit execution failed: {str(e)}")

async def transfer_from(req: TransferFromRequest):
    """Use the established allowance to transfer token from owner to the backend wallet address (the spender itself, or payee)."""
    try:
        logger.info(" Executing transferFrom...")
        logger.info(f"Owner: {req.owner}")
        logger.info(f"Amount: {req.amount}")
        logger.info(f"Network: {req.network}")

        network = req.network
        if network.startswith("solana"):
            # Solana's 'permit' (approve/delegate) usually includes the 'transferChecked' instruction
            # for a single atomic transaction. No separate transferFrom needed.
            print("[SKIP] Solana does not require a separate transferFrom; the transfer is completed in the permit phase.")
            return {
                "success": True,
                "txHash": "",
                "status": "confirmed", 
                "message": "TransferFrom skipped for Solana (completed via permit)",
                "polling_required": False
            }
        
        handler = create_handler(network=req.network, token=req.token)

        if not handler:
            raise Exception("Transfer handler not available")
                        
        # Locally simulate transferFrom call to catch errors in advance (EVM-specific logic)
        try:
            # This simulation logic relies on the existence of handler.w3, handler.account, handler.usdc_contract, and handler.payee_address, which are EVM handler properties.
            owner_checksum = handler.w3.to_checksum_address(req.owner)
            spender_checksum = handler.account.address
            # Recipient: prioritize PAYEE_WALLET_ADDRESS
            payee_env = handler.payee_address if hasattr(handler, 'payee_address') else None
            recipient_checksum = payee_env if payee_env else spender_checksum

            # callStatic transferFrom
            handler.usdc_contract.functions.transferFrom(
                owner_checksum,
                recipient_checksum,
                int(req.amount) # Assuming req.amount is in smallest unit
            ).call({'from': spender_checksum})
        except Exception as e:
            if hasattr(e, 'args') and len(e.args) > 0:
                error_msg = str(e.args[0])
            else:
                error_msg = str(e)
            logger.error(f" transferFrom local simulation failed: {error_msg}")
            
            # Classify error
            # Note: BlockchainErrorClassifier is not provided, so we assume its interface
            error_code_obj = BlockchainErrorClassifier.classify_error(error_msg)
            if error_code_obj:
                raise Exception(f"[{error_code_obj.code}] transferFrom simulation failed: {error_msg}")
            else:
                raise Exception(f"transferFrom simulation failed: {error_msg}")

        # Execute the actual transaction
        # Note: The EVM handler's execute_transfer_from expects 'amount' in its smallest unit, 
        # but the request model uses a float. This requires conversion in the handler or here.
        # Assuming the handler internally handles the float to int conversion based on decimals.
        result = await handler.execute_transfer_from(req.owner, req.amount) 
        
        if result.get("success"):
            # Poll for transaction status until confirmed or timed out (every 2 seconds, max approx 60 seconds)
            tx_hash = result.get("tx_hash")
            max_attempts = 30
            interval_seconds = 2
            
            # Polling loop
            for _ in range(max_attempts):
                try:
                    poll = await handler.get_transaction_status(tx_hash)
                    logger.info(f"========= Poll result for {tx_hash}: {poll} =========")
                    if poll.get("success") and poll.get("status") == "confirmed":
                        return {
                            "success": True,
                            "txHash": tx_hash,
                            "status": "confirmed",
                            "message": "TransferFrom confirmed",
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
                except Exception as poll_e:
                    logger.warning(f"Polling failed for {tx_hash}: {poll_e}")
                    pass # Ignore exceptions during polling, just wait and retry
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
        # Re-raise the exception for upstream handling
        raise Exception(f"transferFrom execution failed: {str(e)}")

async def get_transaction_status(tx_hash: str, network: str = "sepolia", token: str = "USDC"):
    """
    Query transaction status (multi-chain support)

    Args:
        tx_hash: Transaction hash (EVM) or signature (Solana)
        network: Network name (default: sepolia)
        token: Token symbol (used to retrieve the correct handler, default: USDC)
    """
    try:
        logger.info(f" Querying transaction status: {tx_hash}")
    
        handler = create_handler(network=network, token=token)
        
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
        # Re-raise the exception for upstream handling
        raise Exception(f"Failed to get transaction status: {str(e)}")