import os
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from create_directory import FileManager

class TestFileManager(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path("test_files")
        self.temp_dir = self.test_dir / "temp"
        self.notes_dir = self.test_dir / "meeting_notes"
        
        # Create test environment variables
        os.environ['SLACK_BOT_TOKEN'] = 'test-token'
        os.environ['SLACK_CHANNEL_ID'] = 'test-channel'
        
        # Initialize manager with test directories
        self.manager = FileManager()
        self.manager.temp_dir = self.temp_dir
        self.manager.notes_dir = self.notes_dir

    def tearDown(self):
        """Clean up test environment"""
        try:
            if self.test_dir.exists():
                shutil.rmtree(self.test_dir)
        except Exception as e:
            print(f"Warning: Failed to cleanup test directory: {e}")
        
        # Clean up environment variables
        for key in ['SLACK_BOT_TOKEN', 'SLACK_CHANNEL_ID']:
            os.environ.pop(key, None)

    def test_create_directory(self):
        """Test directory creation"""
        test_path = self.test_dir / "new_dir"
        self.manager.create_directory(test_path)
        self.assertTrue(test_path.exists())
        self.assertTrue(test_path.is_dir())

    def test_create_directory_permission_error(self):
        """Test directory creation with permission error"""
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            mock_mkdir.side_effect = PermissionError()
            with self.assertRaises(PermissionError):
                self.manager.create_directory(Path("/root/test"))

    @patch('slack_sdk.WebClient.files_upload')
    def test_create_file_for_slack(self, mock_upload):
        """Test file creation and upload to Slack"""
        # Mock successful upload
        mock_upload.return_value = {'file': {'id': 'test_file_id'}}
        
        # Test file creation
        file_id = self.manager.create_file_for_slack()
        
        self.assertEqual(file_id, 'test_file_id')
        self.assertTrue(self.notes_dir.exists())
        self.assertTrue(any(self.notes_dir.glob('meeting_notes_*.txt')))
        
        # Verify Slack upload was called
        mock_upload.assert_called_once()
        call_args = mock_upload.call_args[1]
        self.assertEqual(call_args['channels'], 'test-channel')
        self.assertTrue('meeting_notes_' in call_args['file'])

    @patch('slack_sdk.WebClient.files_upload')
    def test_update_file(self, mock_upload):
        """Test file update in Slack"""
        # Mock successful upload
        mock_upload.return_value = {'file': {'id': 'new_file_id'}}
        
        # Test file update
        file_id = self.manager.update_file('old_file_id')
        
        self.assertEqual(file_id, 'new_file_id')
        
        # Verify Slack upload was called
        mock_upload.assert_called_once()
        call_args = mock_upload.call_args[1]
        self.assertEqual(call_args['channels'], 'test-channel')
        self.assertTrue('updated_notes_' in call_args['file'])

    def test_cleanup_temp_files(self):
        """Test temporary file cleanup"""
        # Create a test file
        test_file = self.temp_dir / "test_file.txt"
        self.manager.create_directory(self.temp_dir)
        test_file.write_text("test content")
        
        # Test cleanup
        self.assertTrue(test_file.exists())
        self.manager.cleanup_temp_files(test_file)
        self.assertFalse(test_file.exists())

    @patch('slack_sdk.WebClient.files_upload')
    def test_slack_api_error(self, mock_upload):
        """Test handling of Slack API errors"""
        # Mock API error
        mock_upload.side_effect = Exception("Slack API Error")
        
        # Test error handling
        with self.assertRaises(Exception) as context:
            self.manager.create_file_for_slack()
        
        self.assertTrue("Error creating/uploading file" in str(context.exception))

if __name__ == "__main__":
    unittest.main()
