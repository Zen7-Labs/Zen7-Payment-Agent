from log import logger

from dotenv import load_dotenv
import os
from typing import Dict, Any, Optional

load_dotenv()

# Determine which implementation of the permit/transfer functions to import
settlement_mode = os.getenv("SETTLEMENT_MODE")

# Note: The original code uses a variable for module/class import, 
# which is slightly atypical for type checking but functional.
if settlement_mode == "CUSTODIAL":
    # Assumes these modules/functions exist in the custodial service path
    from services.custodial.execute_permit import ExecutePermitRequest, execute_permit, TransferFromRequest, transfer_from
elif settlement_mode == "NONE_CUSTODIAL": # Note: Original code typo: NONE_CUSTODIAL
    # Assumes these modules/functions exist in the non_custodial service path
    from services.non_custodial.execute_permit import ExecutePermitRequest, execute_permit, TransferFromRequest, transfer_from
# else: the functions will be undefined if the env var is missing or misspelled

import asyncio

# Protocol-specific signing simulation/generation functions
from services.execute_sign import sign # For EVM (EIP-2612)
from services.execute_sign_solana import sign_solana_transfer # For Solana (Partial Transaction Signing)

# Data Access Object (DAO) models
from dao.model import (
    SettlementBatchStatus, SettlementDetailStatus, SourceEvent,
)
# Business logic services for recording data
from services.settlement_detail import collect_settlement_detail
from services.settlement_batch import collect_settlement_batch
from datetime import datetime

# Backend/Spender configuration
spender_wallet_address = os.getenv("SPENDER_WALLET_ADDRESS")

# --- Solana Transaction Flow ---

async def permit_and_transfer_for_solana_devnet(
    session_id: str, 
    owner_wallet_address: str, # For general tracking, Payer/Payee are more relevant for Solana
    budget_amount: int, 
    spend_amount: int, 
    deadline: int, 
    signature: str, # This is the Base64 partial transaction
    payer: str, # User address
    payee: str  # Recipient/Fee Payer address
) -> Dict[str, Any]:
    """
    Executes the partially signed Solana transaction (backend complements signature and submits).
    
    In Solana's Fee Payer model, the 'permit' (transaction submission) effectively
    includes the 'transferFrom' (SPL token transfer) as one instruction.
    """
    network = "solana-devnet"
    token = "USDC"
    
    # Use ExecutePermitRequest to pass the partial transaction data
    permit_request = ExecutePermitRequest(
        owner=payer, # Payer(user) address
        spender=payee, # Fee Payer (Receiver) address
        value=budget_amount,
        deadline=deadline, # Deadline is part of the EVM model, but included for data consistency
        signature=signature, # The Base64 encoded partial transaction
        token=token,
        network=network
    )
    logger.info("Executing Solana-devnet permit authorization...")
    
    period_start = datetime.now()
    # The execute_permit implementation for Solana will complete the signature and submit
    result = await execute_permit(permit_request)
    logger.info("Permit Solana-devnet executed successfully!")
    logger.info(f"Result: {result}")
    
    # Solana Note: The transfer instruction is part of the partial transaction submitted in 'permit'
    logger.info("[SKIP] Solana does not require a separate transferFrom; the transfer is completed in the permit stage.")
    current_time = datetime.now()
    period_end = current_time

    # --- Settlement Recording Logic ---
    
    is_success = result.get("success", False)
    settlement_batch_status: Optional[SettlementBatchStatus] = None
    settlement_detail_status: Optional[SettlementDetailStatus] = None
    
    if is_success:
        settlement_batch_status = SettlementBatchStatus.released
        settlement_detail_status = SettlementDetailStatus.released
    else:
        settlement_batch_status = SettlementBatchStatus.failed
        settlement_detail_status = SettlementDetailStatus.failed
        
    tx_hash = result.get("txHash", "N/A")
    owner = payer
    spender = payee # The fee payer is also the recipient in the current design
    merchant_id = "zen7"
    amount = budget_amount # Gross amount of the token transfer
    gas_price = result.get("gasUsed", 0) # Assumes gasUsed is returned by the Solana handler
    net_amount = amount - gas_price
    
    settlement_detail = collect_settlement_detail(
        chain=network, gross_amount=spend_amount, source_event=SourceEvent.settlement_completed,
        fee_amount=gas_price, net_amount=net_amount, settlement_detail_status=settlement_detail_status,
        session_id=session_id, tx_hash=tx_hash, payer_address=owner, 
        payee_address=spender, settled_at=current_time
    )
    
    collect_settlement_batch(
        settlement_detail=settlement_detail, chain=network, tenant_id=spender,
        period_start=period_start, period_end=period_end, total_count=1, total_amount=spend_amount,
        payee_address=spender, merchant_id=merchant_id, check_date=current_time, fee_total=gas_price,
        net_total=net_amount, settlement_status=settlement_batch_status
    )
    return result

# --- EVM Transaction Flow ---

async def permit_and_transfer(
    session_id: str, 
    chain: str, 
    owner_wallet_address: str, 
    budget_amount: int, 
    spend_amount: int, 
    deadline: int, 
    v: int, r: str, s: str
) -> Dict[str, Any]:
    """
    Executes the two-step EVM EIP-2612 process: 
    1. Permit (Authorize Spender)
    2. TransferFrom (Spender moves tokens)
    """
    # 1. Execute Permit (Allowance Authorization)
    permit_request = ExecutePermitRequest(
        owner=owner_wallet_address,
        spender=spender_wallet_address,
        value=budget_amount,
        deadline=deadline,
        v=v,
        r=r,
        s=s,
        network=chain
    )
    logger.info("Executing permit authorization...")
    result_permit = await execute_permit(permit_request) # Store result for logging/data if needed

    logger.info("Permit executed successfully!")
    logger.info(f"Permit Result: {result_permit}")
    
    # 2. Execute TransferFrom (Token Transfer)
    logger.info("Executing transferFrom...")
    transfer_request = TransferFromRequest(
        owner=owner_wallet_address, 
        amount=spend_amount,
        network=chain
    )
    period_start = datetime.now()
    result = await transfer_from(transfer_request)
    logger.info("TransferFrom executed successfully!")
    logger.info(f"TransferFrom Result: {result}")

    current_time = datetime.now()
    period_end = current_time
    
    # --- Settlement Recording Logic ---
    
    is_success = result.get("success", False)
    settlement_batch_status: Optional[SettlementBatchStatus] = None
    settlement_detail_status: Optional[SettlementDetailStatus] = None
    
    if is_success:
        settlement_batch_status = SettlementBatchStatus.released
        settlement_detail_status = SettlementDetailStatus.released
    else:
        settlement_batch_status = SettlementBatchStatus.failed
        settlement_detail_status = SettlementDetailStatus.failed
        
    tx_hash = result.get("txHash", "N/A")

    details = result.get("details", {})
    logger.info(f"Got details from transfer_from: {details}")

    owner = details.get("owner", owner_wallet_address)
    spender = details.get("spender", spender_wallet_address)
    merchant_id = "zen7"
    amount = details.get("amount", spend_amount)
    # The original code assumes gas_price is returned and converts units
    gas_price = details.get("gas_price", 0) / 10000 
    net_amount = amount - gas_price
    
    settlement_detail = collect_settlement_detail(
        chain=chain, gross_amount=spend_amount, source_event=SourceEvent.settlement_completed,
        fee_amount=gas_price, net_amount=net_amount, settlement_detail_status=settlement_detail_status,
        session_id=session_id, tx_hash=tx_hash, payer_address=owner, 
        payee_address=spender, settled_at=current_time
    )
    
    collect_settlement_batch(
        settlement_detail=settlement_detail, chain=chain, tenant_id=spender,
        period_start=period_start, period_end=period_end, total_count=1, total_amount=spend_amount,
        payee_address=spender, merchant_id=merchant_id, check_date=current_time, fee_total=gas_price,
        net_total=net_amount, settlement_status=settlement_batch_status
    )
    return result

# --- Main Payment Service Class ---

class PaymentService:
    def __init__(self, session_id: str, wallet_address: str, payload: Dict[str, Any]):
        """
        Initializes the payment service with session details and payload.
        
        Args:
            session_id: Unique identifier for the payment session.
            wallet_address: The user's wallet address (Owner).
            payload: Contains payment details (network, token, budget, spend_amount, deadline, etc.).
        """
        self.session_id = session_id
        self.wallet_address = wallet_address
        self.payload = payload
        self.sign_info: Dict[str, Any] = {}
        
    async def sign_for_payment(self) -> Optional[Dict[str, Any]]:
        """
        Handles the signing/signature generation step based on the network (EVM or Solana).
        """
        logger.info(f"Sign for payment with payload: {self.payload}")
        network = self.payload.get("network")
        
        if network == "solana-devnet":
            # --- Solana: Generate Partial Transaction ---
            tx_base64, payer, payee = await sign_solana_transfer(
                network=network,
                token=self.payload["token"],
                amount=self.payload["budget"] # Budget is the amount to transfer
            )
            logger.info(f"[OK] Generate Solana partial signature successfully.")
            logger.info(f"[OK] Payer (user): {payer}")
            logger.info(f"[OK] Payee (receiver/fee payer): {payee}")
            self.sign_info = {
                "signature": tx_base64,
                "payer": payer,
                "payee": payee,
                "nonce": 0 # Not directly used for Solana partial signature, but kept for data consistency
            }
            return self.sign_info
        else:
            # --- EVM: Handle EIP-2612 Signature ---
            # Check if signature info is pre-signed and provided in the payload
            if all(key in self.payload for key in ["signature", "r", "s", "v"]):
                logger.info(f"Use pre-signed info for the payment.")
                self.sign_info = {
                    "signature": self.payload["signature"],
                    "r": self.payload["r"], 
                    "s": self.payload["s"],
                    "v": self.payload["v"]
                }
                # No return here, just setting self.sign_info
            else:
                # Self-sign (Simulate client signing)
                logger.info(f"Use self-signed info for the payment.")
                budget = self.payload["budget"]
                deadline = self.payload["deadline"]
                network = self.payload["network"]
                token = self.payload["token"]
                signature, r, s, v, nonce = sign(budget=budget, deadline=deadline, network=network, token=token)
                self.sign_info = {
                    "signature": signature,
                    "r": r, 
                    "s": s,
                    "v": v,
                    "nonce": nonce
                }
            return self.sign_info # Return the collected/generated sign info

    async def do_permit_and_transfer(self, session_id: str, chain: str) -> Dict[str, Any]:
        """
        Submits the transaction(s) using the signed information.
        Routes to the appropriate protocol-specific function.
        """
        logger.info(f"Do permit and transfer with signed info: {self.sign_info}")
        logger.info(f"Do permit and transfer with payload: {self.payload}")
        
        owner_wallet_address = self.wallet_address
        budget_amount = self.payload["budget"]
        spend_amount = self.payload["spend_amount"]
        deadline = self.payload["deadline"]
        
        network = self.payload["network"]
        
        if network == "solana-devnet":
            # Solana Flow
            signature = self.sign_info["signature"]
            payer = self.sign_info["payer"]
            payee = self.sign_info["payee"]
            return await permit_and_transfer_for_solana_devnet(
                session_id=session_id,
                owner_wallet_address=owner_wallet_address,
                budget_amount=budget_amount,
                spend_amount=spend_amount,
                deadline=deadline,
                signature=signature, # Base64 partial transaction
                payer=payer,
                payee=payee
            )
        else:
            # EVM Flow (EIP-2612)
            # Uses r, s, v from the signature info
            r = self.sign_info["r"]
            s = self.sign_info["s"]
            v = self.sign_info["v"]
            return await permit_and_transfer(
                session_id=session_id,
                chain=chain,
                owner_wallet_address=owner_wallet_address, 
                budget_amount=budget_amount, 
                spend_amount=spend_amount, 
                deadline=deadline,
                v=v,
                r=r,
                s=s
            )

    async def cleanup(self):
        """Resets the state after the transaction is complete."""
        self.sign_info = {}
        logger.info(f"Payment service has cleaned up for wallet address: {self.wallet_address}")