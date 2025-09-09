#!/bin/bash
#
# Main test script to run all unit tests for the RAG Service.
#
# This script executes pytest, which will automatically discover and run
# all tests within the 'tests/' directory, covering the core, api,
# and handlers components.
#
set -e # Exit immediately if a command exits with a non-zero status.

echo "🚀 Starting RAG Service Test Suite..."

# Navigate to the script's directory to ensure correct path context
cd "$(dirname "$0")"

# Run pytest using poetry. The -v flag provides verbose output.
poetry run pytest -v

echo "✅ Test suite completed successfully."