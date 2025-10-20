# Zen7 Payment Agent

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.13+-green.svg)](https://python.org)
[![Built with uv](https://img.shields.io/badge/Built%20with-uv-purple.svg)](https://github.com/astral-sh/uv)
[中文版本](README-zh.md)

Zen7 Payment Agent is the first practical implementation of DePA (Decentralized Payment Agent), pioneering the next generation of intelligent payment infrastructure. It not only fully implements the core functionalities of DePA but also successfully deploys innovative application cases in the agentic commerce domain.

As the first practical project in the DePA ecosystem, Zen7 implements several key features: automated encrypted payments between agents, a "permissionless authorization" mechanism, and LLM-driven intent recognition and interaction.

Zen7 Payment Agent adopts a multi-agent collaborative architecture, supporting both A2A and MCP protocols, as well as custodial and non-custodial payment models. It provides a comprehensive payment solution for AI Agents and native Dapp applications with multi-chain, multi-currency, multi-wallet support, high-frequency transactions, gasless operations, and passwordless authentication.

<div align="left">
  <img src="/docs/assets/architecture.png" alt="Zen7 Payment Agent Architecture" width="800">
</div>

## Navigating the Repository

This repository contains the complete implementation of Zen7 Payment Agent, showcasing the core components and architectural design based on the Zen7 Payment Agent (Decentralized Payment Agent) protocol.

### Core Directory Structure

The core implementation of the project is located in the following key directories:

**[`host_agent`](https://github.com/Zen7-Labs/Zen7-Payment-Agent/tree/main/host_agent)** - The core implementation of the multi-agent collaborative architecture. The host agent uses the `gemini-2.0-flash-lite` model as the core coordinator, responsible for query understanding, state management, and response coordination. The sub-agent system (`sub_agents/`) contains three specialized agents: `payer_agent` handles order creation for the payer, EIP-712 signature generation, and wallet balance verification; `settlement_agent` focuses on the settlement process, confirming payment details, executing on-chain transactions, and monitoring transaction status; `payee_agent` handles payee-related operations, receiving settlement notifications, confirming order creation, and notifying payment completion.

**[`a2a_server`](https://github.com/Zen7-Labs/Zen7-Payment-Agent/tree/main/a2a_server) & [`mcp_server`](https://github.com/Zen7-Labs/Zen7-Payment-Agent/tree/main/mcp_server)** - Protocol adaptation layer implementation, providing diverse integration methods. `a2a_server` implements Google's Agent-to-Agent protocol using the `A2AStarletteApplication` framework, exposing agent capabilities through `AgentCard`, supporting inter-agent collaborative communication, and running on port 10000 by default. `mcp_server` implements Model Context Protocol integration based on the `FastMCP` framework, encapsulating payment functionality as tool APIs, providing the core `proceed_payment_and_settlement_detail_info` tool, supporting SSE (Server-Sent Events) transport, and running on port 8015 by default.

**[`services`](https://github.com/Zen7-Labs/Zen7-Payment-Agent/tree/main/services)** - Complete blockchain service implementation. The signature service (`execute_sign.py`) provides EIP-712 typed data signing functionality, supporting permit signatures for USDC and DAI; transfer handlers are divided into `custodial/` mode (backend manages wallets to simplify user experience) and `non_custodial/` mode (users control private keys for enhanced security); constant configuration (`constants.py`) centrally manages blockchain network configurations, contract addresses, and chain IDs; permit execution (`execute_permit.py`) handles ERC-20 token authorization and permit execution.

### Companion Console Demo Application

The companion console demo application is located in a separate [Zen7-Console-Demo](https://github.com/Zen7-Labs/Zen7-Console-Demo) repository, providing users with a complete interactive interface and payment flow demonstration, allowing developers to intuitively experience the workflow of the entire payment system. It includes complete payment flows for both A2A and MCP clients in e-commerce scenarios.
   - [Shopping Agent Client](https://github.com/Zen7-Labs/Zen7-Console-Demo/tree/main/shopping_agent) demonstrates how to use payment agent services in e-commerce scenarios, implementing features such as product browsing, ordering, and payment.


### Technology Stack and Compatibility

**Supported Blockchain Networks**: Ethereum Sepolia, Base Sepolia Testnets  
**Compatible Token Standards**: USDC (Version 2), DAI (Version 1)  
**Signature Standard**: EIP-712 Typed Data Signing  
**Wallet Integration**: MetaMask, Coinbase Wallet  

This design provides developers with a flexible testing environment while ensuring good compatibility with mainstream wallets and blockchain networks.


## Quick Start
- [Quick Start Guide](docs/quick_start.md) - Detailed project setup and running guide
### Environment Setup
- [Basic Environment Installation](docs/install-uv-python-git.md) - Install Python 3.13+, uv tool, and Git
- [Blockchain Environment Configuration](docs/blockchain_environment_setup.md) - Blockchain environment setup and test wallet preparation
### Development Guide
- [Development Guide](docs/development_guide.md) - Developer extension and customization guide

## Security Considerations

- **Private Key Security**: Private keys in the test environment are only for development; use secure key management solutions in production
- **Network Environment**: Currently supports testnets; production environments require corresponding mainnet configurations
- **Token Management**: Ensure test wallets have sufficient test tokens for transactions
- **API Security**: Configure appropriate authentication and authorization mechanisms in production environments

## Support

If you encounter issues or need help, please:

- Check the relevant guides in the [documentation directory](docs/)
- Submit issues on GitHub Issues
- Contact the development team

## About Zen7 Labs

Zen7 Labs is dedicated to building the next generation of decentralized payment infrastructure, focusing on providing innovative payment solutions for Agentic Commerce. By simplifying blockchain payment experiences through AI agent technology, we are pioneering a new paradigm of payments in the agent economy era, making commercial interactions between agents more efficient, secure, and intelligent.

---

## Citation

If you find Zen7 Payment Agent helpful in your research or project, please cite it as:

```bibtex
@misc{zen7paymentagent,
  author = {Zen7 Labs},
  title = {Zen7 Payment Agent: A Dedicated Payment Network for Every Intelligent Agent.},
  year = {2025},
  publisher = {GitHub},
  url = {https://github.com/Zen7-Labs/Zen7-Payment-Agent}
}
```

## License

Apache License Version 2.0
