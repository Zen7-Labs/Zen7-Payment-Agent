#!/bin/bash
set -e
# --- 1. Default Variables ---
ACTION=""
OPTION=""
A2A_HOST="localhost"
A2A_PORT="10000"
MCP_HOST="localhost"
MCP_PORT="8015"

# --- 2. Function to Display Usage ---
usage() {
    echo "Usage: $0 <action> <option> [flags]"
    echo ""
    echo "Actions:"
    echo "  start   : Start the server."
    echo "  stop    : Stop the server."
    echo "  status  : Check server status."
    echo ""
    echo "Options (required for 'start'):"
    echo "  a2a     : Runs A2A as Zen7 Payment Agent server."
    echo "  mcp     : Runs MCP as Zen7 Payment Agent server."
    echo ""
    echo "Flags (required for 'start' with 'a2a' or 'mcp'):"
    echo "  --host <hostname> : The target hostname or IP address."
    echo "  --port <port>     : The target port number."
    echo "  --help            : Display general help."
    echo ""
    echo "Examples:"
    echo "  $0 start a2a --host 127.0.0.1 --port 10001"
    echo "  $0 stop"
    echo "  $0 status"
    exit 1
}

# --- 2b. Function to Display Option-Specific Help ---
help_info() {
    local opt="$1"
    echo "----------------------------------------------------"
    if [ "$opt" = "a2a" ]; then
        echo "Help Information for Option: A2A (Zen7 Payment Agent - A2A)"
        echo "Purpose: The A2A (Agent-to-Agent) option runs the Zen7 Payment Agent server intended for direct agent communication."
        echo "Default Host: $A2A_HOST"
        echo "Default Port: $A2A_PORT"
        echo ""
        echo "Required Flags:"
        echo "  --host : Sets the target hostname/IP for the A2A server."
        echo "  --port : Sets the target port for the A2A server."
        echo ""
        echo "Execution will be:"
        echo "  uv run a2a_server --host \$A2A_HOST --port \$A2A_PORT"
    elif [ "$opt" = "mcp" ]; then
        echo "Help Information for Option: MCP (Zen7 Payment Agent - MCP)"
        echo "Purpose: The MCP (Master Control Program) option runs the Zen7 Payment Agent server for master control and orchestration."
        echo "Default Host: $MCP_HOST"
        echo "Default Port: $MCP_PORT"
        echo ""
        echo "Required Flags:"
        echo "  --host : Sets the target hostname/IP for the MCP server."
        echo "  --port : Sets the target port for the MCP server."
        echo ""
        echo "Execution will be:"
        echo "  uv run mcp_server --host \$MCP_HOST --port \$MCP_PORT"
    else
        echo "No detailed help available for option: '$opt'."
    fi
    echo "----------------------------------------------------"
    exit 0
}

# --- 3. Argument Parsing Loop ---

# Flag to determine if option-specific help was requested (e.g., 'a2a --help')
REQUEST_HELP=false
# Flag to determine if general help was requested as a standalone flag (e.g., '--help')
STANDALONE_HELP=false

# Set ACTION based on the first argument if it's NOT a flag
if [ $# -gt 0 ] && [[ "$1" != --* ]]; then
    ACTION="$1"
    shift
fi

# Set OPTION based on the next argument if it's NOT a flag (only for start action)
if [ "$ACTION" = "start" ] && [ $# -gt 0 ] && [[ "$1" != --* ]]; then
    OPTION="$1"
    shift
fi

# Process flags using a standard 'while' loop for long options
while [ "$1" != "" ]; do
    case "$1" in
        --host)
            # Check if the value is missing
            if [ -z "$2" ]; then
                echo "ERROR: --host requires a value." >&2
                usage
            fi
            # Ensure an option was provided before allowing host/port flags
            if [ -z "$OPTION" ]; then
                echo "ERROR: The --host flag must follow a valid option ('a2a' or 'mcp')." >&2
                usage
            fi
            
            # Set the host based on the current option
            if [ "$OPTION" = "a2a" ]; then
                A2A_HOST="$2"
            elif [ "$OPTION" = "mcp" ]; then
                MCP_HOST="$2"
            fi
            shift 2 # Consume --host and its value
            ;;
        --port)
            if [ -z "$2" ]; then
                echo "ERROR: --port requires a value." >&2
                usage
            fi
            
            # Ensure an option was provided before allowing host/port flags
            if [ -z "$OPTION" ]; then
                echo "ERROR: The --port flag must follow a valid option ('a2a' or 'mcp')." >&2
                usage
            fi

            # Set the port based on the current option
            if [ "$OPTION" = "a2a" ]; then
                A2A_PORT="$2"
            elif [ "$OPTION" = "mcp" ]; then
                MCP_PORT="$2"
            fi
            shift 2 # Consume --port and its value
            ;;
        --help)
            # If OPTION is already set, it's option-specific help
            if [ -n "$OPTION" ]; then
                REQUEST_HELP=true
            else
                # If OPTION is empty, it's general help (standalone)
                STANDALONE_HELP=true
            fi
            shift # Consume --help
            ;;
        *)
            echo "ERROR: Unknown flag or argument: $1" >&2
            usage
            ;;
    esac
done

# --- 4. Operation Validation & Help Check ---

# 4a. Check for standalone --help (e.g., ./script.sh --help)
if $STANDALONE_HELP; then
    usage # Display the total help instruction and exit
fi

# 4b. Check for missing/invalid action
if [ -z "$ACTION" ]; then
    echo "ERROR: No action (start, stop, or status) specified." >&2
    usage
fi

if [ "$ACTION" != "start" ] && [ "$ACTION" != "stop" ] && [ "$ACTION" != "status" ]; then
    echo "ERROR: Invalid action '$ACTION'. Must be 'start', 'stop', or 'status'." >&2
    usage
fi

# 4c. For start action, validate option
if [ "$ACTION" = "start" ]; then
    if [ -z "$OPTION" ]; then
        echo "ERROR: No option (a2a or mcp) specified for start action." >&2
        usage
    fi
    
    if [ "$OPTION" != "a2a" ] && [ "$OPTION" != "mcp" ]; then
        echo "ERROR: Invalid option '$OPTION'. Must be 'a2a' or 'mcp'." >&2
        usage
    fi
    
    # If option-specific --help was requested
    if $REQUEST_HELP; then
        help_info "$OPTION"
    fi
fi

# --- 5. Server Execution Function ---
# NOTE: ZEN7_SERVER_HOST and ZEN7_SERVER_PORT are assumed to be environment variables
# or defined elsewhere outside this script block, as they are not initialized here.
start_server() {
    echo "Starting Zen7 Payment Server..."
    # The 'uvicorn' command is commented out to prevent actual execution errors 
    # if 'server:app' or required variables are missing in the test environment.
    uv run server.py > run.log 2>&1 &
    ZEN7_SERVER_PID=$!
    echo $ZEN7_SERVER_PID > .zen7_server.pid
    
    # Wait a moment for the server to start
    sleep 2
    
    if [ "$OPTION" = "a2a" ]; then
        echo "Running A2A Server Command: uv run a2a_server --host $A2A_HOST --port $A2A_PORT"
        nohup uv run a2a_server --host $A2A_HOST --port $A2A_PORT > a2a_server.log 2>&1 &
        A2A_SERVER_PID=$!
        echo $A2A_SERVER_PID > .a2a_server.pid
        
        # Wait a moment and check if the process is still running
        sleep 3
        if ps -p $A2A_SERVER_PID > /dev/null; then
            echo "✓ A2A Server started successfully (PID: $A2A_SERVER_PID)"
            echo "✓ Zen7 Payment Server running (PID: $ZEN7_SERVER_PID)"
            echo "✓ Server logs: a2a_server.log"
            echo "✓ To stop: kill $A2A_SERVER_PID $ZEN7_SERVER_PID"
            return 0
        else
            echo "✗ A2A Server failed to start. Check a2a_server.log for details."
            kill $ZEN7_SERVER_PID 2>/dev/null
            return 1
        fi
    fi
    if [ "$OPTION" = "mcp" ]; then
        echo "Running MCP Server Command: uv run mcp_server --host $MCP_HOST --port $MCP_PORT"
        nohup uv run mcp_server --host $MCP_HOST --port $MCP_PORT > mcp_server.log 2>&1 &
        MCP_SERVER_PID=$!
        echo $MCP_SERVER_PID > .mcp_server.pid
        
        # Wait a moment and check if the process is still running
        sleep 3
        if ps -p $MCP_SERVER_PID > /dev/null; then
            echo "✓ MCP Server started successfully (PID: $MCP_SERVER_PID)"
            echo "✓ Zen7 Payment Server running (PID: $ZEN7_SERVER_PID)"
            echo "✓ Server logs: mcp_server.log"
            echo "✓ To stop: kill $MCP_SERVER_PID $ZEN7_SERVER_PID"
            return 0
        else
            echo "✗ MCP Server failed to start. Check mcp_server.log for details."
            kill $ZEN7_SERVER_PID 2>/dev/null
            return 1
        fi
    fi
}

# --- 5b. Stop Server Function ---
stop_server() {
    local stopped_any=false
    
    # Function to stop a service by PID file
    stop_service() {
        local pid_file=$1
        local service_name=$2
        
        if [ -f "$pid_file" ]; then
            local pid=$(cat "$pid_file")
            if ps -p $pid > /dev/null 2>&1; then
                echo "Stopping $service_name (PID: $pid)..."
                kill $pid
                sleep 1
                if ps -p $pid > /dev/null 2>&1; then
                    echo "Force stopping $service_name..."
                    kill -9 $pid
                fi
                echo "✓ $service_name stopped."
                stopped_any=true
            else
                echo "✓ $service_name is not running (stale PID: $pid)."
            fi
            rm -f "$pid_file"
        fi
    }
    
    echo "--- Stopping Zen7 Payment Services ---"
    
    # Stop all services
    stop_service ".a2a_server.pid" "A2A Server"
    stop_service ".mcp_server.pid" "MCP Server"
    stop_service ".zen7_server.pid" "Zen7 Payment Server"
    
    if [ "$stopped_any" = false ]; then
        echo "No running services found."
    else
        echo "✓ All services stopped."
    fi
}

# --- 5c. Check Server Status Function ---
check_status() {
    echo "--- Zen7 Payment Services Status ---"
    
    local any_running=false
    
    # Function to check a service by PID file
    check_service() {
        local pid_file=$1
        local service_name=$2
        
        if [ -f "$pid_file" ]; then
            local pid=$(cat "$pid_file")
            if ps -p $pid > /dev/null 2>&1; then
                echo "✓ $service_name is running (PID: $pid)"
                any_running=true
            else
                echo "✗ $service_name is not running (stale PID: $pid)"
                rm -f "$pid_file"
            fi
        else
            echo "✗ $service_name is not running"
        fi
    }
    
    # Check all services
    check_service ".zen7_server.pid" "Zen7 Payment Server"
    check_service ".a2a_server.pid" "A2A Server"
    check_service ".mcp_server.pid" "MCP Server"
    
    echo "-----------------------------------"
    if [ "$any_running" = true ]; then
        return 0
    else
        return 1
    fi
}

# --- 6. Execution Block ---

if [ "$ACTION" = "start" ]; then
    if [ "$OPTION" = "a2a" ]; then
        # 6a. Final check that required flags were provided
        if [ -z "$A2A_HOST" ] || [ -z "$A2A_PORT" ]; then
            echo "ERROR: The '$OPTION' option requires both --host and --port flags." >&2
            usage
        fi
        
        # --- Execute A2A Logic ---
        echo "--- Initialize A2A Server ---"
        echo "A2A Target Host: $A2A_HOST"
        echo "A2A Target Port: $A2A_PORT"
        start_server
        exit_code=$?
        if [ $exit_code -eq 0 ]; then
            echo "✓ A2A Server initialization completed successfully."
        else
            echo "✗ A2A Server initialization failed."
        fi
        exit $exit_code

    elif [ "$OPTION" = "mcp" ]; then
        # 6b. Final check that required flags were provided
        if [ -z "$MCP_HOST" ] || [ -z "$MCP_PORT" ]; then
            echo "ERROR: The '$OPTION' option requires both --host and --port flags." >&2
            usage
        fi
        
        # --- Execute MCP Logic ---
        echo "--- Initializing MCP Server ---"
        echo "MCP Target Host: $MCP_HOST"
        echo "MCP Target Port: $MCP_PORT"
        start_server
        exit_code=$?
        if [ $exit_code -eq 0 ]; then
            echo "✓ MCP Server initialization completed successfully."
        else
            echo "✗ MCP Server initialization failed."
        fi
        exit $exit_code
    fi

elif [ "$ACTION" = "stop" ]; then
    stop_server
    exit 0

elif [ "$ACTION" = "status" ]; then
    check_status
    exit $?
fi

exit 0