#!/bin/bash
# Quick launcher for Holy Calculator Interactive Mode

# Activate virtual environment (adjust path if needed)
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "CALC_env" ]; then
    source CALC_env/bin/activate
else
    echo "Warning: No virtual environment found. Using system Python."
fi

# Run interactive CLI
python3 scripts/interactive_cli.py "$@"
