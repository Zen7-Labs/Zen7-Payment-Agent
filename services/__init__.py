from dotenv import load_dotenv
import os

load_dotenv()

CHAIN_SELECTION = os.getenv("CHAIN_SELECTION")

CHAIN_ID = None
CHAIN_ID_HEX = None
CHAIN_RPC_URL = None
USDC_ADDRESS = None

ACTIVE_TOKEN = os.getenv("ACTIVE_TOKEN", "USDC")

SEPOLIA_DAI_ADDRESS = os.getenv("SEPOLIA_DAI_ADDRESS")

from .constants import ErrorCode

if CHAIN_SELECTION == "SEPOLIA":
    CHAIN_ID = os.getenv("SEPOLIA_CHAIN_ID")
    CHAIN_ID_HEX = os.getenv("SEPOLIA_CHAIN_ID_HEX")
    CHAIN_RPC_URL = os.getenv("SEPOLIA_CHAIN_RPC_URL")
    USDC_ADDRESS = os.getenv("SEPOLIA_USDC_ADDRESS")
elif CHAIN_SELECTION == "BASE_SEPOLIA":
    CHAIN_ID = os.getenv("BASE_SEPOLIA_CHAIN_ID")
    CHAIN_ID_HEX = os.getenv("BASE_SEPOLIA_CHAIN_ID_HEX")
    CHAIN_RPC_URL = os.getenv("BASE_SEPOLIA_CHAIN_RPC_URL")
    USDC_ADDRESS = os.getenv("BASE_SEPOLIA_USDC_ADDRESS")