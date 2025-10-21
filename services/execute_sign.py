from dotenv import load_dotenv

import sys
import os

# Add project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from log import logger

import os

from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_typed_data

load_dotenv()

from services import CHAIN_ID, CHAIN_ID_HEX, CHAIN_RPC_URL, USDC_ADDRESS, ACTIVE_TOKEN, SEPOLIA_DAI_ADDRESS

SEPOLIA_PARAMS = {
    "chainId": CHAIN_ID_HEX,
    "chainName": "Sepolia",
    "nativeCurrency": { "name": "SepoliaETH", "symbol": "ETH", "decimals": 18 },
    "rpcUrls": [CHAIN_RPC_URL],
    "blockExplorerUrls": ["https://sepolia.etherscan.io"]
}

OWNER_PRIVATE_KEY = os.getenv("PAYER_PRIVATE_KEY")
# USDC (Sepolia) from your code

USDC_ADDRESS = Web3.to_checksum_address(USDC_ADDRESS)
USDC_NAME = ACTIVE_TOKEN
USDC_VERSION = "2"
CHAIN_ID = CHAIN_ID  # Sepolia

# Chain Configuration Dictionary
CHAIN_CONFIGS = {
    "sepolia": {
        "chain_id": CHAIN_ID,
        "chain_id_hex": CHAIN_ID_HEX,
        "rpc_url": CHAIN_RPC_URL,  # Using SEPOLIA_RPC_URL
        "name": "Sepolia"
    },
    "basesepolia": {
        "chain_id": CHAIN_ID,
        "chain_id_hex": CHAIN_ID_HEX,
        "rpc_url": CHAIN_RPC_URL,  # Using BASE_SEPOLIA_RPC_URL
        "name": "Base Sepolia"
    }
}

# Token Configuration Dictionary (Multi-chain × Multi-currency)
TOKEN_CONFIGS = {
    "sepolia": {
        "USDC": {
            "address": Web3.to_checksum_address(USDC_ADDRESS),
            "name": "USDC",
            "version": "2"
        },
        "DAI": {
            "address": Web3.to_checksum_address(SEPOLIA_DAI_ADDRESS),
            "name": "DAI",
            "version": "1"
        }
    },
    "basesepolia": {
        "USDC": {
            "address": Web3.to_checksum_address(USDC_ADDRESS),
            "name": "USDC",
            "version": "2"
        }
    }
}

# Spender (backend wallet) from your code
SPENDER = Web3.to_checksum_address(os.getenv("SPENDER_WALLET_ADDRESS"))

# Owner (the signer). For local signing only: provide a test private key.
# WARNING: Never use a real user's key here in production.
OWNER_PRIVATE_KEY = os.getenv("OWNER_PK") or OWNER_PRIVATE_KEY

# Validate private key format
if not OWNER_PRIVATE_KEY:
    raise ValueError("Private key not configured! Please set PAYER_PRIVATE_KEY or OWNER_PK environment variables")

if not OWNER_PRIVATE_KEY.startswith("0x"):
    OWNER_PRIVATE_KEY = "0x" + OWNER_PRIVATE_KEY

# Validate private key length (64 hex characters + 0x prefix = 66 characters)
if len(OWNER_PRIVATE_KEY) != 66:
    raise ValueError(f"Invalid private key format! Length should be 66 characters, actual length is {len(OWNER_PRIVATE_KEY)} characters: {OWNER_PRIVATE_KEY}")

logger.info(f"Using private key: {OWNER_PRIVATE_KEY[:10]}...{OWNER_PRIVATE_KEY[-10:]}")

def get_token_name_onchain(token_address: str, w3: Web3) -> str:
    """
    Retrieves the token name from the chain (used for EIP-712 domain)
    
    Args:
        token_address: Token contract address
        w3: Web3 instance
        
    Returns:
        The token name on the chain
    """
    try:
        name_abi = [{
            "constant": True,
            "inputs": [],
            "name": "name",
            "outputs": [{"name": "", "type": "string"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        }]
        contract = w3.eth.contract(address=token_address, abi=name_abi)
        onchain_name = contract.functions.name().call()
        if isinstance(onchain_name, str) and onchain_name:
            return onchain_name
    except Exception:
        pass
    return None

# ---------- Helpers ----------
def to_uint256(n: int) -> int:
    if n < 0:
        raise ValueError("uint256 must be non-negative")
    return n

def get_deadline_ts(deadline_iso_str: str) -> int:
    # convert to unix seconds; your UI uses absolute time
    dt = Web3.to_datetime(deadline_iso_str)  # supports many formats; if unsure, parse manually
    return int(dt.timestamp())

def fetch_nonce(owner_addr: str, token_address: str, w3: Web3) -> int:
    # nonces(address) selector: keccak256("nonces(address)") -> 0x7ecebe00
    selector = "0x7ecebe00"
    data = selector + owner_addr[2:].rjust(64, "0")
    res = w3.eth.call({"to": token_address, "data": data}, "latest")
    return int(res.hex(), 16)

def fetch_token_balance(owner_addr: str, token_address: str, w3: Web3) -> int:
    # balanceOf(address) selector: 0x70a08231
    selector = "0x70a08231"
    data = selector + owner_addr[2:].rjust(64, "0")
    res = w3.eth.call({"to": token_address, "data": data}, "latest")
    return int(res.hex(), 16)  # smallest unit, 6 decimals for USDC

def sign(budget: int , deadline: int, network: str = "sepolia", token: str = "USDC"):
    """
    Generates the EIP-2612 Permit signature (multi-chain supported)
    
    Args:
        deadline: Expiration timestamp
        network: Network name (sepolia or basesepolia)
        token: Token symbol (USDC or DAI)
        
    Returns:
        (signature, r, s, v) tuple
    """

    network = network.lower()
    token = token.upper()

    # Validate network support
    if network not in CHAIN_CONFIGS:
        raise ValueError(f"Unsupported network: {network}. Supported: {list(CHAIN_CONFIGS.keys())}")
    
    chain_config = CHAIN_CONFIGS[network]
    CHAIN_ID = chain_config["chain_id"]
    
    # Validate RPC URL configuration
    if not chain_config["rpc_url"]:
        raise ValueError(f"{network.upper()}_RPC_URL not configured. Please check .env")
    
    # Create Web3 instance for the corresponding network
    w3 = Web3(Web3.HTTPProvider(chain_config["rpc_url"]))
    
    # Validate token support on the network
    if network not in TOKEN_CONFIGS:
        raise ValueError(f"No token configuration for network: {network}")
    
    if token not in TOKEN_CONFIGS[network]:
        supported_tokens = list(TOKEN_CONFIGS[network].keys())
        raise ValueError(f"Token {token} not supported on {network}. Supported: {supported_tokens}")
    
    token_config = TOKEN_CONFIGS[network][token]
    if not token_config["address"]:
        raise ValueError(f"{token} address not configured for {network}. Please check .env")
    
    TOKEN_ADDRESS = token_config["address"]
    TOKEN_NAME = token_config["name"]
    TOKEN_VERSION = token_config["version"]
    
    # For DAI, prioritize the on-chain name (to avoid domain mismatch)
    if token == "DAI":
        onchain_name = get_token_name_onchain(TOKEN_ADDRESS, w3)
        if onchain_name:
            TOKEN_NAME = onchain_name

    acct = Account.from_key(OWNER_PRIVATE_KEY)
    OWNER = acct.address  # derived from private key

    # UI-provided inputs
    budget_ui = str(budget/10)  # example: your front-end "budget" string (scaled by 100000) - 0.01 USDC
    
    # deadline_iso = "2025-12-31T23:59:59"  # example ISO datetime from your UI

    # ---------- Mirror your UI's value scaling ----------
    # UI budget is a string of "display units" where display = USDC * 100000
    # So on-chain smallest unit (6 decimals) is: floor((budget/100000) * 1e6)
    scaled_budget = float(budget_ui) / 100000.0
    value_smallest = int(scaled_budget * 1_000_000)  # USDC has 6 decimals

    # Optional sanity checks (Dynamically display network information)
    network_name = chain_config["name"]  # Get network name
    
    # Print detailed network and contract information
    logger.info(f">>> Checking Balance - Network: {network_name}, Chain ID: {CHAIN_ID}")
    logger.info(f">>> {token} Contract Address: {TOKEN_ADDRESS}")
    logger.info(f">>> Owner Address: {OWNER}")
    
    # Optional sanity checks similar to your JS:
    eth_balance_wei = w3.eth.get_balance(OWNER)
    if eth_balance_wei <= 0:
        logger.warning("Warning: Owner has 0 Sepolia ETH for gas (only matters if sending a tx).")

    token_balance = fetch_token_balance(OWNER, TOKEN_ADDRESS, w3)
    if token_balance < value_smallest:
        logger.warning(f"Warning: Insufficient USDC. Have {(token_balance/1e6):.2f}, need {(value_smallest/1e6):.2f}")

    nonce = fetch_nonce(OWNER, TOKEN_ADDRESS, w3)

    # current = datetime.now()
    # updates = current + timedelta(seconds=expiry)     
    # deadline = int(updates.timestamp())
    # logger.info(f"deadline: {deadline}")
    
    # ---------- Build EIP-712 typed data ----------
    domain = {
        "name": TOKEN_NAME,
        "version": TOKEN_VERSION,
        "chainId": CHAIN_ID,  # Ensure it's an integer
        "verifyingContract": TOKEN_ADDRESS,
    }

    types = {
        "Permit": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"},
            {"name": "value", "type": "uint256"},
            {"name": "nonce", "type": "uint256"},
            {"name": "deadline", "type": "uint256"},
        ],
    }

    message = {
        "owner": OWNER,
        "spender": SPENDER,
        "value": to_uint256(value_smallest),
        "nonce": to_uint256(nonce),
        "deadline": to_uint256(deadline),
    }

    # ---------- Sign using eth-account (EIP-712 v4) ----------
    # Use the correct parameter format: pass domain, types, message separately
    encoded = encode_typed_data(domain, types, message)
    signed = acct.sign_message(encoded)

    signature_hex = signed.signature.hex()
    r_hex = "0x" + signed.r.to_bytes(32, "big").hex()
    s_hex = "0x" + signed.s.to_bytes(32, "big").hex()
    v_int = signed.v  # usually 27 or 28

    logger.info(f"EIP-2612 Permit Signature: {signature_hex}")
    logger.info(f"r: {r_hex}")
    logger.info(f"s: {s_hex}")
    logger.info(f"v: {v_int}")

    # Optional: verify recovery
    recovered = Account.recover_message(encoded, signature=signature_hex)
    assert recovered.lower() == OWNER.lower(), "Signature recover mismatch"
    logger.info(f"Recovered signer: {recovered}")
    return signature_hex, r_hex, s_hex, v_int