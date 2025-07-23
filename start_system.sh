#!/bin/bash

# MCP Dashboard System Startup Script
# This script starts all components of the MCP Dashboard system

set -e

# Show usage if help is requested
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "🚀 MCP Dashboard System Startup Script"
    echo "======================================"
    echo ""
    echo "Usage:"
    echo "  ./start_system.sh              - Start all services with logs saved to files"
    echo "  ./start_system.sh --show-logs  - Start all services and show logs in real-time"
    echo "  ./start_system.sh --quiet      - Start all services with minimal logging"
    echo "  ./start_system.sh --help       - Show this help message"
    echo ""
    echo "Services:"
    echo "  - MySQL MCP Server (port 8000)"
    echo "  - OpenSearch MCP Server (port 8001)"
    echo "  - Flask Backend (port 5000)"
    echo "  - React Frontend (port 3000)"
    echo ""
    echo "Log files:"
    echo "  - logs/mysql-mcp-server.log"
    echo "  - logs/opensearch-mcp-server.log"
    echo "  - logs/flask-backend.log"
    echo "  - logs/react-frontend.log"
    echo ""
    exit 0
fi

# Set logging level
LOGGING_LEVEL="ERROR"
if [ "$1" = "--quiet" ]; then
    LOGGING_LEVEL="CRITICAL"
    echo -e "${YELLOW}Running in quiet mode with minimal logging${NC}"
fi

# Export logging level for Python applications
export PYTHONLOG=$LOGGING_LEVEL

# Create logs directory if it doesn't exist
mkdir -p logs

echo "🚀 Starting MCP Dashboard System..."
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Function to wait for a service to be ready
wait_for_service() {
    local port=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    echo -e "${BLUE}Waiting for $service_name to be ready on port $port...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if check_port $port; then
            echo -e "${GREEN}✅ $service_name is ready!${NC}"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}❌ $service_name failed to start within $((max_attempts * 2)) seconds${NC}"
    return 1
}

# Check if required directories exist
if [ ! -d "mysql-mcp-server" ]; then
    echo -e "${RED}❌ mysql-mcp-server directory not found${NC}"
    exit 1
fi

if [ ! -d "opensearch-mcp-server" ]; then
    echo -e "${RED}❌ opensearch-mcp-server directory not found${NC}"
    exit 1
fi

if [ ! -d "backend" ]; then
    echo -e "${RED}❌ backend directory not found${NC}"
    exit 1
fi

if [ ! -d "frontend" ]; then
    echo -e "${RED}❌ frontend directory not found${NC}"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    exit 1
fi

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Function to start a service in the background
start_service() {
    local name=$1
    local command=$2
    local log_file="logs/${name}.log"
    
    # Create logs directory if it doesn't exist
    mkdir -p logs
    
    echo -e "${BLUE}Starting $name...${NC}"
    # Start the service and tee the output to both console and log file
    eval "$command 2>&1 | tee $log_file &"
    echo $! > "logs/${name}.pid"
}

# Function to stop a service
stop_service() {
    local name=$1
    local pid_file="logs/${name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 $pid 2>/dev/null; then
            echo -e "${YELLOW}Stopping $name (PID: $pid)...${NC}"
            kill $pid
            rm "$pid_file"
        fi
    fi
}

# Function to kill any process running on a specific port
kill_port() {
    local port=$1
    local pids=$(lsof -ti:$port 2>/dev/null)
    
    if [ ! -z "$pids" ]; then
        echo -e "${YELLOW}Killing processes running on port $port...${NC}"
        echo "$pids" | xargs kill -9
        sleep 1
        echo -e "${GREEN}✅ Port $port is now free${NC}"
    else
        echo -e "${GREEN}✅ Port $port is already free${NC}"
    fi
}

# Function to show logs in real-time
show_logs() {
    local name=$1
    local log_file="logs/${name}.log"
    
    if [ -f "$log_file" ]; then
        echo -e "${BLUE}📋 Showing logs for $name:${NC}"
        echo -e "${BLUE}================================${NC}"
        tail -f "$log_file" &
        local tail_pid=$!
        echo $tail_pid > "logs/${name}-tail.pid"
    else
        echo -e "${RED}❌ Log file not found for $name${NC}"
    fi
}

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down services...${NC}"
    
    # Stop tail processes
    for tail_pid_file in logs/*-tail.pid; do
        if [ -f "$tail_pid_file" ]; then
            local tail_pid=$(cat "$tail_pid_file")
            if kill -0 $tail_pid 2>/dev/null; then
                kill $tail_pid
            fi
            rm "$tail_pid_file"
        fi
    done
    
    # Stop main services
    stop_service "mysql-mcp-server"
    stop_service "opensearch-mcp-server"
    stop_service "flask-backend"
    stop_service "react-frontend"
    echo -e "${GREEN}✅ All services stopped${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start MCP Servers
echo -e "\n${BLUE}📡 Starting MCP Servers...${NC}"

# MCP Servers are already running on docker so we don't need to start them here
echo -e "${GREEN}✅ Assumption : MCP Servers are already running on docker${NC}. No need to start them here."

# Start MySQL MCP Server
# cd mysql-mcp-server
# start_service "mysql-mcp-server" "python3 mysql_mcp_server.py"
# cd ..

# # Start OpenSearch MCP Server
# cd opensearch-mcp-server
# start_service "opensearch-mcp-server" "python3 opensearch_mcp_server.py"
# cd ..

# Wait for MCP servers to be ready
# sleep 5

# Check if MCP servers are running
if ! check_port 8000; then
    echo -e "${RED}❌ MySQL MCP Server failed to start${NC}"
    exit 1
fi

if ! check_port 8001; then
    echo -e "${RED}❌ OpenSearch MCP Server failed to start${NC}"
    exit 1
fi

echo -e "${GREEN}✅ MCP Servers are running${NC}"

# Start Flask Backend
echo -e "\n${BLUE}🔧 Starting Flask Backend...${NC}"

# Kill any existing process on port 5000
kill_port 5000
kill_port 3000
cd backend
start_service "flask-backend" "PYTHONLOG=$LOGGING_LEVEL python3 app.py"
cd ..

# Wait for backend to be ready
wait_for_service 5000 "Flask Backend"

# Start React Frontend
echo -e "\n${BLUE}🎨 Starting React Frontend...${NC}"
cd frontend
start_service "react-frontend" "npm start"
cd ..

# Wait for frontend to be ready
wait_for_service 3000 "React Frontend"

echo -e "\n${GREEN}🎉 MCP Dashboard System is ready!${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "${GREEN}Frontend:${NC} http://localhost:3000"
echo -e "${GREEN}Backend API:${NC} http://localhost:5000"
echo -e "${GREEN}MySQL MCP:${NC} http://localhost:8000/sse"
echo -e "${GREEN}OpenSearch MCP:${NC} http://localhost:8001/sse"
echo -e "\n${YELLOW}Press Ctrl+C to stop all services${NC}"
echo -e "\n${BLUE}📋 Log files are being written to:${NC}"
echo -e "  - logs/mysql-mcp-server.log"
echo -e "  - logs/opensearch-mcp-server.log"
echo -e "  - logs/flask-backend.log"
echo -e "  - logs/react-frontend.log"

# Show logs in real-time if requested
if [ "$1" = "--show-logs" ]; then
    echo -e "\n${BLUE}📋 Showing all logs in real-time...${NC}"
    echo -e "${BLUE}================================${NC}"
    
    # Start tail processes for all log files
    for service in mysql-mcp-server opensearch-mcp-server flask-backend react-frontend; do
        show_logs "$service"
    done
    
    echo -e "\n${GREEN}✅ All logs are now being displayed in real-time${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop all services and log viewing${NC}"
fi

# Keep the script running
while true; do
    sleep 1
done 