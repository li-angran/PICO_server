#!/usr/bin/env python3
"""Test script to verify GPU usage endpoint works."""

import subprocess
import json

def test_gpu_command():
    """Test the GPU command directly."""
    print("Testing GPU command...")
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu", 
             "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5
        )
        print(f"Return code: {result.returncode}")
        print(f"Output:\n{result.stdout}")
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for i, line in enumerate(lines):
                if line.strip():
                    parts = [p.strip() for p in line.split(',')]
                    print(f"\nGPU {i}:")
                    print(f"  Index: {parts[0]}")
                    print(f"  Name: {parts[1]}")
                    print(f"  Memory Total: {parts[2]} MB")
                    print(f"  Memory Used: {parts[3]} MB")
                    print(f"  Memory Free: {parts[4]} MB")
                    print(f"  Utilization: {parts[5]}%")
                    print(f"  Temperature: {parts[6]}°C")
        
    except FileNotFoundError:
        print("nvidia-smi not found!")
    except Exception as e:
        print(f"Error: {e}")

def test_ram_command():
    """Test the RAM command directly."""
    print("\nTesting RAM command...")
    try:
        result = subprocess.run(
            ["free", "-h"],
            capture_output=True,
            text=True,
            timeout=5
        )
        print(f"Return code: {result.returncode}")
        print(f"Output:\n{result.stdout}")
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                print("\nParsed RAM info:")
                mem_line = lines[1].split()
                print(f"  Total: {mem_line[1]}")
                print(f"  Used: {mem_line[2]}")
                print(f"  Free: {mem_line[3]}")
                print(f"  Available: {mem_line[6] if len(mem_line) > 6 else mem_line[3]}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_ram_command()
    test_gpu_command()
