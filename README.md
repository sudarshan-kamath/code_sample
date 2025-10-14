# RTLinux Automation Script

Automate building, deploying, and executing applications on RTLinux target systems using FTP and Telnet.

## Overview

This automation framework allows you to:
1. Build executables locally on Windows WSL
2. Upload binaries and scripts to RTLinux via FTP
3. Execute shell scripts on RTLinux via Telnet
4. Capture metrics and logs for analysis
5. Generate plots from captured data

## Prerequisites

### Local Machine (Windows WSL)
- Python 3.6+
- `pexpect` module: `pip install pexpect`
- GCC compiler (for building C programs)
- Telnet client

### RTLinux Target
- FTP server running (vsftpd, proftpd, etc.)
- Telnet server running (telnetd)
- Write permissions in target directory (default: `/tmp`)
- Execute permissions for uploaded binaries

## Installation

1. Install required Python packages:
```bash
pip install pexpect
```

2. Verify telnet is available:
```bash
which telnet
```

## Configuration

Edit `config.json` to match your environment:

```json
{
  "build": {
    "commands": [
      {
        "command": "gcc -o client.out client.c",
        "output": "client.out"
      },
      {
        "command": "gcc -o server.out server.c",
        "output": "server.out"
      }
    ]
  },
  "ftp": {
    "host": "192.168.1.100",        // Your RTLinux IP
    "port": 21,
    "username": "your_username",     // FTP username
    "password": "your_password",     // FTP password
    "target_directory": "/tmp",      // Upload destination
    "timeout": 30
  },
  "telnet": {
    "host": "192.168.1.100",        // Your RTLinux IP
    "port": 23,
    "username": "your_username",     // Telnet login
    "password": "your_password",     // Telnet password
    "prompt_pattern": "[$#]\\s*",   // Shell prompt regex
    "timeout": 30
  },
  "files_to_upload": [
    {
      "local": "client.out",
      "remote": "client.out"
    },
    {
      "local": "server.out",
      "remote": "server.out"
    },
    {
      "local": "run_test.sh",
      "remote": "run_test.sh"
    }
  ],
  "execution": {
    "script_name": "run_test.sh",
    "timeout": 120,                  // Script execution timeout
    "metrics_file": "metrics.txt"    // Metrics file to download
  }
}
```

### Important Configuration Notes

**Shell Prompt Pattern:**
The `prompt_pattern` must match your RTLinux shell prompt. Common patterns:
- `[$#]\\s*` - Matches `$` or `#` followed by optional whitespace
- `root@.*[$#]\\s*` - For prompts like `root@rtlinux# `
- `.*[$#]\\s*` - Generic pattern for most shells

To find your prompt pattern, connect via telnet and note the exact prompt.

**Timeout Values:**
- `ftp.timeout`: FTP operation timeout (increase for slow networks)
- `telnet.timeout`: Login/command timeout
- `execution.timeout`: How long to wait for script completion

## Usage

### Basic Usage

Run the automation script:
```bash
python3 rtlinux_automation.py
```

This will:
1. Build `client.out` and `server.out` locally
2. Upload them to RTLinux via FTP
3. Execute `run_test.sh` via Telnet
4. Capture and save metrics

### Advanced Usage

Use custom configuration file:
```bash
python3 rtlinux_automation.py -c my_config.json
```

Enable debug mode (shows telnet session):
```bash
python3 rtlinux_automation.py -d
```

Combine options:
```bash
python3 rtlinux_automation.py -c production.json -d
```

## Output Files

The script generates several output files:

- `rtlinux_automation.log` - Detailed execution log
- `metrics_YYYYMMDD_HHMMSS.json` - Captured metrics in JSON format
- `metrics_YYYYMMDD_HHMMSS.txt` - Downloaded metrics file from RTLinux

## Customization

### Modifying Build Commands

Edit `config.json` to add compiler flags or additional builds:
```json
"build": {
  "commands": [
    {
      "command": "gcc -Wall -O2 -o client.out client.c -lpthread",
      "output": "client.out"
    }
  ]
}
```

### Modifying RTLinux Shell Script

Edit `run_test.sh` to change test behavior:
- Adjust `TEST_DURATION` for longer/shorter tests
- Modify `SERVER_PORT` for different port
- Add custom metrics collection
- Change log output format

### Adding More Files

Add entries to `files_to_upload` in `config.json`:
```json
"files_to_upload": [
  {
    "local": "config.ini",
    "remote": "config.ini"
  }
]
```

## Workflow Details

### Step 1: Build
- Compiles C source files using gcc
- Verifies output files exist
- Checks file sizes

### Step 2: FTP Upload
- Connects to RTLinux FTP server
- Uploads binaries in binary mode
- Verifies file sizes match
- Creates target directory if needed

### Step 3: Telnet Execution
- Connects via telnet
- Handles login prompts
- Sets execute permissions (`chmod +x`)
- Executes shell script
- Captures output in real-time
- Downloads metrics file

### Step 4: Metrics Collection
- Saves execution output
- Records execution time
- Downloads metrics file from RTLinux
- Generates JSON metrics file

## Metrics Analysis

After running the automation, you can analyze metrics:

```python
import json
import matplotlib.pyplot as plt

# Load metrics
with open('metrics_20250114_123456.json', 'r') as f:
    metrics = json.load(f)

# Parse and plot
# (Add your custom plotting code here)
```

## Troubleshooting

### Connection Issues

**FTP connection fails:**
- Verify FTP server is running: `systemctl status vsftpd` (on RTLinux)
- Check firewall rules
- Test manually: `ftp <rtlinux_ip>`

**Telnet connection fails:**
- Verify telnetd is running
- Check if telnet is enabled in `/etc/inetd.conf`
- Test manually: `telnet <rtlinux_ip>`

### Permission Issues

**Upload fails with permission denied:**
- Check write permissions in target directory
- Verify FTP user has access rights
- Try a different directory (e.g., `/home/username`)

**Script execution fails:**
- Ensure `chmod +x` succeeds
- Check if target directory has noexec mount option: `mount | grep /tmp`

### Script Execution Issues

**Script times out:**
- Increase `execution.timeout` in config
- Check if processes are hanging
- Add debug output to shell script

**Wrong prompt pattern:**
- Enable debug mode: `-d`
- Observe actual prompt in output
- Adjust `prompt_pattern` in config

### Build Issues

**Compilation fails:**
- Check gcc is installed: `which gcc`
- Verify source files exist
- Check for syntax errors
- Ensure cross-compilation flags are correct

## Security Notes

**Warning:** FTP and Telnet transmit credentials in plain text. Only use on trusted networks or consider alternatives:
- SFTP instead of FTP (requires SSH)
- SSH instead of Telnet (requires modifying script to use Paramiko)

## Example Session

```
$ python3 rtlinux_automation.py

============================================================
RTLinux Automation Script Started
============================================================

============================================================
STEP 1: Building executables
============================================================
Building: client.out
Command: gcc -o client.out client.c
✓ Successfully built client.out (17352 bytes)
Building: server.out
Command: gcc -o server.out server.c
✓ Successfully built server.out (18104 bytes)
All executables built successfully

============================================================
STEP 2: Uploading files via FTP
============================================================
Connecting to FTP server: 192.168.1.100
✓ FTP connected successfully
✓ Changed to directory: /tmp
Uploading: client.out -> client.out
✓ Upload verified: client.out (17352 bytes)
Uploading: server.out -> server.out
✓ Upload verified: server.out (18104 bytes)
Uploading: run_test.sh -> run_test.sh
✓ Upload verified: run_test.sh (2543 bytes)
All files uploaded successfully

============================================================
STEP 3: Executing script via Telnet
============================================================
Connecting to Telnet: 192.168.1.100
Waiting for login prompt...
Waiting for password prompt...
Waiting for shell prompt...
✓ Login successful
Changing to directory: /tmp
Setting execute permissions...
✓ Permissions set
Executing script: run_test.sh
Script timeout: 120 seconds
------------------------------------------------------------
Script output:
[Script output appears here...]
------------------------------------------------------------
✓ Script completed in 15.23 seconds
Downloading metrics file: metrics.txt
✓ Metrics downloaded to: metrics_20250114_143022.txt
Closing telnet session...
✓ Telnet session closed

✓ Metrics saved to: metrics_20250114_143022.json
============================================================
✓ Automation completed successfully in 25.67 seconds
============================================================
```

## License

MIT License - Feel free to modify and use as needed.

## Support

For issues or questions, check the logs in `rtlinux_automation.log`.
