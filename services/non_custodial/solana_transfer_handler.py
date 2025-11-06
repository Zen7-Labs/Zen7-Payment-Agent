"""
Solana Blockchain Transfer Handler (inherits from BaseTransferHandler)

Supported Solana Networks:
- Devnet

Supported Protocol:
- Fee Payer Model (Backend pays for gas)
- SPL Token Transfer (Requires user's partial signature)

Workflow (Similar to EVM's EIP-2612):
1. User partially signs the transfer transaction on the frontend (without specifying the fee payer)
2. The partial signature is sent to the backend
3. The backend acts as the fee_payer, adds its signature, and submits the transaction
4. The backend pays all gas fees (approx. $0.00025)
"""

import os
import base64
from typing import Dict, Any, Optional
from dotenv import load_dotenv
# Note: Assuming BaseTransferHandler is correctly imported from services.non_custodial.base_handler
from services.non_custodial.base_handler import BaseTransferHandler

# The original code imported Web3 and eth_account, which are not strictly needed for Solana logic
# from web3 import Web3
# from eth_account import Account
# from services.non_custodial.evm_transfer_handler import TOKEN_ABI

# Solana Dependencies (requires installation)
try:
    from solders.keypair import Keypair  # type: ignore
    from solders.pubkey import Pubkey  # type: ignore
    from solders.transaction import Transaction  # type: ignore
    # from solders.system_program import TransferParams, transfer  # type: ignore # Not needed for SPL Token Transfer
    # from solders.message import Message  # type: ignore # Not strictly needed here
    from solana.rpc.async_api import AsyncClient  # type: ignore
    from solana.rpc.commitment import Confirmed  # type: ignore
    from spl.token.instructions import (  # type: ignore
        get_associated_token_address,
        # transfer_checked, # Not used in handler, as the user creates the instruction
        # TransferCheckedParams
    )
    # from spl.token.constants import TOKEN_PROGRAM_ID  # type: ignore # Not strictly needed here
    SOLANA_AVAILABLE = True
except ImportError:
    SOLANA_AVAILABLE = False
    print("Solana dependencies not installed. Please run: pip install solders solana spl-token")

# Load environment variables
load_dotenv()

# ==================== Solana Configuration ====================

CHAIN_CONFIGS = {
    "solana-devnet": {
        "protocol": "solana",
        "cluster": "devnet",
        "rpc_url": os.getenv("SOLANA_DEVNET_RPC_URL") or "https://api.devnet.solana.com",
        "name": "Solana Devnet",
        "native_currency": "SOL"
    },
    # Mainnet and Testnet support are commented out
}

TOKEN_CONFIGS = {
    "solana-devnet": {
        "USDC": {
            "mint_address": "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU",  # Devnet USDC
            "decimals": 6,
            "program_id": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"  # SPL Token Program
        }
    }
}


class SolanaTransferHandler(BaseTransferHandler):
    """Solana Blockchain Transfer Handler (Fee Payer Model)"""
    
    def __init__(self, network: str = "solana-devnet", token: str = "USDC"):
        """
        Initializes the Solana TransferHandler
        
        Args:
            network: Network name (solana-devnet)
            token: Token symbol (USDC)
        """
        if not SOLANA_AVAILABLE:
            raise ImportError(
                "Solana dependencies not installed. "
                "Please run: pip install solders solana spl-token"
            )
        
        super().__init__(network, token)
        
        # Normalize parameters
        network = network.lower()
        token = token.upper()
        
        # Validate network support
        if network not in CHAIN_CONFIGS:
            raise ValueError(
                f"Unsupported Solana network: {network}. "
                f"Supported: {list(CHAIN_CONFIGS.keys())}"
            )
        
        chain_config = CHAIN_CONFIGS[network]
        
        # Validate token support on the network
        if network not in TOKEN_CONFIGS:
            raise ValueError(f"No token configuration for Solana network: {network}")
        
        if token not in TOKEN_CONFIGS[network]:
            supported_tokens = list(TOKEN_CONFIGS[network].keys())
            raise ValueError(
                f"Token {token} not supported on {network}. "
                f"Supported: {supported_tokens}"
            )
        
        token_config = TOKEN_CONFIGS[network][token]
        
        # Load backend wallet (Fee Payer) private key
        backend_key = os.getenv("FEE_PAYER_KEY")
        if not backend_key:
            raise ValueError(
                "FEE_PAYER_KEY not configured. "
                "Please set it in .env file."
            )
        
        try:
            # Support Base58 or Hex format
            if len(backend_key) == 88:  # Base58 format
                self.backend_keypair = Keypair.from_base58_string(backend_key)
            else:  # Hex format (64 bytes = 128 characters)
                if backend_key.startswith('0x'):
                    backend_key = backend_key[2:]
                key_bytes = bytes.fromhex(backend_key)
                self.backend_keypair = Keypair.from_bytes(key_bytes)
        except Exception as e:
            raise ValueError(f"Invalid FEE_PAYER_KEY format: {e}")
        
        # Save configuration
        self.network = network
        self.chain_config = chain_config
        self.token_config = token_config
        self.token_symbol = token
        
        # Create Solana RPC client
        # The AsyncClient should be closed in the close() method
        self.client = AsyncClient(chain_config["rpc_url"], commitment=Confirmed)
        
        # Token Mint Address
        self.token_mint = Pubkey.from_string(token_config["mint_address"])
        
        # Payee Address (Optional, defaults to Fee Payer)
        payee_env = os.getenv("PAYEE_ADDRESS") or os.getenv("SOLANA_PAYEE_ADDRESS")
        self.payee_pubkey = Pubkey.from_string(payee_env) if payee_env else self.backend_keypair.pubkey()
        
        print(f">>> [Solana] Connected to {chain_config['name']}: {chain_config['rpc_url']}")
        print(f">>> [Solana] Current Token: {token} (Mint: {token_config['mint_address']})")
        print(f">>> [Solana] Fee Payer (Gas Payer): {str(self.backend_keypair.pubkey())}")
        print(f">>> [Solana] Payee (Token Recipient): {str(self.payee_pubkey)}")
    
    def simulate_permit(
        self,
        owner: str,
        spender: str,
        value: float,
        deadline: int,
        v: int = None,
        r: str = None,
        s: str = None,
        signature: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Simulates Solana transfer (local validation)
        
        Note: Solana does not have the EVM 'callStatic' concept.
        This only performs basic parameter validation.
        
        Returns:
            Validation result dictionary
        """
        try:
            # Basic parameter validation
            if not signature:
                return {
                    "success": False,
                    "error": "Missing signature parameter"
                }
            
            # Validate address format
            try:
                Pubkey.from_string(owner)
                # Spender is the backend wallet; its pubkey is self.backend_keypair.pubkey()
                # We can check if the provided spender matches the expected backend address
                if Pubkey.from_string(spender) != self.backend_keypair.pubkey():
                    return {
                        "success": False,
                        "error": "Spender address does not match backend fee payer address"
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Invalid Solana address format: {e}"
                }
            
            # Validate signature format (Base64)
            try:
                tx_bytes = base64.b64decode(signature)
                # Attempt to deserialize the transaction to check integrity
                Transaction.from_bytes(tx_bytes)
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Invalid transaction signature format or decoding failed: {e}"
                }
            
            # NOTE: For a real application, you should also deserialize the transaction
            # and verify the instructions (amount, recipient, source account) match expectations.
            
            return {
                "success": True,
                "message": "Solana transaction simulation passed (basic checks only)"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Solana simulation failed due to an internal error"
            }
    
    async def execute_permit(
        self,
        owner: str,
        spender: str,
        value: float, # Note: value is expected in base units in the original function call, but float in the service layer request.
        deadline: int,
        v: int = None,
        r: str = None,
        s: str = None,
        signature: str = None,  # Solana partial signed transaction (Base64 encoded)
        **kwargs
    ) -> Dict[str, Any]:
        """
        Executes Solana transfer (Fee Payer model)
        
        Note: Solana does not have the EIP-2612 permit concept.
        Here, "permit" actually executes the transfer, with the backend paying for gas.
        
        Args:
            owner: Token holder address (Solana Pubkey)
            spender: Authorized address (Backend address, used for validation)
            value: Transfer amount (smallest unit, e.g., 30000 = 0.03 USDC). Note: Type adjusted for consistency with service layer.
            deadline: Expiration timestamp (for validation, Solana transactions have their own expiration mechanism)
            signature: User's partial signed transaction (Base64 encoded)
            
        Returns:
            Dictionary containing the transaction signature
        """
        # Convert value from float to smallest unit (lamports/token decimals)
        try:
            amount_in_smallest_unit = int(value)
        except ValueError:
            return {
                "success": False,
                "error": "Invalid value format. Expected integer in smallest unit.",
                "message": "Amount value is not a valid integer."
            }

        try:
            print(f"[Solana] Executing transfer (Fee Payer Mode)...")
            print(f"Owner: {owner}")
            print(f"Spender (Backend): {spender}")
            print(f"Value: {amount_in_smallest_unit} ({amount_in_smallest_unit / (10 ** self.token_config['decimals'])} {self.token_symbol})")
            print(f"Deadline: {deadline}")
            
            if not signature:
                return {
                    "success": False,
                    "error": "Missing signature parameter",
                    "message": "Solana requires the user's partial signed transaction"
                }
            
            # 1. Deserialize the user's partial signed transaction
            try:
                tx_bytes = base64.b64decode(signature)
                transaction = Transaction.from_bytes(tx_bytes)
            except Exception as e:
                print(f"[Solana] Error decoding transaction: {e}")
                return {
                    "success": False,
                    "error": f"Invalid transaction signature: {e}",
                    "message": "Could not parse user signature"
                }
            
            # 2. Validate transaction content (Security Check)
            # IMPORTANT: In a production system, a full validation of the instructions 
            # (token, amount, recipient, source account, deadline/recent_blockhash validity) 
            # should happen here to prevent malicious transactions. 
            print("[Solana] Transaction content validation (TODO: Implement full security check)")
            
            # 3. Backend signs as fee_payer
            # Solana transactions require a recent blockhash to be valid. The client signing
            # must ensure this blockhash is still valid when submitting.
            # We assume the user-provided transaction's blockhash is valid for a short period.
            transaction.partial_sign([self.backend_keypair], transaction.message.recent_blockhash)
            print("[Solana] Backend signed the transaction.")
            
            # 4. Submit transaction
            response = await self.client.send_transaction(transaction)
            
            if response.value:
                tx_signature = str(response.value)
                print(f"[Solana] Transaction submitted: {tx_signature}")
                
                return {
                    "success": True,
                    "signature": tx_signature,  # Solana uses signature instead of tx_hash
                    "tx_hash": tx_signature,    # Compatible with EVM interface
                    "status": "pending",
                    "message": "Solana transaction submitted (backend paid gas)",
                    "polling_required": True,
                    "details": {
                        "owner": owner,
                        "fee_payer": str(self.backend_keypair.pubkey()),
                        "recipient": str(self.payee_pubkey),
                        "amount": amount_in_smallest_unit,
                        "amount_display": amount_in_smallest_unit / (10 ** self.token_config['decimals']),
                        "estimated_fee": 0.000005  # SOL (approx)
                    }
                }
            else:
                return {
                    "success": False,
                    "error": response.error.message if response.error else "Unknown RPC error",
                    "message": "Solana RPC returned an error or null response"
                }
                
        except Exception as e:
            print(f"[Solana] Transfer execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Solana transfer execution failed"
            }
    
    async def execute_transfer_from(
        self,
        owner_address: str,
        amount: float, # Adjusted type to match service layer
        **kwargs
    ) -> Dict[str, Any]:
        """
        Executes Solana SPL Token transfer
        
        Note: In Fee Payer mode, this method is typically not called separately.
        The transfer and authorization are done together in execute_permit (Fee Payer mode).
        
        Args:
            owner_address: Token holder address
            amount: Transfer amount (in base units)
            
        Returns:
            Dictionary containing the transaction signature (or error)
        """
        # In Fee Payer mode, this method is usually not used independently
        # Users should call execute_permit and pass the partial signature
        print("[Solana] WARNING: execute_transfer_from called in Fee Payer mode, which is not the standard workflow.")
        return {
            "success": False,
            "error": "Use execute_permit with user signature for Fee Payer mode",
            "message": "Please use execute_permit for Solana Fee Payer mode"
        }
    
    async def get_transaction_status(self, tx_hash: str) -> Dict[str, Any]:
        """
        Queries Solana transaction status
        
        Args:
            tx_hash: Transaction signature (Solana signature)
            
        Returns:
            Dictionary containing the transaction status
        """
        try:
            from solders.signature import Signature  # type: ignore
            
            # Convert to Solana Signature object
            sig = Signature.from_string(tx_hash)
            
            # Query transaction status
            # Use Confirmed commitment for faster initial response
            response = await self.client.get_transaction(sig, max_supported_transaction_version=0, commitment=Confirmed)
            
            if response.value:
                tx_info = response.value
                
                # Check for transaction success
                if tx_info.transaction.meta.err is None:
                    # Transaction is confirmed and successful
                    return {
                        "success": True,
                        "status": "confirmed",
                        "signature": tx_hash,
                        "tx_hash": tx_hash,
                        "message": "Solana transaction confirmed successfully",
                        "details": {
                            "slot": tx_info.slot,
                            "block_time": tx_info.block_time,
                            "fee": tx_info.transaction.meta.fee
                        }
                    }
                else:
                    # Transaction is confirmed but failed
                    return {
                        "success": False,
                        "status": "failed",
                        "signature": tx_hash,
                        "tx_hash": tx_hash,
                        "message": f"Solana transaction failed: {tx_info.transaction.meta.err}",
                        "details": {
                            "error": str(tx_info.transaction.meta.err)
                        }
                    }
            else:
                # Transaction is not confirmed yet or does not exist (may still be pending)
                # We can try to check with a higher commitment level if this returns pending,
                # but for simplicity, we return pending if not found with Confirmed.
                return {
                    "success": True,
                    "status": "pending",
                    "signature": tx_hash,
                    "tx_hash": tx_hash,
                    "message": "Solana transaction waiting for confirmation"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to query Solana transaction status"
            }
    
    async def check_allowance(self, owner_address: str) -> Dict[str, Any]:
        """
        Checks the token balance (Solana does not have the EVM allowance concept)
        
        Solana's Token Account Delegate mechanism is different from EVM's allowance.
        Here, we return the user's Token Account balance as a reference.
        
        Args:
            owner_address: User's public key (address)
            
        Returns:
            Dictionary containing balance information (used as 'allowance' in the service layer)
        """
        try:
            owner_pubkey = Pubkey.from_string(owner_address)
            
            # Get the user's Associated Token Account
            user_token_account = get_associated_token_address(
                owner_pubkey,
                self.token_mint
            )
            
            # Query balance
            response = await self.client.get_token_account_balance(user_token_account)
            
            if response.value:
                balance_info = response.value
                balance = int(balance_info.amount)
                decimals = self.token_config['decimals']
                
                return {
                    "success": True,
                    "allowance": balance,  # Solana has no allowance, return balance
                    "allowance_display": balance / (10 ** decimals),
                    "owner": owner_address,
                    "spender": str(self.backend_keypair.pubkey()),
                    "note": "Solana uses Token Account balance, not allowance"
                }
            else:
                # Token Account might not exist, meaning balance is 0
                return {
                    "success": True,
                    "allowance": 0,
                    "allowance_display": 0.0,
                    "owner": owner_address,
                    "spender": str(self.backend_keypair.pubkey()),
                    "note": f"User's {self.token_symbol} Token Account not found (treated as 0 balance)"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to query Token Account balance"
            }
    
    async def get_native_balance(self, address: str) -> float:
        """
        Gets the SOL balance (native currency)
        
        Args:
            address: Solana address (Base58 format)
            
        Returns:
            SOL balance as a float
        """
        try:
            print(f"[Solana] Querying SOL balance for address {address}...")
            pubkey = Pubkey.from_string(address)
            print(f"[Solana] Converted to Pubkey: {pubkey}")
            response = await self.client.get_balance(pubkey)
            print(f"[Solana] RPC Response: {response}")
            
            if response.value is not None:
                # Solana balance unit is lamports (1 SOL = 10^9 lamports)
                balance_lamports = response.value
                balance_sol = balance_lamports / 1_000_000_000
                print(f"[Solana] Query successful: {balance_sol} SOL ({balance_lamports} lamports)")
                return float(balance_sol)
            else:
                print(f"[Solana] RPC returned value is None")
                return 0.0
                
        except Exception as e:
            import traceback
            print(f"[Solana] Failed to get SOL balance: {e}")
            print(f"[Solana] Detailed Error: {traceback.format_exc()}")
            return 0.0
    
    async def close(self):
        """Closes the Solana RPC connection"""
        try:
            # Note: This requires the solana.rpc.async_api.AsyncClient to be implemented correctly
            await self.client.close()
            print("[Solana] RPC connection closed.")
        except Exception as e:
            print(f"[Solana] Failed to close connection: {e}")