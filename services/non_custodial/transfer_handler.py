from log import logger
from services import CHAIN_ID, CHAIN_RPC_URL, USDC_ADDRESS, ACTIVE_TOKEN, SEPOLIA_DAI_ADDRESS
from services.blockchain_errors import BlockchainErrorClassifier, create_error_response

import os
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
import asyncio
from typing import Dict, Any

# Load environment variables
load_dotenv()


# Ethereum Sepolia Testnet USDC Configuration
SEPOLIA_USDC_CONFIG = {
    "chain_id": CHAIN_ID,  # Ethereum Sepolia testnet
    "rpc_url": CHAIN_RPC_URL,  # Using Alchemy's free node
    "usdc_address": USDC_ADDRESS,  # Ethereum Sepolia USDC
    "usdc_abi": [
        # Basic ERC20 functions
        {
            "constant": True,
            "inputs": [],
            "name": "name",
            "outputs": [{"name": "", "type": "string"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "symbol",
            "outputs": [{"name": "", "type": "string"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [
                {"name": "_owner", "type": "address"},
                {"name": "_spender", "type": "address"}
            ],
            "name": "allowance",
            "outputs": [{"name": "", "type": "uint256"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": False,
            "inputs": [
                {"name": "_spender", "type": "address"},
                {"name": "_value", "type": "uint256"}
            ],
            "name": "approve",
            "outputs": [{"name": "", "type": "bool"}],
            "payable": False,
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "constant": False,
            "inputs": [
                {"name": "_to", "type": "address"},
                {"name": "_value", "type": "uint256"}
            ],
            "name": "transfer",
            "outputs": [{"name": "", "type": "bool"}],
            "payable": False,
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "constant": False,
            "inputs": [
                {"name": "_from", "type": "address"},
                {"name": "_to", "type": "address"},
                {"name": "_value", "type": "uint256"}
            ],
            "name": "transferFrom",
            "outputs": [{"name": "", "type": "bool"}],
            "payable": False,
            "stateMutability": "nonpayable",
            "type": "function"
        },
        # EIP-2612 Permit function
        {
            "constant": False,
            "inputs": [
                {"name": "owner", "type": "address"},
                {"name": "spender", "type": "address"},
                {"name": "value", "type": "uint256"},
                {"name": "deadline", "type": "uint256"},
                {"name": "v", "type": "uint8"},
                {"name": "r", "type": "bytes32"},
                {"name": "s", "type": "bytes32"}
            ],
            "name": "permit",
            "outputs": [],
            "payable": False,
            "stateMutability": "nonpayable",
            "type": "function"
        }
    ]
}

class TransferHandler:
    def __init__(self):
        # Prioritize SPENDER_KEY, use PRIVATE_KEY if not found
        self.private_key = os.getenv("SPENDER_KEY") or os.getenv("PAYER_PRIVATE_KEY")
        if not self.private_key:
            raise ValueError("SPENDER_KEY or PAYER_PRIVATE_KEY not configured")
        
        if not self.private_key.startswith("0x"):
            self.private_key = f"0x{self.private_key}"
        
        self.account = Account.from_key(self.private_key)
        
        self.config = SEPOLIA_USDC_CONFIG
        logger.info(f"Connecting to Ethereum Sepolia Testnet: {self.config['rpc_url']}")


        if ACTIVE_TOKEN == "DAI":
            # Overwrite the token address in the configuration with the DAI address
            self.config["usdc_address"] = SEPOLIA_DAI_ADDRESS
        logger.info(f"Connect to the Ethereum Sepolia testnet:{self.config['rpc_url']}")
        print(f"Current Tokens: {ACTIVE_TOKEN} @ {self.config['usdc_address']}")
        
        self.w3 = Web3(Web3.HTTPProvider(self.config["rpc_url"]))
        
        # Check network connection
        if not self.w3.is_connected():
            raise ConnectionError(f"Failed to connect to {self.config['rpc_url']}")
        
        # Create a token contract instance (variable names remain backward compatible)
        self.usdc_contract = self.w3.eth.contract(
            address=self.config["usdc_address"],
            abi=self.config["usdc_abi"]
        )

        # Read the recipient address (optional), used as the receiver for transferFrom
        self.payee_address = os.getenv("PAYEE_WALLET_ADDRESS")
        if self.payee_address:
            try:
                self.payee_address = Web3.to_checksum_address(self.payee_address)
            except Exception as e:
                raise ValueError(f"Invalid PAYEE_WALLET_ADDRESS: {e}")
    
    async def execute_transfer_from(
        self, 
        owner_address: str, 
        amount: str = "10000"  # 0.05 USDC (6 decimal places)
    ) -> Dict[str, Any]:
        """
        Execute transferFrom call (asynchronously submit, do not wait for confirmation)
        
        Args:
            owner_address: The address that granted you the allowance
            amount: Transfer amount (6 decimal places)
        
        Returns:
            A dictionary containing the transaction hash, requires polling for results
        """
        try:
            # 0. Convert address format to checksum address
            owner_address_checksum = Web3.to_checksum_address(owner_address)
            
            # 1. Check allowance
            allowance = self.usdc_contract.functions.allowance(
                owner_address_checksum, 
                self.account.address
            ).call()
            
            if allowance < int(amount):
                error_msg = f"Insufficient allowance. Required: {int(amount)}, Available: {allowance}"
                return create_error_response(error_msg)
            
            # 2. Get current nonce (includes pending transactions to avoid conflicts with the previous one)
            nonce = self.w3.eth.get_transaction_count(self.account.address, 'pending')
            
            # 3. Build transferFrom transaction (recipient prioritizes PAYEE_WALLET_ADDRESS)
            to_checksum = self.payee_address if hasattr(self, 'payee_address') and self.payee_address else self.account.address
            transfer_txn = self.usdc_contract.functions.transferFrom(
                owner_address_checksum,      # from (owner)
                to_checksum,  # to (recipient)
                int(amount)            # amount
            ).build_transaction({
                'from': self.account.address,
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce
            })
            
            # 4. Sign and send transaction (do not wait for confirmation)
            signed_txn = self.account.sign_transaction(transfer_txn)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            logger.info(f" TransferFrom transaction submitted: {tx_hash.hex()}")
            
            # Immediately return transaction hash, do not wait for confirmation
            return {
                "success": True,
                "tx_hash": tx_hash.hex(),
                "status": "pending",
                "message": f"TransferFrom transaction submitted, waiting for confirmation...",
                "polling_required": True,
                "details": {
                    "owner": owner_address_checksum,
                    "spender": self.account.address,
                    "to": to_checksum,
                    "amount": int(amount),
                    "amount_usdc": int(amount) / 1000000,
                    "gas_limit": transfer_txn['gas'],
                    "gas_price": transfer_txn['gasPrice']
                }
            }
                
        except Exception as e:
            return create_error_response(str(e))
    
    async def check_usdc_balance(self) -> Dict[str, Any]:
        """Check the current address's USDC balance"""
        try:
            balance = self.usdc_contract.functions.balanceOf(self.account.address).call()
            return {
                "success": True,
                "balance": balance,
                "balance_usdc": balance / 1000000,
                "address": self.account.address
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to check USDC balance"
            }
    
    async def check_allowance(self, owner_address: str) -> Dict[str, Any]:
        """Check allowance"""
        try:
            # Convert address format to checksum address
            owner_address_checksum = Web3.to_checksum_address(owner_address)
            allowance = self.usdc_contract.functions.allowance(
                owner_address_checksum, 
                self.account.address
            ).call()
            return {
                "success": True,
                "allowance": allowance,
                "allowance_usdc": allowance / 1000000,
                "owner": owner_address_checksum,
                "spender": self.account.address
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to check allowance"
            }

    async def get_eth_balance(self, address: str) -> float:
        """Get the ETH balance of the specified address"""
        try:
            balance_wei = self.w3.eth.get_balance(address)
            balance_eth = self.w3.from_wei(balance_wei, 'ether')
            return float(balance_eth)
        except Exception as e:
            logger.info(f" Failed to get ETH balance: {e}")
            return 0.0

    async def execute_permit(
        self, 
        owner: str, 
        spender: str, 
        value: str, 
        deadline: int, 
        v: int, 
        r: str, 
        s: str,
        network: str = "sepolia" # Default to sepolia as it's the only supported network
    ) -> Dict[str, Any]:
        """
        Execute EIP-2612 permit authorization (asynchronously submit, do not wait for confirmation)
        
        Args:
            owner: Token holder address
            spender: Authorized address
            value: Authorized amount (6 decimal places)
            deadline: Expiration timestamp
            v, r, s: Signature parameters
        
        Returns:
            A dictionary containing the transaction hash, requires polling for results
        """
        try:
            logger.info(f" Executing EIP-2612 permit authorization (Web3)...")
            logger.info(f"Owner: {owner}")
            logger.info(f"Spender: {spender}")
            logger.info(f"Value: {value}")
            logger.info(f"Deadline: {deadline}")
            
            # Check spender address's ETH balance
            spender_eth_balance = await self.get_eth_balance(spender)
            logger.info(f"Spender ETH Balance: {spender_eth_balance} ETH")
            
            # Convert address format to checksum address
            owner_checksum = Web3.to_checksum_address(owner)
            spender_checksum = Web3.to_checksum_address(spender)
            
            # Get current nonce (includes pending transactions to avoid conflicts with the previous one)
            nonce = self.w3.eth.get_transaction_count(self.account.address, 'pending')
            
            # Build permit transaction
            logger.info(f" Building permit transaction...")
            logger.info(f"   USDC Contract Address: {self.config['usdc_address']}")
            logger.info(f"   USDC Contract Instance: {self.usdc_contract}")
            logger.info(f"   Permit Function: {self.usdc_contract.functions.permit}")
            
            # Check if the contract has the permit function
            if not hasattr(self.usdc_contract.functions, 'permit'):
                raise ValueError("USDC contract does not have the permit function")
            
            permit_txn = self.usdc_contract.functions.permit(
                owner_checksum,
                spender_checksum,
                int(value),
                deadline,
                v,
                bytes.fromhex(r[2:]) if r.startswith('0x') else bytes.fromhex(r),  # Remove 0x prefix
                bytes.fromhex(s[2:]) if s.startswith('0x') else bytes.fromhex(s)  # Remove 0x prefix
            ).build_transaction({
                'from': self.account.address,
                'gas': 150000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce
            })
            
            logger.info(f" Permit transaction built successfully")
            logger.info(f"   To: {permit_txn['to']}")
            logger.info(f"   Data: {permit_txn['data'][:100]}...")
            logger.info(f"   Gas: {permit_txn['gas']}")
            logger.info(f"   Nonce: {permit_txn['nonce']}")
            
            # Sign and send transaction (do not wait for confirmation)
            signed_txn = self.account.sign_transaction(permit_txn)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            logger.info(f" Permit transaction submitted: {tx_hash.hex()}")
            
            # Immediately return transaction hash, do not wait for confirmation
            return {
                "success": True,
                "tx_hash": tx_hash.hex(),
                "status": "pending",
                "message": f"Permit transaction submitted, waiting for confirmation...",
                "polling_required": True,
                "details": {
                    "owner": owner_checksum,
                    "spender": spender_checksum,
                    "value": int(value),
                    "deadline": deadline,
                    "gas_limit": permit_txn['gas'],
                    "gas_price": permit_txn['gasPrice']
                }
            }
                
        except Exception as e:
            logger.error(f" Web3 permit execution failed: {str(e)}")
            return create_error_response(str(e))

    async def get_transaction_status(self, tx_hash: str) -> Dict[str, Any]:
        """
        Query transaction status
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            A dictionary containing the transaction status
        """
        try:
            # Query transaction receipt
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            
            if receipt:
                if receipt.status == 1:
                    return {
                        "success": True,
                        "status": "confirmed",
                        "tx_hash": tx_hash,
                        "message": "Transaction confirmed",
                        "details": {
                            "gas_used": receipt.gasUsed,
                            "block_number": receipt.blockNumber,
                            "transaction_index": receipt.transactionIndex,
                            "confirmations": 1  # Can calculate the number of confirmations as needed
                        }
                    }
                else:
                    # Receipt exists but status is 0 (failed)
                    return {
                        "success": False,
                        "status": "failed",
                        "tx_hash": tx_hash,
                        "message": "Transaction failed",
                        "details": {
                            "gas_used": receipt.gasUsed,
                            "block_number": receipt.blockNumber
                        }
                    }
            else:
                # Transaction hasn't been mined yet, check if it's in the mempool
                try:
                    tx = self.w3.eth.get_transaction(tx_hash)
                    if tx:
                        return {
                            "success": True,
                            "status": "pending",
                            "tx_hash": tx_hash,
                            "message": "Transaction waiting for confirmation",
                            "details": {
                                "from": tx['from'],
                                "to": tx['to'],
                                "gas": tx['gas'],
                                "gas_price": tx['gasPrice']
                            }
                        }
                except:
                    pass
                
                # Transaction not found in receipt or mempool, still treat as pending/unknown
                return {
                    "success": True,
                    "status": "pending",
                    "tx_hash": tx_hash,
                    "message": "Transaction waiting for confirmation",
                    "details": {}
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to query transaction status"
            }

    def simulate_permit(self, owner, spender, value, deadline, v, r, s):
        """
        Locally simulate permit call to catch contract-level errors (like expired, invalid signature, etc.) in advance
        """
        try:
            owner_checksum = Web3.to_checksum_address(owner)
            spender_checksum = Web3.to_checksum_address(spender)
            self.usdc_contract.functions.permit(
                owner_checksum,
                spender_checksum,
                int(value),
                deadline,
                v,
                bytes.fromhex(r[2:]) if r.startswith('0x') else bytes.fromhex(r),
                bytes.fromhex(s[2:]) if s.startswith('0x') else bytes.fromhex(s)
            ).call({'from': self.account.address})
            return {"success": True}
        except Exception as e:
            # Return error with classification
            error_msg = str(e.args[0]) if hasattr(e, 'args') and len(e.args) > 0 else str(e)
            error_code = BlockchainErrorClassifier.classify_error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "error_code": error_code.code if error_code else None
            }

# Global instance
transfer_handler_sepolia = None

def get_transfer_handler():
    """Get TransferHandler instance (Sepolia only supported)"""
    raise NotImplementedError("Only Sepolia network is supported. Use create_sepolia_handler() instead.")

def create_sepolia_handler():
    """Get Sepolia TransferHandler instance"""
    global transfer_handler_sepolia
    if transfer_handler_sepolia is None:
        try:
            transfer_handler_sepolia = TransferHandler()
        except Exception as e:
            logger.error(f"Failed to initialize Sepolia TransferHandler: {e}")
            return None
    return transfer_handler_sepolia