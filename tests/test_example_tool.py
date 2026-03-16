"""
Tests for example_tool.py
"""

import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.example_tool import process


def test_process_success():
    """Test successful processing."""
    output_path = ".tmp/test_output.txt"
    result = process("test input", output_path)
    assert result is True
    assert os.path.exists(output_path)

    # Verify content
    with open(output_path, 'r') as f:
        content = f.read()
    assert "Processed: test input" in content


def test_process_with_subdirectory():
    """Test handling of output path with subdirectories."""
    output_path = ".tmp/subdir/output.txt"
    result = process("test", output_path)
    assert result is True
    assert os.path.exists(output_path)


def test_process_with_special_characters():
    """Test processing input with special characters."""
    output_path = ".tmp/special_test.txt"
    result = process("test with special chars: @#$%", output_path)
    assert result is True


def teardown_module():
    """Clean up test files."""
    test_files = [
        ".tmp/test_output.txt",
        ".tmp/subdir/output.txt",
        ".tmp/special_test.txt"
    ]
    for f in test_files:
        if os.path.exists(f):
            try:
                os.remove(f)
            except Exception:
                pass  # Ignore cleanup errors
