"""
Blockchain Transfer Handler Factory (Multi-Protocol Support)

Supported Protocols:
- EVM (Ethereum, Base, BNB Chain) → evm_transfer_handler.py
- Solana → solana_transfer_handler.py

Design Pattern: Abstract Base Class + Factory Pattern + Singleton Cache

Backward Compatibility Notes:
- Original import statement remains available: from transfer_handler import create_handler
- EVM-related configurations have been moved to evm_transfer_handler.py
"""
from log import logger
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from services.non_custodial.base_handler import BaseTransferHandler

# Load environment variables
load_dotenv()

# ==================== Unified Configuration (All Protocols) ====================

# Import configurations for each protocol
from services.non_custodial.evm_transfer_handler import CHAIN_CONFIGS as EVM_CHAIN_CONFIGS, TOKEN_CONFIGS as EVM_TOKEN_CONFIGS
try:
    from services.non_custodial.solana_transfer_handler import CHAIN_CONFIGS as SOLANA_CHAIN_CONFIGS, TOKEN_CONFIGS as SOLANA_TOKEN_CONFIGS
    SOLANA_AVAILABLE = True
except ImportError:
    SOLANA_CHAIN_CONFIGS: Dict[str, Any] = {}
    SOLANA_TOKEN_CONFIGS: Dict[str, Any] = {}
    SOLANA_AVAILABLE = False

# Merge all configurations
CHAIN_CONFIGS = {
    **EVM_CHAIN_CONFIGS,
    **SOLANA_CHAIN_CONFIGS
}

TOKEN_CONFIGS = {
    **EVM_TOKEN_CONFIGS,
    **SOLANA_TOKEN_CONFIGS
}

# ==================== Global Instance Cache (Singleton Pool) ====================

_handler_cache: Dict[tuple, BaseTransferHandler] = {}


def create_handler(network: str = "sepolia", token: str = "USDC") -> Optional[BaseTransferHandler]:
    """
    Creates or retrieves a TransferHandler instance (Multi-Protocol Factory Pattern + Singleton Cache)
    
    Automatically selects the protocol based on the network:
    - EVM Chains: sepolia, basesepolia, bnbtestnet
    - Solana Chains: solana-devnet, solana-mainnet, solana-testnet
    
    Args:
        network: Network name (e.g., sepolia, solana-devnet)
        token: Token symbol (e.g., USDC, DAI)
        
    Returns:
        BaseTransferHandler instance (EVMTransferHandler or SolanaTransferHandler), or None if creation fails.
        
    Example:
        >>> # EVM Chain
        >>> handler = create_handler("sepolia", "USDC")
        >>> # Solana Chain
        >>> handler = create_handler("solana-devnet", "USDC")
    """
    network = network.lower()
    token = token.upper()
    
    # Cache key
    cache_key = (network, token)
    
    # Check cache
    if cache_key in _handler_cache:
        logger.info(f"[CACHE HIT] Returning cached {network}/{token} TransferHandler instance.")
        return _handler_cache[cache_key]
    
    # Validate network support
    if network not in CHAIN_CONFIGS:
        logger.error(f"[ERROR] Unsupported network: {network}")
        logger.error(f"[ERROR] Supported networks: {list(CHAIN_CONFIGS.keys())}")
        return None
    
    # Detect protocol type
    protocol = CHAIN_CONFIGS[network].get("protocol", "unknown")
    
    try:
        if protocol == "evm":
            # EVM Chain
            # Dynamic import to avoid circular dependency and only load necessary classes
            from services.non_custodial.evm_transfer_handler import EVMTransferHandler
            handler = EVMTransferHandler(network=network, token=token)
            logger.info(f"[OK] Created EVM {network}/{token} TransferHandler instance")
        
        elif protocol == "solana":
            # Solana Chain
            if not SOLANA_AVAILABLE:
                logger.error(f"[ERROR] Solana dependencies are not installed. Please run: pip install solders solana spl-token")
                return None
            
            from services.non_custodial.solana_transfer_handler import SolanaTransferHandler
            handler = SolanaTransferHandler(network=network, token=token)
            logger.info(f"[OK] Created Solana {network}/{token} TransferHandler instance")
        
        else:
            logger.error(f"[ERROR] Unknown protocol: {protocol} for network: {network}")
            return None
        
        # Cache the instance
        _handler_cache[cache_key] = handler
        return handler
        
    except Exception as e:
        logger.error(f"[ERROR] Failed to initialize {network}/{token} TransferHandler: {e}")
        return None


# ==================== Backward Compatible Aliases ====================

def create_sepolia_handler(token: str = "USDC") -> Optional[BaseTransferHandler]:
    """
    [DEPRECATED] Use create_handler(network, token) instead.
    
    This function is kept for backward compatibility, defaulting to the sepolia network.
    """
    logger.warning("[DEPRECATED] create_sepolia_handler is deprecated. Use create_handler('sepolia', token) instead.")
    return create_handler(network="sepolia", token=token)


# Export original EVM class (Backward Compatibility)
try:
    # Attempt to load EVM specific exports for older codebases that used them directly
    from services.non_custodial.evm_transfer_handler import EVMTransferHandler as TransferHandler
    from services.non_custodial.evm_transfer_handler import CHAIN_CONFIGS as EVM_CHAIN_CONFIGS_EXPORT
    from services.non_custodial.evm_transfer_handler import TOKEN_CONFIGS as EVM_TOKEN_CONFIGS_EXPORT
    from services.non_custodial.evm_transfer_handler import TOKEN_ABI
except ImportError:
    logger.error("[WARNING] Unable to import EVM TransferHandler for backward compatibility. Ensure evm_transfer_handler is configured.")


# ==================== Module Exports ====================

__all__ = [
    "create_handler",
    "create_sepolia_handler",
    "TransferHandler",  # Backward compatibility
    "CHAIN_CONFIGS",
    "TOKEN_CONFIGS"
]