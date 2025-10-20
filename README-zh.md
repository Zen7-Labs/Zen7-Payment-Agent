# Zen7 Payment Agent

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.13+-green.svg)](https://python.org)
[![Built with uv](https://img.shields.io/badge/Built%20with-uv-purple.svg)](https://github.com/astral-sh/uv)

Zen7 Payment Agent是DePA（Decentralized Payment Agent）的首个实践项目，开创了下一代智能支付基础设施。它不仅全面实现了DePA的核心功能，更在智能体电商领域成功部署了创新应用案例。

作为DePA生态下的首个实践项目，Zen7实现了多项关键特性：自动化的智能体间的加密支付、“授权免密”机制，以及大语言模型驱动的意图识别与交互。

Zen7 Payment Agent 采用多Agent协同架构，支持A2A以及MCP协议，支持支付资金托管与非托管型两种模式。面向AI Agent与Dapp原生应用提供多链、多币种、多钱包、高频、免密以及免gas费的完美支付解决方案。

<div align="left">
  <img src="/docs/assets/architecture.png" alt="Zen7 Payment Agent Architecture" width="800">
</div>

## 仓库导航指引（Navigating the Repository）

本仓库包含了 Zen7 Payment Agent 的完整实现，展示了基于 Zen7 Payment Agent（去中心化支付代理）协议的核心组件和架构设计。

### 核心目录结构

项目的核心实现位于以下关键目录：

**[`host_agent`](https://github.com/Zen7-Labs/Zen7-Payment-Agent/tree/main/host_agent)** 目录为多代理协同架构的核心实现，主代理（`host agent`）使用 `gemini-2.0-flash-lite` 模型作为核心协调器，负责查询理解、状态管理和响应协调。子代理系统（`sub_agents/`）包含三个专门的代理：`payer_agent` 负责支付方的订单创建、EIP-712签名生成和钱包余额验证；`settlement_agent` 专注于结算流程，确认支付详情、执行链上交易并监控交易状态；`payee_agent` 则处理收款方相关业务，接收结算通知、确认订单创建并通知支付完成。

**[`a2a_server`](https://github.com/Zen7-Labs/Zen7-Payment-Agent/tree/main/a2a_server) & [`mcp_server`](https://github.com/Zen7-Labs/Zen7-Payment-Agent/tree/main/mcp_server)** - 协议适配层的实现，提供多样化的接入方式。`a2a_server` 实现了 Google 的 Agent-to-Agent 协议，使用 `A2AStarletteApplication` 框架，通过 `AgentCard` 暴露代理能力，支持代理间协作通信，默认运行在 10000 端口。`mcp_server` 基于 `FastMCP` 框架实现 Model Context Protocol 集成，将支付功能封装为工具 API，提供 `proceed_payment_and_settlement_detail_info` 核心工具，支持 SSE（服务器发送事件）传输，默认运行在 8015 端口。

**[`services`](https://github.com/Zen7-Labs/Zen7-Payment-Agent/tree/main/services)** - 完整的区块链服务实现。签名服务（`execute_sign.py`）提供 EIP-712 类型化数据签名功能，支持 USDC 和 DAI 的许可签名；转账处理器分为 `custodial/` 托管模式（后端管理钱包以简化用户体验）和 `non_custodial/` 非托管模式（用户控制私钥以增强安全性）；常量配置（`constants.py`）集中管理区块链网络配置、合约地址和链 ID；许可执行（`execute_permit.py`）负责 ERC-20 代币的授权和许可执行。

### 配套的控制台演示应用

配套的控制台演示应用位于独立的 [Zen7-Console-Demo](https://github.com/Zen7-Labs/Zen7-Console-Demo) 仓库，为用户提供完整的交互界面和支付流程演示，让开发者能够直观体验整个支付系统的工作流程。包含两个A2A, MCP 两个客户端在电商场景下的完整支付流程。
   - [购物代理客户端](https://github.com/Zen7-Labs/Zen7-Console-Demo/tree/main/shopping_agent)展示了如何在电商场景中使用支付代理服务，实现商品浏览、下单和支付等功能。


### 技术栈与兼容性

**支持的区块链网络**：Ethereum Sepolia、Base Sepolia 测试网  
**兼容的代币标准**：USDC（版本 2）、DAI（版本 1）  
**签名标准**：EIP-712 类型化数据签名  
**钱包集成**：MetaMask，Coinbase 钱包  

这种设计为开发者提供了灵活的测试环境，同时确保了与主流钱包和区块链网络的良好兼容性。


## 快速开始
- [快速开始指南](docs/quick_start.md) - 详细的项目设置和运行指南
### 环境准备
- [基础环境安装](docs/install-uv-python-git.md) - 安装 Python 3.13+、uv 工具和 Git
- [区块链环境配置](docs/blockchain_environment_setup.md) - 区块链环境设置和测试钱包准备
### 开发指南
- [开发指南](docs/development_guide.md) - 开发者扩展和定制指南

## 安全注意事项

- **私钥安全**: 测试环境中的私钥仅用于开发，生产环境请使用安全的密钥管理方案
- **网络环境**: 当前支持测试网，生产环境需要相应的主网配置
- **代币管理**: 确保测试钱包有足够的测试代币进行交易
- **API安全**: 生产环境中请配置适当的身份验证和授权机制

## 支持

如果您遇到问题或需要帮助，请：

- 查看 [文档目录](docs/) 中的相关指南
- 在 GitHub Issues 中提交问题
- 联系开发团队

## 关于Zen7 Labs

Zen7 Labs 致力于构建下一代去中心化支付基础设施，专注于为 Agentic Commerce 提供创新的支付解决方案。通过 AI 代理技术简化区块链支付体验，我们正在开创智能体经济时代的支付新范式，让智能体间的商业交互变得更加高效、安全和智能。

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
