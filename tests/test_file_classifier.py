#!/usr/bin/env python3
"""
Unit tests for the FileClassifier class.

Tests the file classification system to ensure it correctly categorizes
project files according to the GitHub preparation requirements.
"""

import unittest
import tempfile
import os
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from indextts.github_preparation.file_classifier import (
    FileClassifier, FileType, FileAction, FileInfo
)


class TestFileClassifier(unittest.TestCase):
    """Test cases for FileClassifier."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.classifier = FileClassifier(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_source_code_classification(self):
        """Test classification of source code files."""
        # Test core package files
        test_cases = [
            ("indextts/cli.py", FileType.SOURCE_CODE, True, FileAction.NEVER_TOUCH),
            ("indextts/infer.py", FileType.SOURCE_CODE, True, FileAction.NEVER_TOUCH),
            ("webui.py", FileType.SOURCE_CODE, True, FileAction.NEVER_TOUCH),
            ("pyproject.toml", FileType.SOURCE_CODE, True, FileAction.NEVER_TOUCH),
        ]
        
        for file_path, expected_type, expected_essential, expected_action in test_cases:
            with self.subTest(file_path=file_path):
                # Create test file
                full_path = Path(self.temp_dir) / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.touch()
                
                # Classify file
                file_info = self.classifier.classify_file(str(full_path))
                
                self.assertEqual(file_info.file_type, expected_type)
                self.assertEqual(file_info.is_essential, expected_essential)
                self.assertEqual(file_info.action, expected_action)
    
    def test_test_file_classification(self):
        """Test classification of test files."""
        test_cases = [
            ("tests/test_example.py", FileType.TEST_FILE, False, FileAction.KEEP),
            ("test_root_level.py", FileType.TEST_FILE, False, FileAction.RELOCATE),
            ("example_test.py", FileType.TEST_FILE, False, FileAction.RELOCATE),
        ]
        
        for file_path, expected_type, expected_essential, expected_action in test_cases:
            with self.subTest(file_path=file_path):
                # Create test file
                full_path = Path(self.temp_dir) / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.touch()
                
                # Classify file
                file_info = self.classifier.classify_file(str(full_path))
                
                self.assertEqual(file_info.file_type, expected_type)
                self.assertEqual(file_info.is_essential, expected_essential)
                self.assertEqual(file_info.action, expected_action)
                
                # Check relocation target for root-level tests
                if expected_action == FileAction.RELOCATE:
                    expected_target = f"tests/{Path(file_path).name}"
                    self.assertEqual(file_info.target_location, expected_target)
    
    def test_temporary_file_classification(self):
        """Test classification of temporary and debug files."""
        test_cases = [
            ("debug_test.py", FileType.DEBUG, False, FileAction.DELETE),
            ("debug_output.wav", FileType.DEBUG, False, FileAction.DELETE),
            ("test_output.wav", FileType.TEMPORARY, False, FileAction.DELETE),
        ]
        
        for file_path, expected_type, expected_essential, expected_action in test_cases:
            with self.subTest(file_path=file_path):
                # Create test file
                full_path = Path(self.temp_dir) / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.touch()
                
                # Classify file
                file_info = self.classifier.classify_file(str(full_path))
                
                self.assertEqual(file_info.file_type, expected_type)
                self.assertEqual(file_info.is_essential, expected_essential)
                self.assertEqual(file_info.action, expected_action)
    
    def test_model_checkpoint_classification(self):
        """Test classification of model checkpoint files."""
        test_cases = [
            ("checkpoints/model.pth", FileType.MODEL_CHECKPOINT, False, FileAction.PRESERVE_LOCAL),
            ("checkpoints/config.yaml", FileType.CONFIGURATION, True, FileAction.KEEP),
            ("checkpoints/qwen_model.bin", FileType.MODEL_CHECKPOINT, False, FileAction.PRESERVE_LOCAL),
        ]
        
        for file_path, expected_type, expected_essential, expected_action in test_cases:
            with self.subTest(file_path=file_path):
                # Create test file
                full_path = Path(self.temp_dir) / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.touch()
                
                # Classify file
                file_info = self.classifier.classify_file(str(full_path))
                
                self.assertEqual(file_info.file_type, expected_type)
                self.assertEqual(file_info.is_essential, expected_essential)
                self.assertEqual(file_info.action, expected_action)
    
    def test_user_generated_content_classification(self):
        """Test classification of user-generated content."""
        test_cases = [
            ("outputs/generated.wav", FileType.USER_GENERATED, False, FileAction.PRESERVE_LOCAL),
            ("prompts/user_prompt.wav", FileType.USER_GENERATED, False, FileAction.PRESERVE_LOCAL),
            ("logs/app.log", FileType.USER_GENERATED, False, FileAction.PRESERVE_LOCAL),
        ]
        
        for file_path, expected_type, expected_essential, expected_action in test_cases:
            with self.subTest(file_path=file_path):
                # Create test file
                full_path = Path(self.temp_dir) / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.touch()
                
                # Classify file
                file_info = self.classifier.classify_file(str(full_path))
                
                self.assertEqual(file_info.file_type, expected_type)
                self.assertEqual(file_info.is_essential, expected_essential)
                self.assertEqual(file_info.action, expected_action)
    
    def test_virtual_environment_protection(self):
        """Test that virtual environment files are never touched."""
        test_cases = [
            (".venv/lib/python3.10/site-packages/package.py", FileType.VIRTUAL_ENV, True, FileAction.NEVER_TOUCH),
            ("venv/Scripts/activate.bat", FileType.VIRTUAL_ENV, True, FileAction.NEVER_TOUCH),
        ]
        
        for file_path, expected_type, expected_essential, expected_action in test_cases:
            with self.subTest(file_path=file_path):
                # Create test file
                full_path = Path(self.temp_dir) / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.touch()
                
                # Classify file
                file_info = self.classifier.classify_file(str(full_path))
                
                self.assertEqual(file_info.file_type, expected_type)
                self.assertEqual(file_info.is_essential, expected_essential)
                self.assertEqual(file_info.action, expected_action)
    
    def test_documentation_classification(self):
        """Test classification of documentation files."""
        test_cases = [
            ("README.md", FileType.DOCUMENTATION, True, FileAction.KEEP),
            ("docs/guide.md", FileType.DOCUMENTATION, True, FileAction.KEEP),
            ("DEPLOYMENT_GUIDE.md", FileType.DOCUMENTATION, True, FileAction.KEEP),
        ]
        
        for file_path, expected_type, expected_essential, expected_action in test_cases:
            with self.subTest(file_path=file_path):
                # Create test file
                full_path = Path(self.temp_dir) / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.touch()
                
                # Classify file
                file_info = self.classifier.classify_file(str(full_path))
                
                self.assertEqual(file_info.file_type, expected_type)
                self.assertEqual(file_info.is_essential, expected_essential)
                self.assertEqual(file_info.action, expected_action)
    
    def test_audio_sample_classification(self):
        """Test classification of audio sample files."""
        test_cases = [
            ("examples/voice_01.wav", FileType.AUDIO_SAMPLE, True, FileAction.KEEP),
            ("samples/demo.mp3", FileType.AUDIO_SAMPLE, True, FileAction.KEEP),
        ]
        
        for file_path, expected_type, expected_essential, expected_action in test_cases:
            with self.subTest(file_path=file_path):
                # Create test file
                full_path = Path(self.temp_dir) / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.touch()
                
                # Classify file
                file_info = self.classifier.classify_file(str(full_path))
                
                self.assertEqual(file_info.file_type, expected_type)
                self.assertEqual(file_info.is_essential, expected_essential)
                self.assertEqual(file_info.action, expected_action)
    
    def test_scan_project_functionality(self):
        """Test the project scanning functionality."""
        # Create a small test project structure
        test_files = [
            "indextts/test.py",
            "test_example.py",
            "debug_file.py",
            "README.md",
            "checkpoints/model.pth"
        ]
        
        for file_path in test_files:
            full_path = Path(self.temp_dir) / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.touch()
        
        # Scan project
        file_infos = self.classifier.scan_project()
        
        # Verify we got results
        self.assertGreater(len(file_infos), 0)
        
        # Verify all files are FileInfo objects
        for file_info in file_infos:
            self.assertIsInstance(file_info, FileInfo)
            self.assertIsInstance(file_info.file_type, FileType)
            self.assertIsInstance(file_info.action, FileAction)
            self.assertIsInstance(file_info.is_essential, bool)
            self.assertIsInstance(file_info.should_preserve_locally, bool)
    
    def test_grouping_functionality(self):
        """Test file grouping by type and action."""
        # Create test files
        test_files = [
            ("test1.py", FileType.TEST_FILE, FileAction.RELOCATE),
            ("src.py", FileType.SOURCE_CODE, FileAction.KEEP),
            ("debug.py", FileType.TEMPORARY, FileAction.DELETE),
        ]
        
        file_infos = []
        for file_path, file_type, action in test_files:
            file_info = FileInfo(
                path=file_path,
                file_type=file_type,
                is_essential=False,
                should_preserve_locally=False,
                target_location=None,
                action=action,
                reason="Test file"
            )
            file_infos.append(file_info)
        
        # Test grouping by type
        by_type = self.classifier.get_files_by_type(file_infos)
        self.assertIn(FileType.TEST_FILE, by_type)
        self.assertIn(FileType.SOURCE_CODE, by_type)
        self.assertIn(FileType.TEMPORARY, by_type)
        
        # Test grouping by action
        by_action = self.classifier.get_files_by_action(file_infos)
        self.assertIn(FileAction.RELOCATE, by_action)
        self.assertIn(FileAction.KEEP, by_action)
        self.assertIn(FileAction.DELETE, by_action)


if __name__ == '__main__':
    unittest.main()