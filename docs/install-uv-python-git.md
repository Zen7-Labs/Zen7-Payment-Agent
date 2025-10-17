# uv / Python / Git Installation Guide

> Target Audience: Developers who are new to the Zen7 Payment Agent project and have not yet configured `uv`, Python 3.11+, or Git on their local machine.
>
> Objective: Complete the basic installation and verification of these three tools on macOS, Windows, and Linux.

---

## 1. Python 3.11+ Installation

### 1.1 macOS

1. Install Homebrew (skip if already installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
2. Install Python 3.11:
   ```bash
   brew install python@3.11
   ```
3. Verify version:
   ```bash
   python3 --version
   ```
   Installation is successful if it outputs `Python 3.11.x`.

### 1.2 Windows

1. Visit the [Python official download page](https://www.python.org/downloads/windows/).
2. Download the `Windows installer (64-bit)`, check **Add Python to PATH**, and run the installation wizard.
3. Verify version (in PowerShell):
   ```powershell
   python --version
   ```

### 1.3 Linux (Debian / Ubuntu)

1. Update package index and install dependencies:
   ```bash
   sudo apt update
   sudo apt install software-properties-common -y
   ```
2. Add deadsnakes PPA and install Python 3.11:
   ```bash
   sudo add-apt-repository ppa:deadsnakes/ppa -y
   sudo apt update
   sudo apt install python3.11 python3.11-venv python3.11-dev -y
   ```
3. Verify version:
   ```bash
   python3.11 --version
   ```

> For other distributions, refer to the corresponding package manager (e.g., Fedora uses `dnf install python3.11`).

---

## 2. Git Installation

### 2.1 macOS

1. Use Homebrew:
   ```bash
   brew install git
   ```
2. Verify:
   ```bash
   git --version
   ```

### 2.2 Windows

1. Visit the [Git for Windows official page](https://git-scm.com/download/win) and download the latest installer.
2. Keep default options during installation (including Git Bash and adding to PATH).
3. Verify (PowerShell or Git Bash):
   ```powershell
   git --version
   ```

### 2.3 Linux

- Debian / Ubuntu:
  ```bash
  sudo apt update
  sudo apt install git -y
  ```
- Fedora:
  ```bash
  sudo dnf install git -y
  ```
- Arch:
  ```bash
  sudo pacman -S git
  ```

Verify:

```bash
git --version
```

---

## 3. uv Installation

`uv` is a Python package management and virtual environment tool from Astral that can replace `pip` + `virtualenv`.

### 3.1 macOS / Linux

1. Run the official installation script:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
2. Follow the output prompts to add `~/.cargo/bin` (or the path indicated by the installation script) to your `PATH`.
3. Verify:
   ```bash
   uv --version
   ```

### 3.2 Windows

1. Open PowerShell (administrator privileges recommended).
2. Run the installation script:
   ```powershell
   irm https://astral.sh/uv/install.ps1 | iex
   ```
3. PowerShell will prompt to automatically add the `uv.exe` directory to PATH. Confirm and restart the terminal.
4. Verify:
   ```powershell
   uv --version
   ```

---

## 4. Post-Installation Checklist

Run the following commands in your terminal to confirm all three tools are available:

```bash
python3 --version   # or python --version on Windows
uv --version
git --version
```

If any command fails:

- Check if the executable directory has been added to `PATH`.
- Restart the terminal session (especially on Windows).
- macOS users should ensure the Homebrew installation path is written to `~/.zprofile` or `~/.zshrc`.

---

## 5. Additional Resources

- [Python Official Documentation](https://www.python.org/doc/)
- [Git Official Documentation](https://git-scm.com/doc)
- [uv Official Guide](https://docs.astral.sh/uv/)

> After completing the above environment setup, you can return to the project documentation and continue with the steps for Examples 1~4.
