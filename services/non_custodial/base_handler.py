"""
Abstract Base Class: Define a unified interface for all blockchain protocols

Supported Protocols:
- EVM (Ethereum, Base, BNB Chain)
- Solana

Design Pattern: Abstract Base Class + Factory Pattern
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseTransferHandler(ABC):
    """
    Abstract Base Class for Blockchain Transfer Processors
    
    Handlers for all protocols must implement the following methods:
    - execute_permit: Execute authorization (EVM: permit, Solana: approve/delegate)
    - execute_transfer_from: Execute transfer
    - get_transaction_status: Query transaction status
    - check_allowance: Check allowance
    - get_native_balance: Get native token balance (ETH/SOL, etc.)
    """
    
    def __init__(self, network: str, token: str):
        """
        Initialize the processor
        
        Args:
            network: Network name (e.g., sepolia, solana-devnet)
            token: Token symbol (e.g., USDC, DAI)
        """
        self.network = network
        self.token_symbol = token
    
    @abstractmethod
    async def execute_permit(
        self, 
        owner: str, 
        spender: str, 
        value: int, 
        deadline: int, 
        v: int = None, 
        r: str = None, 
        s: str = None,
        signature: str = None,  # Used by Solana
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute the authorization operation (permit/approve)
        
        EVM: Execute EIP-2612 permit (spender pays gas)
        Solana: Execute approve + transferChecked (backend as fee_payer)
        
        Args:
            owner: Address of the token holder
            spender: Address authorized to spend
            value: Amount to authorize
            deadline: Expiration timestamp
            v, r, s: EVM signature parameters (EVM specific)
            signature: Partial signature for Solana (Solana specific)
            
        Returns:
            {
                "success": bool,
                "tx_hash" or "signature": str,  # Transaction hash
                "status": "pending" | "confirmed" | "failed",
                "message": str,
                "details": dict
            }
        """
        pass
    
    @abstractmethod
    async def execute_transfer_from(
        self, 
        owner_address: str, 
        amount: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute the transfer operation
        
        EVM: Execute transferFrom (transfer from owner to spender/payee)
        Solana: Execute transferChecked (transfer from owner's token account to the target token account)
        
        Args:
            owner_address: Authorizer's address
            amount: Transfer amount
            
        Returns:
            {
                "success": bool,
                "tx_hash" or "signature": str,
                "status": "pending" | "confirmed" | "failed",
                "message": str,
                "details": dict
            }
        """
        pass
    
    @abstractmethod
    async def get_transaction_status(self, tx_hash: str) -> Dict[str, Any]:
        """
        Query transaction status
        
        Args:
            tx_hash: Transaction hash (EVM) or signature (Solana)
            
        Returns:
            {
                "success": bool,
                "status": "pending" | "confirmed" | "failed",
                "tx_hash": str,
                "message": str,
                "details": dict
            }
        """
        pass
    
    @abstractmethod
    async def check_allowance(self, owner_address: str) -> Dict[str, Any]:
        """
        Check the allowance amount
        
        Args:
            owner_address: Authorizer's address
            
        Returns:
            {
                "success": bool,
                "allowance": int,  # Smallest unit
                "allowance_display": float,  # Display unit (e.g., 0.03 USDC)
                "owner": str,
                "spender": str
            }
        """
        pass
    
    @abstractmethod
    async def get_native_balance(self, address: str) -> float:
        """
        Get native token balance (ETH/BNB/SOL)
        
        Args:
            address: Address
            
        Returns:
            Balance (unit: ETH/BNB/SOL)
        """
        pass
    
    # Optional: Public helper method
    def get_protocol_type(self) -> str:
        """
        Get the protocol type
        
        Returns:
            "evm" or "solana"
        """
        if hasattr(self, 'chain_config'):
            return self.chain_config.get("protocol", "unknown")
        return "unknown"