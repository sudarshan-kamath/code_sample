#!/usr/bin/env python3
"""
RTLinux Automation Script
==========================

Automates the complete workflow for deploying and testing applications on RTLinux targets:
1. Builds executables locally (WSL/Linux)
2. Uploads binaries and scripts via FTP
3. Executes test scripts via Telnet
4. Captures metrics and logs for analysis

Author: RTLinux Automation Team
License: MIT
"""

import os
import sys
import subprocess
import time
import json
from ftplib import FTP
from datetime import datetime
import logging

try:
    import pexpect
except ImportError:
    print("ERROR: pexpect module not found. Install it with: pip install pexpect")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rtlinux_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RTLinuxAutomation:
    """Automate build, deploy, and execution on RTLinux target."""

    def __init__(self, config_file='config.json', target_name=None):
        """
        Initialize with configuration from JSON file.

        Args:
            config_file: Path to JSON configuration file
            target_name: Name of target to use (e.g., 'target1', 'target2')
        """
        self.config_file = config_file
        self.full_config = self.load_config(config_file)
        self.target_name = target_name or self.full_config.get('default_target', 'target1')
        self.config = self.select_target_config(self.target_name)
        self.metrics = {}

        logger.info(f"Selected target: {self.target_name}")
        if 'description' in self.config:
            logger.info(f"Description: {self.config['description']}")

    def load_config(self, config_file):
        """Load configuration from JSON file."""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from {config_file}")
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file {config_file} not found!")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            sys.exit(1)

    def select_target_config(self, target_name):
        """Select and return the configuration for the specified target."""
        if 'targets' not in self.full_config:
            logger.error("Configuration file missing 'targets' section!")
            sys.exit(1)

        targets = self.full_config['targets']

        if target_name not in targets:
            logger.error(f"Target '{target_name}' not found in configuration!")
            logger.error(f"Available targets: {', '.join(targets.keys())}")
            sys.exit(1)

        return targets[target_name]

    def list_targets(self):
        """List all available targets from configuration."""
        if 'targets' not in self.full_config:
            logger.error("Configuration file missing 'targets' section!")
            return

        print("\nAvailable Targets:")
        print("=" * 80)

        for name, config in self.full_config['targets'].items():
            desc = config.get('description', 'No description')
            host = config.get('telnet', {}).get('host', 'N/A')
            print(f"\n  {name}")
            print(f"    Description: {desc}")
            print(f"    Host: {host}")
            print(f"    Build: {config.get('build', {}).get('command', 'N/A')[:60]}...")

        print("\n" + "=" * 80)
        default = self.full_config.get('default_target', 'target1')
        print(f"Default target: {default}\n")

    def build_executables(self):
        """Build executables locally using the configured build command."""
        logger.info("=" * 60)
        logger.info("STEP 1: Building executables")
        logger.info("=" * 60)

        build_config = self.config.get('build', {})
        source_directory = build_config.get('source_directory', '.')
        build_command = build_config.get('command')
        output_files = build_config.get('outputs', [])

        if not build_command:
            logger.error("No build command specified in target configuration!")
            return False

        # Get absolute path for source directory
        source_dir_abs = os.path.abspath(source_directory)

        # Check if source directory exists
        if not os.path.exists(source_dir_abs):
            logger.error(f"✗ Source directory does not exist: {source_dir_abs}")
            return False

        # Save current working directory
        original_cwd = os.getcwd()

        logger.info(f"Source directory: {source_dir_abs}")
        logger.info(f"Build command: {build_command}")
        logger.info(f"Expected outputs: {', '.join(output_files)}")

        try:
            # Change to source directory
            logger.info(f"Changing to source directory: {source_dir_abs}")
            os.chdir(source_dir_abs)

            # Execute build command
            result = subprocess.run(
                build_command,
                shell=True,
                check=True,
                capture_output=True,
                text=True
            )

            if result.stdout:
                logger.info(f"Build output:\n{result.stdout}")

            if result.stderr:
                logger.warning(f"Build warnings:\n{result.stderr}")

            # Verify all output files exist (relative to source directory)
            all_exist = True
            for output_file in output_files:
                output_path = os.path.join(source_dir_abs, output_file)
                if os.path.exists(output_path):
                    size = os.path.getsize(output_path)
                    logger.info(f"✓ Successfully built {output_path} ({size} bytes)")
                else:
                    logger.error(f"✗ Expected output file not found: {output_path}")
                    all_exist = False

            # Return to original directory
            os.chdir(original_cwd)

            if not all_exist:
                return False

            logger.info("All executables built successfully\n")
            return True

        except subprocess.CalledProcessError as e:
            # Return to original directory on error
            os.chdir(original_cwd)
            logger.error(f"✗ Build failed with exit code {e.returncode}")
            logger.error(f"STDERR: {e.stderr}")
            if e.stdout:
                logger.error(f"STDOUT: {e.stdout}")
            return False
        except Exception as e:
            # Return to original directory on any other error
            os.chdir(original_cwd)
            logger.error(f"✗ Build error: {e}")
            return False

    def upload_files_ftp(self):
        """Upload executables and scripts to RTLinux via FTP."""
        logger.info("=" * 60)
        logger.info("STEP 2: Uploading files via FTP")
        logger.info("=" * 60)

        ftp_config = self.config['ftp']
        files_to_upload = self.config['files_to_upload']

        try:
            # Connect to FTP server
            logger.info(f"Connecting to FTP server: {ftp_config['host']}:{ftp_config.get('port', 21)}")
            ftp = FTP(timeout=ftp_config.get('timeout', 30))
            ftp.connect(ftp_config['host'], ftp_config.get('port', 21))
            ftp.login(ftp_config['username'], ftp_config['password'])

            logger.info(f"✓ FTP connected successfully")
            logger.info(f"FTP Welcome: {ftp.getwelcome()}")

            # Change to target directory
            target_dir = ftp_config['target_directory']
            try:
                ftp.cwd(target_dir)
                logger.info(f"✓ Changed to directory: {target_dir}")
            except Exception as e:
                logger.warning(f"Directory {target_dir} may not exist, trying to create it")
                try:
                    ftp.mkd(target_dir)
                    ftp.cwd(target_dir)
                    logger.info(f"✓ Created and changed to directory: {target_dir}")
                except Exception as e2:
                    logger.error(f"✗ Failed to create/access directory: {e2}")
                    ftp.quit()
                    return False

            # Upload each file
            for file_info in files_to_upload:
                local_file = file_info['local']
                remote_file = file_info['remote']

                if not os.path.exists(local_file):
                    logger.error(f"✗ Local file not found: {local_file}")
                    ftp.quit()
                    return False

                logger.info(f"Uploading: {local_file} -> {remote_file}")

                with open(local_file, 'rb') as f:
                    ftp.storbinary(f'STOR {remote_file}', f)

                # Verify upload
                size = ftp.size(remote_file)
                local_size = os.path.getsize(local_file)

                if size == local_size:
                    logger.info(f"✓ Upload verified: {remote_file} ({size} bytes)")
                else:
                    logger.warning(f"⚠ Size mismatch: local={local_size}, remote={size}")

            ftp.quit()
            logger.info("All files uploaded successfully\n")
            return True

        except Exception as e:
            logger.error(f"✗ FTP error: {e}")
            return False

    def execute_via_telnet(self):
        """Connect via telnet and execute the shell script."""
        logger.info("=" * 60)
        logger.info("STEP 3: Executing script via Telnet")
        logger.info("=" * 60)

        telnet_config = self.config['telnet']
        execution_config = self.config['execution']

        try:
            # Connect via telnet
            logger.info(f"Connecting to Telnet: {telnet_config['host']}:{telnet_config.get('port', 23)}")

            child = pexpect.spawn(
                f"telnet {telnet_config['host']} {telnet_config.get('port', 23)}",
                timeout=telnet_config.get('timeout', 30),
                encoding='utf-8'
            )

            # Enable logging of telnet session
            if self.full_config.get('debug', False):
                child.logfile = sys.stdout

            # Handle login
            logger.info("Waiting for login prompt...")
            child.expect(['login:', 'Login:', 'Username:'], timeout=10)
            child.sendline(telnet_config['username'])

            logger.info("Waiting for password prompt...")
            child.expect(['password:', 'Password:'], timeout=10)
            child.sendline(telnet_config['password'])

            # Wait for shell prompt
            logger.info("Waiting for shell prompt...")
            prompt_pattern = telnet_config.get('prompt_pattern', '[$#>]')
            child.expect(prompt_pattern, timeout=10)
            logger.info("✓ Login successful")

            # Navigate to target directory
            target_dir = self.config['ftp']['target_directory']
            logger.info(f"Changing to directory: {target_dir}")
            child.sendline(f'cd {target_dir}')
            child.expect(prompt_pattern, timeout=5)

            # Set execute permissions
            logger.info("Setting execute permissions...")
            # chmod_files = ' '.join([f['remote'] for f in self.config['files_to_upload']])
            # child.sendline(f'chmod +x {chmod_files}')
            # child.expect(prompt_pattern, timeout=5)
            # logger.info("✓ Permissions set")

            # Execute the shell script
            script_name = execution_config['script_name']
            script_timeout = execution_config.get('timeout', 60)

            logger.info(f"Executing script: {script_name}")
            logger.info(f"Script timeout: {script_timeout} seconds")
            logger.info("-" * 60)

            start_time = time.time()
            child.sendline(f'./{script_name}')

            # Wait for script to complete
            try:
                child.expect(prompt_pattern, timeout=script_timeout)
                execution_time = time.time() - start_time

                # Capture output
                output = child.before
                logger.info("Script output:")
                logger.info("-" * 60)
                print(output)
                logger.info("-" * 60)
                logger.info(f"✓ Script completed in {execution_time:.2f} seconds")

                # Store output for metrics parsing
                # self.metrics['output'] = output
                # self.metrics['execution_time'] = execution_time
                # self.metrics['timestamp'] = datetime.now().isoformat()
                # self.metrics['target'] = self.target_name

            except pexpect.TIMEOUT:
                logger.error(f"✗ Script execution timed out after {script_timeout} seconds")
                logger.error("Attempting to capture partial output...")
                output = child.before
                logger.info("Partial output:")
                print(output)
                child.close(force=True)
                return False

            # Optional: Download metrics file if configured
            if execution_config.get('metrics_file'):
                self.download_metrics_file(execution_config['metrics_file'])

            # Exit telnet session
            logger.info("Closing telnet session...")
            child.sendline('exit')
            child.expect(pexpect.EOF, timeout=5)
            child.close()
            logger.info("✓ Telnet session closed\n")

            return True

        except pexpect.TIMEOUT as e:
            logger.error(f"✗ Telnet timeout: {e}")
            return False
        except pexpect.EOF as e:
            logger.error(f"✗ Telnet connection closed unexpectedly: {e}")
            return False
        except Exception as e:
            logger.error(f"✗ Telnet error: {e}")
            return False

    def download_metrics_file(self, metrics_file):
        """Download metrics file from RTLinux via FTP."""
        logger.info(f"Downloading metrics file: {metrics_file}")

        ftp_config = self.config['ftp']
        target_dir = ftp_config['target_directory']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        local_path = f"metrics_{self.target_name}_{timestamp}.txt"

        try:
            ftp = FTP(timeout=ftp_config.get('timeout', 30))
            ftp.connect(ftp_config['host'], ftp_config.get('port', 21))
            ftp.login(ftp_config['username'], ftp_config['password'])
            ftp.cwd(target_dir)

            with open(local_path, 'wb') as f:
                ftp.retrbinary(f'RETR {metrics_file}', f.write)

            ftp.quit()
            logger.info(f"✓ Metrics downloaded to: {local_path}")
            self.metrics['metrics_file'] = local_path

        except Exception as e:
            logger.warning(f"⚠ Failed to download metrics file: {e}")

    def save_metrics(self):
        """Save captured metrics to JSON file."""
        if not self.metrics:
            logger.warning("No metrics to save")
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        metrics_file = f"metrics_{self.target_name}_{timestamp}.json"

        try:
            with open(metrics_file, 'w') as f:
                json.dump(self.metrics, f, indent=2)
            logger.info(f"✓ Metrics saved to: {metrics_file}")
        except Exception as e:
            logger.error(f"✗ Failed to save metrics: {e}")

    def run(self):
        """Execute the complete automation workflow."""
        logger.info("\n" + "=" * 60)
        logger.info(f"RTLinux Automation Script Started - Target: {self.target_name}")
        logger.info("=" * 60 + "\n")

        start_time = time.time()

        # Step 1: Build
        if not self.build_executables():
            logger.error("Build failed. Aborting.")
            return False

        # Step 2: Upload
        if not self.upload_files_ftp():
            logger.error("FTP upload failed. Aborting.")
            return False

        # Step 3: Execute
        if not self.execute_via_telnet():
            logger.error("Telnet execution failed.")
            return False

        # Save metrics
        self.save_metrics()

        total_time = time.time() - start_time
        logger.info("=" * 60)
        logger.info(f"✓ Automation completed successfully in {total_time:.2f} seconds")
        logger.info("=" * 60 + "\n")

        return True


def create_help_text():
    """Create comprehensive help documentation."""
    return """
RTLinux Automation Script - Complete Deployment and Testing Automation
========================================================================

SYNOPSIS
    rtlinux_automation.py [OPTIONS]

DESCRIPTION
    Automates the complete workflow for deploying and testing applications on
    RTLinux target systems. The script performs three main operations:

    1. BUILD    - Compiles source code locally (WSL/Linux)
    2. DEPLOY   - Uploads binaries and scripts via FTP
    3. EXECUTE  - Runs test scripts via Telnet and captures metrics

    All operations are configured via a JSON configuration file that supports
    multiple target systems with different build configurations.

OPTIONS
    -h, --help
        Display this help message and exit.

    -c FILE, --config FILE
        Specify configuration file (default: config.json)
        The file must be a valid JSON file containing target configurations.

    -t NAME, --target NAME
        Specify target to use (e.g., target1, target2, target3)
        If not specified, uses the default_target from configuration.

    --target1
        Shorthand for --target target1

    --target2
        Shorthand for --target target2

    --target3
        Shorthand for --target target3

    -l, --list-targets
        List all available targets from configuration and exit.
        Shows target descriptions, hosts, and build commands.

    -d, --debug
        Enable debug mode. Shows detailed telnet session output in real-time.
        Useful for troubleshooting connection and execution issues.

CONFIGURATION FILE
    The configuration file (config.json) defines multiple targets. Each target
    contains:

    - description: Human-readable description of the target
    - build: Build command and expected output files
    - ftp: FTP server connection details
    - telnet: Telnet connection details and shell prompt pattern
    - files_to_upload: List of files to transfer
    - execution: Script execution parameters and timeout

    Example structure:

    {
      "targets": {
        "target1": {
          "description": "Primary RTLinux target",
          "build": {
            "command": "gcc -o client.out client.c && gcc -o server.out server.c",
            "outputs": ["client.out", "server.out"]
          },
          "ftp": {
            "host": "192.168.1.100",
            "username": "user",
            "password": "pass",
            "target_directory": "/tmp"
          },
          ...
        }
      },
      "default_target": "target1"
    }

EXAMPLES
    Run automation using default target:
        ./rtlinux_automation.py

    Run automation on target2:
        ./rtlinux_automation.py --target2

    Run with custom configuration file:
        ./rtlinux_automation.py -c production.json --target1

    List all available targets:
        ./rtlinux_automation.py --list-targets

    Run in debug mode to see telnet session:
        ./rtlinux_automation.py --target1 --debug

    Use specific target by name:
        ./rtlinux_automation.py --target my_custom_target

WORKFLOW
    The automation follows this sequence:

    1. CONFIGURATION LOADING
       - Load JSON configuration file
       - Select target based on command-line arguments
       - Validate configuration completeness

    2. BUILD PHASE
       - Execute build command locally
       - Verify all expected output files exist
       - Check file sizes and permissions

    3. DEPLOYMENT PHASE
       - Connect to RTLinux FTP server
       - Create target directory if needed
       - Upload all specified files in binary mode
       - Verify uploaded file sizes

    4. EXECUTION PHASE
       - Connect to RTLinux via Telnet
       - Authenticate and wait for shell prompt
       - Navigate to target directory
       - Set execute permissions on uploaded files
       - Execute the specified shell script
       - Capture all output in real-time
       - Download metrics file if configured

    5. METRICS COLLECTION
       - Parse script output for metrics
       - Record execution time and timestamp
       - Save metrics to JSON file
       - Download additional metrics files from target

OUTPUT FILES
    The script generates several files:

    - rtlinux_automation.log
        Detailed log of all operations with timestamps

    - metrics_<target>_<timestamp>.json
        Metrics in JSON format for further analysis

    - metrics_<target>_<timestamp>.txt
        Downloaded metrics file from RTLinux (if configured)

EXIT STATUS
    0   Success - all operations completed successfully
    1   Failure - build, deployment, or execution failed

ENVIRONMENT
    Requires:
        - Python 3.6 or higher
        - pexpect module (pip install pexpect)
        - telnet client
        - gcc or appropriate cross-compiler for RTLinux
        - Network access to RTLinux FTP and Telnet services

TROUBLESHOOTING
    Build fails:
        - Verify gcc is installed and in PATH
        - Check source files exist
        - Review build command in configuration
        - Check compiler flags for target architecture

    FTP connection fails:
        - Verify FTP server is running on RTLinux
        - Check host, port, username, password in config
        - Test manually: ftp <host>
        - Check firewall rules

    Telnet connection fails:
        - Verify telnetd is running on RTLinux
        - Check host, port, username, password in config
        - Test manually: telnet <host>
        - Verify prompt_pattern matches actual shell prompt

    Script execution times out:
        - Increase execution.timeout in configuration
        - Use --debug to see real-time output
        - Check if script is hanging on RTLinux

    Permission denied on RTLinux:
        - Verify target_directory has write permissions
        - Check FTP user has access to directory
        - Ensure directory is not mounted with noexec

SECURITY NOTES
    WARNING: FTP and Telnet transmit credentials in plain text.

    - Only use on trusted, isolated networks
    - Consider using SFTP instead of FTP (requires SSH)
    - Consider using SSH instead of Telnet (requires Paramiko)
    - Store passwords securely (environment variables, keyring)
    - Use SSH key authentication where possible

AUTHOR
    RTLinux Automation Team

VERSION
    1.0.0

SEE ALSO
    plot_metrics.py - Plot and analyze captured metrics
    config.json - Configuration file with target definitions
"""


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='RTLinux Automation Script - Build, Deploy, and Execute',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False  # We'll add custom help
    )

    # Help and information
    info_group = parser.add_argument_group('Information')
    info_group.add_argument(
        '-h', '--help',
        action='store_true',
        help='Show this help message and exit'
    )
    info_group.add_argument(
        '-l', '--list-targets',
        action='store_true',
        help='List all available targets and exit'
    )

    # Configuration
    config_group = parser.add_argument_group('Configuration')
    config_group.add_argument(
        '-c', '--config',
        default='config.json',
        help='Configuration file (default: config.json)'
    )

    # Target selection
    target_group = parser.add_argument_group('Target Selection')
    target_group.add_argument(
        '-t', '--target',
        help='Specify target by name (e.g., target1, target2)'
    )
    target_group.add_argument(
        '--target1',
        action='store_const',
        const='target1',
        dest='target_shorthand',
        help='Use target1 (shorthand for --target target1)'
    )
    target_group.add_argument(
        '--target2',
        action='store_const',
        const='target2',
        dest='target_shorthand',
        help='Use target2 (shorthand for --target target2)'
    )
    target_group.add_argument(
        '--target3',
        action='store_const',
        const='target3',
        dest='target_shorthand',
        help='Use target3 (shorthand for --target target3)'
    )

    # Options
    options_group = parser.add_argument_group('Options')
    options_group.add_argument(
        '-d', '--debug',
        action='store_true',
        help='Enable debug mode (show telnet session)'
    )

    args = parser.parse_args()

    # Handle help
    if args.help:
        print(create_help_text())
        sys.exit(0)

    # Create automation instance (for list-targets we need to load config)
    target_name = args.target or args.target_shorthand
    automation = RTLinuxAutomation(args.config, target_name)

    # Handle list-targets
    if args.list_targets:
        automation.list_targets()
        sys.exit(0)

    # Set debug mode
    if args.debug:
        automation.full_config['debug'] = True

    # Run automation
    success = automation.run()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
