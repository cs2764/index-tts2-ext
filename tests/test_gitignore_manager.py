"""
Tests for GitIgnoreManager

Tests the functionality of updating .gitignore files with proper exclusion patterns
for the IndexTTS2 project.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open

from indextts.github_preparation.gitignore_manager import GitIgnoreManager


class TestGitIgnoreManager:
    """Test cases for GitIgnoreManager class."""
    
    def test_init(self):
        """Test GitIgnoreManager initialization."""
        manager = GitIgnoreManager(".")
        assert manager.project_root == Path(".").resolve()
        assert manager.gitignore_path == Path(".").resolve() / ".gitignore"
    
    def test_get_required_patterns(self):
        """Test getting required gitignore patterns."""
        manager = GitIgnoreManager()
        patterns = manager.get_required_patterns()
        
        # Check that all required pattern categories are included
        assert "/outputs/" in patterns  # User-generated content
        assert "/prompts/" in patterns
        assert "/logs/" in patterns
        assert "__pycache__/" in patterns  # Python cache
        assert ".venv*/" in patterns  # Virtual environments
        assert "/checkpoints/*.pth" in patterns  # Model checkpoints
        assert "*.tmp" in patterns  # Temporary files
        assert "debug_*" in patterns  # Debug files
        
        # Ensure patterns are strings
        assert all(isinstance(p, str) for p in patterns)
        assert len(patterns) > 20  # Should have substantial number of patterns
    
    def test_read_current_gitignore_nonexistent(self):
        """Test reading gitignore when file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = GitIgnoreManager(temp_dir)
            patterns = manager.read_current_gitignore()
            assert patterns == set()
    
    def test_read_current_gitignore_existing(self):
        """Test reading existing gitignore file."""
        gitignore_content = """# Comment
__pycache__/
*.pyc
/outputs/

# Another comment
.venv/
"""
        
        with patch("builtins.open", mock_open(read_data=gitignore_content)):
            with patch.object(Path, "exists", return_value=True):
                manager = GitIgnoreManager()
                patterns = manager.read_current_gitignore()
                
                expected_patterns = {"__pycache__/", "*.pyc", "/outputs/", ".venv/"}
                assert patterns == expected_patterns
    
    def test_get_missing_patterns(self):
        """Test identifying missing patterns."""
        existing_content = "__pycache__/\n/outputs/\n"
        
        with patch("builtins.open", mock_open(read_data=existing_content)):
            with patch.object(Path, "exists", return_value=True):
                manager = GitIgnoreManager()
                missing = manager.get_missing_patterns()
                
                # Should not include patterns that already exist
                assert "__pycache__/" not in missing
                assert "/outputs/" not in missing
                
                # Should include patterns that don't exist
                assert "/prompts/" in missing
                assert "/logs/" in missing
    
    def test_validate_gitignore_complete(self):
        """Test validation when gitignore is complete."""
        manager = GitIgnoreManager()
        
        # Mock all required patterns as existing
        with patch.object(manager, 'get_missing_patterns', return_value=[]):
            result = manager.validate_gitignore()
            assert result is True
    
    def test_validate_gitignore_incomplete(self):
        """Test validation when gitignore is missing patterns."""
        manager = GitIgnoreManager()
        
        # Mock some missing patterns
        missing_patterns = ["/prompts/", "*.tmp"]
        with patch.object(manager, 'get_missing_patterns', return_value=missing_patterns):
            result = manager.validate_gitignore()
            assert result is False
    
    def test_update_gitignore_dry_run(self):
        """Test dry run mode of gitignore update."""
        manager = GitIgnoreManager()
        
        missing_patterns = ["/prompts/", "*.tmp"]
        with patch.object(manager, 'get_missing_patterns', return_value=missing_patterns):
            result = manager.update_gitignore(dry_run=True)
            assert result is True  # Should return True indicating changes would be made
    
    def test_update_gitignore_no_changes_needed(self):
        """Test update when no changes are needed."""
        manager = GitIgnoreManager()
        
        with patch.object(manager, 'get_missing_patterns', return_value=[]):
            result = manager.update_gitignore()
            assert result is False  # No changes needed
    
    def test_update_gitignore_with_changes(self):
        """Test updating gitignore with new patterns."""
        existing_content = "# Existing content\n__pycache__/\n"
        missing_patterns = ["/prompts/", "*.tmp", "/logs/"]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = GitIgnoreManager(temp_dir)
            gitignore_path = manager.gitignore_path
            
            # Create existing gitignore
            with open(gitignore_path, 'w') as f:
                f.write(existing_content)
            
            # Mock missing patterns
            with patch.object(manager, 'get_missing_patterns', return_value=missing_patterns):
                result = manager.update_gitignore()
                
                assert result is True
                
                # Check that file was updated
                with open(gitignore_path, 'r') as f:
                    updated_content = f.read()
                
                assert "# Existing content" in updated_content
                assert "__pycache__/" in updated_content
                assert "/prompts/" in updated_content
                assert "*.tmp" in updated_content
                assert "/logs/" in updated_content
                assert "# GitHub Preparation - Additional Patterns" in updated_content
    
    def test_get_status_report(self):
        """Test getting status report."""
        manager = GitIgnoreManager()
        
        with patch.object(manager, 'get_required_patterns', return_value=['pattern1', 'pattern2']):
            with patch.object(manager, 'read_current_gitignore', return_value={'pattern1'}):
                with patch.object(manager, 'get_missing_patterns', return_value=['pattern2']):
                    with patch.object(Path, 'exists', return_value=True):
                        report = manager.get_status_report()
                        
                        assert report['gitignore_exists'] is True
                        assert report['total_required_patterns'] == 2
                        assert report['current_patterns_count'] == 1
                        assert report['missing_patterns_count'] == 1
                        assert report['missing_patterns'] == ['pattern2']
                        assert report['is_complete'] is False
    
    def test_pattern_categories(self):
        """Test that patterns are properly categorized."""
        manager = GitIgnoreManager()
        patterns = manager.get_required_patterns()
        
        # Test user-generated content patterns
        user_patterns = [p for p in patterns if any(x in p for x in ['/outputs/', '/prompts/', '/logs/'])]
        assert len(user_patterns) >= 3
        
        # Test Python cache patterns
        python_patterns = [p for p in patterns if any(x in p for x in ['__pycache__', '*.py', '.mypy_cache'])]
        assert len(python_patterns) >= 5
        
        # Test model checkpoint patterns
        model_patterns = [p for p in patterns if '/checkpoints/' in p or '/cache/' in p]
        assert len(model_patterns) >= 3
        
        # Test temporary file patterns
        temp_patterns = [p for p in patterns if any(x in p for x in ['*.tmp', 'debug_', '*.bak'])]
        assert len(temp_patterns) >= 4


if __name__ == "__main__":
    pytest.main([__file__])