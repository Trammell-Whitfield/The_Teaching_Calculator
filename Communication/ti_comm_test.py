#!/usr/bin/env python3
import subprocess
import sys

def check_calculator():
    """Check if calculator is connected"""
    result = subprocess.run(['lsusb'], capture_output=True, text=True)
    return 'Texas Instruments' in result.stdout

def send_to_calculator(filename):
    """Send a file to the calculator"""
    try:
        result = subprocess.run(
            ['tilp', '--no-gui', '--cable', 'DirectLink', '--calc', 'TI84+', 
             filename],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)

def get_calculator_info():
    """Probe calculator and get connection info using tilp"""
    try:
        # Run tilp in no-gui mode without a file to trigger probe
        result = subprocess.run(
            ['tilp', '--no-gui', '--cable', 'DirectLink', '--calc', 'TI84+CE'],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout + result.stderr

        # Parse the output for calculator info
        info = {}
        for line in output.split('\n'):
            if 'found TI-' in line:
                # Extract model and version
                import re
                match = re.search(r'found (TI-[\w\s\+]+) on #(\d+), version <([\d.]+)>', line)
                if match:
                    info['model'] = match.group(1).strip()
                    info['port'] = match.group(2)
                    info['version'] = match.group(3)
                    break

        return bool(info), info if info else output
    except Exception as e:
        return False, str(e)

if __name__ == "__main__":
    print("Testing TI-84 Communication")
    print("=" * 40)

    if check_calculator():
        print("✓ Calculator detected via USB")

        # Get detailed calculator info via tilp probe
        print("\nProbing calculator connection...")
        success, info = get_calculator_info()

        if success and isinstance(info, dict):
            print(f"✓ Connection established")
            print(f"  Model:   {info.get('model', 'Unknown')}")
            print(f"  Port:    #{info.get('port', '?')}")
            print(f"  Version: {info.get('version', 'Unknown')}")
        else:
            print("✗ Could not get calculator info")
            if isinstance(info, str):
                # Print relevant lines from output
                for line in info.split('\n'):
                    if 'WARNING' in line or 'ERROR' in line or 'found' in line.lower():
                        print(f"  {line.strip()}")
    else:
        print("✗ Calculator not found")