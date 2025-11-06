"""
EVM Blockchain Transfer Handler (Inherits from BaseTransferHandler)

Supported EVM Chains:
- Ethereum Sepolia
- Base Sepolia
- BNB Chain Testnet

Supported Protocols:
- EIP-2612 Permit (Off-chain signed authorization)
- ERC-20 transferFrom
"""
from log import logger
import os
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
from typing import Dict, Any
from services.non_custodial.base_handler import BaseTransferHandler

# Load environment variables
load_dotenv()

# ==================== EVM Multi-Chain Configuration ====================

# Chain configuration dictionary
CHAIN_CONFIGS = {
    "sepolia": {
        "protocol": "evm",
        "chain_id": 11155111,  # Ethereum Sepolia testnet
        "rpc_url": os.getenv("SEPOLIA_RPC_URL"),
        "name": "Sepolia",
        "native_currency": "ETH"
    },
    "basesepolia": {
        "protocol": "evm",
        "chain_id": 84532,  # Base Sepolia testnet
        "rpc_url": os.getenv("BASE_SEPOLIA_RPC_URL"),
        "name": "Base Sepolia",
        "native_currency": "ETH"
    },
    "bnbtestnet": {
        "protocol": "evm",
        "chain_id": 97,  # BNB Chain Testnet
        "rpc_url": os.getenv("BNBChain_Testnet_RPC_URL"),
        "name": "BNB Chain Testnet",
        "native_currency": "BNB"
    }
}

# Token configuration dictionary (Multi-chain × Multi-token)
TOKEN_CONFIGS = {
    "sepolia": {
        "USDC": {
            "address": os.getenv("SEPOLIA_USDC_ADDRESS"),
            "name": "USDC",
            "version": "2",
            "decimals": 6
        },
        "DAI": {
            "address": os.getenv("SEPOLIA_DAI_ADDRESS"),
            "name": "DAI",
            "version": "1",
            "decimals": 18
        }
    },
    "basesepolia": {
        "USDC": {
            "address": os.getenv("BASE_SEPOLIA_USDC_ADDRESS"),
            "name": "USDC",
            "version": "2",
            "decimals": 6
        }
    },
    "bnbtestnet": {
        "USDC": {
            "address": os.getenv("BNBChain_Testnet_USDC_ADDRESS"),
            "name": "USD Coin",
            "version": "1",
            "decimals": 6
        }
    }
}

# General ERC20 + EIP-2612 ABI
TOKEN_ABI = [
    # Basic ERC20 Functions
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
    # EIP-2612 Permit Function
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


class EVMTransferHandler(BaseTransferHandler):
    """EVM Blockchain Transfer Handler (Supports EIP-2612 Permit)"""
    
    def __init__(self, network: str = "sepolia", token: str = "USDC"):
        """
        Initialize the EVM TransferHandler
        
        Args:
            network: Network name (sepolia, basesepolia, bnbtestnet)
            token: Token symbol (USDC, DAI)
        """
        super().__init__(network, token)
        
        # Normalize parameters
        network = network.lower()
        token = token.upper()
        
        # Validate network support
        if network not in CHAIN_CONFIGS:
            raise ValueError(f"Unsupported EVM network: {network}. Supported: {list(CHAIN_CONFIGS.keys())}")
        
        chain_config = CHAIN_CONFIGS[network]
        
        # Validate RPC URL configuration
        if not chain_config["rpc_url"]:
            raise ValueError(f"{network.upper()}_RPC_URL not configured. Please set it in .env")
        
        # Validate token support on the network
        if network not in TOKEN_CONFIGS:
            raise ValueError(f"No token configuration for EVM network: {network}")
        
        if token not in TOKEN_CONFIGS[network]:
            supported_tokens = list(TOKEN_CONFIGS[network].keys())
            raise ValueError(f"Token {token} not supported on {network}. Supported: {supported_tokens}")
        
        token_config = TOKEN_CONFIGS[network][token]
        
        # Validate token address configuration
        if not token_config["address"]:
            env_var = f"{network.upper()}_{token}_ADDRESS"
            raise ValueError(f"{token} address not configured for {network}. Please set {env_var} in .env")
        
        # Prioritize SPENDER_KEY, otherwise use PRIVATE_KEY
        self.private_key = os.getenv("SPENDER_KEY") or os.getenv("PRIVATE_KEY")
        if not self.private_key:
            raise ValueError("SPENDER_KEY or PRIVATE_KEY not configured")
        
        if not self.private_key.startswith("0x"):
            self.private_key = f"0x{self.private_key}"
        
        self.account = Account.from_key(self.private_key)
        
        # Save configuration
        self.network = network
        self.chain_config = chain_config
        self.token_config = token_config
        self.token_symbol = token
        
        logger.info(f">>> [EVM] Connecting to {chain_config['name']}: {chain_config['rpc_url']}")
        logger.info(f">>> [EVM] Current Token: {token} @ {token_config['address']}")
        
        self.w3 = Web3(Web3.HTTPProvider(self.chain_config["rpc_url"]))
        
        # Check network connection
        if not self.w3.is_connected():
            raise ConnectionError(f"Failed to connect to {self.chain_config['rpc_url']}")
        
        # Create token contract instance
        self.usdc_contract = self.w3.eth.contract(
            address=token_config["address"],
            abi=TOKEN_ABI
        )

        # Read payee address (optional)
        self.payee_address = os.getenv("PAYEE_WALLET_ADDRESS")
        if self.payee_address:
            try:
                self.payee_address = Web3.to_checksum_address(self.payee_address)
            except Exception as e:
                raise ValueError(f"Invalid PAYEE_WALLET_ADDRESS: {e}")
    
    async def execute_transfer_from(
        self, 
        owner_address: str, 
        amount: str = "10000"
    ) -> Dict[str, Any]:
        """
        Execute the ERC-20 transferFrom call
        
        Args:
            owner_address: The address authorized to you
            amount: The transfer amount (in the smallest unit)
        
        Returns:
            A dictionary containing the transaction hash
        """
        try:
            # Convert address format
            owner_address_checksum = Web3.to_checksum_address(owner_address)
            
            # Check allowance
            allowance = self.usdc_contract.functions.allowance(
                owner_address_checksum, 
                self.account.address
            ).call()
            
            if allowance < int(amount):
                return {
                    "success": False,
                    "error": f"Insufficient allowance. Required: {int(amount)}, Available: {allowance}",
                    "message": "Insufficient allowance for transferFrom"
                }
            
            # Get current nonce
            nonce = self.w3.eth.get_transaction_count(self.account.address, 'pending')
            
            # Build transferFrom transaction
            to_checksum = self.payee_address if self.payee_address else self.account.address
            transfer_txn = self.usdc_contract.functions.transferFrom(
                owner_address_checksum,
                to_checksum,
                int(amount)
            ).build_transaction({
                'from': self.account.address,
                'gas': 100000,
                # Note: For EIP-1559 chains (Ethereum, Base), 'maxFeePerGas'/'maxPriorityFeePerGas' should be used instead of 'gasPrice'
                'gasPrice': self.w3.eth.gas_price, 
                'nonce': nonce
            })
            
            # Sign and send the transaction
            signed_txn = self.account.sign_transaction(transfer_txn)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            logger.info(f"[EVM] TransferFrom transaction submitted: {tx_hash.hex()}")
            
            return {
                "success": True,
                "tx_hash": tx_hash.hex(),
                "status": "pending",
                "message": f"TransferFrom transaction submitted",
                "polling_required": True,
                "details": {
                    "owner": owner_address_checksum,
                    "spender": self.account.address,
                    "to": to_checksum,
                    "amount": int(amount),
                    "amount_display": int(amount) / (10 ** self.token_config['decimals']),
                    "gas_limit": transfer_txn['gas'],
                    "gas_price": transfer_txn['gasPrice']
                }
            }
                
        except Exception as e:
            logger.error(f"[EVM] transferFrom execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to execute transferFrom"
            }
    
    # Helper for checking token balance (not part of ABC but useful)
    async def check_usdc_balance(self) -> Dict[str, Any]:
        """Check the token balance of the current address"""
        try:
            balance = self.usdc_contract.functions.balanceOf(self.account.address).call()
            decimals = self.token_config['decimals']
            return {
                "success": True,
                "balance": balance,
                "balance_display": balance / (10 ** decimals),
                "address": self.account.address
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to check token balance"
            }
    
    async def check_allowance(self, owner_address: str) -> Dict[str, Any]:
        """Check the allowance amount"""
        try:
            owner_address_checksum = Web3.to_checksum_address(owner_address)
            allowance = self.usdc_contract.functions.allowance(
                owner_address_checksum, 
                self.account.address
            ).call()
            decimals = self.token_config['decimals']
            return {
                "success": True,
                "allowance": allowance,
                "allowance_display": allowance / (10 ** decimals),
                "owner": owner_address_checksum,
                "spender": self.account.address
            }
        except Exception as e:
            logger.error(f"[EVM] check_allowance failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to check allowance"
            }

    async def get_native_balance(self, address: str) -> float:
        """Get the native token balance (ETH/BNB) for the specified address"""
        try:
            checksum_address = Web3.to_checksum_address(address)
            balance_wei = self.w3.eth.get_balance(checksum_address)
            balance_native = self.w3.from_wei(balance_wei, 'ether')
            return float(balance_native)
        except Exception as e:
            native_currency = self.chain_config.get("native_currency", "ETH")
            logger.info(f"[EVM] Failed to get {native_currency} balance for {address}: {e}")
            return 0.0
    
    async def get_eth_balance(self, address: str) -> float:
        """[Deprecated] Use get_native_balance instead"""
        return await self.get_native_balance(address)

    async def execute_permit(
        self, 
        owner: str, 
        spender: str, 
        value: int, 
        deadline: int, 
        v: int, 
        r: str, 
        s: str,
        network: str = None, # Unused for EVM, kept for interface consistency
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute the EIP-2612 permit authorization
        
        Args:
            owner: Token holder's address
            spender: Authorized address
            value: Authorization amount
            deadline: Expiration timestamp
            v, r, s: Signature parameters
        
        Returns:
            A dictionary containing the transaction hash
        """
        try:
            logger.info(f"[EVM] Executing EIP-2612 permit authorization...")
            logger.info(f"Owner: {owner}")
            logger.info(f"Spender: {spender}")
            logger.info(f"Value: {value}")
            logger.info(f"Deadline: {deadline}")
            
            # Check spender balance (must have native token to pay for gas)
            native_currency = self.chain_config.get("native_currency", "ETH")
            spender_balance = await self.get_native_balance(self.account.address) # Spender is the wallet configured via SPENDER_KEY
            logger.info(f">>> Spender {native_currency} Balance: {spender_balance} {native_currency}")
            
            # Convert address format
            owner_checksum = Web3.to_checksum_address(owner)
            spender_checksum = Web3.to_checksum_address(spender)
            
            # Get current nonce
            nonce = self.w3.eth.get_transaction_count(self.account.address, 'pending')
            
            # Build permit transaction
            # r and s are expected to be bytes32 in Solidity; we handle hex string conversion
            r_bytes = bytes.fromhex(r[2:]) if r.startswith('0x') else bytes.fromhex(r)
            s_bytes = bytes.fromhex(s[2:]) if s.startswith('0x') else bytes.fromhex(s)
            
            permit_txn = self.usdc_contract.functions.permit(
                owner_checksum,
                spender_checksum,
                int(value),
                deadline,
                v,
                r_bytes,
                s_bytes
            ).build_transaction({
                'from': self.account.address,
                'gas': 150000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce
            })
            
            # Sign and send the transaction
            signed_txn = self.account.sign_transaction(permit_txn)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            logger.info(f"[EVM] Permit transaction submitted: {tx_hash.hex()}")
            
            return {
                "success": True,
                "tx_hash": tx_hash.hex(),
                "status": "pending",
                "message": f"Permit transaction submitted",
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
            logger.error(f"[EVM] permit execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "EVM permit execution failed"
            }

    async def get_transaction_status(self, tx_hash: str) -> Dict[str, Any]:
        """Query transaction status"""
        try:
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
                            "transaction_index": receipt.transactionIndex
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
                # Transaction not yet confirmed
                try:
                    tx = self.w3.eth.get_transaction(tx_hash)
                    if tx:
                        return {
                            "success": True,
                            "status": "pending",
                            "tx_hash": tx_hash,
                            "message": "Transaction waiting for confirmation"
                        }
                except:
                    pass
                
                return {
                    "success": True,
                    "status": "pending",
                    "tx_hash": tx_hash,
                    "message": "Transaction waiting for confirmation"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to query transaction status"
            }

    def simulate_permit(self, owner, spender, value, deadline, v, r, s):
        """Locally simulate the permit call"""
        try:
            owner_checksum = Web3.to_checksum_address(owner)
            spender_checksum = Web3.to_checksum_address(spender)
            r_bytes = bytes.fromhex(r[2:]) if r.startswith('0x') else bytes.fromhex(r)
            s_bytes = bytes.fromhex(s[2:]) if s.startswith('0x') else bytes.fromhex(s)
            
            self.usdc_contract.functions.permit(
                owner_checksum,
                spender_checksum,
                int(value),
                deadline,
                v,
                r_bytes,
                s_bytes
            ).call({'from': self.account.address})
            return {"success": True}
        except Exception as e:
            if hasattr(e, 'args') and len(e.args) > 0:
                # web3.py often wraps the revert message in the first argument
                return {"success": False, "error": str(e.args[0]), "message": "Permit simulation failed"} 
            return {"success": False, "error": str(e), "message": "Permit simulation failed"}