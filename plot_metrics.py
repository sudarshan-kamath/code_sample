#!/usr/bin/env python3
"""
Plot metrics captured from RTLinux automation runs.
"""

import json
import sys
import glob
from datetime import datetime
import matplotlib.pyplot as plt

def load_latest_metrics():
    """Load the most recent metrics file."""
    metrics_files = glob.glob('metrics_*.json')

    if not metrics_files:
        print("No metrics files found!")
        print("Run rtlinux_automation.py first to generate metrics.")
        return None

    # Sort by filename (which includes timestamp)
    latest_file = sorted(metrics_files)[-1]

    print(f"Loading metrics from: {latest_file}")

    with open(latest_file, 'r') as f:
        metrics = json.load(f)

    return metrics, latest_file

def parse_metrics(metrics):
    """Parse metrics from the captured output."""
    output = metrics.get('output', '')

    # Example parsing - customize based on your actual output format
    data = {
        'messages_sent': 0,
        'messages_received': 0,
        'execution_time': metrics.get('execution_time', 0),
        'timestamp': metrics.get('timestamp', ''),
    }

    # Parse output for metrics
    for line in output.split('\n'):
        if 'Messages sent:' in line:
            try:
                data['messages_sent'] = int(line.split(':')[1].strip())
            except (IndexError, ValueError):
                pass

        if 'Server log lines:' in line:
            try:
                data['server_lines'] = int(line.split(':')[1].strip())
            except (IndexError, ValueError):
                pass

        if 'Client log lines:' in line:
            try:
                data['client_lines'] = int(line.split(':')[1].strip())
            except (IndexError, ValueError):
                pass

    return data

def plot_metrics(data, filename):
    """Create visualization of metrics."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle(f'RTLinux Test Metrics\n{data["timestamp"]}', fontsize=14)

    # Plot 1: Execution Time
    axes[0, 0].bar(['Execution Time'], [data['execution_time']], color='steelblue')
    axes[0, 0].set_ylabel('Time (seconds)')
    axes[0, 0].set_title('Total Execution Time')
    axes[0, 0].grid(axis='y', alpha=0.3)

    # Plot 2: Messages
    if 'messages_sent' in data:
        axes[0, 1].bar(['Messages Sent'], [data['messages_sent']], color='green')
        axes[0, 1].set_ylabel('Count')
        axes[0, 1].set_title('Messages Sent')
        axes[0, 1].grid(axis='y', alpha=0.3)
    else:
        axes[0, 1].text(0.5, 0.5, 'No message data',
                        ha='center', va='center', transform=axes[0, 1].transAxes)
        axes[0, 1].set_title('Messages Sent')

    # Plot 3: Log Lines
    if 'server_lines' in data and 'client_lines' in data:
        categories = ['Server', 'Client']
        values = [data.get('server_lines', 0), data.get('client_lines', 0)]
        axes[1, 0].bar(categories, values, color=['orange', 'purple'])
        axes[1, 0].set_ylabel('Lines')
        axes[1, 0].set_title('Log Lines Count')
        axes[1, 0].grid(axis='y', alpha=0.3)
    else:
        axes[1, 0].text(0.5, 0.5, 'No log data',
                        ha='center', va='center', transform=axes[1, 0].transAxes)
        axes[1, 0].set_title('Log Lines Count')

    # Plot 4: Summary Text
    axes[1, 1].axis('off')
    summary_text = f"""
    Summary Statistics:

    Execution Time: {data['execution_time']:.2f}s
    Messages Sent: {data.get('messages_sent', 'N/A')}
    Server Log Lines: {data.get('server_lines', 'N/A')}
    Client Log Lines: {data.get('client_lines', 'N/A')}

    Timestamp: {data['timestamp']}
    Source File: {filename}
    """
    axes[1, 1].text(0.1, 0.5, summary_text,
                   ha='left', va='center',
                   fontfamily='monospace',
                   fontsize=10,
                   transform=axes[1, 1].transAxes)

    plt.tight_layout()

    # Save plot
    output_file = filename.replace('.json', '_plot.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\nPlot saved to: {output_file}")

    # Show plot
    plt.show()

def compare_multiple_runs():
    """Compare metrics across multiple test runs."""
    metrics_files = sorted(glob.glob('metrics_*.json'))

    if len(metrics_files) < 2:
        print("Need at least 2 metrics files for comparison.")
        return

    print(f"Found {len(metrics_files)} metrics files for comparison")

    execution_times = []
    timestamps = []

    for mfile in metrics_files:
        with open(mfile, 'r') as f:
            metrics = json.load(f)
            execution_times.append(metrics.get('execution_time', 0))

            # Extract timestamp from filename
            ts_str = mfile.replace('metrics_', '').replace('.json', '')
            try:
                ts = datetime.strptime(ts_str, '%Y%m%d_%H%M%S')
                timestamps.append(ts)
            except ValueError:
                timestamps.append(datetime.now())

    # Plot comparison
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(timestamps, execution_times, marker='o', linewidth=2, markersize=8)
    ax.set_xlabel('Test Run Time')
    ax.set_ylabel('Execution Time (seconds)')
    ax.set_title('Execution Time Across Multiple Test Runs')
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()

    output_file = 'comparison_plot.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\nComparison plot saved to: {output_file}")

    plt.show()

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Plot RTLinux test metrics')
    parser.add_argument('-c', '--compare', action='store_true',
                       help='Compare multiple test runs')
    parser.add_argument('-f', '--file', type=str,
                       help='Specific metrics file to plot')

    args = parser.parse_args()

    if args.compare:
        compare_multiple_runs()
        return

    if args.file:
        print(f"Loading metrics from: {args.file}")
        with open(args.file, 'r') as f:
            metrics = json.load(f)
        filename = args.file
    else:
        result = load_latest_metrics()
        if result is None:
            sys.exit(1)
        metrics, filename = result

    # Parse and plot
    data = parse_metrics(metrics)
    plot_metrics(data, filename)

if __name__ == '__main__':
    main()
