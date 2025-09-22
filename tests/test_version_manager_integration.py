"""
Integration tests for VersionManager with actual project structure.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from indextts.github_preparation.version_manager import VersionManager


class TestVersionManagerIntegration:
    """Integration tests for VersionManager with real project files."""
    
    @pytest.fixture
    def project_copy(self):
        """Create a temporary copy of the actual project for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "test_project"
            
            # Copy essential files for testing
            current_project = Path.cwd()
            project_root.mkdir()
            
            # Copy pyproject.toml
            if (current_project / "pyproject.toml").exists():
                shutil.copy2(current_project / "pyproject.toml", project_root / "pyproject.toml")
            
            # Copy README if it exists
            if (current_project / "README.md").exists():
                shutil.copy2(current_project / "README.md", project_root / "README.md")
            
            yield project_root
    
    def test_real_project_version_operations(self, project_copy):
        """Test version operations with real project structure."""
        vm = VersionManager(project_copy)
        
        # Test getting current version
        current_version = vm.get_current_version()
        assert current_version is not None
        assert len(current_version.split('.')) >= 3  # Should have at least major.minor.patch
        
        # Test version increment
        new_version = vm.increment_version('patch')
        assert new_version != current_version
        assert '-' in new_version  # Should have date suffix
        
        # Test metadata retrieval
        metadata = vm.get_project_metadata()
        assert 'name' in metadata
        assert 'version' in metadata
        assert metadata['name'] == 'indextts'
    
    def test_real_project_validation(self, project_copy):
        """Test version validation with real project structure."""
        vm = VersionManager(project_copy)
        
        # Test validation
        issues = vm.validate_version_consistency()
        # Should not have critical issues with current project structure
        critical_issues = [issue for issue in issues if 'Invalid version format' in issue]
        assert len(critical_issues) == 0
    
    def test_real_project_changelog_generation(self, project_copy):
        """Test changelog generation with real project."""
        vm = VersionManager(project_copy)
        
        current_version = vm.get_current_version()
        
        # Test changelog entry generation
        entry = vm.generate_changelog_entry(current_version)
        assert f'[{current_version}]' in entry
        assert 'GitHub release' in entry
        
        # Test changelog file creation
        vm.update_changelog(current_version, ['Test integration'])
        
        changelog_path = project_copy / 'CHANGELOG.md'
        assert changelog_path.exists()
        
        content = changelog_path.read_text()
        assert 'Test integration' in content
    
    def test_real_project_metadata_update(self, project_copy):
        """Test metadata update with real project structure."""
        vm = VersionManager(project_copy)
        
        original_version = vm.get_current_version()
        
        # Test updating with new metadata
        test_metadata = {
            'description': 'Test updated description for IndexTTS2'
        }
        
        vm.update_pyproject_toml(metadata_updates=test_metadata)
        
        # Verify the update
        updated_metadata = vm.get_project_metadata()
        assert updated_metadata['description'] == test_metadata['description']
        
        # Verify version was incremented
        new_version = updated_metadata['version']
        assert new_version != original_version
        assert '-' in new_version  # Should have date suffix


if __name__ == '__main__':
    pytest.main([__file__])