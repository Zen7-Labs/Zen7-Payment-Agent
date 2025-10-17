# Zen7 Payment Agent Blockchain Environment Setup Guide

This guide will walk you through the blockchain environment configuration for the Zen7 Payment Agent project, ensuring that Permit, Transfer, Settlement, and other functions operate correctly.

## 📋 Table of Contents

1. [Network Selection and RPC Configuration](#1-network-selection-and-rpc-configuration)
2. [Blockchain Service Provider Registration](#2-blockchain-service-provider-registration)
3. [Wallet Configuration and Account Management](#3-wallet-configuration-and-account-management)
4. [Test Token Acquisition](#4-test-token-acquisition)
5. [Environment Variables Configuration](#5-environment-variables-configuration)
6. [Configuration Verification](#6-configuration-verification)
7. [Common Issues Troubleshooting](#7-common-issues-troubleshooting)

---

## 1. Network Selection and RPC Configuration

### 1.1 Supported Test Networks

Zen7 Payment Agent currently supports the following test networks:

| Network Name | Chain ID (Hex) | Chain ID (Dec) | Recommendation Level |
|---------|----------------|----------------|----------|
| **Ethereum Sepolia** | `0xaa36a7` | `11155111` | ⭐⭐⭐ Highly Recommended |
| **Base Sepolia** | `0x14a34` | `84532` | ⭐⭐ Alternative |

> **Recommended: Ethereum Sepolia** - More mature and stable, easy to obtain test tokens, comprehensive documentation.

### 1.2 Network Features Comparison

| Feature | Ethereum Sepolia | Base Sepolia |
|-----|-----------------|--------------|
| Gas Fees | Higher | Lower |
| Network Stability | Very High | High |
| Test Token Availability | Easy | Moderate |
| Block Confirmation Time | ~12 seconds | ~2 seconds |
| Community Support | Best | Good |

---

## 2. Blockchain Service Provider Registration

### 2.1 Recommended RPC Service Providers

Choosing a reliable RPC service provider is crucial for ensuring stable application operation:

#### 🥇 Infura (Recommended)
- **Website**: https://infura.io/
- **Features**: High stability, generous free tier
- **Free Tier**: 100,000 requests/day
- **Registration Steps**:
  1. Register for an Infura account
  2. Create a new project
  3. Select Ethereum network
  4. Obtain Project ID

#### 🥈 Alchemy
- **Website**: https://www.alchemy.com/
- **Features**: Excellent performance, rich toolset
- **Free Tier**: 300M compute units/month
- **Registration Steps**:
  1. Register for an Alchemy account
  2. Create a new application
  3. Select Sepolia testnet
  4. Obtain API Key

#### 🥉 Coinbase Cloud
- **Website**: https://www.coinbase.com/cloud
- **Features**: Enterprise-grade service
- **Free Tier**: Limited
- **Registration Steps**:
  1. Register for a Coinbase Cloud account
  2. Create API key
  3. Configure network access permissions

### 2.2 RPC URL Format

Based on your chosen service provider, the RPC URL format is as follows:

```bash
# Infura
https://sepolia.infura.io/v3/YOUR_PROJECT_ID

# Alchemy  
https://eth-sepolia.g.alchemy.com/v2/YOUR_API_KEY

# Coinbase Cloud
https://sepolia.ethereum.coinbasecloud.net/YOUR_API_KEY
```

---

## 3. Wallet Configuration and Account Management

### 3.1 Wallet Installation and Setup

#### Recommended Wallets:
- **MetaMask**: https://metamask.io/
- **Coinbase Wallet**: https://wallet.coinbase.com/

#### Security Recommendations:
1. **Create dedicated test accounts**: Use fresh mnemonic phrases to avoid mixing funds
2. **Backup mnemonic phrases**: Securely save mnemonic phrases and private keys
3. **Network isolation**: Ensure test networks are separated from mainnet

### 3.2 Adding Sepolia Testnet

Manually add network in MetaMask:

```json
{
  "Network Name": "Sepolia",
  "New RPC URL": "https://sepolia.infura.io/v3/YOUR_PROJECT_ID",
  "Chain ID": "11155111",
  "Currency Symbol": "ETH",
  "Block Explorer URL": "https://sepolia.etherscan.io"
}
```

### 3.3 Generating Test Accounts

The project requires the following account types:

| Account Type | Purpose | Environment Variable |
|---------|------|----------|
| **Payer Account** | Sign Permit, authorize transfers | `PAYER_PRIVATE_KEY` |
| **Settlement Account** | Execute final transfer operations | `SETTLEMENT_PRIVATE_KEY` |
| **Payee Account** | Receive funds | Specified in transaction |

---

## 4. Test Token Acquisition

### 4.1 Obtaining Test ETH (Gas Fees)

#### Ethereum Sepolia Test ETH:
- **SepoliaFaucet**: https://sepoliafaucet.com/
- **Alchemy Faucet**: https://sepoliafaucet.com/
- **Infura Faucet**: https://www.infura.io/faucet/sepolia

#### Steps:
1. Visit the faucet website
2. Connect MetaMask wallet
3. Confirm network is Sepolia
4. Click to request test ETH
5. Wait for transfer confirmation (usually 1-2 minutes)

### 4.2 Obtaining Test USDC

#### Circle USDC Test Token Faucet:
- **Official Faucet**: https://faucet.circle.com/
- **Contract Address**: `0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238`

#### Steps:
1. Visit Circle test faucet
2. Connect wallet and switch to Sepolia network
3. Request test USDC
4. Confirm token receipt

#### Manually Adding USDC Token:
If wallet doesn't automatically display USDC, add manually:
```
Token Contract Address: 0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238
Token Symbol: USDC
Decimals: 6
```

---

## 5. Environment Variables Configuration

### 5.1 Creating .env File

Create a `.env` file in the project root directory:

```bash
# Copy example configuration file
cp .env.example .env
```

### 5.2 Complete .env Configuration Example

```dotenv
# =============================================================================
# Zen7 Payment Agent Environment Configuration
# =============================================================================

# Google AI Configuration
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=your_gemini_api_key_here

# =============================================================================
# Blockchain Network Configuration
# =============================================================================

# Network Selection (SEPOLIA or BASE_SEPOLIA)
CHAIN_SELECTION=SEPOLIA

# Ethereum Sepolia Configuration
SEPOLIA_CHAIN_ID_HEX=0xaa36a7
SEPOLIA_CHAIN_RPC_URL=https://sepolia.infura.io/v3/YOUR_INFURA_PROJECT_ID
SEPOLIA_USDC_ADDRESS=0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238

# Base Sepolia Configuration (Alternative)
BASE_SEPOLIA_CHAIN_ID_HEX=0x14a34
BASE_SEPOLIA_CHAIN_RPC_URL=https://sepolia.base.org
BASE_SEPOLIA_USDC_ADDRESS=0x036CbD53842c5426634e7929541eC2318f3dCF7e

# =============================================================================
# Account Private Key Configuration (⚠️ For Test Networks Only)
# =============================================================================

# Payer Private Key - Used for signing Permit authorization
PAYER_PRIVATE_KEY=0x0000000000000000000000000000000000000000000000000000000000000000

# Settlement Private Key - Used for executing final transfer
SETTLEMENT_PRIVATE_KEY=0x0000000000000000000000000000000000000000000000000000000000000000

# Alternative Private Key Configuration Name
OWNER_PK=0x0000000000000000000000000000000000000000000000000000000000000000

# =============================================================================
# Server Configuration
# =============================================================================

# Local Server Configuration
ZEN7_PAYMENT_SERVER_HOST=localhost
ZEN7_PAYMENT_SERVER_PORT=8080

# Notification Callback URL
NOTIFICATION_URL=http://your-app.com/payment-notification

# =============================================================================
# Security Reminder
# =============================================================================
# ⚠️  Warning: The above private keys are examples only, replace with actual test account private keys
# ⚠️  Never use this configuration in production environment
# ⚠️  Ensure .env file is added to .gitignore
```

### 5.3 Configuration Verification Checklist

Before starting the application, please confirm the following configuration items:

- [ ] ✅ `GOOGLE_API_KEY` is set and valid
- [ ] ✅ `SEPOLIA_CHAIN_RPC_URL` contains a valid Project ID/API Key
- [ ] ✅ `PAYER_PRIVATE_KEY` is a 64-character hexadecimal string (without 0x prefix) or 66 characters (with 0x prefix)
- [ ] ✅ `SETTLEMENT_PRIVATE_KEY` format is correct
- [ ] ✅ Payer account has sufficient test ETH (for Gas)
- [ ] ✅ Payer account has sufficient test USDC (for transfer)
- [ ] ✅ Settlement account has sufficient test ETH (for executing transfer)

---

## 6. Configuration Verification

### 6.1 Environment Check Script

Use the project-provided script to check environment configuration:

```bash
# Check configuration
./run.ps1 --help

# Start test service
./run.ps1 a2a --host localhost --port 8080
```

### 6.2 Manual Verification Steps

#### Verify RPC Connection:
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  https://sepolia.infura.io/v3/YOUR_PROJECT_ID
```

#### Verify Account Balance:
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_getBalance","params":["YOUR_ACCOUNT_ADDRESS","latest"],"id":1}' \
  https://sepolia.infura.io/v3/YOUR_PROJECT_ID
```

#### Verify USDC Balance:
Visit Sepolia Etherscan: https://sepolia.etherscan.io/
Search for your account address and check the USDC token balance.

---

## 7. Common Issues Troubleshooting

### 7.1 RPC Connection Issues

**Problem**: RPC URL cannot connect
**Solution**:
1. Check if Project ID/API Key is correct
2. Confirm RPC service provider quota is not exhausted
3. Check network connection and firewall settings

### 7.2 Private Key Format Issues

**Problem**: Private key format error
**Solution**:
```python
# Correct format examples
PAYER_PRIVATE_KEY=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
# or
PAYER_PRIVATE_KEY=0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
```

### 7.3 Insufficient Gas Fees

**Problem**: Transaction failed, insufficient Gas
**Solution**:
1. Request more test ETH from faucet
2. Check current network congestion
3. Appropriately increase Gas Price

### 7.4 Insufficient USDC Token Balance

**Problem**: Permit signature succeeds but transfer fails
**Solution**:
1. Check payer account USDC balance
2. Confirm transfer amount does not exceed balance
3. Request test USDC again

### 7.5 Chain ID Mismatch

**Problem**: Signature verification failed
**Solution**:
1. Confirm wallet network settings are correct
2. Check `SEPOLIA_CHAIN_ID_HEX` configuration in `.env`
3. Re-switch wallet network

---

## 📞 Technical Support

If you encounter configuration issues, please:

1. Check project log files: `logs/errors.log` and `logs/server.log`
2. Refer to [Quick Start Guide](quick_start.md)
3. See [Deployment Guide](deployment_guide.md)
4. Submit an Issue to the project repository

---

## 🔗 Related Links

- **Ethereum Sepolia Explorer**: https://sepolia.etherscan.io/
- **Base Sepolia Explorer**: https://sepolia.basescan.org/
- **Infura Documentation**: https://docs.infura.io/
- **MetaMask Help**: https://support.metamask.io/
- **Circle USDC Documentation**: https://developers.circle.com/

---

> **Security Reminder**: All operations covered in this guide are for test network environments. In production environments, always follow best security practices and protect private keys and sensitive information.
