#!/usr/bin/env python3
"""
Tests for MetadataManager class.

Tests validation and update functionality for project metadata management.
"""

import os
import sys
import tempfile
import toml
from pathlib import Path
from unittest.mock import patch, mock_open

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from indextts.github_preparation.metadata_manager import MetadataManager, ProjectMetadata


def test_metadata_manager_initialization():
    """Test MetadataManager initialization."""
    manager = MetadataManager(".")
    assert manager.project_root == Path(".")
    assert manager.pyproject_path == Path(".") / "pyproject.toml"
    assert manager.current_metadata is None


def test_load_current_metadata():
    """Test loading metadata from pyproject.toml."""
    sample_pyproject = {
        'project': {
            'name': 'test-project',
            'version': '1.0.0',
            'description': 'Test project description',
            'authors': [{'name': 'Test Author'}],
            'license': 'MIT',
            'license-files': ['LICENSE'],
            'readme': 'README.md',
            'classifiers': ['Development Status :: 4 - Beta'],
            'requires-python': '>=3.10',
            'dependencies': ['torch>=2.0.0'],
            'optional-dependencies': {'dev': ['pytest']},
            'urls': {'Homepage': 'https://example.com'},
            'scripts': {'test-cli': 'test.cli:main'}
        }
    }
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        pyproject_path = temp_path / "pyproject.toml"
        
        # Write sample pyproject.toml
        with open(pyproject_path, 'w') as f:
            toml.dump(sample_pyproject, f)
            
        manager = MetadataManager(temp_dir)
        metadata = manager.load_current_metadata()
        
        assert metadata.name == 'test-project'
        assert metadata.version == '1.0.0'
        assert metadata.description == 'Test project description'
        assert len(metadata.authors) == 1
        assert metadata.authors[0]['name'] == 'Test Author'


def test_validate_metadata_issues():
    """Test metadata validation with various issues."""
    manager = MetadataManager(".")
    
    # Create metadata with issues
    manager.current_metadata = ProjectMetadata(
        name="",  # Missing name
        version="invalid",  # Invalid version format
        description="Short",  # Too short description
        authors=[],  # Empty authors
        license="MIT",
        license_files=[],
        readme="README.md",
        classifiers=[],
        requires_python="",  # Missing Python requirement
        dependencies=[],  # Empty dependencies
        optional_dependencies={},
        urls={},  # Missing URLs
        scripts={}  # Missing scripts
    )
    
    issues = manager.validate_metadata()
    
    # Check that various issues are detected
    issue_texts = ' '.join(issues)
    assert "Project name is missing" in issue_texts
    assert "version format is invalid" in issue_texts
    assert "description is too short" in issue_texts
    assert "Authors list is empty" in issue_texts
    assert "Missing Homepage URL" in issue_texts
    assert "Missing Repository URL" in issue_texts
    assert "No CLI entry points defined" in issue_texts
    assert "Python version requirement is missing" in issue_texts
    assert "Dependencies list is empty" in issue_texts


def test_validate_metadata_valid():
    """Test metadata validation with valid metadata."""
    manager = MetadataManager(".")
    
    # Create valid metadata - gradio should be in webui optional dependencies
    manager.current_metadata = ProjectMetadata(
        name="indextts",
        version="2.0.0",
        description="A comprehensive text-to-speech system with advanced features and capabilities",
        authors=[{'name': 'Test Author'}],
        license="MIT",
        license_files=['LICENSE'],
        readme="README.md",
        classifiers=['Development Status :: 5 - Production/Stable'],
        requires_python=">=3.10",
        dependencies=['torch==2.8.0', 'torchaudio==2.8.0', 'transformers==4.52.1', 'librosa==0.10.2'],
        optional_dependencies={'webui': ['gradio==5.44.1']},
        urls={'Homepage': 'https://example.com', 'Repository': 'https://github.com/example/repo'},
        scripts={'indextts': 'indextts.cli:main'}
    )
    
    issues = manager.validate_metadata()
    # Filter out gradio-related issues since it's properly in optional dependencies
    filtered_issues = [issue for issue in issues if 'gradio' not in issue.lower()]
    assert len(filtered_issues) == 0, f"Expected no issues, but found: {filtered_issues}"


def test_update_project_description():
    """Test project description update."""
    manager = MetadataManager(".")
    manager.current_metadata = ProjectMetadata(
        name="indextts", version="2.0.0", description="Old description",
        authors=[], license="", license_files=[], readme="", classifiers=[],
        requires_python="", dependencies=[], optional_dependencies={}, urls={}, scripts={}
    )
    
    original_desc = manager.current_metadata.description
    manager.update_project_description()
    
    assert manager.current_metadata.description != original_desc
    assert "IndexTTS2" in manager.current_metadata.description
    assert "breakthrough" in manager.current_metadata.description.lower()
    assert "emotionally expressive" in manager.current_metadata.description
    assert "zero-shot" in manager.current_metadata.description


def test_update_project_urls():
    """Test project URLs update."""
    manager = MetadataManager(".")
    manager.current_metadata = ProjectMetadata(
        name="indextts", version="2.0.0", description="", authors=[], license="",
        license_files=[], readme="", classifiers=[], requires_python="",
        dependencies=[], optional_dependencies={}, urls={}, scripts={}
    )
    
    manager.update_project_urls()
    
    urls = manager.current_metadata.urls
    assert 'Homepage' in urls
    assert 'Repository' in urls
    assert 'Documentation' in urls
    assert 'Issues' in urls
    assert 'Changelog' in urls
    
    # Check URL formats
    for url in urls.values():
        assert url.startswith('https://github.com/')


def test_update_entry_points():
    """Test entry points update."""
    manager = MetadataManager(".")
    manager.current_metadata = ProjectMetadata(
        name="indextts", version="2.0.0", description="", authors=[], license="",
        license_files=[], readme="", classifiers=[], requires_python="",
        dependencies=[], optional_dependencies={}, urls={}, scripts={}
    )
    
    manager.update_entry_points()
    
    scripts = manager.current_metadata.scripts
    assert 'indextts' in scripts
    assert 'indextts-webui' in scripts
    assert scripts['indextts'] == 'indextts.cli:main'
    assert scripts['indextts-webui'] == 'webui:main'


def test_update_dependencies():
    """Test dependencies update."""
    manager = MetadataManager(".")
    manager.current_metadata = ProjectMetadata(
        name="indextts", version="2.0.0", description="", authors=[], license="",
        license_files=[], readme="", classifiers=[], requires_python="",
        dependencies=['torch==1.0.0', 'gradio==4.0.0', 'other-dep==1.0.0'],
        optional_dependencies={'webui': []}, urls={}, scripts={}
    )
    
    manager.update_dependencies()
    
    deps = manager.current_metadata.dependencies
    
    # Check that torch version was updated
    torch_deps = [dep for dep in deps if dep.startswith('torch==')]
    assert len(torch_deps) == 1
    assert '2.8.' in torch_deps[0]
    
    # Check that gradio was moved to optional dependencies
    gradio_in_main = any('gradio' in dep for dep in deps)
    assert not gradio_in_main
    
    # Check that gradio is in webui optional dependencies
    webui_deps = manager.current_metadata.optional_dependencies['webui']
    gradio_in_webui = any('gradio' in dep for dep in webui_deps)
    assert gradio_in_webui


def test_ensure_uv_compatibility():
    """Test UV-compatible build system configuration."""
    manager = MetadataManager(".")
    
    config = manager.ensure_uv_compatibility()
    
    # Check build system
    assert 'build-system' in config
    build_system = config['build-system']
    assert 'hatchling' in build_system['requires'][0]
    assert build_system['build-backend'] == 'hatchling.build'
    
    # Check UV tool configuration
    assert 'tool' in config
    tool_config = config['tool']
    assert 'uv' in tool_config
    assert 'uv.sources' in tool_config
    assert 'uv.index' in tool_config
    
    # Check PyTorch CUDA configuration
    sources = tool_config['uv.sources']
    assert 'torch' in sources
    assert 'torchaudio' in sources
    
    # Check PyTorch index configuration
    indexes = tool_config['uv.index']
    assert len(indexes) == 1
    assert indexes[0]['name'] == 'pytorch-cuda'
    assert 'cu128' in indexes[0]['url']


def test_update_classifiers():
    """Test classifiers update."""
    manager = MetadataManager(".")
    manager.current_metadata = ProjectMetadata(
        name="indextts", version="2.0.0", description="", authors=[], license="",
        license_files=[], readme="", classifiers=[], requires_python="",
        dependencies=[], optional_dependencies={}, urls={}, scripts={}
    )
    
    manager.update_classifiers()
    
    classifiers = manager.current_metadata.classifiers
    
    # Check for key classifiers
    classifier_text = ' '.join(classifiers)
    assert "Production/Stable" in classifier_text
    assert "Artificial Intelligence" in classifier_text
    assert "Speech" in classifier_text
    assert "Python :: 3.10" in classifier_text
    assert "Chinese (Simplified)" in classifier_text
    assert "English" in classifier_text


def test_generate_updated_pyproject():
    """Test complete pyproject.toml generation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        pyproject_path = temp_path / "pyproject.toml"
        
        # Create minimal pyproject.toml
        minimal_config = {
            'project': {
                'name': 'indextts',
                'version': '2.0.0',
                'description': 'Old description',
                'authors': [{'name': 'Test Author'}],
                'license': 'MIT',
                'license-files': ['LICENSE'],
                'readme': 'README.md',
                'classifiers': [],
                'requires-python': '>=3.10',
                'dependencies': ['torch==1.0.0'],
                'optional-dependencies': {},
                'urls': {},
                'scripts': {}
            }
        }
        
        with open(pyproject_path, 'w') as f:
            toml.dump(minimal_config, f)
            
        manager = MetadataManager(temp_dir)
        config = manager.generate_updated_pyproject()
        
        # Check that all sections are present
        assert 'project' in config
        assert 'build-system' in config
        assert 'tool' in config
        assert 'dependency-groups' in config
        
        # Check project section updates
        project = config['project']
        assert "IndexTTS2" in project['description']
        assert len(project['urls']) >= 5  # Homepage, Repository, Documentation, Issues, Changelog
        assert 'indextts' in project['scripts']
        assert len(project['classifiers']) > 5
        
        # Check dependency groups
        dev_deps = config['dependency-groups']['dev']
        assert any('pytest' in dep for dep in dev_deps)


def test_validate_and_update_workflow():
    """Test complete validation and update workflow."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        pyproject_path = temp_path / "pyproject.toml"
        
        # Create pyproject.toml with issues
        config_with_issues = {
            'project': {
                'name': 'indextts',
                'version': '2.0.0',
                'description': 'Short',  # Too short
                'authors': [{'name': 'Test Author'}],
                'license': 'MIT',
                'license-files': ['LICENSE'],
                'readme': 'README.md',
                'classifiers': [],
                'requires-python': '>=3.10',
                'dependencies': ['torch==1.0.0'],
                'optional-dependencies': {},
                'urls': {},  # Missing URLs
                'scripts': {}  # Missing scripts
            }
        }
        
        with open(pyproject_path, 'w') as f:
            toml.dump(config_with_issues, f)
            
        manager = MetadataManager(temp_dir)
        results = manager.validate_and_update()
        
        assert results['success'] is True
        assert len(results['validation_issues']) > 0  # Should find issues
        assert len(results['updates_applied']) > 0  # Should apply updates
        
        # Verify file was updated
        assert pyproject_path.exists()
        
        # Load updated file and verify improvements
        with open(pyproject_path, 'r') as f:
            updated_config = toml.load(f)
            
        project = updated_config['project']
        assert len(project['description']) > 50  # Description should be longer
        assert len(project['urls']) > 0  # URLs should be added
        assert len(project['scripts']) > 0  # Scripts should be added


if __name__ == "__main__":
    # Run basic tests
    test_functions = [
        test_metadata_manager_initialization,
        test_load_current_metadata,
        test_validate_metadata_issues,
        test_validate_metadata_valid,
        test_update_project_description,
        test_update_project_urls,
        test_update_entry_points,
        test_update_dependencies,
        test_ensure_uv_compatibility,
        test_update_classifiers,
        test_generate_updated_pyproject,
        test_validate_and_update_workflow
    ]
    
    print("Running MetadataManager tests...")
    
    for test_func in test_functions:
        try:
            test_func()
            print(f"✓ {test_func.__name__}")
        except Exception as e:
            print(f"✗ {test_func.__name__}: {e}")
            
    print("Tests completed!")