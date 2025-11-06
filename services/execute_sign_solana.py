"""
Solana Partial Signature Generation Script (Simulating Client-Side Operation)

Functionality:
- User locally generates an SPL Token transfer transaction
- User signs the transaction (but does not specify the fee_payer)
- Sends the partially signed transaction to the backend
- Backend acts as the fee_payer, completes the signature, and submits

Analogy to EVM's execute_sign.py (EIP-2612 permit signature)
"""

from dotenv import load_dotenv
import sys
import os
import base64
import asyncio
from datetime import datetime, timedelta
from typing import Tuple, Optional

# Assuming 'log' is configured for logging
from log import logger

# Solana Dependencies
try:
    from solders.keypair import Keypair  # type: ignore
    from solders.pubkey import Pubkey  # type: ignore
    from solders.transaction import Transaction  # type: ignore
    # from solders.message import Message  # type: ignore # Not strictly needed here
    from solders.hash import Hash  # type: ignore
    from solders.instruction import Instruction, AccountMeta  # type: ignore
    from solana.rpc.async_api import AsyncClient  # type: ignore
    from solana.rpc.commitment import Confirmed  # type: ignore
    from spl.token.instructions import (  # type: ignore
        get_associated_token_address,
        transfer_checked,
        TransferCheckedParams,
        create_associated_token_account,
    )
    from spl.token.constants import TOKEN_PROGRAM_ID, ASSOCIATED_TOKEN_PROGRAM_ID  # type: ignore
    # Re-import Message here as it's used explicitly below
    from solders.message import Message
    SOLANA_AVAILABLE = True
except ImportError:
    SOLANA_AVAILABLE = False
    logger.error("Solana dependencies not installed. Please run: pip install solders solana spl-token")
    sys.exit(1)

load_dotenv()

# ==================== Solana Configuration ====================

CHAIN_CONFIGS = {
    "solana-devnet": {
        "cluster": "devnet",
        "rpc_url": os.getenv("SOLANA_DEVNET_RPC_URL") or "https://api.devnet.solana.com",
        "name": "Solana Devnet",
        "native_currency": "SOL"
    }
}

TOKEN_CONFIGS = {
    "solana-devnet": {
        "USDC": {
            "mint_address": "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU",  # Devnet USDC
            "decimals": 6
        }
    }
}

# Payer Private Key (Client-side, used to sign the transaction)
PAYER_PRIVATE_KEY = os.getenv("SOLANA_PAYER_PRIVATE_KEY")

# Fee Payer Address (Backend, pays for gas)
FEE_PAYER_ADDRESS = os.getenv("FEE_PAYER_ADDRESS")

# Payee Address (The actual recipient of the tokens, defaults to Fee Payer)
PAYEE_ADDRESS = os.getenv("PAYEE_ADDRESS") or FEE_PAYER_ADDRESS

# Configuration Validation
if not PAYER_PRIVATE_KEY:
    raise ValueError("Payer Private Key not configured! Please set SOLANA_PAYER_PRIVATE_KEY in the .env file.")

if not FEE_PAYER_ADDRESS:
    raise ValueError("Fee Payer Address not configured! Please set FEE_PAYER_ADDRESS in the .env file.")


async def sign_solana_transfer(
    network: str = "solana-devnet",
    token: str = "USDC",
    amount: int = 30000  # 0.03 USDC in smallest units
) -> Tuple[str, str, str]:
    """
    Generates a partially signed Solana transfer transaction (Client-Side)
    
    Args:
        network: Network name (solana-devnet)
        token: Token symbol (USDC)
        amount: Transfer amount (in smallest units)
        
    Returns:
        (base64_encoded_transaction, payer_address, payee_address)
    """
    network = network.lower()
    token = token.upper()
    
    # Validate network and token
    if network not in CHAIN_CONFIGS:
        raise ValueError(f"Unsupported network: {network}")
    
    if network not in TOKEN_CONFIGS or token not in TOKEN_CONFIGS[network]:
        raise ValueError(f"Token {token} not supported on {network}")
    
    chain_config = CHAIN_CONFIGS[network]
    token_config = TOKEN_CONFIGS[network][token]
    
    # Create Solana client
    client = AsyncClient(chain_config["rpc_url"], commitment=Confirmed)
    
    # Load Payer Keypair (Client-side)
    try:
        if len(PAYER_PRIVATE_KEY) == 88:  # Base58
            payer_keypair = Keypair.from_base58_string(PAYER_PRIVATE_KEY)
        else:
            key_hex = PAYER_PRIVATE_KEY[2:] if PAYER_PRIVATE_KEY.startswith('0x') else PAYER_PRIVATE_KEY
            key_bytes = bytes.fromhex(key_hex)
            payer_keypair = Keypair.from_bytes(key_bytes)
    except Exception as e:
        raise ValueError(f"Invalid private key format: {e}")
    
    payer_pubkey = payer_keypair.pubkey()
    
    # Fee Payer Address (Backend, pays for gas)
    fee_payer_pubkey = Pubkey.from_string(FEE_PAYER_ADDRESS)
    
    # Payee Address (The actual recipient)
    payee_pubkey = Pubkey.from_string(PAYEE_ADDRESS)
    
    # Token Mint Address
    token_mint = Pubkey.from_string(token_config["mint_address"])
    
    # Get Associated Token Accounts
    payer_token_account = get_associated_token_address(payer_pubkey, token_mint)
    payee_token_account = get_associated_token_address(payee_pubkey, token_mint)
    
    logger.info(f">>> Checking Balances - Network: {chain_config['name']}")
    logger.info(f">>> {token} Mint Address (Token Contract): {token_config['mint_address']}")
    logger.info(f">>> Payer (User): {str(payer_pubkey)}")
    logger.info(f">>> Fee Payer (Pays Gas): {str(fee_payer_pubkey)}")
    logger.info(f">>> Payee (Receives Tokens): {str(payee_pubkey)}")
    
    # Check SOL balance (Optional, as fee payer handles it)
    sol_balance_response = await client.get_balance(payer_pubkey)
    sol_balance = sol_balance_response.value / 1_000_000_000 if sol_balance_response.value else 0
    
    if sol_balance <= 0:
        logger.warning(f"Warning: Payer has no SOL balance (Fee Payer will pay gas, not a concern)")
    else:
        logger.info(f">>> Payer SOL Balance: {sol_balance} SOL")
    
    # Check token balance
    try:
        token_balance_response = await client.get_token_account_balance(payer_token_account)
        if token_balance_response.value:
            token_balance = int(token_balance_response.value.amount)
            token_balance_display = token_balance / (10 ** token_config['decimals'])
            logger.info(f">>> Payer {token} Balance: {token_balance_display} {token}")
            
            if token_balance < amount:
                logger.warning(
                    f"Warning: Insufficient {token} balance. "
                    f"Current: {token_balance_display}, Required: {amount / (10 ** token_config['decimals'])}"
                )
        else:
            logger.warning(f"Warning: Payer's {token} Token Account does not exist")
    except Exception as e:
        logger.warning(f"Warning: Failed to query {token} balance: {e}")
    
    # Get the latest blockhash
    blockhash_response = await client.get_latest_blockhash()
    recent_blockhash = blockhash_response.value.blockhash
    
    # Check if the payee's Token Account exists
    instructions = []
    try:
        payee_account_info = await client.get_account_info(payee_token_account)
        if not payee_account_info.value:
            logger.warning(f">>> Payee's {token} Token Account does not exist, will create automatically")
            # Create Associated Token Account instruction
            create_ata_ix = create_associated_token_account(
                payer=fee_payer_pubkey,  # Fee Payer pays the creation fee (SOL rent)
                owner=payee_pubkey,      # Owner of the Token Account
                mint=token_mint          # Token Mint Address
            )
            instructions.append(create_ata_ix)
            logger.info(f">>> Added Create Token Account instruction (Fee Payer will cover the cost)")
        else:
            logger.info(f">>> Payee's {token} Token Account already exists")
    except Exception as e:
        logger.warning(f"Warning: Cannot check Payee Token Account, attempting to create anyway: {e}")
        # If unable to confirm, add the creation instruction (it will be skipped if it exists)
        create_ata_ix = create_associated_token_account(
            payer=fee_payer_pubkey,
            owner=payee_pubkey,
            mint=token_mint
        )
        instructions.append(create_ata_ix)
    
    # Build SPL Token Transfer Instruction (Transfer to Payee)
    transfer_ix = transfer_checked(
        TransferCheckedParams(
            program_id=TOKEN_PROGRAM_ID,
            source=payer_token_account,
            mint=token_mint,
            dest=payee_token_account,  # Transfer to the payee's account
            owner=payer_pubkey,        # SPL Token API parameter name, remains 'owner' (the authority)
            amount=amount,
            decimals=token_config['decimals']
        )
    )
    instructions.append(transfer_ix)
    
    # Build the Transaction Message (fee_payer set to the backend address)
    message = Message.new_with_blockhash(
        instructions,      # May contain Create Token Account + Transfer instructions
        fee_payer_pubkey,  # Specify backend as the Fee Payer (pays gas)
        recent_blockhash
    )
    
    # Create the transaction (do not pass signers to prevent immediate full signing)
    transaction = Transaction.new_unsigned(message)
    
    # Payer partially signs (only signs the SPL Token transfer authorization part)
    # Note: partial_sign needs all required signers (payer and fee_payer) listed in the message.
    # The payer_keypair is one of the required signers for the SPL transfer.
    transaction.partial_sign([payer_keypair], recent_blockhash)
    
    # Serialize to Base64
    tx_bytes = bytes(transaction)
    tx_base64 = base64.b64encode(tx_bytes).decode('utf-8')
    
    # Close client
    await client.close()
    
    # Output the required parameters for the backend execute_permit function
    logger.info("=" * 80)
    logger.info(f">>> Copy the following parameters to the test data in execute_permit.py ({network}/{token}):")
    logger.info("=" * 80)
    logger.info(f'owner="{str(payer_pubkey)}"       # Payer (User) Address')
    logger.info(f'spender="{str(fee_payer_pubkey)}"  # Fee Payer (Gas Payer) Address')
    logger.info(f'value={amount}             # {amount / (10 ** token_config["decimals"])} {token}')
    logger.info(f'deadline={int((datetime.now() + timedelta(days=3)).timestamp())}  # Expires in 3 days (For reference only)')
    logger.info(f'signature="{tx_base64}"  # Solana Partial Signed Transaction')
    logger.info(f'token="{token}"')
    logger.info(f'network="{network}"')
    logger.info("=" * 80)
    logger.info(f">>> Actual Recipient: {str(payee_pubkey)}  # Tokens are transferred to this address")
    logger.info(f">>> Transaction Size: {len(tx_bytes)} bytes")
    logger.info("=" * 80)
    
    return tx_base64, str(payer_pubkey), str(payee_pubkey)