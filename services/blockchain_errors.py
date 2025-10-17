"""
Blockchain-specific error codes for Zen7 Payment Agent.
Based on actual errors from transfer_handler.py, execute_permit.py, and agent.py
"""

from enum import Enum
from typing import Optional, Dict, Any


class BlockchainErrorCode(Enum):
    """
    Blockchain transaction error codes (110014-110030)
    Extends constants.py (110001-110013)
    """
    
    # Nonce errors (110014-110016)
    NONCE_TOO_LOW = ("110014", "Transaction nonce conflict. Please try again.")
    NONCE_TOO_HIGH = ("110015", "Transaction nonce too high. Please refresh and try again.")
    REPLACEMENT_UNDERPRICED = ("110016", "Transaction replacement gas price too low.")
    
    # Gas errors (110017-110019)
    OUT_OF_GAS = ("110017", "Transaction ran out of gas.")
    GAS_PRICE_TOO_LOW = ("110018", "Gas price too low.")
    INSUFFICIENT_FUNDS_FOR_GAS = ("110019", "Insufficient ETH for gas fees.")
    
    # Signature errors (110020-110023)
    INVALID_SIGNATURE = ("110020", "Permit signature is invalid. Please re-authorize.")
    SIGNATURE_EXPIRED = ("110021", "Permit signature has expired. Please create new authorization.")
    SIGNATURE_ALREADY_USED = ("110022", "Permit already used. Please create new authorization.")
    WRONG_SIGNER = ("110023", "Signature does not match wallet address.")
    
    # Allowance/Balance errors (110024-110026)
    INSUFFICIENT_ALLOWANCE = ("110024", "Insufficient token allowance. Please authorize more tokens.")
    INSUFFICIENT_BALANCE = ("110025", "Insufficient token balance. Please add funds.")
    ALLOWANCE_BELOW_ZERO = ("110026", "Invalid allowance amount.")
    
    # Network errors (110027-110029)
    NETWORK_CONNECTION_FAILED = ("110027", "Failed to connect to blockchain network.")
    RPC_ERROR = ("110028", "Blockchain RPC error. Please try again later.")
    TRANSACTION_REVERTED = ("110029", "Transaction was reverted.")
    
    # Simulation errors (110030)
    SIMULATION_FAILED = ("110030", "Transaction simulation failed.")

    @property
    def code(self) -> str:
        return self.value[0]

    @property
    def desc(self) -> str:
        return self.value[1]


class ErrorCategory(Enum):
    """Error category"""
    RETRYABLE = "retryable"
    NON_RETRYABLE = "non_retryable"
    USER_ACTION_REQUIRED = "user_action_required"
    SYSTEM_ERROR = "system_error"


class BlockchainErrorClassifier:
    """Classify blockchain errors"""
    
    ERROR_PATTERNS = {
        # Nonce
        "nonce too low": BlockchainErrorCode.NONCE_TOO_LOW,
        "nonce too high": BlockchainErrorCode.NONCE_TOO_HIGH,
        "replacement transaction underpriced": BlockchainErrorCode.REPLACEMENT_UNDERPRICED,
        # Gas
        "out of gas": BlockchainErrorCode.OUT_OF_GAS,
        "gas too low": BlockchainErrorCode.GAS_PRICE_TOO_LOW,
        "insufficient funds for gas": BlockchainErrorCode.INSUFFICIENT_FUNDS_FOR_GAS,
        # Signature
        "eip2612: invalid signature": BlockchainErrorCode.INVALID_SIGNATURE,
        "invalid signature": BlockchainErrorCode.INVALID_SIGNATURE,
        "eip2612: expired": BlockchainErrorCode.SIGNATURE_EXPIRED,
        "expired": BlockchainErrorCode.SIGNATURE_EXPIRED,
        "deadline": BlockchainErrorCode.SIGNATURE_EXPIRED,
        # Allowance/Balance
        "insufficient allowance": BlockchainErrorCode.INSUFFICIENT_ALLOWANCE,
        "transfer amount exceeds allowance": BlockchainErrorCode.INSUFFICIENT_ALLOWANCE,
        "erc20: insufficient allowance": BlockchainErrorCode.INSUFFICIENT_ALLOWANCE,
        "insufficient balance": BlockchainErrorCode.INSUFFICIENT_BALANCE,
        "transfer amount exceeds balance": BlockchainErrorCode.INSUFFICIENT_BALANCE,
        "erc20: transfer amount exceeds balance": BlockchainErrorCode.INSUFFICIENT_BALANCE,
        # Network
        "connection refused": BlockchainErrorCode.NETWORK_CONNECTION_FAILED,
        "connection timeout": BlockchainErrorCode.NETWORK_CONNECTION_FAILED,
        "network error": BlockchainErrorCode.NETWORK_CONNECTION_FAILED,
        "execution reverted": BlockchainErrorCode.TRANSACTION_REVERTED,
    }
    
    ERROR_CATEGORIES = {
        # Retryable
        BlockchainErrorCode.NONCE_TOO_LOW: ErrorCategory.RETRYABLE,
        BlockchainErrorCode.NONCE_TOO_HIGH: ErrorCategory.RETRYABLE,
        BlockchainErrorCode.GAS_PRICE_TOO_LOW: ErrorCategory.RETRYABLE,
        BlockchainErrorCode.NETWORK_CONNECTION_FAILED: ErrorCategory.RETRYABLE,
        BlockchainErrorCode.RPC_ERROR: ErrorCategory.RETRYABLE,
        # Non-retryable
        BlockchainErrorCode.INVALID_SIGNATURE: ErrorCategory.NON_RETRYABLE,
        BlockchainErrorCode.SIGNATURE_EXPIRED: ErrorCategory.NON_RETRYABLE,
        BlockchainErrorCode.SIGNATURE_ALREADY_USED: ErrorCategory.NON_RETRYABLE,
        BlockchainErrorCode.WRONG_SIGNER: ErrorCategory.NON_RETRYABLE,
        BlockchainErrorCode.OUT_OF_GAS: ErrorCategory.NON_RETRYABLE,
        BlockchainErrorCode.ALLOWANCE_BELOW_ZERO: ErrorCategory.NON_RETRYABLE,
        # User action required
        BlockchainErrorCode.INSUFFICIENT_ALLOWANCE: ErrorCategory.USER_ACTION_REQUIRED,
        BlockchainErrorCode.INSUFFICIENT_BALANCE: ErrorCategory.USER_ACTION_REQUIRED,
        BlockchainErrorCode.INSUFFICIENT_FUNDS_FOR_GAS: ErrorCategory.USER_ACTION_REQUIRED,
        BlockchainErrorCode.REPLACEMENT_UNDERPRICED: ErrorCategory.USER_ACTION_REQUIRED,
        # System errors
        BlockchainErrorCode.SIMULATION_FAILED: ErrorCategory.SYSTEM_ERROR,
        BlockchainErrorCode.TRANSACTION_REVERTED: ErrorCategory.SYSTEM_ERROR,
    }
    
    @classmethod
    def classify_error(cls, error_message: str) -> Optional[BlockchainErrorCode]:
        """Classify error message to error code"""
        if not error_message:
            return None
        error_lower = error_message.lower()
        for pattern, error_code in cls.ERROR_PATTERNS.items():
            if pattern in error_lower:
                return error_code
        return None
    
    @classmethod
    def get_error_category(cls, error_code: BlockchainErrorCode) -> ErrorCategory:
        """Get error category"""
        return cls.ERROR_CATEGORIES.get(error_code, ErrorCategory.SYSTEM_ERROR)
    
    @classmethod
    def is_retryable(cls, error_code: BlockchainErrorCode) -> bool:
        """Check if error is retryable"""
        return cls.get_error_category(error_code) == ErrorCategory.RETRYABLE
    
    @classmethod
    def parse_error(cls, error_message: str) -> Dict[str, Any]:
        """Parse error and return structured info"""
        error_code = cls.classify_error(error_message)
        if error_code:
            category = cls.get_error_category(error_code)
            return {
                "error_code": error_code.code,
                "user_message": error_code.desc,
                "category": category.value,
                "is_retryable": cls.is_retryable(error_code),
                "technical_error": error_message
            }
        else:
            return {
                "error_code": "110029",
                "user_message": "Transaction failed. Please try again.",
                "category": ErrorCategory.SYSTEM_ERROR.value,
                "is_retryable": False,
                "technical_error": error_message
            }


def create_error_response(error_message: str, additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create standardized error response"""
    parsed_error = BlockchainErrorClassifier.parse_error(error_message)
    response = {
        "success": False,
        "error_code": parsed_error["error_code"],
        "message": parsed_error["user_message"],
        "category": parsed_error["category"],
        "is_retryable": parsed_error["is_retryable"],
    }
    if additional_context and additional_context.get("include_technical"):
        response["technical_error"] = parsed_error["technical_error"]
    if additional_context:
        response.update(additional_context)
    return response


def create_success_response(message: str, **data) -> Dict[str, Any]:
    """Create standardized success response"""
    response = {"success": True, "message": message}
    response.update(data)
    return response
