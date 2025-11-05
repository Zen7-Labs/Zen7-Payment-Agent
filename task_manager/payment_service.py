from log import logger

from dotenv import load_dotenv
import os

load_dotenv()

settlement_mode = os.getenv("SETTLEMENT_MODE")

if settlement_mode == "CUSTODIAL":
    from services.custodial.execute_permit import ExecutePermitRequest, execute_permit, TransferFromRequest, transfer_from
if settlement_mode == "NONE_CUSTODIAL":
    from services.non_custodial.execute_permit import ExecutePermitRequest, execute_permit, TransferFromRequest, transfer_from

import asyncio

from services.execute_sign import sign

from services.constants import ChainID, AssetID, TokenDecimals
from dao.model import (
    SettlementDetail, SettlementBatch, SettlementBatchStatus, 
    SettlementDetailStatus, SourceEvent,
)
from services.settlement_detail import collect_settlement_detail
from services.settlment_batch import collect_settlement_batch
from datetime import datetime

spender_wallet_address = os.getenv("SPENDER_WALLET_ADDRESS")

async def permit_and_transfer(session_id, chain, owner_wallet_address, budget_amount, spend_amount, deadline, v, r, s):
    permit_request = ExecutePermitRequest(
        owner=owner_wallet_address,  # Retrieve from "Recovered signer" in execute_sign.py
        spender=spender_wallet_address,  # Retrieve SPENDER from execute_sign.py
        value=budget_amount,  # 0.01 USDC (6 decimals) = 10000
        deadline=deadline,  # Use deadline from execute_sign.py (expires in 3 days)
        v=v,  # Use v value from execute_sign.py
        r=r,  # Use r value from execute_sign.py
        s=s,  # Use s value from execute_sign.py
        network=chain
    )
    logger.info("Executing permit authorization...")
    result = await execute_permit(permit_request)
    logger.info("Permit executed successfully!")
    logger.info("Result:", result)
    logger.info("Executing transferFrom...")
    transfer_request = TransferFromRequest(
        owner=owner_wallet_address,  # Same owner as in permit
        amount=spend_amount,  # 0.01 USDC (6 decimals)
        network=chain
    )
    period_start = datetime.now()
    result = await transfer_from(transfer_request)
    logger.info("TransferFrom executed successfully!")
    
    current_time = datetime.now()
    period_end = current_time

    logger.info("Result:", result)
    
    is_success = result["success"]
    settlement_batch_status = None
    settlement_detail_status = None
    if is_success:
        settlement_batch_status = SettlementBatchStatus.released
        settlement_detail_status = SettlementDetailStatus.released
    else:
        settlement_batch_status = SettlementBatchStatus.failed
        settlement_detail_status = SettlementDetailStatus.failed
    tx_hash = result["txHash"]

    details = result["details"]
    logger.info(f"Got details from transfer_from: {details}")

    owner = details["owner"]
    spender = details["spender"]
    amount = details["amount"]
    gas_price = details["gas_price"] / 10000
    net_amount = amount - gas_price
    settlement_detail = collect_settlement_detail(chain=chain, gross_amount=spend_amount, source_event=SourceEvent.settlement_completed,
            fee_amount=gas_price, net_amount=net_amount, settlement_detail_status=settlement_detail_status,
            session_id=session_id, tx_hash=tx_hash, payer_address=owner, 
            payee_address=spender, settled_at=current_time)
    
    collect_settlement_batch(settlement_detail=settlement_detail, chain=chain, tenant_id=spender,
            period_start=period_start, period_end=period_end, total_count=1, total_amount=spend_amount,
            payee_address=spender, merchant_id=spender, check_date=current_time, fee_total=gas_price,
            net_total=net_amount, settlement_status=settlement_batch_status)
    return result

class PaymentService:
    def __init__(self, session_id: str, wallet_address: str, payload: dict[str, any]):
        self.session_id = session_id
        self.wallet_address = wallet_address
        self.payload = payload
        self.sign_info = {}
        
    async def sign_for_payment(self) -> dict[str, any]:
        logger.info(f"Sign for payment with payload: {self.payload}")
        if "signature" in self.payload and "r" in self.payload and "s" in self.payload and "v" in self.payload:
            logger.info(f"Use pre-signed info for the payment.")
            self.sign_info = {
                "signature": self.payload["signature"],
                "r": self.payload["r"], 
                "s": self.payload["s"],
                "v": self.payload["v"],
            }
            return
        logger.info(f"Use self-signed info for the payment.")
        budget = self.payload["budget"]
        deadline = self.payload["deadline"]
        network = self.payload["network"]
        token = self.payload["token"]
        signature, r, s, v, nonce = sign(budget=budget, deadline=deadline, network=network, token=token)
        await asyncio.sleep(1)
        self.sign_info = {
            "signature": signature,
            "r": r, 
            "s": s,
            "v": v,
            "nonce": nonce
        }
        return self.sign_info

    async def do_permit_and_transfer(self, session_id: str, chain: str) -> dict[str, any]:
        logger.info(f"Do permit and transfer with signed info: {self.sign_info}")
        owner_wallet_address = self.wallet_address
        budget_amount = self.payload["budget"]
        spend_amount = self.payload["spend_amount"]
        deadline = self.payload["deadline"]
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
        self.sign_info = {}
        logger.info(f"Payment service has cleaned up for wallet address: {self.wallet_address}")