from enum import Enum

ChainID = {
    "eth": "eip155:1",
    "polygon": "eip155:137",
    "base_sepolia": "eip155:84532",
    "sepolia": "eip155:11155111",
    "bnbtestnet": "eip155:97",
    "solana-devnet": "solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1"
}

ChainConfig = {
    "sepolia": {
        "chain_id": 11155111,
        "chain_id_hex": "0xaa36a7",
        "name": "Sepolia",
        "native_currency": "ETH"
    },
    "basesepolia": {
        "chain_id": 84532,
        "chain_id_hex": "0x14a34",
        "name": "Base Sepolia",
        "native_currency": "ETH"
    },
    "bnbtestnet": {
        "chain_id": 97,
        "chain_id_hex": "0x61",
        "name": "BNB Chain Testnet",
        "native_currency": "BNB"
    }
}

AssetID = {
    "eip155:1": "eip155:1/erc20:0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "eip155:84532": "eip155:84532/erc20:0x036CbD53842c5426634e7929541eC2318f3dCF7e",
    "eip155:11155111": "eip155:11155111/slip44:60",
    "eip155:27": "eip155:27/slip44:710",
    "eip155:137": "eip155:137/slip44:60",
    "solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1": "solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1/slip44:501"
}

TokenDecimals = {
    "eip155:1": 6,
    "eip155:84532": 6,
    "eip155:11155111": 18,
    "eip155:27":18,
    "eip155:137": 18,
    "solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1": 9
}

class ErrorCode(Enum):
    TRANSACTION_SERVICE_FAILED = (
        "110001",
        "Insufficient balance to complete the payment. Please check your account and try again.",
    )
    NO_TRANSACTION_TXHASH = (
        "110002",
        "Failed to get transaction hash. Please try again later.",
    )
    TRANSACTION_POLLING_TIMEOUT = (
        "110003",
        "Payment is taking longer than expected. Please check your order status later or contact support.",
    )
    AUTO_TRANSFER_FAILED = (
        "110004",
        "Automatic transfer failed. Please try again or contact support.",
    )
    TRANSACTION_TRANSACTION_FAILED = (
        "110005",
        "Payment transaction failed. Please check your balance or contact support.",
    )
    EXECUTE_PERMIT_FAILED = (
        "110006",
        "Authorization signature failed. Please refresh the page and try again.",
    )
    NO_AVAILABLE_VALUE = (
        "110007",
        "No available quota detected. Please re-authorize and try again.",
    )
    PAYMENT_SERVICE_FAILED = (
        "110008",
        "Payment service is currently unavailable due to invalid signature. Please try again later or contact support.",
    )
    NO_TXHASH_FOUND = (
        "110009",
        "Payment voucher not received. Please try again later.",
    )
    SKIP_PAYMENT_FAILED = (
        "110010",
        "Payment process was not completed. Please check your information and try again.",
    )
    AVAILABLE_QUERY_FAILED = (
        "110011",
        "Failed to check available quota. Please try again later.",
    )
    REDUCE_AMOUNT_FAILED = (
        "110012",
        "There was an error processing the payment amount. Please try again later.",
    )
    NO_ORDERID_FAILED = (
        "110013",
        "Order create failed. Please try again later.",
    )

    @property
    def code(self) -> str:
        return self.value[0]

    @property
    def desc(self) -> str:
        return self.value[1]
