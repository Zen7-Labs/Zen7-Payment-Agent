# Quick start for Zen7 Payment Agent

This guide walks you through setting up your Python development environment with **$\text{uv}$** and running the **Zen7 Payment Service** application.

-----

## Environment Setup 🔧

Before getting started with Zen7 Payment Agent, ensure your development environment has the following required tools installed:

### Basic Development Tools
- **Python 3.11+** - Base runtime environment for the project
- **Git** - Version control and code repository cloning
- **uv** - High-performance Python package manager

### Blockchain Environment Requirements
- **Blockchain RPC Service** - Ethereum/Base Sepolia testnet access
- **Test Wallet** - MetaMask or compatible wallet for testing
- **Test Tokens** - USDC testnet tokens for transactions
- **Private Keys** - Payer and Settlement account private keys

#### Installation Guides:

📖 **[Complete Environment Installation Guide](install-uv-python-git.md)**
- Step-by-step installation instructions for Python, Git, and uv on macOS, Windows, and Linux

🔗 **[Blockchain Environment Setup Guide](blockchain_environment_setup.md)**
- Detailed blockchain configuration including RPC setup, wallet configuration, and testnet token acquisition

These guides contain comprehensive installation instructions and troubleshooting methods for all supported platforms.

-----

## Part 1: Initial Tool Setup 🛠️

First, install the high-performance package manager, **$\text{uv}$**.

### 1.1 Install $\text{uv}$

The standalone installer is the fastest way to get $\text{uv}$.

**For Linux/macOS:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**For Windows (using PowerShell):**

```bash
irm https://astral.sh/uv/install.ps1 | iex
```

-----

## Part 2: Project Setup and Dependencies 📂

This section clones the project, creates the isolated environment, and installs dependencies.

### 2.1 Clone the Sample Repository

Clone the quickstart repository.

```bash
git clone https://github.com/Zen7-Labs/Zen7-Payment-Agent.git
```

### 2.2 Navigate to the Project

Change your working directory into the newly cloned project folder.

```bash
cd Zen7-Payment-Agent
```

### 2.3 Create and Activate a Virtual Environment

Create the isolated environment **inside** the project folder and activate it.

1.  **Create the environment:**

    ```bash
    uv venv
    ```

    (This creates a new environment folder named **`.venv`**.)

2.  **Activate the environment:**

      * **Linux/macOS:**
        ```bash
        source .venv/bin/activate
        ```
      * **Windows (Command Prompt):**
        ```bash
        .venv\Scripts\activate
        ```
      * **Windows (PowerShell):**
        ```powershell
        .venv\Scripts\Activate.ps1
        ```

> **Note:** Your command line prompt should now show **`(venv)`** at the beginning.

### 2.4 Install Dependencies with $\text{uv sync}$

Use **$\text{uv sync}$** to install all required packages listed in the project's **`pyproject.toml`** file into the active environment.

```bash
(venv) $ uv sync
```

### 2.5 Configure API Keys and Server Settings

Securely add your keys and server configuration corresponding to a **`.env`** file in the project root:

> **🔗 Blockchain Setup Required:** Before configuring the `.env` file, ensure you have completed the blockchain environment setup. Refer to the **[Blockchain Environment Setup Guide](blockchain_environment_setup.md)** for detailed instructions on obtaining RPC URLs, private keys, and testnet tokens.

  - Update the file named **`.env`** (replace the placeholder values):
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

#### Configuration Parameters Explained:

**🤖 AI Service Configuration:**
- `GOOGLE_API_KEY`: Gemini API key required by the Zen7 Payment Agent. Request one via [Gemini API Keys](https://ai.google.dev/gemini-api/docs/api-key).

**🔑 Blockchain Account Keys:**
- `PAYER_PRIVATE_KEY`: Private key for the account that initiates payments
- `SETTLEMENT_PRIVATE_KEY`: Private key for the account that handles settlement operations

**🌐 Network Selection:**
- `CHAIN_SELECTION`: Choose between `SEPOLIA` (recommended) or `BASE_SEPOLIA`

**🔗 RPC Configuration:**
- Replace `<YOUR_INFURA_PROJECT_ID>` with your actual Infura project ID
- For other RPC providers, update the URLs accordingly

**💰 Token Addresses:**
- Pre-configured USDC testnet contract addresses for both networks
  
> 🔔 Note: Replace <NOTIFICATION_URL> with the actual endpoint of your client application configured to receive the settlement confirmation.
- The notification service provides a response like:
```json
{
  "status": true,
  "message": "<Your settlement confirmation info>"
}
```
-----
## Part 3: Running the Service
Use `run.sh` on Linux/macOS environments (see Part 3.1) and `run.ps1` on Windows PowerShell (see Part 3.2) to start the Zen7 Payment Service.

### Part 3.1: Running the Service with `run.sh` 🚀

To run the Zen7 Payment Service, execute `run.sh` followed by the desired **protocol** (`a2a` or `mcp`) and the required **`--host`** and **`--port`** options.

### 3.1.1 View Available Commands (Help Flag)

Check the help flag for current usage:

```bash
(venv) $ ./run.sh --help
```

### 3.1.2 Execute Specific Payment Flows (Start Zen7 Service)

Use the protocol name (`a2a`, `mcp`, or `agent`) directly after `start` to launch the server with the desired payment flow.

#### Option 1: Start as Model Context Protocol Service Provision (`mcp`)

This option starts the **Zen7 Payment Service** for **MCP (Model Context Protocol) service provision**.

```bash
(venv) $ ./run.sh start mcp --host 127.0.0.1 --port 8015
```

**Function:** Starts the Zen7 Payment Service at the specified host and port, providing services governed by the Model Context Protocol (MCP).

#### Option 2: Start as Google Agent2Agent Protocol Service Provision (`a2a`)

This option starts the **Zen7 Payment Service** for **Google A2A (Agent2Agent Protocol) service provision**.

```bash
(venv) $ ./run.sh start a2a --host 127.0.0.1 --port 10000
```

**Function:** Starts the Zen7 Payment Service at the specified host and port, providing services for the Google Agent2Agent Protocol.

**Note:** Always specify a **`--host`** and **`--port`** for the server to start successfully.

-----

## Part 3.2: Running the Service with `run.ps1` (Windows) 🪟

For **Windows PowerShell** users, use the `run.ps1` script as an equivalent to `run.sh`. This script provides the same functionality with PowerShell-specific syntax.

### 3.2.1 View Available Commands (Help Flag)

Check the help flag for current usage:

```powershell
(venv) PS> .\run.ps1 -Help
```

### 3.2.2 Execute Specific Payment Flows (Start Zen7 Service)

Use the protocol name (`a2a` or `mcp`) as the first parameter followed by the **`-Hostname`** and **`-Port`** parameters.

#### Option 1: Start as Model Context Protocol Service Provision (`mcp`)

This option starts the **Zen7 Payment Service** for **MCP (Model Context Protocol) service provision**.

```powershell
(venv) PS> .\run.ps1 mcp -Hostname 127.0.0.1 -Port 8015
```

**Function:** Starts the Zen7 Payment Service at the specified host and port, providing services governed by the Model Context Protocol (MCP).

#### Option 2: Start as Google Agent2Agent Protocol Service Provision (`a2a`)

This option starts the **Zen7 Payment Service** for **Google A2A (Agent2Agent Protocol) service provision**.

```powershell
(venv) PS> .\run.ps1 a2a -Hostname 127.0.0.1 -Port 10000
```

**Function:** Starts the Zen7 Payment Service at the specified host and port, providing services for the Google Agent2Agent Protocol.

### 3.2.3 Get Option-Specific Help

You can also view detailed help information for each specific option:

```powershell
(venv) PS> .\run.ps1 a2a -Help
(venv) PS> .\run.ps1 mcp -Help
```

**Note:** 
- Always specify both **`-Hostname`** and **`-Port`** parameters for the server to start successfully.
- The PowerShell script uses named parameters (e.g., `-Hostname`, `-Port`) instead of flags (e.g., `--host`, `--port`).

-----

## Citation

If you find Zen7 Payment Agent helpful in your research or project, please cite it as:

```bibtex
@misc{zen7paymentagent,
  author = {Zen7 Labs},
  title = {Zen7 Payment Agent: AI-Powered Blockchain Payment Service},
  year = {2025},
  publisher = {GitHub},
  url = {https://github.com/Zen7-Labs/Zen7-Payment-Agent}
}
```

## License

Apache License Version 2.0