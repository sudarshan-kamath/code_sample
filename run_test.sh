#!/bin/sh
#
# RTLinux Test Execution Script
# This script runs client and server executables and captures metrics
#

echo "=========================================="
echo "RTLinux Test Execution Script"
echo "Started at: $(date)"
echo "=========================================="
echo ""

# Configuration
METRICS_FILE="metrics.txt"
SERVER_PORT=8080
TEST_DURATION=10

# Initialize metrics file
echo "Test Run: $(date)" > $METRICS_FILE
echo "----------------------------------------" >> $METRICS_FILE

# Start server in background
echo "[1/4] Starting server..."
./server.out $SERVER_PORT > server.log 2>&1 &
SERVER_PID=$!
echo "Server PID: $SERVER_PID"
echo "Server PID: $SERVER_PID" >> $METRICS_FILE

# Wait for server to initialize
sleep 2

# Check if server is running
if kill -0 $SERVER_PID 2>/dev/null; then
    echo "Server is running"
    echo "Server Status: Running" >> $METRICS_FILE
else
    echo "ERROR: Server failed to start"
    echo "Server Status: Failed" >> $METRICS_FILE
    cat server.log
    exit 1
fi

# Start client
echo ""
echo "[2/4] Starting client..."
./client.out localhost $SERVER_PORT > client.log 2>&1 &
CLIENT_PID=$!
echo "Client PID: $CLIENT_PID"
echo "Client PID: $CLIENT_PID" >> $METRICS_FILE

# Wait for test duration
echo ""
echo "[3/4] Running test for $TEST_DURATION seconds..."
sleep $TEST_DURATION

# Check client status
if kill -0 $CLIENT_PID 2>/dev/null; then
    echo "Client Status: Running" >> $METRICS_FILE
    CLIENT_STATUS="Running"
else
    echo "Client Status: Completed/Exited" >> $METRICS_FILE
    CLIENT_STATUS="Completed"
fi

# Check server status
if kill -0 $SERVER_PID 2>/dev/null; then
    echo "Server Status (during test): Running" >> $METRICS_FILE
    SERVER_STATUS="Running"
else
    echo "Server Status (during test): Stopped" >> $METRICS_FILE
    SERVER_STATUS="Stopped"
fi

echo "Client status: $CLIENT_STATUS"
echo "Server status: $SERVER_STATUS"

# Stop client if still running
echo ""
echo "[4/4] Stopping processes..."
if kill -0 $CLIENT_PID 2>/dev/null; then
    echo "Stopping client (PID: $CLIENT_PID)..."
    kill $CLIENT_PID 2>/dev/null
    sleep 1
    # Force kill if needed
    kill -9 $CLIENT_PID 2>/dev/null
fi

# Stop server
if kill -0 $SERVER_PID 2>/dev/null; then
    echo "Stopping server (PID: $SERVER_PID)..."
    kill $SERVER_PID 2>/dev/null
    sleep 1
    # Force kill if needed
    kill -9 $SERVER_PID 2>/dev/null
fi

# Capture logs
echo "" >> $METRICS_FILE
echo "=== SERVER LOG ===" >> $METRICS_FILE
cat server.log >> $METRICS_FILE
echo "" >> $METRICS_FILE
echo "=== CLIENT LOG ===" >> $METRICS_FILE
cat client.log >> $METRICS_FILE
echo "" >> $METRICS_FILE

# Calculate some metrics (example)
SERVER_LINES=$(wc -l < server.log)
CLIENT_LINES=$(wc -l < client.log)

echo "Metrics Summary:" >> $METRICS_FILE
echo "  Server log lines: $SERVER_LINES" >> $METRICS_FILE
echo "  Client log lines: $CLIENT_LINES" >> $METRICS_FILE
echo "  Test duration: ${TEST_DURATION}s" >> $METRICS_FILE
echo "  End time: $(date)" >> $METRICS_FILE

# Display summary
echo ""
echo "=========================================="
echo "Test Completed"
echo "=========================================="
echo "Server log lines: $SERVER_LINES"
echo "Client log lines: $CLIENT_LINES"
echo ""
echo "Logs saved to: server.log, client.log"
echo "Metrics saved to: $METRICS_FILE"
echo ""
echo "--- Server Log ---"
cat server.log
echo ""
echo "--- Client Log ---"
cat client.log
echo ""
echo "Test completed successfully"
exit 0
