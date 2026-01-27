#!/bin/bash

echo "=== Running flake8 on backend ==="
flake8 backend/ --count --select=E9,F63,F7,F82 --show-source --statistics
echo ""
echo "=== Running flake8 with all checks ==="
flake8 backend/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
