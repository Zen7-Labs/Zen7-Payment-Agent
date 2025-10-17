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

# Spender (backend wallet) from your code
SPENDER = Web3.to_checksum_address(os.getenv("SPENDER_WALLET_ADDRESS"))

# Owner (the signer). For local signing only: provide a test private key.
# WARNING: Never use a real user's key here in production.
OWNER_PRIVATE_KEY = os.getenv("OWNER_PK") or OWNER_PRIVATE_KEY

# USDC/DAI (Sepolia) based on env (initial defaults; DAI will refine after w3 init)
if ACTIVE_TOKEN == "DAI":
    if not SEPOLIA_DAI_ADDRESS:
        raise ValueError("ACTIVE_TOKEN=DAI but SEPOLIA_DAI_ADDRESS is not configured")
    USDC_ADDRESS = Web3.to_checksum_address(SEPOLIA_DAI_ADDRESS)
    USDC_NAME = "DAI"
    USDC_VERSION = os.getenv("DAI_VERSION", "1")  # DAI is usually 1

# Sepolia

# Validate private key format
if not OWNER_PRIVATE_KEY:
    raise ValueError("Private key not configured! Please set PAYER_PRIVATE_KEY or OWNER_PK environment variables")

if not OWNER_PRIVATE_KEY.startswith("0x"):
    OWNER_PRIVATE_KEY = "0x" + OWNER_PRIVATE_KEY

# Validate private key length (64 hex characters + 0x prefix = 66 characters)
if len(OWNER_PRIVATE_KEY) != 66:
    raise ValueError(f"Invalid private key format! Length should be 66 characters, actual length is {len(OWNER_PRIVATE_KEY)} characters: {OWNER_PRIVATE_KEY}")

logger.info(f"Using private key: {OWNER_PRIVATE_KEY[:10]}...{OWNER_PRIVATE_KEY[-10:]}")

SEPOLIA_RPC = SEPOLIA_PARAMS["rpcUrls"][0]
w3 = Web3(Web3.HTTPProvider(SEPOLIA_RPC))

if ACTIVE_TOKEN == "DAI":
    try:
        dai_name_abi = [{
            "constant": True,
            "inputs": [],
            "name": "name",
            "outputs": [{"name": "", "type": "string"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        }]
        dai_contract = w3.eth.contract(address=USDC_ADDRESS, abi=dai_name_abi)
        onchain_name = dai_contract.functions.name().call()
        if isinstance(onchain_name, str) and onchain_name:
            USDC_NAME = onchain_name
    except Exception:
        pass

# ---------- Helpers ----------
def to_uint256(n: int) -> int:
    if n < 0:
        raise ValueError("uint256 must be non-negative")
    return n

def get_deadline_ts(deadline_iso_str: str) -> int:
    # convert to unix seconds; your UI uses absolute time
    dt = Web3.to_datetime(deadline_iso_str)  # supports many formats; if unsure, parse manually
    return int(dt.timestamp())

def fetch_nonce(owner_addr: str) -> int:
    # nonces(address) selector: keccak256("nonces(address)") -> 0x7ecebe00
    selector = "0x7ecebe00"
    data = selector + owner_addr[2:].rjust(64, "0")
    res = w3.eth.call({"to": USDC_ADDRESS, "data": data}, "latest")
    return int(res.hex(), 16)

def fetch_usdc_balance(owner_addr: str) -> int:
    # balanceOf(address) selector: 0x70a08231
    selector = "0x70a08231"
    data = selector + owner_addr[2:].rjust(64, "0")
    res = w3.eth.call({"to": USDC_ADDRESS, "data": data}, "latest")
    return int(res.hex(), 16)  # smallest unit, 6 decimals for USDC

def sign(budget: int , deadline: int):
    # ---------- Config ----------
    # SEPOLIA_RPC = "https://sepolia.infura.io/v3/<YOUR_INFURA_KEY>"

    acct = Account.from_key(OWNER_PRIVATE_KEY)
    OWNER = acct.address  # derived from private key

    # UI-provided inputs
    budget_ui = str(budget/10)  # example: your front-end "budget" string (scaled by 100000) - 0.01 USDC
    
    # deadline_iso = "2025-12-31T23:59:59"  # example ISO datetime from your UI

    # ---------- Mirror your UI's value scaling ----------
    # UI budget is a string of "display units" where display = USDC * 100000
    # So on-chain smallest unit (6 decimals) is: floor((budget/100000) * 1e6)
    scaled_budget_usdc = float(budget_ui) / 100000.0
    value_smallest = int(scaled_budget_usdc * 1_000_000)  # USDC has 6 decimals

    # Optional sanity checks similar to your JS:
    eth_balance_wei = w3.eth.get_balance(OWNER)
    if eth_balance_wei <= 0:
        logger.warning("Warning: Owner has 0 Sepolia ETH for gas (only matters if sending a tx).")

    usdc_balance = fetch_usdc_balance(OWNER)
    if usdc_balance < value_smallest:
        logger.warning(f"Warning: Insufficient USDC. Have {(usdc_balance/1e6):.2f}, need {(value_smallest/1e6):.2f}")

    nonce = fetch_nonce(OWNER)

    # current = datetime.now()
    # updates = current + timedelta(seconds=expiry)     
    # deadline = int(updates.timestamp())
    # logger.info(f"deadline: {deadline}")
    
    # ---------- Build EIP-712 typed data ----------
    domain = {
        "name": USDC_NAME,
        "version": USDC_VERSION,
        "chainId": CHAIN_ID,  # Ensure this is an integer
        "verifyingContract": USDC_ADDRESS,
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