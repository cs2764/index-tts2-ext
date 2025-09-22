"""
Tests for the VersionManager class.
"""

import pytest
import tempfile
import toml
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, mock_open

from indextts.github_preparation.version_manager import VersionManager


class TestVersionManager:
    """Test cases for VersionManager functionality."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory with pyproject.toml."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create a sample pyproject.toml
            pyproject_content = {
                'project': {
                    'name': 'test-project',
                    'version': '1.0.0',
                    'description': 'Test project',
                    'authors': [{'name': 'Test Author'}]
                }
            }
            
            pyproject_path = project_root / 'pyproject.toml'
            with open(pyproject_path, 'w') as f:
                toml.dump(pyproject_content, f)
                
            yield project_root
    
    def test_init(self, temp_project):
        """Test VersionManager initialization."""
        vm = VersionManager(temp_project)
        assert vm.project_root == temp_project
        assert vm.pyproject_path == temp_project / 'pyproject.toml'
        assert vm.changelog_path == temp_project / 'CHANGELOG.md'
    
    def test_get_current_version(self, temp_project):
        """Test getting current version from pyproject.toml."""
        vm = VersionManager(temp_project)
        version = vm.get_current_version()
        assert version == '1.0.0'
    
    def test_get_current_version_missing_file(self):
        """Test error handling when pyproject.toml is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            vm = VersionManager(Path(temp_dir))
            with pytest.raises(FileNotFoundError):
                vm.get_current_version()
    
    def test_get_current_version_missing_version_field(self, temp_project):
        """Test error handling when version field is missing."""
        # Create pyproject.toml without version field
        pyproject_content = {'project': {'name': 'test'}}
        pyproject_path = temp_project / 'pyproject.toml'
        with open(pyproject_path, 'w') as f:
            toml.dump(pyproject_content, f)
            
        vm = VersionManager(temp_project)
        with pytest.raises(KeyError):
            vm.get_current_version()
    
    @patch('indextts.github_preparation.version_manager.datetime')
    def test_increment_version_patch(self, mock_datetime, temp_project):
        """Test patch version increment with date suffix."""
        mock_datetime.now.return_value.strftime.return_value = '20250921'
        
        vm = VersionManager(temp_project)
        new_version = vm.increment_version('patch')
        assert new_version == '1.0.1-20250921'
    
    @patch('indextts.github_preparation.version_manager.datetime')
    def test_increment_version_minor(self, mock_datetime, temp_project):
        """Test minor version increment with date suffix."""
        mock_datetime.now.return_value.strftime.return_value = '20250921'
        
        vm = VersionManager(temp_project)
        new_version = vm.increment_version('minor')
        assert new_version == '1.1.0-20250921'
    
    @patch('indextts.github_preparation.version_manager.datetime')
    def test_increment_version_major(self, mock_datetime, temp_project):
        """Test major version increment with date suffix."""
        mock_datetime.now.return_value.strftime.return_value = '20250921'
        
        vm = VersionManager(temp_project)
        new_version = vm.increment_version('major')
        assert new_version == '2.0.0-20250921'
    
    def test_increment_version_with_existing_date_suffix(self, temp_project):
        """Test version increment when current version already has date suffix."""
        # Update pyproject.toml with version that has date suffix
        pyproject_content = {
            'project': {
                'name': 'test-project',
                'version': '1.0.0-20250920',
                'description': 'Test project'
            }
        }
        pyproject_path = temp_project / 'pyproject.toml'
        with open(pyproject_path, 'w') as f:
            toml.dump(pyproject_content, f)
        
        with patch('indextts.github_preparation.version_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = '20250921'
            
            vm = VersionManager(temp_project)
            new_version = vm.increment_version('patch')
            assert new_version == '1.0.1-20250921'
    
    def test_increment_version_invalid_format(self, temp_project):
        """Test error handling for invalid version format."""
        # Update pyproject.toml with invalid version
        pyproject_content = {
            'project': {
                'name': 'test-project',
                'version': 'invalid.version',
                'description': 'Test project'
            }
        }
        pyproject_path = temp_project / 'pyproject.toml'
        with open(pyproject_path, 'w') as f:
            toml.dump(pyproject_content, f)
        
        vm = VersionManager(temp_project)
        with pytest.raises(ValueError):
            vm.increment_version()
    
    @patch('indextts.github_preparation.version_manager.datetime')
    def test_update_pyproject_toml(self, mock_datetime, temp_project):
        """Test updating pyproject.toml with new version and metadata."""
        mock_datetime.now.return_value.strftime.return_value = '20250921'
        
        vm = VersionManager(temp_project)
        
        metadata_updates = {
            'description': 'Updated description',
            'license': 'MIT'
        }
        
        vm.update_pyproject_toml(metadata_updates=metadata_updates)
        
        # Verify the file was updated
        with open(temp_project / 'pyproject.toml', 'r') as f:
            config = toml.load(f)
        
        assert config['project']['version'] == '1.0.1-20250921'
        assert config['project']['description'] == 'Updated description'
        assert config['project']['license'] == 'MIT'
    
    def test_update_pyproject_toml_with_specific_version(self, temp_project):
        """Test updating pyproject.toml with specific version."""
        vm = VersionManager(temp_project)
        vm.update_pyproject_toml(new_version='2.5.0-20250921')
        
        # Verify the version was set correctly
        with open(temp_project / 'pyproject.toml', 'r') as f:
            config = toml.load(f)
        
        assert config['project']['version'] == '2.5.0-20250921'
    
    def test_ensure_github_metadata(self, temp_project):
        """Test that GitHub metadata is properly ensured."""
        # Create minimal pyproject.toml
        pyproject_content = {'project': {'version': '1.0.0'}}
        pyproject_path = temp_project / 'pyproject.toml'
        with open(pyproject_path, 'w') as f:
            toml.dump(pyproject_content, f)
        
        vm = VersionManager(temp_project)
        vm.update_pyproject_toml()
        
        # Verify GitHub metadata was added
        with open(pyproject_path, 'r') as f:
            config = toml.load(f)
        
        project = config['project']
        assert project['name'] == 'indextts'
        assert 'IndexTTS2' in project['description']
        assert project['authors'] == [{"name": "Bilibili IndexTTS Team"}]
        assert 'urls' in project
        assert project['urls']['Homepage'] == "https://github.com/index-tts/index-tts"
        assert 'classifiers' in project
    
    def test_validate_version_consistency_valid(self, temp_project):
        """Test version consistency validation with valid version."""
        vm = VersionManager(temp_project)
        issues = vm.validate_version_consistency()
        assert len(issues) == 0
    
    def test_validate_version_consistency_invalid_format(self, temp_project):
        """Test version consistency validation with invalid format."""
        # Update with invalid version format
        pyproject_content = {
            'project': {
                'name': 'test-project',
                'version': 'invalid',
                'description': 'Test project'
            }
        }
        pyproject_path = temp_project / 'pyproject.toml'
        with open(pyproject_path, 'w') as f:
            toml.dump(pyproject_content, f)
        
        vm = VersionManager(temp_project)
        issues = vm.validate_version_consistency()
        assert len(issues) > 0
        assert 'Invalid version format' in issues[0]
    
    def test_validate_version_consistency_with_version_mismatch(self, temp_project):
        """Test version consistency validation with version mismatch in other files."""
        vm = VersionManager(temp_project)
        
        # Create README with different version
        readme_path = temp_project / 'README.md'
        readme_path.write_text('# Project\nVersion: 2.0.0\n')
        
        issues = vm.validate_version_consistency()
        assert len(issues) > 0
        assert 'Version mismatch' in issues[0]
    
    @patch('indextts.github_preparation.version_manager.datetime')
    def test_generate_changelog_entry(self, mock_datetime, temp_project):
        """Test changelog entry generation."""
        mock_datetime.now.return_value.strftime.return_value = '2025-09-21'
        
        vm = VersionManager(temp_project)
        
        changes = ['Added new feature', 'Fixed bug']
        entry = vm.generate_changelog_entry('1.0.1-20250921', changes)
        
        assert '## [1.0.1-20250921] - 2025-09-21' in entry
        assert '- Added new feature' in entry
        assert '- Fixed bug' in entry
    
    def test_generate_changelog_entry_default_changes(self, temp_project):
        """Test changelog entry generation with default changes."""
        vm = VersionManager(temp_project)
        entry = vm.generate_changelog_entry('1.0.1-20250921')
        
        assert 'Prepared project for GitHub release' in entry
        assert 'Cleaned up development artifacts' in entry
    
    @patch('indextts.github_preparation.version_manager.datetime')
    def test_update_changelog_new_file(self, mock_datetime, temp_project):
        """Test creating new changelog file."""
        mock_datetime.now.return_value.strftime.return_value = '2025-09-21'
        
        vm = VersionManager(temp_project)
        vm.update_changelog('1.0.1-20250921', ['Test change'])
        
        changelog_path = temp_project / 'CHANGELOG.md'
        assert changelog_path.exists()
        
        content = changelog_path.read_text()
        assert '# Changelog' in content
        assert '## [1.0.1-20250921] - 2025-09-21' in content
        assert '- Test change' in content
    
    @patch('indextts.github_preparation.version_manager.datetime')
    def test_update_changelog_existing_file(self, mock_datetime, temp_project):
        """Test updating existing changelog file."""
        mock_datetime.now.return_value.strftime.return_value = '2025-09-21'
        
        # Create existing changelog
        changelog_path = temp_project / 'CHANGELOG.md'
        existing_content = """# Changelog

## [1.0.0] - 2025-09-20

### Added
- Initial release
"""
        changelog_path.write_text(existing_content)
        
        vm = VersionManager(temp_project)
        vm.update_changelog('1.0.1-20250921', ['New feature'])
        
        content = changelog_path.read_text()
        assert '## [1.0.1-20250921] - 2025-09-21' in content
        assert '- New feature' in content
        assert '## [1.0.0] - 2025-09-20' in content  # Old entry preserved
    
    def test_get_project_metadata(self, temp_project):
        """Test getting project metadata."""
        vm = VersionManager(temp_project)
        metadata = vm.get_project_metadata()
        
        assert metadata['name'] == 'test-project'
        assert metadata['version'] == '1.0.0'
        assert metadata['description'] == 'Test project'
        assert metadata['authors'] == [{'name': 'Test Author'}]


if __name__ == '__main__':
    pytest.main([__file__])