import pytest
from slack_file_manager import handle_file_query

def test_handle_file_query():
    # Test with a valid file path
    valid_file_path = "path/to/your/file.txt"  # Replace with an actual file path for testing
    response = handle_file_query(valid_file_path)
    assert response is not None  # Add appropriate assertions based on expected behavior
