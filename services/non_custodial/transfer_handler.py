from log import logger
from services import CHAIN_ID, CHAIN_RPC_URL, USDC_ADDRESS, ACTIVE_TOKEN, SEPOLIA_DAI_ADDRESS
from services.blockchain_errors import BlockchainErrorClassifier, create_error_response

import os
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()

# ==================== Multi-Chain Configuration (Factory Pattern) ====================

# Chain configuration dictionary
CHAIN_CONFIGS = {
    "sepolia": {
        "chain_id": CHAIN_ID,  # Ethereum Sepolia testnet
        "rpc_url": CHAIN_RPC_URL,
        "name": "Sepolia"
    },
    "basesepolia": {
        "chain_id": CHAIN_ID,  # Base Sepolia testnet
        "rpc_url": CHAIN_RPC_URL,
        "name": "Base Sepolia"
    }
}

# Token configuration dictionary (Multi-chain × Multi-currency)
TOKEN_CONFIGS = {
    "sepolia": {
        "USDC": {
            "address": USDC_ADDRESS,
            "name": "USDC",
            "version": "2",
            "decimals": 6
        },
        "DAI": {
            "address": SEPOLIA_DAI_ADDRESS,
            "name": "DAI",
            "version": "1",
            "decimals": 18
        }
    },
    "basesepolia": {
        "USDC": {
            "address": USDC_ADDRESS,
            "name": "USDC",
            "version": "2",
            "decimals": 6
        }
    }
}

# General ERC20 + EIP-2612 ABI
TOKEN_ABI = [
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

class TransferHandler:
    def __init__(self, network: str = "sepolia", token: str = "USDC"):
        """
        Initializes TransferHandler (Multi-chain factory pattern)
        
        Args:
            network: Network name (sepolia or basesepolia)
            token: Token symbol (USDC or DAI)
        """
        # Normalize parameters
        network = network.lower()
        token = token.upper()
        
        # Validate network support
        if network not in CHAIN_CONFIGS:
            raise ValueError(f"Unsupported network: {network}. Supported networks: {list(CHAIN_CONFIGS.keys())}")
        
        chain_config = CHAIN_CONFIGS[network]
        
        # Validate RPC URL configuration
        if not chain_config["rpc_url"]:
            raise ValueError(f"{network.upper()}_RPC_URL not configured. Please set it in .env")
        
        # Validate token support on the network
        if network not in TOKEN_CONFIGS:
            raise ValueError(f"No token configuration for network: {network}")
        
        if token not in TOKEN_CONFIGS[network]:
            supported_tokens = list(TOKEN_CONFIGS[network].keys())
            raise ValueError(f"Token {token} not supported on {network}. Supported tokens: {supported_tokens}")
        
        token_config = TOKEN_CONFIGS[network][token]
        
        # Validate token address configuration
        if not token_config["address"]:
            env_var = f"{network.upper()}_{token}_ADDRESS"
            raise ValueError(f"{token} address not configured for {network}. Please set {env_var} in .env")
        
        # Prioritize SPENDER_KEY, fall back to PRIVATE_KEY if not found
        self.private_key = os.getenv("SPENDER_KEY") or os.getenv("PRIVATE_KEY")
        if not self.private_key:
            raise ValueError("SPENDER_KEY or PRIVATE_KEY not configured")
        
        if not self.private_key.startswith("0x"):
            self.private_key = f"0x{self.private_key}"
        
        self.account = Account.from_key(self.private_key)
        
        # Save configuration (Multi-chain mode)
        self.network = network
        self.chain_config = chain_config
        self.token_config = token_config
        self.token_symbol = token
        
        logger.info(f">>> Connecting to {chain_config['name']}: {chain_config['rpc_url']}")
        logger.info(f">>> Current Token: {token} @ {token_config['address']}")
        
        self.w3 = Web3(Web3.HTTPProvider(self.chain_config["rpc_url"]))
        
        # Check network connection
        if not self.w3.is_connected():
            raise ConnectionError(f"Failed to connect to {self.chain_config['rpc_url']}")
        
        # Create token contract instance (variable name kept for backward compatibility)
        self.usdc_contract = self.w3.eth.contract(
            address=token_config["address"],
            abi=TOKEN_ABI
        )

        # Read payee address (optional), used as the recipient for transferFrom
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
        Executes the transferFrom call (submits asynchronously, does not wait for confirmation)
        
        Args:
            owner_address: The address that authorized you
            amount: The transfer amount (in 6 decimal places)
        
        Returns:
            A dictionary containing the transaction hash, which requires polling for the result
        """
        try:
            # 0. Convert address format to checksum address
            owner_address_checksum = Web3.to_checksum_address(owner_address)
            
            # 1. Check allowance amount
            allowance = self.usdc_contract.functions.allowance(
                owner_address_checksum, 
                self.account.address
            ).call()
            
            if allowance < int(amount):
                return {
                    "success": False,
                    "error": f"Insufficient allowance. Required: {int(amount)}, Available: {allowance}"
                }
            
            # 2. Get the current nonce (including pending transactions to avoid conflicts with the last one)
            nonce = self.w3.eth.get_transaction_count(self.account.address, 'pending')
            
            # 3. Build the transferFrom transaction (recipient prioritizes PAYEE_WALLET_ADDRESS)
            to_checksum = self.payee_address if hasattr(self, 'payee_address') and self.payee_address else self.account.address
            transfer_txn = self.usdc_contract.functions.transferFrom(
                owner_address_checksum,      # from (owner)
                to_checksum,  # to (recipient)
                int(amount)         # amount
            ).build_transaction({
                'from': self.account.address,
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce
            })
            
            # 4. Sign and send the transaction (do not wait for confirmation)
            signed_txn = self.account.sign_transaction(transfer_txn)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            logger.info(f" TransferFrom transaction submitted: {tx_hash.hex()}")
            
            # Immediately return the transaction hash, without waiting for confirmation
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
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to execute transferFrom"
            }
    
    async def check_usdc_balance(self) -> Dict[str, Any]:
        """Checks the USDC balance of the current address"""
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
        """Checks the allowance amount"""
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
        """Gets the ETH balance of the specified address"""
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
        Executes EIP-2612 permit authorization (submits asynchronously, does not wait for confirmation)
        
        Args:
            owner: Token holder address
            spender: Authorized address
            value: Authorization amount (in 6 decimal places)
            deadline: Expiration timestamp
            v, r, s: Signature parameters
        
        Returns:
            A dictionary containing the transaction hash, which requires polling for the result
        """
        try:
            logger.info(f" Executing EIP-2612 permit authorization (Web3)...")
            logger.info(f"Owner: {owner}")
            logger.info(f"Spender: {spender}")
            logger.info(f"Value: {value}")
            logger.info(f"Deadline: {deadline}")
            
            # Check the spender address's ETH balance
            spender_eth_balance = await self.get_eth_balance(spender)
            logger.info(f">>> Spender ETH Balance: {spender_eth_balance} ETH")
            
            # Convert address format to checksum address
            owner_checksum = Web3.to_checksum_address(owner)
            spender_checksum = Web3.to_checksum_address(spender)
            
            # Get the current nonce (including pending transactions to avoid conflicts with the last one)
            nonce = self.w3.eth.get_transaction_count(self.account.address, 'pending')
            
            # Build the permit transaction
            logger.info(f" Building permit transaction...")
            logger.info(f"   Token Contract Address: {self.token_config['address']}")
            logger.info(f"   Token Symbol: {self.token_symbol}")
            logger.info(f"   Contract Instance: {self.usdc_contract}")
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
            
            logger.info(f" Permit transaction successfully built")
            logger.info(f"   To: {permit_txn['to']}")
            logger.info(f"   Data: {permit_txn['data'][:100]}...")
            logger.info(f"   Gas: {permit_txn['gas']}")
            logger.info(f"   Nonce: {permit_txn['nonce']}")
            
            # Sign and send the transaction (do not wait for confirmation)
            signed_txn = self.account.sign_transaction(permit_txn)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            logger.info(f" Permit transaction submitted: {tx_hash.hex()}")
            
            # Immediately return the transaction hash, without waiting for confirmation
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
            return {
                "success": False,
                "error": str(e),
                "message": "Web3 permit execution failed"
            }

    async def get_transaction_status(self, tx_hash: str) -> Dict[str, Any]:
        """
        Queries transaction status
        
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
                            "confirmations": 1  # Confirmations can be calculated as needed
                        }
                    }
                else:
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
                # The transaction has not been mined yet, check if it's in the mempool
                try:
                    tx = self.w3.eth.get_transaction(tx_hash)
                    if tx:
                        return {
                            "success": True,
                            "status": "pending",
                            "tx_hash": tx_hash,
                            "message": "Transaction awaiting confirmation",
                            "details": {
                                "from": tx['from'],
                                "to": tx['to'],
                                "gas": tx['gas'],
                                "gas_price": tx['gasPrice']
                            }
                        }
                except:
                    pass
                
                return {
                    "success": True,
                    "status": "pending",
                    "tx_hash": tx_hash,
                    "message": "Transaction awaiting confirmation",
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
        Locally simulates the permit call to catch contract-level errors (e.g., expired, invalid signature) in advance.
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
            # Return only the human-readable revert reason
            if hasattr(e, 'args') and len(e.args) > 0:
                return {"success": False, "error": str(e.args[0])}
            return {"success": False, "error": str(e)}

# Global instance cache (Singleton pool - Multi-chain mode)
_handler_cache = {}

def create_handler(network: str = "sepolia", token: str = "USDC") -> TransferHandler:
    """
    Creates or retrieves a TransferHandler instance (Multi-chain factory pattern + Singleton cache)
    
    Args:
        network: Network name (sepolia or basesepolia), default sepolia
        token: Token symbol (USDC or DAI), default USDC
        
    Returns:
        TransferHandler instance
        
    Example:
        >>> # USDC on Sepolia chain
        >>> handler = create_handler("sepolia", "USDC")
        >>> # USDC on Base Sepolia chain
        >>> handler = create_handler("basesepolia", "USDC")
        >>> # DAI on Sepolia chain
        >>> handler = create_handler("sepolia", "DAI")
    """
    network = network.lower()
    token = token.upper()
    
    # Cache key: (network, token)
    cache_key = (network, token)
    
    # Check cache to avoid duplicate creation
    if cache_key not in _handler_cache:
        try:
            _handler_cache[cache_key] = TransferHandler(network=network, token=token)
            logger.info(f"[OK] Created {network}/{token} TransferHandler instance")
        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize {network}/{token} TransferHandler: {e}")
            return None
    
    return _handler_cache[cache_key]

# Backward compatibility alias (Single-chain mode)
def create_sepolia_handler(token: str = "USDC") -> TransferHandler:
    """
    [Deprecated] Use create_handler(network, token) instead
    
    This function is kept only for backward compatibility, defaults to the sepolia network
    """
    return create_handler(network="sepolia", token=token)