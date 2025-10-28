#!/usr/bin/env python3
"""
Monitor PICO Platform experiments and system status.
"""
import os
import sys
import time
from datetime import datetime
import psutil

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Experiment

def format_bytes(bytes):
    """Format bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0

def get_gpu_info():
    """Get GPU information."""
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        return [{
            'id': gpu.id,
            'name': gpu.name,
            'memory_free': gpu.memoryFree,
            'memory_used': gpu.memoryUsed,
            'memory_total': gpu.memoryTotal,
            'load': gpu.load * 100,
            'temperature': gpu.temperature
        } for gpu in gpus]
    except:
        return []

def monitor_experiments():
    """Monitor all experiments."""
    with app.app_context():
        experiments = Experiment.query.all()
        
        print("\n" + "="*80)
        print(f"PICO Platform Status - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # System info
        print("\n[System Information]")
        print(f"CPU Usage: {psutil.cpu_percent()}%")
        print(f"Memory Usage: {psutil.virtual_memory().percent}%")
        print(f"Disk Usage: {psutil.disk_usage('/').percent}%")
        
        # GPU info
        gpus = get_gpu_info()
        if gpus:
            print("\n[GPU Information]")
            for gpu in gpus:
                print(f"GPU {gpu['id']}: {gpu['name']}")
                print(f"  Load: {gpu['load']:.1f}%")
                print(f"  Memory: {gpu['memory_used']:.0f}/{gpu['memory_total']:.0f} MB")
                if 'temperature' in gpu and gpu['temperature']:
                    print(f"  Temperature: {gpu['temperature']}°C")
        
        # Experiments
        print("\n[Experiments]")
        if not experiments:
            print("No experiments found.")
        else:
            # Group by status
            by_status = {}
            for exp in experiments:
                if exp.status not in by_status:
                    by_status[exp.status] = []
                by_status[exp.status].append(exp)
            
            for status in ['running', 'created', 'completed', 'failed', 'stopped']:
                if status in by_status:
                    print(f"\n{status.upper()}: {len(by_status[status])}")
                    for exp in by_status[status]:
                        print(f"  [{exp.id}] {exp.name}")
                        print(f"      User: {exp.user.username}")
                        print(f"      GPU: {exp.gpu_id}")
                        if exp.pid:
                            # Check if process is still running
                            try:
                                process = psutil.Process(exp.pid)
                                cpu = process.cpu_percent()
                                mem = process.memory_info().rss / 1024 / 1024  # MB
                                print(f"      PID: {exp.pid} (CPU: {cpu:.1f}%, Mem: {mem:.1f} MB)")
                            except psutil.NoSuchProcess:
                                print(f"      PID: {exp.pid} (process not found)")
                        if exp.started_at:
                            elapsed = datetime.utcnow() - exp.started_at
                            print(f"      Runtime: {elapsed}")
        
        print("\n" + "="*80 + "\n")

def monitor_loop(interval=10):
    """Monitor in a loop."""
    try:
        while True:
            monitor_experiments()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Monitor PICO Platform')
    parser.add_argument('--interval', type=int, default=10, 
                        help='Monitoring interval in seconds (default: 10)')
    parser.add_argument('--once', action='store_true',
                        help='Run once and exit')
    args = parser.parse_args()
    
    if args.once:
        monitor_experiments()
    else:
        monitor_loop(args.interval)
