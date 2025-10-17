# Zen7 Payment Agent 快速入门

本指南将带你使用 **$\text{uv}$** 配置 Python 开发环境，并运行 **Zen7 Payment Service** 应用。

-----

## 环境准备 🔧

在开始使用 Zen7 Payment Agent 之前，请确保你的开发环境已经安装以下必要工具：

### 基础开发工具
- **Python 3.11+** - 项目所需的运行时环境
- **Git** - 用于版本控制和克隆代码仓库
- **uv** - 高性能的 Python 包管理器

### 区块链环境要求
- **区块链 RPC 服务** - 访问以太坊/Base Sepolia 测试网的入口
- **测试钱包** - 用于测试的 MetaMask 或兼容钱包
- **测试代币** - 用于交易的 USDC 测试网代币
- **私钥** - 付款账户与结算账户的私钥

#### 安装指南：

📖 **[完整环境安装指南](install-uv-python-git.md)**
- 提供 macOS、Windows、Linux 平台上 Python、Git 与 uv 的详细安装步骤

🔗 **[区块链环境搭建指南](blockchain_environment_setup.md)**
- 包含 RPC 配置、钱包设置和测试网代币获取等详细说明

这些指南覆盖所有支持平台的完整安装流程与常见问题排查方法。

-----

## 第 1 部分：工具初始安装 🛠️

首先安装高性能的包管理器 **$\text{uv}$**。

### 1.1 安装 $\text{uv}$

使用独立安装脚本是获取 $\text{uv}$ 的最快方式。

**Linux/macOS：**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows（PowerShell）：**

```bash
irm https://astral.sh/uv/install.ps1 | iex
```

-----

## 第 2 部分：项目初始化与依赖安装 📂

本节将完成仓库克隆、隔离环境创建与依赖安装。

### 2.1 克隆示例仓库

克隆快速入门仓库：

```bash
git clone https://github.com/Zen7-Labs/Zen7-Payment-Agent.git
```

### 2.2 切换至项目目录

进入刚刚克隆的项目文件夹：

```bash
cd Zen7-Payment-Agent
```

### 2.3 创建并激活虚拟环境

在项目目录 **内部** 创建隔离环境并激活。

1.  **创建环境：**

    ```bash
    uv venv
    ```

    （该命令会生成名为 **`.venv`** 的环境文件夹。）

2.  **激活环境：**

      * **Linux/macOS：**
        ```bash
        source .venv/bin/activate
        ```
      * **Windows（命令提示符）：**
        ```bash
        .venv\Scripts\activate
        ```
      * **Windows（PowerShell）：**
        ```powershell
        .venv\Scripts\Activate.ps1
        ```

> **注意：** 命令行提示符前应出现 **`(venv)`**，表示虚拟环境已激活。

### 2.4 使用 $\text{uv sync}$ 安装依赖

在已激活的环境中运行 **$\text{uv sync}$**，安装 `pyproject.toml` 中声明的所有依赖。

```bash
(venv) $ uv sync
```

### 2.5 配置 API 密钥与服务器参数

在项目根目录创建并配置 **`.env`** 文件，安全地填入密钥与服务器信息：

> **🔗 区块链配置前置：** 在编辑 `.env` 之前，请先完成区块链环境配置。参见 **[区块链环境搭建指南](blockchain_environment_setup.md)** 获取 RPC 地址、私钥与测试网代币。
  - 将 .env.example 重命名为 .env
  - 更新 **`.env`** 文件（替换占位内容）：
    ```dotenv
    # .env
    # AI Service Configuration
    GOOGLE_GENAI_USE_VERTEXAI=FALSE
    GOOGLE_API_KEY=<PLEASE_FILL_YOUR_API_KEY>

    # Blockchain Account Configuration
    PAYER_PRIVATE_KEY=<PLEASE_FILL_THE_PAYER_PRIVATE_KEY>
    SETTLEMENT_PRIVATE_KEY=<PLEASE_FILL_THE_SETTLEMENT_PRIVATE_KEY>

    # Server Configuration  
    ZEN7_PAYMENT_SERVER_HOST=localhost
    ZEN7_PAYMENT_SERVER_PORT=8080

    # Blockchain Network Selection (SEPOLIA or BASE_SEPOLIA)
    CHAIN_SELECTION=SEPOLIA

    # Ethereum Sepolia Testnet Configuration
    SEPOLIA_CHAIN_ID_HEX=0xaa36a7
    SEPOLIA_CHAIN_RPC_URL=https://sepolia.infura.io/v3/<YOUR_INFURA_PROJECT_ID>
    SEPOLIA_USDC_ADDRESS=0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238

    # Base Sepolia Testnet Configuration (Alternative)
    BASE_SEPOLIA_CHAIN_ID_HEX=0x14a34
    BASE_SEPOLIA_CHAIN_RPC_URL=https://sepolia.base.org
    BASE_SEPOLIA_USDC_ADDRESS=0x036CbD53842c5426634e7929541eC2318f3dCF7e

    # Notification Service
    NOTIFICATION_URL=<NOTIFICATION_URL>
    ```

#### 配置项说明：

**🤖 AI 服务配置：**
- `GOOGLE_API_KEY`：Zen7 Payment Agent 需要的 Gemini API Key，可通过 [Gemini API Keys](https://ai.google.dev/gemini-api/docs/api-key) 申请。

**🔑 区块链账户密钥：**
- `PAYER_PRIVATE_KEY`：用于发起支付交易的账户私钥
- `SETTLEMENT_PRIVATE_KEY`：用于处理结算的账户私钥

**🌐 网络选择：**
- `CHAIN_SELECTION`：可选 `SEPOLIA`（推荐）或 `BASE_SEPOLIA`

**🔗 RPC 配置：**
- 将 `<YOUR_INFURA_PROJECT_ID>` 替换为实际的 Infura 项目 ID
- 若使用其他 RPC 服务商，请相应调整 URL

**💰 代币合约地址：**
- 默认提供了两个测试网中的 USDC 合约地址
  
> 🔔 注意：将 <NOTIFICATION_URL> 替换为客户端用于接收结算回执的实际回调地址。
- 通知服务的响应示例：
```json
{
  "status": true,
  "message": "<Your settlement confirmation info>"
}
```
-----
## 第 3 部分：运行服务
在 Linux/macOS 环境下使用 `run.sh`（见第 3.1 节），在 Windows PowerShell 中使用 `run.ps1`（见第 3.2 节）启动 Zen7 Payment Service。

### 第 3.1 节：使用 `run.sh` 运行服务 🚀

执行 `run.sh`，并在命令后指定要运行的 **协议**（`a2a` 或 `mcp`）以及必需的 **`--host`** 与 **`--port`** 参数。

### 3.1.1 查看可用命令（帮助标志）

查看当前的命令用法：

```bash
(venv) $ ./run.sh --help
```

### 3.1.2 启动特定支付流程（启动 Zen7 服务）

在 `start` 后直接跟随协议名称（`a2a`、`mcp` 或 `agent`），即可启动对应支付流程的服务。

#### 方案 1：作为 Model Context Protocol 服务（`mcp`）

该命令以 **MCP（Model Context Protocol）服务模式**启动 **Zen7 Payment Service**。

```bash
(venv) $ ./run.sh start mcp --host 127.0.0.1 --port 8015
```

**作用：** 在指定主机和端口启动 Zen7 Payment Service，提供符合 Model Context Protocol 的服务。

#### 方案 2：作为 Google Agent2Agent Protocol 服务（`a2a`）

该命令以 **Google A2A（Agent2Agent Protocol）服务模式**启动 **Zen7 Payment Service**。

```bash
(venv) $ ./run.sh start a2a --host 127.0.0.1 --port 10000
```

**作用：** 在指定主机和端口启动 Zen7 Payment Service，提供适用于 Google Agent2Agent Protocol 的服务。

**注意：** 启动服务时必须同时指定 **`--host`** 与 **`--port`**。

-----

## 第 3.2 节：使用 `run.ps1` 运行服务（Windows）🪟

对于 **Windows PowerShell** 用户，可使用 `run.ps1` 脚本，它与 `run.sh` 提供相同功能，但使用 PowerShell 语法。

### 3.2.1 查看可用命令（帮助标志）

查看当前的命令用法：

```powershell
(venv) PS> .\run.ps1 -Help
```

### 3.2.2 启动特定支付流程（启动 Zen7 服务）

将协议名称（`a2a` 或 `mcp`）作为第一个参数，并提供 **`-Hostname`** 与 **`-Port`**。

#### 方案 1：作为 Model Context Protocol 服务（`mcp`）

该命令以 **MCP（Model Context Protocol）服务模式**启动 **Zen7 Payment Service**。

```powershell
(venv) PS> .\run.ps1 mcp -Hostname 127.0.0.1 -Port 8015
```

**作用：** 在指定主机和端口启动 Zen7 Payment Service，提供符合 Model Context Protocol 的服务。

#### 方案 2：作为 Google Agent2Agent Protocol 服务（`a2a`）

该命令以 **Google A2A（Agent2Agent Protocol）服务模式**启动 **Zen7 Payment Service**。

```powershell
(venv) PS> .\run.ps1 a2a -Hostname 127.0.0.1 -Port 10000
```

**作用：** 在指定主机和端口启动 Zen7 Payment Service，提供适用于 Google Agent2Agent Protocol 的服务。

### 3.2.3 查看特定选项帮助

也可以查看各协议的详细帮助信息：

```powershell
(venv) PS> .\run.ps1 a2a -Help
(venv) PS> .\run.ps1 mcp -Help
```

**注意：** 
- 启动服务时必须同时指定 **`-Hostname`** 与 **`-Port`**。
- PowerShell 脚本使用命名参数（例如 `-Hostname`、`-Port`），而不是命令行标志（例如 `--host`、`--port`）。

-----

## 引用

如果 Zen7 Payment Agent 对你的研究或项目有所帮助，请按如下格式引用：

```bibtex
@misc{zen7paymentagent,
  author = {Zen7 Labs},
  title = {Zen7 Payment Agent: AI-Powered Blockchain Payment Service},
  year = {2025},
  publisher = {GitHub},
  url = {https://github.com/Zen7-Labs/Zen7-Payment-Agent}
}
```

## 许可证

Apache License Version 2.0
