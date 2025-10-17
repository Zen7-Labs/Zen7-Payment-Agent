# Zen7 Payment Agent PowerShell Script
# Equivalent to run.sh but designed for Windows PowerShell

# --- 1. Default Variables ---
param(
    [Parameter(Position=0)]
    [string]$Option = "",
    
    [string]$Hostname = "",
    [string]$Port = "",
    [switch]$Help
)

# Default values
$A2A_HOST = "localhost"
$A2A_PORT = "10000"
$MCP_HOST = "localhost"
$MCP_PORT = "8015"

# --- 2. Function to Display Usage ---
function Show-Usage {
    Write-Host "Usage: .\run.ps1 <option> [flags]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  a2a     : Runs A2A as Zen7 Payment Agent server."
    Write-Host "  mcp     : Runs MCP as Zen7 Payment Agent server."
    Write-Host ""
    Write-Host "Flags (required for 'a2a' and 'mcp'):"
    Write-Host "  -Hostname <hostname> : The target hostname or IP address."
    Write-Host "  -Port <port>     : The target port number."
    Write-Host "  -Help            : Display general help, or detailed help for the chosen option (e.g., .\run.ps1 a2a -Help)."
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\run.ps1 a2a -Hostname example.com -Port 8080"
    Write-Host "  .\run.ps1 mcp -Hostname localhost -Port 8015"
    exit 1
}

# --- 2b. Function to Display Option-Specific Help ---
function Show-HelpInfo {
    param([string]$Opt)
    
    Write-Host "----------------------------------------------------"
    if ($Opt -eq "a2a") {
        Write-Host "Help Information for Option: A2A (Zen7 Payment Agent - A2A)"
        Write-Host "Purpose: The A2A (Agent-to-Agent) option runs the Zen7 Payment Agent server intended for direct agent communication."
        Write-Host "Default Host: $A2A_HOST"
        Write-Host "Default Port: $A2A_PORT"
        Write-Host ""
        Write-Host "Required Flags:"
        Write-Host "  -Hostname : Sets the target hostname/IP for the A2A server."
        Write-Host "  -Port : Sets the target port for the A2A server."
        Write-Host ""
        Write-Host "Execution will be:"
        Write-Host "  uv run a2a_server --host `$A2A_HOST --port `$A2A_PORT"
    }
    elseif ($Opt -eq "mcp") {
        Write-Host "Help Information for Option: MCP (Zen7 Payment Agent - MCP)"
        Write-Host "Purpose: The MCP (Master Control Program) option runs the Zen7 Payment Agent server for master control and orchestration."
        Write-Host "Default Host: $MCP_HOST"
        Write-Host "Default Port: $MCP_PORT"
        Write-Host ""
        Write-Host "Required Flags:"
        Write-Host "  -Hostname : Sets the target hostname/IP for the MCP server."
        Write-Host "  -Port : Sets the target port for the MCP server."
        Write-Host ""
        Write-Host "Execution will be:"
        Write-Host "  uv run mcp_server --host `$MCP_HOST --port `$MCP_PORT"
    }
    else {
        Write-Host "No detailed help available for option: '$Opt'."
    }
    Write-Host "----------------------------------------------------"
    exit 0
}

# --- 3. Argument Processing ---

# Check for standalone help
if ($Help -and [string]::IsNullOrEmpty($Option)) {
    Show-Usage
}

# Validate option
if ([string]::IsNullOrEmpty($Option)) {
    Write-Error "ERROR: No option (a2a or mcp) specified."
    Show-Usage
}

if ($Option -ne "a2a" -and $Option -ne "mcp") {
    Write-Error "ERROR: Invalid option '$Option'. Must be 'a2a' or 'mcp'."
    Show-Usage
}

# Check for option-specific help
if ($Help -and -not [string]::IsNullOrEmpty($Option)) {
    Show-HelpInfo $Option
}

# --- 4. Validate and Set Host/Port ---

# Validate that host and port are provided
if ([string]::IsNullOrEmpty($Hostname) -or [string]::IsNullOrEmpty($Port)) {
    Write-Error "ERROR: The '$Option' option requires both -Hostname and -Port parameters."
    Show-Usage
}

# Set the appropriate host and port based on option
if ($Option -eq "a2a") {
    $A2A_HOST = $Hostname
    $A2A_PORT = $Port
}
elseif ($Option -eq "mcp") {
    $MCP_HOST = $Hostname
    $MCP_PORT = $Port
}

# --- 5. Server Execution Function ---
function Start-Server {
    Write-Host "Starting Zen7 Payment Server..."
    
    # Start the main server in background
    try {
        $serverProcess = Start-Process -FilePath "uv" -ArgumentList "run", "server.py" -RedirectStandardOutput "run.log" -RedirectStandardError "run_error.log" -PassThru -NoNewWindow
        $Global:ZEN7_SERVER_PID = $serverProcess.Id
        Write-Host "Zen7 Payment Server started with PID: $Global:ZEN7_SERVER_PID"
    }
    catch {
        Write-Warning "Could not start background server: $($_.Exception.Message)"
        $Global:ZEN7_SERVER_PID = $null
    }
    
    try {
        if ($Option -eq "a2a") {
            Write-Host "Running A2A Server Command: uv run a2a_server --host $A2A_HOST --port $A2A_PORT"
            & uv run a2a_server --host $A2A_HOST --port $A2A_PORT
        }
        elseif ($Option -eq "mcp") {
            Write-Host "Running MCP Server Command: uv run mcp_server --host $MCP_HOST --port $MCP_PORT"
            & uv run mcp_server --host $MCP_HOST --port $MCP_PORT
        }
    }
    finally {
        # Stop the main server
        if ($Global:ZEN7_SERVER_PID) {
            Write-Host "Stopping Zen7 Payment Server (PID $Global:ZEN7_SERVER_PID)..."
            try {
                Stop-Process -Id $Global:ZEN7_SERVER_PID -Force -ErrorAction SilentlyContinue
                Write-Host "Zen7 Payment Server stopped."
            }
            catch {
                Write-Warning "Could not stop server process: $($_.Exception.Message)"
            }
        }
        else {
            Write-Host "No background server process to stop."
        }
    }
}

# --- 6. Execution Block ---

if ($Option -eq "a2a") {
    Write-Host "--- Initialize A2A Server ---"
    Write-Host "A2A Target Host: $A2A_HOST"
    Write-Host "A2A Target Port: $A2A_PORT"
    Start-Server
    Write-Host "A2A Server execution finished."
}
elseif ($Option -eq "mcp") {
    Write-Host "--- Initializing MCP Server ---"
    Write-Host "MCP Target Host: $MCP_HOST"
    Write-Host "MCP Target Port: $MCP_PORT"
    Start-Server
    Write-Host "MCP Server execution finished."
}

# Exit successfully
exit 0