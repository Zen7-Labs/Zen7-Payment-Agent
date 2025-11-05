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

spender_wallet_address = os.getenv("SPENDER_WALLET_ADDRESS")

async def permit_and_transfer(owner_wallet_address, budget_amount, spend_amount, deadline, v, r, s):
    permit_request = ExecutePermitRequest(
        owner=owner_wallet_address,  # Retrieve from "Recovered signer" in execute_sign.py
        spender=spender_wallet_address,  # Retrieve SPENDER from execute_sign.py
        value=budget_amount,  # 0.01 USDC (6 decimals) = 10000
        deadline=deadline,  # Use deadline from execute_sign.py (expires in 3 days)
        v=v,  # Use v value from execute_sign.py
        r=r,  # Use r value from execute_sign.py
        s=s,  # Use s value from execute_sign.py
        network="sepolia"
    )
    logger.info("Executing permit authorization...")
    result = await execute_permit(permit_request)
    logger.info("Permit executed successfully!")
    logger.info("Result:", result)
    
    logger.info("Executing transferFrom...")
    transfer_request = TransferFromRequest(
        owner=owner_wallet_address,  # Same owner as in permit
        amount=spend_amount,  # 0.01 USDC (6 decimals)
        network="sepolia"
    )

    result = await transfer_from(transfer_request)
    logger.info("TransferFrom executed successfully!")
    logger.info("Result:", result)
    return result

class PaymentService:
    def __init__(self, wallet_address: str, payload: dict[str, any]):
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

    async def do_permit_and_transfer(self) -> dict[str, any]:
        logger.info(f"Do permit and transfer with signed info: {self.sign_info}")
        owner_wallet_address = self.wallet_address
        budget_amount = self.payload["budget"]
        spend_amount = self.payload["spend_amount"]
        deadline = self.payload["deadline"]
        r = self.sign_info["r"]
        s = self.sign_info["s"]
        v = self.sign_info["v"]
        return await permit_and_transfer(
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