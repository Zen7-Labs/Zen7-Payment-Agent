# uv / Python / Git 安装指南

> 适用人群：初次接触 Zen7 Payment Agent 项目，且尚未在本地配置 `uv`、Python 3.11+ 或 Git 的开发者。
>
> 目标：在 macOS、Windows 与 Linux 上完成上述三款工具的基础安装与验证。

---

## 1. 安装 Python 3.11+

### 1.1 macOS

1. 安装 Homebrew（如已安装可跳过）：
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
2. 安装 Python 3.11：
   ```bash
   brew install python@3.11
   ```
3. 校验版本：
   ```bash
   python3 --version
   ```
   若输出 `Python 3.11.x`，说明安装成功。

### 1.2 Windows

1. 前往 [Python 官方下载页](https://www.python.org/downloads/windows/)。
2. 下载 `Windows installer (64-bit)`，勾选 **Add Python to PATH**，按照安装向导完成安装。
3. 在 PowerShell 中校验版本：
   ```powershell
   python --version
   ```

### 1.3 Linux（以 Debian / Ubuntu 为例）

1. 更新软件索引并安装依赖：
   ```bash
   sudo apt update
   sudo apt install software-properties-common -y
   ```
2. 添加 deadsnakes PPA 并安装 Python 3.11：
   ```bash
   sudo add-apt-repository ppa:deadsnakes/ppa -y
   sudo apt update
   sudo apt install python3.11 python3.11-venv python3.11-dev -y
   ```
3. 校验版本：
   ```bash
   python3.11 --version
   ```

> 其他发行版请参考对应的软件包管理器（例如 Fedora 使用 `dnf install python3.11`）。

---

## 2. 安装 Git

### 2.1 macOS

1. 通过 Homebrew 安装：
   ```bash
   brew install git
   ```
2. 校验安装：
   ```bash
   git --version
   ```

### 2.2 Windows

1. 访问 [Git for Windows 官方页面](https://git-scm.com/download/win) 并下载最新安装包。
2. 安装过程中保持默认选项（包含 Git Bash 以及添加到 PATH）。
3. 在 PowerShell 或 Git Bash 中校验：
   ```powershell
   git --version
   ```

### 2.3 Linux

- Debian / Ubuntu：
  ```bash
  sudo apt update
  sudo apt install git -y
  ```
- Fedora：
  ```bash
  sudo dnf install git -y
  ```
- Arch：
  ```bash
  sudo pacman -S git
  ```

校验命令：

```bash
git --version
```

---

## 3. 安装 uv

`uv` 是 Astral 推出的 Python 包管理与虚拟环境工具，可替代 `pip` + `virtualenv` 的组合。

### 3.1 macOS / Linux

1. 执行官方安装脚本：
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
2. 根据终端输出提示，将 `~/.cargo/bin`（或脚本提示的路径）加入 `PATH`。
3. 校验安装：
   ```bash
   uv --version
   ```

### 3.2 Windows

1. 打开 PowerShell（建议以管理员身份运行）。
2. 执行安装脚本：
   ```powershell
   irm https://astral.sh/uv/install.ps1 | iex
   ```
3. PowerShell 会提示自动将 `uv.exe` 所在目录添加到 PATH，确认后重启终端。
4. 校验安装：
   ```powershell
   uv --version
   ```

---

## 4. 安装完成后自检

在终端依次执行以下命令，确认三款工具均可用：

```bash
python3 --version   # Windows 可使用 python --version
uv --version
git --version
```

若任何命令执行失败，可按以下步骤排查：

- 确认可执行文件所在目录已加入 `PATH`。
- 重启终端会话（Windows 尤其需要）。
- macOS 用户需确保 Homebrew 安装路径已写入 `~/.zprofile` 或 `~/.zshrc`。

---

## 5. 参考资料

- [Python 官方文档](https://www.python.org/doc/)
- [Git 官方文档](https://git-scm.com/doc)
- [uv 官方指南](https://docs.astral.sh/uv/)

> 完成上述环境配置后，可返回项目文档继续执行示例 1~4 等后续步骤。
