# Zen7 支付代理区块链环境配置指南

本文档将带你完成 Zen7 Payment Agent 项目的区块链环境配置，确保 Permit、Transfer、Settlement 等功能能够顺利运行。

## 📋 目录

1. [网络选择与 RPC 配置](#1-网络选择与-rpc-配置)
2. [区块链服务商注册](#2-区块链服务商注册)
3. [钱包配置与账户管理](#3-钱包配置与账户管理)
4. [测试代币领取](#4-测试代币领取)
5. [环境变量配置](#5-环境变量配置)
6. [配置验证](#6-配置验证)
7. [常见问题排查](#7-常见问题排查)

---

## 1. 网络选择与 RPC 配置

### 1.1 支持的测试网络

Zen7 Payment Agent 目前支持以下测试网络：

| 网络名称 | Chain ID（十六进制） | Chain ID（十进制） | 推荐级别 |
|---------|--------------------|------------------|----------|
| **Ethereum Sepolia** | `0xaa36a7` | `11155111` | ⭐⭐⭐ 强烈推荐 |
| **Base Sepolia** | `0x14a34` | `84532` | ⭐⭐ 可选 |

> **推荐使用 Ethereum Sepolia**：网络成熟稳定、测试代币获取方便、文档资源丰富。

### 1.2 网络特性对比

| 特性 | Ethereum Sepolia | Base Sepolia |
|-----|-----------------|--------------|
| Gas 费用 | 较高 | 较低 |
| 网络稳定性 | 非常高 | 较高 |
| 测试代币获取 | 容易 | 一般 |
| 区块确认时间 | ~12 秒 | ~2 秒 |
| 社区支持 | 最好 | 良好 |

---

## 2. 区块链服务商注册

### 2.1 推荐的 RPC 服务提供商

选择可靠的 RPC 服务商对于保证应用稳定运行至关重要：

#### 🥇 Infura（推荐）
- **官网**：https://infura.io/
- **特点**：稳定性高，免费额度充足
- **免费额度**：100,000 次请求/天
- **注册流程**：
  1. 注册 Infura 账号
  2. 创建新项目
  3. 选择 Ethereum 网络
  4. 获取 Project ID

#### 🥈 Alchemy
- **官网**：https://www.alchemy.com/
- **特点**：性能优秀，工具链丰富
- **免费额度**：300M 计算单位/月
- **注册流程**：
  1. 注册 Alchemy 账号
  2. 创建新应用
  3. 选择 Sepolia 测试网
  4. 获取 API Key

#### 🥉 Coinbase Cloud
- **官网**：https://www.coinbase.com/cloud
- **特点**：企业级服务
- **免费额度**：有限
- **注册流程**：
  1. 注册 Coinbase Cloud 账号
  2. 创建 API Key
  3. 配置网络访问权限

### 2.2 RPC URL 格式

根据所选服务商填写 RPC URL，格式示例如下：

```bash
# Infura
https://sepolia.infura.io/v3/YOUR_PROJECT_ID

# Alchemy
https://eth-sepolia.g.alchemy.com/v2/YOUR_API_KEY

# Coinbase Cloud
https://sepolia.ethereum.coinbasecloud.net/YOUR_API_KEY
```

---

## 3. 钱包配置与账户管理

### 3.1 钱包安装与初始化

#### 推荐钱包：
- **MetaMask**：https://metamask.io/
- **Coinbase Wallet**：https://wallet.coinbase.com/

#### 安全建议：
1. **创建专用测试账号**：使用全新助记词，避免与生产环境混用
2. **妥善备份助记词**：安全保存助记词与私钥
3. **区分网络环境**：确保测试网与主网互不干扰

### 3.2 添加 Sepolia 测试网

在 MetaMask 中手动添加网络：

```json
{
  "Network Name": "Sepolia",
  "New RPC URL": "https://sepolia.infura.io/v3/YOUR_PROJECT_ID",
  "Chain ID": "11155111",
  "Currency Symbol": "ETH",
  "Block Explorer URL": "https://sepolia.etherscan.io"
}
```

### 3.3 创建测试账户

项目需要以下类型的账户：

| 账户类型 | 用途 | 对应环境变量 |
|---------|------|--------------|
| **付款人账户** | 签署 Permit、授权转账 | `PAYER_PRIVATE_KEY` |
| **结算账户** | 执行最终转账操作 | `SETTLEMENT_PRIVATE_KEY` |
| **收款人账户** | 接收资金 | 在交易内指定 |

---

## 4. 测试代币领取

### 4.1 领取测试 ETH（Gas 费用）

#### Ethereum Sepolia 测试 ETH：
- **SepoliaFaucet**：https://sepoliafaucet.com/
- **Alchemy Faucet**：https://sepoliafaucet.com/
- **Infura Faucet**：https://www.infura.io/faucet/sepolia

#### 操作步骤：
1. 打开水龙头网站
2. 连接 MetaMask 钱包
3. 确认当前网络为 Sepolia
4. 点击申请测试 ETH
5. 等待到账（通常 1-2 分钟）

### 4.2 领取测试 USDC

#### Circle USDC 测试代币水龙头：
- **官方水龙头**：https://faucet.circle.com/
- **合约地址**：`0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238`

#### 操作步骤：
1. 打开 Circle 测试水龙头
2. 连接钱包并切换至 Sepolia 网络
3. 申请测试 USDC
4. 确认代币到账

#### 手动添加 USDC 代币：
若钱包未自动显示 USDC，可手动添加：
```
Token Contract Address: 0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238
Token Symbol: USDC
Decimals: 6
```

---

## 5. 环境变量配置

### 5.1 创建 .env 文件

在项目根目录创建 `.env` 文件：

```bash
# 复制示例配置文件
cp .env.example .env
```

### 5.2 完整 .env 配置示例

```dotenv
# =============================================================================
# Zen7 Payment Agent 环境配置
# =============================================================================

# Google AI 配置
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=your_gemini_api_key_here

# =============================================================================
# 区块链网络配置
# =============================================================================

# 网络选择（SEPOLIA 或 BASE_SEPOLIA）
CHAIN_SELECTION=SEPOLIA

# Ethereum Sepolia 配置
SEPOLIA_CHAIN_ID_HEX=0xaa36a7
SEPOLIA_CHAIN_RPC_URL=https://sepolia.infura.io/v3/YOUR_INFURA_PROJECT_ID
SEPOLIA_USDC_ADDRESS=0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238

# Base Sepolia 配置（可选）
BASE_SEPOLIA_CHAIN_ID_HEX=0x14a34
BASE_SEPOLIA_CHAIN_RPC_URL=https://sepolia.base.org
BASE_SEPOLIA_USDC_ADDRESS=0x036CbD53842c5426634e7929541eC2318f3dCF7e

# =============================================================================
# 账户私钥配置（⚠️ 仅限测试网络）
# =============================================================================

# 付款人私钥——用于签署 Permit 授权
PAYER_PRIVATE_KEY=0x0000000000000000000000000000000000000000000000000000000000000000

# 结算账户私钥——用于执行最终转账
SETTLEMENT_PRIVATE_KEY=0x0000000000000000000000000000000000000000000000000000000000000000

# 备用私钥变量名
OWNER_PK=0x0000000000000000000000000000000000000000000000000000000000000000

# =============================================================================
# 服务端配置
# =============================================================================

# 本地服务端配置
ZEN7_PAYMENT_SERVER_HOST=localhost
ZEN7_PAYMENT_SERVER_PORT=8080

# 通知回调地址
NOTIFICATION_URL=http://your-app.com/payment-notification

# =============================================================================
# 安全提醒
# =============================================================================
# ⚠️ 以上私钥仅为示例，请替换为实际测试账户私钥
# ⚠️ 切勿在生产环境中使用该配置
# ⚠️ 确保 .env 文件已加入 .gitignore
```

### 5.3 配置检查清单

启动应用前，请逐项确认：

- [ ] ✅ `GOOGLE_API_KEY` 已配置且有效
- [ ] ✅ `SEPOLIA_CHAIN_RPC_URL` 已填写正确的 Project ID/API Key
- [ ] ✅ `PAYER_PRIVATE_KEY` 为 64 位十六进制字符串（无 0x 前缀）或 66 位（带 0x 前缀）
- [ ] ✅ `SETTLEMENT_PRIVATE_KEY` 格式正确
- [ ] ✅ 付款人账户拥有足够的测试 ETH（用于 Gas）
- [ ] ✅ 付款人账户拥有足够的测试 USDC（用于转账）
- [ ] ✅ 结算账户拥有足够的测试 ETH（用于执行转账）

---

## 6. 配置验证

### 6.1 环境检测脚本

使用项目提供的脚本检查环境配置：

```bash
# 查看脚本帮助
./run.ps1 --help

# 启动测试服务
./run.ps1 a2a --host localhost --port 8080
```

### 6.2 手动验证步骤

#### 验证 RPC 连接：
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  https://sepolia.infura.io/v3/YOUR_PROJECT_ID
```

#### 查询账户余额：
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_getBalance","params":["YOUR_ACCOUNT_ADDRESS","latest"],"id":1}' \
  https://sepolia.infura.io/v3/YOUR_PROJECT_ID
```

#### 查询 USDC 余额：
访问 Sepolia Etherscan：https://sepolia.etherscan.io/
搜索你的账户地址并查看 USDC 代币余额。

---

## 7. 常见问题排查

### 7.1 RPC 连接异常

**问题**：RPC URL 无法连接
**解决方案**：
1. 检查 Project ID/API Key 是否正确
2. 确认服务商额度未用尽
3. 检查本地网络与防火墙设置

### 7.2 私钥格式错误

**问题**：私钥格式无效
**解决方案**：
```python
# 正确格式示例
PAYER_PRIVATE_KEY=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
# 或
PAYER_PRIVATE_KEY=0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
```

### 7.3 Gas 费用不足

**问题**：交易失败，提示 Gas 不足
**解决方案**：
1. 重新申请测试 ETH
2. 检查当前网络是否拥堵
3. 适当提高 Gas Price

### 7.4 USDC 余额不足

**问题**：Permit 签名成功但转账失败
**解决方案**：
1. 核对付款人账户 USDC 余额
2. 确认转账金额未超过余额
3. 再次申请测试 USDC

### 7.5 Chain ID 不匹配

**问题**：签名验证失败
**解决方案**：
1. 检查钱包网络设置是否正确
2. 核对 `.env` 中 `SEPOLIA_CHAIN_ID_HEX` 配置
3. 在钱包中重新切换网络

---

## 📞 技术支持

如遇到配置问题，可按以下步骤排查：

1. 查看项目日志：`logs/errors.log`、`logs/server.log`
2. 参考 [快速开始指南](quick_start.md)
3. 阅读 [部署指南](deployment_guide.md)
4. 在项目仓库提交 Issue

---

## 🔗 相关链接

- **Ethereum Sepolia 区块浏览器**：https://sepolia.etherscan.io/
- **Base Sepolia 区块浏览器**：https://sepolia.basescan.org/
- **Infura 文档**：https://docs.infura.io/
- **MetaMask 帮助中心**：https://support.metamask.io/
- **Circle USDC 开发文档**：https://developers.circle.com/

---

> **安全提醒**：本文所述操作仅适用于测试网络。生产环境中务必遵循最佳安全实践，妥善保护私钥与敏感信息。
