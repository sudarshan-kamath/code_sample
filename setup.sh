#!/bin/bash
#
# Quick setup script for RTLinux automation
#

echo "======================================"
echo "RTLinux Automation Setup"
echo "======================================"
echo ""

# Check Python version
echo "[1/4] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✓ Found: $PYTHON_VERSION"
echo ""

# Check pip
echo "[2/4] Checking pip..."
if ! command -v pip3 &> /dev/null; then
    echo "ERROR: pip3 is not installed"
    exit 1
fi
echo "✓ pip3 is available"
echo ""

# Install requirements
echo "[3/4] Installing Python dependencies..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi
echo "✓ Dependencies installed"
echo ""

# Check telnet
echo "[4/4] Checking telnet..."
if ! command -v telnet &> /dev/null; then
    echo "WARNING: telnet not found. Please install it:"
    echo "  Ubuntu/Debian: sudo apt-get install telnet"
    echo "  Fedora/RHEL: sudo yum install telnet"
else
    echo "✓ telnet is available"
fi
echo ""

# Make scripts executable
echo "Setting execute permissions..."
chmod +x rtlinux_automation.py
chmod +x plot_metrics.py
chmod +x run_test.sh
echo "✓ Permissions set"
echo ""

echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Edit config.json with your RTLinux connection details"
echo "2. Replace client.c and server.c with your actual code"
echo "3. Run: python3 rtlinux_automation.py"
echo ""
echo "For help: python3 rtlinux_automation.py --help"
echo ""
